import os
import logging
import neo4j
from pathlib import Path
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import VertexAILLM
from vertexai.generative_models import GenerationConfig
from neo4j_graphrag.embeddings import OpenAIEmbeddings

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GraphRAGService:
    def __init__(self):
        self.driver = None
        self.llm = None
        self.embedder = None
        self.kg_builder = None
    
    async def initialize(self):
        """Initialize Neo4j connection and GraphRAG components."""
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "admin123")
        
        self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
        
        # Set Google Cloud credentials for Vertex AI
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        generation_config = GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
        self.llm = VertexAILLM(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )
        
        # Initialize OpenAI embeddings (uses OPENAI_API_KEY from environment)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Set the API key in environment for OpenAI client
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        self.embedder = OpenAIEmbeddings()
        
        self.kg_builder = SimpleKGPipeline(
            llm=self.llm,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=True,
        )
        
        logger.info("GraphRAG service initialized")
    
    async def process_document(self, file_path: str, case_id: str):
        """Process a document and add it to the knowledge graph."""
        try:
            logger.info(f"Processing document: {file_path} for case: {case_id}")
            
            await self.kg_builder.run_async(file_path=file_path)
            
            # Tag all nodes that don't have a case_id yet with this case_id
            # This assumes nodes from this document were just created
            with self.driver.session() as session:
                # Set case_id on all nodes that don't have one yet
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.case_id IS NULL
                    SET n.case_id = $case_id, n.document_path = $file_path
                    RETURN count(n) as updated_count
                    """,
                    file_path=file_path,
                    case_id=case_id
                )
                record = result.single()
                if record:
                    logger.info(f"Tagged {record['updated_count']} nodes with case_id: {case_id}")
            
            logger.info(f"Document processed successfully: {file_path}")
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    async def get_graph_data(self, case_id: str):
        """Get graph data for visualization."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n.case_id = $case_id
                OPTIONAL MATCH (n)-[r]->(m)
                WHERE m.case_id = $case_id
                RETURN n, r, m
                LIMIT 500
                """,
                case_id=case_id
            )
            
            nodes = {}
            edges = []
            
            for record in result:
                if record["n"]:
                    node = record["n"]
                    node_id = node.element_id
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "label": node.get("name", node.get("id", "Unknown")),
                            "type": list(node.labels)[0] if node.labels else "Node"
                        }
                
                if record["m"]:
                    node = record["m"]
                    node_id = node.element_id
                    if node_id not in nodes:
                        nodes[node_id] = {
                            "id": node_id,
                            "label": node.get("name", node.get("id", "Unknown")),
                            "type": list(node.labels)[0] if node.labels else "Node"
                        }
                
                if record["r"]:
                    rel = record["r"]
                    edges.append({
                        "source": rel.start_node.element_id,
                        "target": rel.end_node.element_id,
                        "label": rel.type
                    })
            
            return {
                "nodes": list(nodes.values()),
                "edges": edges
            }
    
    async def search_context(self, query: str, case_id: str) -> str:
        """Search for relevant context in the knowledge graph."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                WHERE n.case_id = $case_id 
                AND (n.text CONTAINS $search_query OR n.name CONTAINS $search_query)
                RETURN n.text as text, n.name as name
                LIMIT 5
                """,
                case_id=case_id,
                search_query=query
            )
            
            context_parts = []
            for record in result:
                if record["text"]:
                    context_parts.append(record["text"])
                elif record["name"]:
                    context_parts.append(record["name"])
            
            return "\n\n".join(context_parts) if context_parts else "No relevant context found."
    
    async def close(self):
        """Close connections."""
        if self.llm and hasattr(self.llm, 'async_client'):
            await self.llm.async_client.close()
        if self.driver:
            self.driver.close()
