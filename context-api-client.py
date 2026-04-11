"""
Context API Client Examples
Demonstrasi penggunaan Context API dengan berbagai skenario
"""

import requests
import json
import sys
from typing import List, Dict, Any

class ContextAPIClient:
    """Client untuk Context API"""
    
    def __init__(self, base_url: str = "http://localhost:5000", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=self.timeout)
            elif method.upper() == "POST":
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=self.timeout
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            return response.json()
        
        except requests.exceptions.ConnectionError:
            return {
                "status": "error",
                "message": f"Cannot connect to API at {self.base_url}"
            }
        except requests.exceptions.Timeout:
            return {
                "status": "error",
                "message": "Request timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        return self._make_request("GET", "/health")
    
    def get_info(self) -> Dict[str, Any]:
        """Get available vector stores info"""
        return self._make_request("GET", "/api/context/info")
    
    def retrieve_context(self, query: str, k: int = 5, use_mistral: bool = False) -> Dict[str, Any]:
        """Retrieve context documents from query"""
        payload = {
            "query": query,
            "k": k,
            "use_mistral": use_mistral
        }
        return self._make_request("POST", "/api/context/retrieve", payload)
    
    def query_with_llm(self, query: str, k: int = 5, use_mistral: bool = False) -> Dict[str, Any]:
        """Query and get LLM answer"""
        payload = {
            "query": query,
            "k": k,
            "use_mistral": use_mistral
        }
        return self._make_request("POST", "/api/context/query", payload)
    
    def search_documents(self, query: str, k: int = 5, use_mistral: bool = False) -> Dict[str, Any]:
        """Search documents with similarity scores"""
        payload = {
            "query": query,
            "k": k,
            "use_mistral": use_mistral
        }
        return self._make_request("POST", "/api/context/search", payload)
    
    def batch_query(self, queries: List[str], k: int = 5, use_mistral: bool = False) -> Dict[str, Any]:
        """Query multiple questions in batch"""
        payload = {
            "queries": queries,
            "k": k,
            "use_mistral": use_mistral
        }
        return self._make_request("POST", "/api/context/batch", payload)


def print_response(response: Dict[str, Any], title: str = "Response"):
    """Pretty print response"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(json.dumps(response, indent=2, ensure_ascii=False))


def example_health_check():
    """Example 1: Health Check"""
    print("\n[EXAMPLE 1] Health Check")
    print("-" * 60)
    
    client = ContextAPIClient()
    response = client.health_check()
    
    if response.get("status") == "healthy":
        print("✓ API is healthy")
        print(f"  Vector stores: {response['vector_stores']}")
    else:
        print("✗ API is not healthy")
        print(f"  Error: {response.get('message')}")


def example_get_info():
    """Example 2: Get Available Vector Stores"""
    print("\n[EXAMPLE 2] Get Available Vector Stores Info")
    print("-" * 60)
    
    client = ContextAPIClient()
    response = client.get_info()
    
    if response.get("status") == "success":
        print("Available Vector Stores:")
        for store in response.get("vector_stores", []):
            print(f"  - {store['name']}: {store['status']}")
            print(f"    Path: {store['path']}")
    else:
        print(f"Error: {response.get('message')}")


def example_retrieve_context():
    """Example 3: Retrieve Context Documents"""
    print("\n[EXAMPLE 3] Retrieve Context Documents")
    print("-" * 60)
    
    client = ContextAPIClient()
    query = "Apa itu machine learning?"
    
    print(f"Query: {query}")
    response = client.retrieve_context(query, k=3)
    
    if response.get("status") == "success":
        print(f"✓ Retrieved {response['reference_count']} documents")
        print(f"Model: {response['model']}")
        
        for ref in response.get("references", []):
            print(f"\n  Document {ref['id']}:")
            print(f"    Source: {ref['source']}")
            print(f"    Page: {ref['page']}")
            print(f"    Content: {ref['content']}")
    else:
        print(f"✗ Error: {response.get('message')}")


def example_query_with_llm():
    """Example 4: Query with LLM Answer"""
    print("\n[EXAMPLE 4] Query with LLM Answer")
    print("-" * 60)
    
    client = ContextAPIClient()
    query = "Bagaimana cara membuat model machine learning yang baik?"
    
    print(f"Query: {query}")
    response = client.query_with_llm(query, k=3)
    
    if response.get("status") == "success":
        print(f"✓ Got LLM answer")
        print(f"Model: {response['model']}")
        
        answer = response.get("answer", "")
        if answer:
            print(f"\nAnswer:\n{answer}")
        
        print(f"\n✓ References ({response['reference_count']} documents):")
        for ref in response.get("references", []):
            print(f"  - {ref['source']} (Page {ref['page']})")
    else:
        print(f"✗ Error: {response.get('message')}")


def example_search_with_scores():
    """Example 5: Search with Similarity Scores"""
    print("\n[EXAMPLE 5] Search Documents with Similarity Scores")
    print("-" * 60)
    
    client = ContextAPIClient()
    query = "deep learning"
    
    print(f"Query: {query}")
    response = client.search_documents(query, k=5)
    
    if response.get("status") == "success":
        print(f"✓ Found {response['result_count']} documents")
        print(f"Model: {response['model']}")
        
        for result in response.get("results", []):
            print(f"\n  Result {result['id']}:")
            print(f"    Score: {result['score']:.4f}")
            print(f"    Source: {result['source']}")
            print(f"    Page: {result['page']}")
            print(f"    Content: {result['content'][:100]}...")
    else:
        print(f"✗ Error: {response.get('message')}")


def example_batch_query():
    """Example 6: Batch Query Multiple Questions"""
    print("\n[EXAMPLE 6] Batch Query Multiple Questions")
    print("-" * 60)
    
    client = ContextAPIClient()
    queries = [
        "Apa itu neural network?",
        "Apa itu supervised learning?",
        "Bagaimana cara training model?"
    ]
    
    print(f"Queries: {len(queries)}")
    for q in queries:
        print(f"  - {q}")
    
    response = client.batch_query(queries, k=2)
    
    if response.get("status") == "success":
        print(f"\n✓ Processed {response['batch_size']} queries")
        print(f"Model: {response['model']}")
        
        for result in response.get("results", []):
            print(f"\n  Q: {result['query']}")
            print(f"  References: {result['reference_count']} documents")
            if result.get("context"):
                print(f"  Context: {result['context'][:150]}...")
    else:
        print(f"✗ Error: {response.get('message')}")


def interactive_mode():
    """Interactive mode untuk query manual"""
    print("\n[INTERACTIVE MODE]")
    print("-" * 60)
    
    client = ContextAPIClient()
    
    print("Commands:")
    print("  1 - Retrieve context")
    print("  2 - Query with LLM")
    print("  3 - Search documents")
    print("  4 - Batch query")
    print("  0 - Exit")
    
    while True:
        choice = input("\nSelect command (0-4): ").strip()
        
        if choice == "0":
            break
        
        elif choice == "1":
            query = input("Enter query: ").strip()
            k = int(input("Number of documents (default 5): ") or "5")
            response = client.retrieve_context(query, k=k)
            print_response(response, "Context Retrieval Result")
        
        elif choice == "2":
            query = input("Enter query: ").strip()
            k = int(input("Number of documents (default 5): ") or "5")
            response = client.query_with_llm(query, k=k)
            print_response(response, "LLM Query Result")
        
        elif choice == "3":
            query = input("Enter search term: ").strip()
            k = int(input("Number of results (default 5): ") or "5")
            response = client.search_documents(query, k=k)
            print_response(response, "Search Result")
        
        elif choice == "4":
            queries_str = input("Enter queries (comma-separated): ").strip()
            queries = [q.strip() for q in queries_str.split(",")]
            k = int(input("Number of documents per query (default 5): ") or "5")
            response = client.batch_query(queries, k=k)
            print_response(response, "Batch Query Result")
        
        else:
            print("Invalid choice")


def main():
    """Main entry point"""
    print("Context API Client Examples")
    print("=" * 60)
    
    if len(sys.argv) > 1 and sys.argv[1] == "-i":
        interactive_mode()
    else:
        # Run all examples
        try:
            example_health_check()
            example_get_info()
            example_retrieve_context()
            example_query_with_llm()
            example_search_with_scores()
            example_batch_query()
            
            print("\n" + "=" * 60)
            print("All examples completed!")
            print("\nRun with -i for interactive mode:")
            print("  python context-api-client.py -i")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")


if __name__ == "__main__":
    main()
