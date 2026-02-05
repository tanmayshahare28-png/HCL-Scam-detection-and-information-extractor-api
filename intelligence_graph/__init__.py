"""
Intelligence Graph Module for Honeypot API Project

This module provides graph-based intelligence capabilities for tracking
scam patterns, entities, and relationships between cases.
"""

from .graph_engine import (
    add_node,
    add_edge,
    process_case,
    get_risk_score,
    get_enhanced_risk_score,
    get_regionally_adapted_threshold,
    generate_case_report,
    get_visualization_data,
    get_statistics,
    graph
)

from .transcript_analysis import (
    initialize_transcript_enhancement,
    load_scam_transcripts,
    extract_scam_patterns
)

from .ollama_agent import (
    generate_response as generate_ollama_response,
    is_ollama_available,
    call_ollama
)

__all__ = [
    'add_node',
    'add_edge',
    'process_case',
    'get_risk_score',
    'get_enhanced_risk_score',
    'get_regionally_adapted_threshold',
    'generate_case_report',
    'get_visualization_data',
    'get_statistics',
    'graph',
    'initialize_transcript_enhancement',
    'load_scam_transcripts',
    'extract_scam_patterns',
    'generate_ollama_response',
    'is_ollama_available',
    'call_ollama'
]