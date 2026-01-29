import google.generativeai as genai
import json
import os
import math
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=API_KEY)

DB_FILE = "gov_docs.json"

class KnowledgeBase:
    def __init__(self):
        self.documents = []

        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                self.documents = json.load(f)
            print(f"Loaded {len(self.documents)} pages from knowledge base.")
        else:
            print("Initialized new empty Knowledge Base.")

    def _get_embedding(self, text):
        """
        Uses Google's AI to turn text into a 'Vector' (list of numbers).
        """
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document",
            title="Government Document"
        )
        return result['embedding']

    def ingest_text(self, filename: str, full_text: str):
        """
        Chunks text and saves it with embeddings to a JSON file.
        """
        print(f"Indexing {filename} via Google AI...")
        
        # Simple chunking (approx 1000 characters per chunk)
        chunk_size = 1000
        chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
        
        new_entries = []
        for i, chunk in enumerate(chunks):
            vector = self._get_embedding(chunk)
            entry = {
                "id": f"{filename}_{i}",
                "source": filename,
                "text": chunk,
                "vector": vector
            }
            new_entries.append(entry)
            print(f" - Embedded chunk {i+1}/{len(chunks)}")
        
        self.documents.extend(new_entries)
        self._save_db()
        print(f"Saved {len(new_entries)} new chunks to database.")

    def search(self, query: str, top_k=3):
        """
        Finds the most relevant chunks using 'Cosine Similarity' math.
        """
        print(f"Thinking about: '{query}'...")
        # 1. Embed the user's question
        query_vector = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )['embedding']
        
        # 2. Compare against all documents (Math Magic)
        scored_results = []
        for doc in self.documents:
            score = self._cosine_similarity(query_vector, doc['vector'])
            scored_results.append((score, doc))
            
        # 3. Sorts by best match
        scored_results.sort(key=lambda x: x[0], reverse=True)
        
        # 4. Return top K
        return [item[1] for item in scored_results[:top_k]]

    def _save_db(self):
        with open(DB_FILE, "w") as f:
            json.dump(self.documents, f)

    def _cosine_similarity(self, v1, v2):
        """
        Calculates how 'similar' two vectors are (Pure Math).
        """
        dot_product = sum(a*b for a, b in zip(v1, v2))
        magnitude_v1 = math.sqrt(sum(a*a for a in v1))
        magnitude_v2 = math.sqrt(sum(b*b for b in v2))
        if magnitude_v1 * magnitude_v2 == 0:
            return 0
        return dot_product / (magnitude_v1 * magnitude_v2)

# Unit Tests 
if __name__ == "__main__":
    kb = KnowledgeBase()
    
    # Test Data
    kb.ingest_text("test_policy.pdf", "The penalty for AI non-compliance is $50,000.")
    
    # Test Search
    results = kb.search("What is the fine amount?")
    for r in results:
        print(f"FOUND: {r['text']}")