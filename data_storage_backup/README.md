# Data Storage and Intelligence Graph Backup

This directory contains all the data storage and intelligence graph components of the honeypot API system.

## Directory Structure

```
data_storage_backup/
├── intelligence_graph/          # Intelligence graph engine and analysis modules
│   ├── __pycache__/            # Compiled Python files
│   ├── dataset_integration.py  # Cybercrime dataset integration
│   ├── graph_engine.py         # Core graph engine for intelligence mapping
│   ├── ollama_agent.py         # Ollama integration for intelligence
│   ├── transcript_analysis.py  # Scam transcript analysis module
│   └── __init__.py             # Package initialization
├── Scam_transcripts/           # Scam conversation transcripts for training
│   └── BETTER30.csv            # CSV file with scam conversation data
├── archive/                    # Archived datasets
│   └── Dataset_CyberCrime_Sean.csv  # Cybercrime statistics dataset
├── ok/                         # Alternative implementation with advanced features
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/           # Intelligence-related services
│   │   │   ├── intelligence_extractor.py  # Intelligence extraction service
│   │   │   ├── ollama_client.py         # Ollama integration
│   │   │   ├── scam_detector.py         # Scam detection service
│   │   │   ├── state_machine.py         # Conversation state management
│   │   │   └── __init__.py
│   │   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── main.py
│   ├── logs/
│   ├── static/
│   ├── venv/                   # Virtual environment
│   ├── .env
│   ├── .env.example
│   ├── README.md
│   ├── requirements.txt
│   └── run.sh
└── logs/                       # Runtime logs (currently empty)
```

## Components Description

### Intelligence Graph
- **graph_engine.py**: Core intelligence graph engine that maps relationships between scam entities (cases, UPI IDs, phone numbers, URLs, behavioral patterns)
- **dataset_integration.py**: Integrates cybercrime statistics to enhance detection accuracy
- **transcript_analysis.py**: Analyzes scam conversation transcripts to improve detection patterns
- **ollama_agent.py**: Ollama integration for enhanced intelligence processing

### Data Sources
- **BETTER30.csv**: Contains scam conversation transcripts with labels and annotations for training
- **Dataset_CyberCrime_Sean.csv**: Contains cybercrime statistics by city and crime type for regional adaptation

### Intelligence Services (from 'ok' directory)
- **intelligence_extractor.py**: Extracts structured intelligence from scam messages
- **ollama_client.py**: Client for interacting with local Ollama LLM
- **scam_detector.py**: Detects scam intent using multi-layered analysis
- **state_machine.py**: Manages conversation state transitions for the honeypot agent

### Runtime Data
- **logs/**: Directory for runtime logs (created but currently empty as logs are in-memory during execution)

## Usage

These components are used by the main API to:
- Build intelligence graphs of scam networks
- Analyze scam conversation patterns
- Integrate cybercrime statistics for regional adaptation
- Enhance detection accuracy with historical data
- Generate risk scores for scam entities
- Extract structured intelligence from scam messages
- Manage multi-turn conversation states
- Interface with Ollama for AI-powered responses

## Note

The actual in-memory data (conversation histories, extracted intelligence, session data) is stored temporarily during runtime in the main API's global variables and is not persisted to disk. The files in this backup represent the foundational data structures, datasets, and services used by the system.