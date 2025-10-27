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
        
        # Create vector index if it doesn't exist (defaults to chunk embeddings)
        index_name = os.getenv("NEO4J_INDEX_NAME", "chunk-embeddings")
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
        """Ensure the vector index exists with correct label/property and dimensions.
        Detects the label carrying the 'embedding' property (prefers __Chunk__).
        If an index with the same name exists but mismatches, it is dropped and recreated.
        """
        with self.driver.session() as session:
            # Detect label and embedding dimension
            label, dimension = self._detect_embedding_schema(session)
            if label is None:
                # Fallback to common defaults for neo4j-graphrag chunks
                label = "__Chunk__"
            if dimension is None:
                # OpenAI text-embedding-3-large default
                dimension = 3072

            logger.info(f"Embedding schema resolved: label={label}, property=embedding, dim={dimension}")

            # Inspect existing index with this name
            info = session.run(
                """
                SHOW INDEXES YIELD name, type, labelsOrTypes, properties, state
                WHERE name = $name
                RETURN name, type, labelsOrTypes, properties, state
                """,
                name=index_name,
            ).single()

            needs_create = False
            if info is None:
                needs_create = True
            else:
                idx_type = info["type"]
                idx_labels = info["labelsOrTypes"] or []
                idx_props = info["properties"] or []
                # Validate type, label and property
                if idx_type != "VECTOR" or "embedding" not in idx_props or label not in idx_labels:
                    logger.info(
                        f"Existing index '{index_name}' mismatched (type={idx_type}, labels={idx_labels}, props={idx_props}). Recreating."
                    )
                    session.run(f"DROP INDEX `{index_name}` IF EXISTS")
                    needs_create = True

            if needs_create:
                logger.info(f"Creating vector index '{index_name}' on :{label}(embedding) with dim={dimension}")
                session.run(
                    f"""
                    CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
                    FOR (n:{label})
                    ON (n.embedding)
                    OPTIONS {{
                        indexConfig: {{
                            `vector.dimensions`: {dimension},
                            `vector.similarity_function`: 'cosine'
                        }}
                    }}
                    """
                )
                logger.info(f"Vector index '{index_name}' created successfully")
            else:
                logger.info(f"Vector index '{index_name}' already exists and matches schema")

    def _detect_embedding_schema(self, session):
        """Detect the label and embedding dimension from existing nodes.
        Prefers __Chunk__ if available. Returns (label, dimension) or (None, None).
        """
        try:
            # Prefer chunks
            rec = session.run(
                """
                MATCH (n:__Chunk__)
                WHERE n.embedding IS NOT NULL
                RETURN '__Chunk__' AS label, size(n.embedding) AS dim
                LIMIT 1
                """
            ).single()
            if rec and rec["dim"] is not None:
                return rec["label"], rec["dim"]

            # Fallback: any node with embedding
            rec = session.run(
                """
                MATCH (n)
                WHERE n.embedding IS NOT NULL
                RETURN labels(n)[0] AS label, size(n.embedding) AS dim
                LIMIT 1
                """
            ).single()
            if rec and rec["label"]:
                return rec["label"], rec["dim"]
        except Exception as e:
            logger.warning(f"Embedding schema detection failed: {e}")
        return None, None
    
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
