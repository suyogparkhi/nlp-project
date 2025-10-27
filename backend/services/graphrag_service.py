import os
import logging
import neo4j
from pathlib import Path
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.llm import VertexAILLM
from vertexai.generative_models import GenerationConfig
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever
from neo4j_graphrag.generation import GraphRAG

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class GraphRAGService:
    def __init__(self):
        self.driver = None
        self.llm = None
        self.embedder = None
        self.kg_builder = None
        self.rag = None
        self.retriever = None
    
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
        
        # Initialize OpenAI embeddings (uses OPENAI_API_KEY from environment)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        # Set the API key in environment for OpenAI client
        os.environ["OPENAI_API_KEY"] = openai_api_key
        
        self.embedder = OpenAIEmbeddings(model="text-embedding-3-large")
        
        # Initialize LLM for both ingestion and retrieval
        generation_config = GenerationConfig(
            temperature=0.0,
        )
        self.llm = VertexAILLM(
            model_name="gemini-2.5-flash",
            generation_config=generation_config
        )
        
        # Initialize KG builder for document ingestion
        kg_generation_config = GenerationConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
        kg_llm = VertexAILLM(
            model_name="gemini-2.5-flash",
            generation_config=kg_generation_config
        )
        
        self.kg_builder = SimpleKGPipeline(
            llm=kg_llm,
            driver=self.driver,
            embedder=self.embedder,
            from_pdf=True,
        )
        
        # Create vector index if it doesn't exist
        index_name = os.getenv("NEO4J_INDEX_NAME", "entity-embeddings")
        await self._ensure_vector_index(index_name)
        
        # Initialize retriever with vector index
        self.retriever = VectorRetriever(
            driver=self.driver,
            index_name=index_name,
            embedder=self.embedder
        )
        
        # Initialize GraphRAG pipeline (combines retriever + llm)
        self.rag = GraphRAG(retriever=self.retriever, llm=self.llm)
        
        logger.info("GraphRAG service initialized")
    
    async def _ensure_vector_index(self, index_name: str):
        """Create vector index if it doesn't exist."""
        with self.driver.session() as session:
            # Check if index exists
            result = session.run("SHOW INDEXES")
            existing_indexes = [record["name"] for record in result]
            
            if index_name not in existing_indexes:
                logger.info(f"Creating vector index: {index_name}")
                # Create vector index on __Entity__ nodes with embedding property
                # Dimension 3072 for text-embedding-3-large
                session.run(f"""
                    CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
                    FOR (n:__Entity__)
                    ON n.embedding
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: 3072,
                            `vector.similarity_function`: 'cosine'
                        }}
                    }}
                """)
                logger.info(f"Vector index '{index_name}' created successfully")
            else:
                logger.info(f"Vector index '{index_name}' already exists")
    
    async def process_document(self, file_path: str):
        """Process a document and add it to the knowledge graph."""
        try:
            logger.info(f"Processing document: {file_path}")
            
            await self.kg_builder.run_async(file_path=file_path)
            
            # Tag all nodes with document path
            with self.driver.session() as session:
                # Set document_path on all nodes that don't have one yet
                result = session.run(
                    """
                    MATCH (n)
                    WHERE n.document_path IS NULL
                    SET n.document_path = $file_path
                    RETURN count(n) as updated_count
                    """,
                    file_path=file_path
                )
                record = result.single()
                if record:
                    logger.info(f"Tagged {record['updated_count']} nodes with document_path")
            
            logger.info(f"Document processed successfully: {file_path}")
        except Exception as e:
            logger.error(f"Error processing document {file_path}: {e}")
            raise
    
    async def get_graph_data(self):
        """Get graph data for visualization."""
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n, r, m
                LIMIT 500
                """
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
    
    def query_graph(self, user_query: str):
        """Query the knowledge graph using VectorRetriever and GraphRAG."""
        try:
            logger.info(f"🔹 Query: {user_query}")
            
            # Use GraphRAG search (synchronous)
            response = self.rag.search(
                query_text=user_query,
                retriever_config={"top_k": 5}
            )
            
            logger.info(f"🔹 Answer: {response.answer}")
            logger.info(f"🔹 Context items: {len(response.items) if hasattr(response, 'items') else 'N/A'}")
            
            return response
        except Exception as e:
            logger.error(f"Error querying graph: {e}")
            raise
    
    async def close(self):
        """Close connections."""
        if self.llm and hasattr(self.llm, 'async_client'):
            await self.llm.async_client.close()
        if self.driver:
            self.driver.close()
