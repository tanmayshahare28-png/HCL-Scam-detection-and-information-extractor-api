#!/usr/bin/env python3
"""
Honeypot API Server Starter

This script starts the Honeypot API server locally on port 5000.
"""

import sys
import os
sys.path.insert(0, '..')  # Add parent directory to path to import from api
from api.main import app

def main():
    print("=" * 60)
    print("HONEYPOT API SERVER - LOCAL STARTER")
    print("=" * 60)
    print("Starting Honeypot API server...")
    print("Access the API at: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Start the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    main()