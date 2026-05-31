import uuid
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np


class SecurityVectorStore:
    def __init__(self, collection_name: str = "security_knowledge", embedding_model: str = "all-MiniLM-L6-v2"):
        self.collection_name = collection_name
        self.client = QdrantClient(":memory:")
        self.encoder = SentenceTransformer(embedding_model)
        self.vector_size = self.encoder.get_sentence_embedding_dimension()
        self._create_collection()
    
    def _create_collection(self):
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
        )
    
    def add_documents(self, documents: List[Dict]) -> List[str]:
        points = []
        ids = []
        
        for doc in documents:
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            
            text = doc.get("text", "")
            if not text:
                continue
            
            embedding = self.encoder.encode(text).tolist()
            
            payload = {
                "text": text,
                "source": doc.get("source", "unknown"),
                "category": doc.get("category", "general"),
                "metadata": doc.get("metadata", {})
            }
            
            points.append(PointStruct(id=doc_id, vector=embedding, payload=payload))
        
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
        
        return ids
    
    def search(self, query: str, limit: int = 5, filters: Optional[Dict] = None) -> List[Dict]:
        query_vector = self.encoder.encode(query).tolist()
        
        search_filter = None
        if filters:
            from qdrant_client.models import FieldCondition, MatchValue, Filter
            conditions = []
            for key, value in filters.items():
                conditions.append(FieldCondition(key=key, match=MatchValue(value=value)))
            search_filter = Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )
        
        return [
            {
                "id": result.id,
                "score": result.score,
                "text": result.payload.get("text", ""),
                "source": result.payload.get("source", "unknown"),
                "category": result.payload.get("category", "general"),
                "metadata": result.payload.get("metadata", {})
            }
            for result in results
        ]
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        result = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[doc_id]
        )
        
        if result:
            return {
                "id": result[0].id,
                "text": result[0].payload.get("text", ""),
                "source": result[0].payload.get("source", "unknown"),
                "category": result[0].payload.get("category", "general"),
                "metadata": result[0].payload.get("metadata", {})
            }
        return None
    
    def delete_document(self, doc_id: str) -> bool:
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=[doc_id]
        )
        return True
    
    def count_documents(self) -> int:
        result = self.client.count(collection_name=self.collection_name)
        return result.count
    
    def get_stats(self) -> Dict:
        collection_info = self.client.get_collection(self.collection_name)
        return {
            "total_documents": collection_info.points_count,
            "vector_size": self.vector_size,
            "collection_name": self.collection_name
        }