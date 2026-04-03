"""
Test script for FastAPI server
Run this to verify the API server is working correctly
"""
import sys
import os
import time
import subprocess
import threading
sys.path.insert(0, '.')

from pathlib import Path

# Check if requests is available
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def wait_for_server(url: str, timeout: int = 30) -> bool:
    """Wait for server to become available"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False


def test_api_endpoints(base_url: str = "http://localhost:8000"):
    """Test all API endpoints"""
    print("=" * 50)
    print("FASTAPI SERVER ENDPOINT TESTS")
    print("=" * 50)
    
    if not REQUESTS_AVAILABLE:
        print("\n✗ 'requests' package not installed. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], 
                      capture_output=True)
        import requests
    
    # Test health endpoint
    print(f"\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Health check passed")
            print(f"      Status: {data.get('status')}")
            print(f"      Firebase: {data.get('firebase_connected')}")
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"   ✗ Cannot connect to server at {base_url}")
        print(f"   Make sure the API server is running:")
        print(f"   python api_server.py")
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return False
    
    # Test root endpoint
    print(f"\n2. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Root endpoint working")
            print(f"      Service: {data.get('service')}")
            print(f"      Version: {data.get('version')}")
        else:
            print(f"   ⚠ Root returned: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test POST - save post
    print(f"\n3. Testing POST /posts...")
    try:
        test_post = {
            "page_name": "Test Page",
            "post_id": "api_test_001",
            "content": "This is a test post from the API test script",
            "likes": 150,
            "shares": 30,
            "comment_count": 25
        }
        response = requests.post(f"{base_url}/posts", json=test_post, timeout=10)
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"   ✓ Post created successfully")
            print(f"      ID: {data.get('id', data.get('post_id'))}")
        else:
            print(f"   ⚠ Create post returned: {response.status_code}")
            print(f"      {response.text[:200]}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test GET - retrieve posts
    print(f"\n4. Testing GET /posts...")
    try:
        response = requests.get(f"{base_url}/posts", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"   ✓ Retrieved {len(data)} posts")
            elif isinstance(data, dict) and 'posts' in data:
                print(f"   ✓ Retrieved {len(data['posts'])} posts")
            else:
                print(f"   ✓ Response: {str(data)[:100]}")
        else:
            print(f"   ⚠ Get posts returned: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test GET - single post
    print(f"\n5. Testing GET /posts/api_test_001...")
    try:
        response = requests.get(f"{base_url}/posts/api_test_001", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Retrieved post successfully")
            print(f"      Content: {data.get('content', '')[:50]}...")
        elif response.status_code == 404:
            print(f"   ⚠ Post not found (may not persist without Firebase)")
        else:
            print(f"   ⚠ Get post returned: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test analysis endpoint
    print(f"\n6. Testing POST /analyze...")
    try:
        analysis_request = {
            "post_ids": ["api_test_001"],
            "analysis_types": ["sentiment", "engagement"]
        }
        response = requests.post(f"{base_url}/analyze", json=analysis_request, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Analysis completed")
            if isinstance(data, list):
                print(f"      Results: {len(data)} analyses")
            else:
                print(f"      Result: {str(data)[:100]}")
        else:
            print(f"   ⚠ Analysis returned: {response.status_code}")
            print(f"      (This may fail if ML module isn't properly initialized)")
    except Exception as e:
        print(f"   ⚠ Analysis error (not critical): {e}")
    
    # Test stats endpoint
    print(f"\n7. Testing GET /stats...")
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Stats retrieved successfully")
            print(f"      Total posts: {data.get('total_posts', 'N/A')}")
            print(f"      Total pages: {data.get('total_pages', 'N/A')}")
        else:
            print(f"   ⚠ Stats returned: {response.status_code}")
    except Exception as e:
        print(f"   ⚠ Stats error: {e}")
    
    # Test OpenAPI docs
    print(f"\n8. Testing API documentation...")
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ Swagger UI available at {base_url}/docs")
        
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        if response.status_code == 200:
            print(f"   ✓ OpenAPI schema available")
    except Exception as e:
        print(f"   ⚠ Docs check error: {e}")
    
    print("\n" + "=" * 50)
    print("✓ API SERVER TESTS COMPLETED!")
    print("=" * 50)
    print(f"\nAPI Documentation: {base_url}/docs")
    print(f"Alternative Docs: {base_url}/redoc")
    
    return True


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test FastAPI server")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API server")
    parser.add_argument("--start-server", action="store_true",
                       help="Start the server before testing")
    args = parser.parse_args()
    
    if args.start_server:
        print("Starting API server in background...")
        print("(Press Ctrl+C to stop after tests)")
        
        # Start server in background
        server_process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent
        )
        
        # Wait for server to start
        print("Waiting for server to start...")
        if wait_for_server(args.url):
            print("Server started successfully!\n")
            try:
                success = test_api_endpoints(args.url)
            finally:
                print("\nStopping server...")
                server_process.terminate()
        else:
            print("Server failed to start within timeout")
            server_process.terminate()
            return False
    else:
        success = test_api_endpoints(args.url)
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
