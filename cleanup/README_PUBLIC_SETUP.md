# Honeypot API - Public Deployment Guide

## Overview
This guide explains how to deploy your Honeypot API publicly using a free tunneling service.

## Prerequisites
- Python 3.8+ installed
- Git for Windows (includes SSH client) OR OpenSSH installed
- All Python dependencies installed (flask, requests, python-dotenv)

## Step-by-Step Instructions

### Step 1: Start the API Server
1. Open Command Prompt as Administrator (recommended)
2. Navigate to the project directory:
   ```cmd
   cd C:\Validation and testing honeypot\honeypot-api-project
   ```
3. Start the API server:
   ```cmd
   cd api
   python main.py
   ```
   - The API will start on `http://localhost:5000`
   - Keep this window open

### Step 2: Create Public Tunnel
1. Open a NEW Command Prompt window (don't close the first one!)
2. Navigate to the project directory:
   ```cmd
   cd C:\Validation and testing honeypot\honeypot-api-project
   ```
3. Start the tunnel:
   ```cmd
   start_tunnel.bat
   ```
   OR manually run:
   ```cmd
   ssh -R 80:localhost:5000 serveo.net
   ```
   - The first time, you may need to type 'yes' when prompted
   - You'll receive a public URL like `http://XXXXXX.serveo.net`
   - Keep this window open

### Step 3: Test Your Public URL
1. Copy the public URL from the tunnel window
2. Test it using the validation script:
   ```cmd
   validate_public_url.bat
   ```
   - Enter your public URL when prompted
   - The script will run several tests to verify functionality

### Step 4: Submit for Evaluation
- Use your public URL with the test API key: `test_key_123`
- The API supports these test keys:
  - `test_key_123`
  - Any key starting with `eval_`
  - Any key starting with `hackathon_`

## API Endpoints
- `GET /health` - Health check
- `POST /api/honeypot/` - Main honeypot endpoint
- `GET /api/validate` - Validation endpoint

## Troubleshooting
- If the API fails to start, ensure all dependencies are installed: `pip install flask requests python-dotenv`
- If the tunnel fails, ensure SSH is available in your PATH
- Both the API server and tunnel must be running simultaneously
- Firewall may block connections; ensure ports 5000 and SSH are allowed

## Important Notes
- The public URL is temporary and will change each time you restart the tunnel
- Keep both command windows open for the service to remain accessible
- The service will be available as long as both processes remain running