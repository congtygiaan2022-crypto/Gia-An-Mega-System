import json
import os
from typing import List

class MemoryStore:
    def __init__(self, db_path="memory/memory.json"):
        self.db_path = db_path
        self.collections = {}
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.collections = json.load(f)
            except Exception:
                self.collections = {}

    def _save_db(self):
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.collections, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")

    def get_all(self, namespace: str) -> List[str]:
        return self.collections.get(namespace, [])

    def save(self, text: str, namespace: str = "javis_memory"):
        if namespace not in self.collections:
            self.collections[namespace] = []
            
        if text not in self.collections[namespace]:
            self.collections[namespace].append(text)
            self._save_db()

    def search(self, query: str, n_results: int = 5, namespace: str = "javis_memory") -> List[str]:
        collection = self.collections.get(namespace, [])
        if not collection:
            return []
            
        query_words = query.lower().split()
        scored_docs = []
        for doc in collection:
            score = sum(1 for word in query_words if word in doc.lower())
            scored_docs.append((score, doc))
            
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        results = [doc for score, doc in scored_docs if score > 0]
        if not results:
            results = collection[::-1] # return most recent if no match
            
        return results[:n_results]

global_memory = MemoryStore()
