import os
from typing import List, Dict, Optional
from rag.vector_store import SecurityVectorStore
from rag.ingest import ingest_all_data


class LLMClient:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    def generate(self, prompt: str, system_prompt: str = "", provider: str = "openai") -> str:
        if provider == "openai" and self.openai_key:
            try:
                import openai
                client = openai.OpenAI(api_key=self.openai_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI error: {e}")
        
        if provider == "anthropic" and self.anthropic_key:
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=self.anthropic_key)
                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    temperature=0.7,
                    system=system_prompt,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            except Exception as e:
                print(f"Anthropic error: {e}")
        
        return self._fallback_generate(prompt, system_prompt)
    
    def _fallback_generate(self, prompt: str, system_prompt: str) -> str:
        return f"[Fallback Response]\n\nBased on the retrieved context, here is the analysis:\n\n{prompt[:500]}...\n\nNote: LLM API not configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables."


class RAGEngine:
    def __init__(self, vector_store: Optional[SecurityVectorStore] = None):
        self.vector_store = vector_store or SecurityVectorStore()
        self.llm = LLMClient()
        self._ensure_data_loaded()
    
    def _ensure_data_loaded(self):
        if self.vector_store.count_documents() == 0:
            print("Loading initial security data...")
            ingest_all_data(self.vector_store)
    
    def query(self, question: str, category: Optional[str] = None, top_k: int = 5) -> Dict:
        filters = {"category": category} if category else None
        
        retrieved_docs = self.vector_store.search(question, limit=top_k, filters=filters)
        
        context = "\n\n".join([
            f"[{doc['category']}] {doc['text'][:500]}..."
            for doc in retrieved_docs
        ])
        
        system_prompt = """You are a cybersecurity expert assistant. Use the provided context to answer the user's question accurately and comprehensively. If the context doesn't contain enough information, say so clearly."""
        
        prompt = f"""Context:
{context}

Question: {question}

Please provide a detailed answer based on the context above."""
        
        response = self.llm.generate(prompt, system_prompt)
        
        return {
            "question": question,
            "answer": response,
            "sources": [
                {
                    "id": doc["id"],
                    "source": doc["source"],
                    "category": doc["category"],
                    "relevance_score": doc["score"],
                    "text_preview": doc["text"][:200] + "..."
                }
                for doc in retrieved_docs
            ],
            "documents_retrieved": len(retrieved_docs)
        }
    
    def search_cve(self, cve_id: str) -> Dict:
        results = self.vector_store.search(cve_id, limit=10)
        cve_results = [r for r in results if r["category"] == "CVE"]
        
        return {
            "cve_id": cve_id,
            "found": len(cve_results) > 0,
            "results": cve_results
        }
    
    def search_exploit(self, keyword: str) -> Dict:
        results = self.vector_store.search(keyword, limit=10)
        exploit_results = [r for r in results if r["category"] == "EXPLOIT"]
        
        return {
            "keyword": keyword,
            "found": len(exploit_results) > 0,
            "results": exploit_results
        }
    
    def get_stats(self) -> Dict:
        return self.vector_store.get_stats()