#!/usr/bin/env python
"""
Local API server startup script with configuration and validation.
Run this to test the API locally before deploying to Render.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

def setup_environment():
    """Load environment configuration."""
    # Try to load .env file
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
    else:
        print(f"⚠ No .env file found, using defaults or environment variables")
    
    # Validate Firebase credentials
    creds_path = os.getenv("FIREBASE_CREDENTIALS", "firebase_credentials.json")
    if not Path(creds_path).exists():
        print(f"⚠ Warning: Firebase credentials not found at {creds_path}")
        print("  API will run but Firebase features may fail")
        print("  Get credentials: https://console.firebase.google.com/ → Project Settings → Service Accounts")
    else:
        try:
            with open(creds_path, 'r') as f:
                creds = json.load(f)
                print(f"✓ Firebase credentials loaded: {creds.get('project_id', 'unknown')}")
        except Exception as e:
            print(f"✗ Error reading Firebase credentials: {e}")

def print_startup_info():
    """Print startup information."""
    api_host = os.getenv("API_HOST", "0.0.0.0")
    api_port = os.getenv("API_PORT", "8000")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    token = os.getenv("FB_SCRAPER_API_TOKEN", "dev-token-change-in-production")
    
    print("\n" + "="*70)
    print("  🚀 Facebook Scraper API - Local Development Server")
    print("="*70)
    print(f"\n  Host: http://localhost:{api_port}")
    print(f"  Debug Mode: {'Enabled' if debug else 'Disabled'}")
    print(f"  API Token: {token[:20]}..." if len(token) > 20 else f"  API Token: {token}")
    print("\n  📚 Documentation:")
    print(f"    - Interactive Docs: http://localhost:{api_port}/docs")
    print(f"    - ReDoc: http://localhost:{api_port}/redoc")
    print(f"    - Health Check: http://localhost:{api_port}/health")
    print("\n  🔐 Authentication:")
    print(f"    Add header: Authorization: Bearer {token}")
    print("\n  📝 Example Curl Request:")
    print(f"    curl -H 'Authorization: Bearer {token}' \\")
    print(f"      http://localhost:{api_port}/api/v1/posts")
    print("\n" + "="*70)
    print("  Press Ctrl+C to stop the server")
    print("="*70 + "\n")

def main():
    """Main startup function."""
    try:
        # Setup
        setup_environment()
        print_startup_info()
        
        # Import and run
        import uvicorn
        
        api_host = os.getenv("API_HOST", "0.0.0.0")
        api_port = int(os.getenv("API_PORT", "8000"))
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Start server
        uvicorn.run(
            "api_server:app",
            host=api_host,
            port=api_port,
            reload=debug,
            log_level="debug" if debug else "info"
        )
    
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("  1. Check that all dependencies are installed:")
        print("     pip install -r requirements.txt")
        print("  2. Make sure port 8000 is not in use")
        print("  3. Verify Python version >= 3.9")
        sys.exit(1)

if __name__ == "__main__":
    main()
