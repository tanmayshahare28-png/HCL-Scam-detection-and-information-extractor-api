#!/usr/bin/env python3
"""
Honeypot API with Ngrok Tunnel Starter

This script starts the Honeypot API server and automatically creates an ngrok tunnel
to expose it publicly. It displays the public URL for external access.
"""

import os
import sys
import time
import subprocess
import threading
import requests
from pathlib import Path

def check_port(port=5000):
    """Check if the port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def start_api_server():
    """Start the Flask API server in a separate thread"""
    sys.path.insert(0, '..')  # Add parent directory to path to import from api
    from api.main import app
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

def start_ngrok():
    """Start ngrok tunnel and return the public URL"""
    try:
        # Check if ngrok is installed
        result = subprocess.run(['ngrok', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("ERROR: ngrok is not installed or not in PATH")
            print("Please install ngrok from https://ngrok.com/download")
            return None
    except FileNotFoundError:
        print("ERROR: ngrok is not installed or not in PATH")
        print("Please install ngrok from https://ngrok.com/download")
        return None
    
    # Start ngrok tunnel
    print("Starting ngrok tunnel...")
    ngrok_process = subprocess.Popen([
        'ngrok', 'http', '5000'
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Wait a bit for ngrok to start
    time.sleep(3)
    
    # Get the public URL from ngrok API
    try:
        response = requests.get('http://localhost:4040/api/tunnels')
        tunnels = response.json()
        
        for tunnel in tunnels.get('tunnels', []):
            if tunnel.get('proto') == 'http':
                public_url = tunnel.get('public_url')
                if public_url:
                    print(f"✓ Ngrok tunnel active: {public_url}")
                    return public_url, ngrok_process
    except Exception as e:
        print(f"Could not get ngrok URL: {e}")
        # Alternative: parse from ngrok process output if API doesn't work
        # This is a fallback approach
        pass
    
    print("Could not retrieve ngrok URL. Please check ngrok dashboard at http://localhost:4040")
    return None, ngrok_process

def main():
    print("=" * 60)
    print("HONEYPOT API - NGROK TUNNEL STARTER")
    print("=" * 60)
    
    # Check if required dependencies are installed
    try:
        import flask
        import requests
    except ImportError as e:
        print(f"ERROR: Missing dependencies: {e}")
        print("Please run: pip install -r ../requirements.txt")
        return
    
    # Check if port 5000 is available
    if not check_port(5000):
        print("ERROR: Port 5000 is already in use")
        print("Please close any applications using port 5000")
        return
    
    print("✓ Dependencies check passed")
    print("✓ Port 5000 is available")
    
    # Start API server in a separate thread
    print("\nStarting Honeypot API server...")
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Wait a bit for the API server to start
    time.sleep(3)
    
    # Verify API server is running
    try:
        response = requests.get('http://localhost:5000/health', timeout=5)
        if response.status_code == 200:
            print("✓ Honeypot API server is running on http://localhost:5000")
        else:
            print("WARNING: API server may not be responding correctly")
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server")
        return
    
    # Start ngrok tunnel
    public_url, ngrok_process = start_ngrok()
    
    if public_url:
        print(f"\n🎉 Honeypot API is now accessible at: {public_url}")
        print(f"📱 Local access: http://localhost:5000")
        print(f"📊 Ngrok dashboard: http://localhost:4040")
        print(f"💬 Web interface: {public_url}/ (open honeypot_tester.html in browser)")
    else:
        print("\n⚠️  Could not start ngrok tunnel automatically")
        print("💡 Please start ngrok manually: ngrok http 5000")
        print("📱 API is running locally at: http://localhost:5000")
    
    print("\nPress Ctrl+C to stop the servers")
    
    try:
        # Keep the process alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if ngrok_process:
            ngrok_process.terminate()
        print("Goodbye!")

if __name__ == "__main__":
    main()