"""
Scam Transcript Analysis Module

This module analyzes scam conversation transcripts to enhance
scam detection patterns and improve accuracy.
"""
import csv
import os
import re
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
import json

def load_scam_transcripts(file_path: str) -> List[Dict]:
    """
    Load scam transcripts from CSV file
    """
    transcripts = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                transcripts.append(row)
    except FileNotFoundError:
        print(f"Transcript file not found: {file_path}")
        return []
    except Exception as e:
        print(f"Error loading transcripts: {e}")
        return []
    
    return transcripts


def extract_scam_patterns(transcripts: List[Dict]) -> Dict[str, List[str]]:
    """
    Extract scam patterns from the transcripts based on labels
    """
    scam_patterns = {
        'suspicious_phrases': [],
        'scam_indicators': [],
        'typical_scam_openers': [],
        'urgency_indicators': [],
        'authority_claims': [],
        'verification_avoidance': [],
        'threat_indicators': []
    }
    
    # Define pattern categories based on labels and features
    for record in transcripts:
        text = record.get('TEXT', '')
        label = record.get('LABEL', '').lower()
        features = record.get('FEATURES', '').lower()
        annotations = record.get('ANNOTATIONS', '').lower()
        
        # Extract patterns based on labels
        if 'suspicious' in label or 'highly_suspicious' in label:
            scam_patterns['scam_indicators'].append(text)
            
            # Look for specific scam tactics in the text
            if any(word in text.lower() for word in ['urgent', 'immediate', 'right now', 'today only']):
                scam_patterns['urgency_indicators'].append(text)
                
            if any(word in text.lower() for word in ['government', 'tax', 'irs', 'police', 'bank', 'official']):
                scam_patterns['authority_claims'].append(text)
                
            if any(word in text.lower() for word in ['verify', 'confirm', 'send', 'provide', 'details']):
                scam_patterns['verification_avoidance'].append(text)
                
            if any(word in text.lower() for word in ['penalty', 'legal action', 'consequences', 'suspended', 'blocked']):
                scam_patterns['threat_indicators'].append(text)
        
        # Extract based on features
        if 'urgency' in features:
            scam_patterns['urgency_indicators'].append(text)
            
        if 'authority_figure' in features:
            scam_patterns['authority_claims'].append(text)
            
        if 'evasion' in features:
            scam_patterns['verification_avoidance'].append(text)
            
        if 'threat' in features:
            scam_patterns['threat_indicators'].append(text)
    
    # Remove duplicates and return
    for key in scam_patterns:
        scam_patterns[key] = list(set(scam_patterns[key]))
    
    return scam_patterns


def generate_regex_patterns(scam_patterns: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """
    Generate regex patterns from scam phrases for detection
    """
    regex_patterns = {}
    
    for category, phrases in scam_patterns.items():
        regex_list = []
        for phrase in phrases:
            # Create a flexible regex pattern from the phrase
            # Escape special characters but allow for variations
            escaped_phrase = re.escape(phrase.lower())
            # Replace spaces with flexible whitespace pattern
            flexible_pattern = re.sub(r'\\s+', r'\\s*', escaped_phrase)
            regex_list.append(f"(?i){flexible_pattern}")  # Case insensitive
        
        regex_patterns[category] = regex_list
    
    return regex_patterns


def analyze_conversation_flows(transcripts: List[Dict]) -> Dict:
    """
    Analyze conversation flows to identify typical scam progression patterns
    """
    conversation_flows = defaultdict(list)
    scam_conversations = set()
    
    # Group by conversation ID to analyze flows
    for record in transcripts:
        conv_id = record.get('CONVERSATION_ID', '')
        step = int(record.get('CONVERSATION_STEP', 0))
        text = record.get('TEXT', '')
        label = record.get('LABEL', '').lower()
        
        conversation_flows[conv_id].append({
            'step': step,
            'text': text,
            'label': label
        })
        
        # Track conversations that contain suspicious elements
        if 'suspicious' in label or 'highly_suspicious' in label:
            scam_conversations.add(conv_id)
    
    # Analyze scam conversation patterns
    scam_flow_patterns = []
    for conv_id in scam_conversations:
        if conv_id in conversation_flows:
            flow = sorted(conversation_flows[conv_id], key=lambda x: x['step'])
            scam_flow_patterns.append(flow)
    
    return {
        'total_conversations': len(conversation_flows),
        'scam_conversations': len(scam_conversations),
        'conversation_flows': dict(conversation_flows),
        'scam_flow_patterns': scam_flow_patterns
    }


def get_training_keywords(transcripts: List[Dict]) -> Dict[str, List[str]]:
    """
    Extract training keywords from transcripts to enhance detection
    """
    keywords = {
        'scam_keywords': set(),
        'normal_keywords': set(),
        'context_indicators': set()
    }
    
    for record in transcripts:
        text = record.get('TEXT', '')
        label = record.get('LABEL', '').lower()
        context = record.get('CONTEXT', '').lower()
        
        # Extract words based on labels
        words = re.findall(r'\b\w+\b', text.lower())
        context_words = re.findall(r'\b\w+\b', context.lower())
        
        if 'suspicious' in label or 'highly_suspicious' in label:
            keywords['scam_keywords'].update(words)
        else:
            keywords['normal_keywords'].update(words)
        
        keywords['context_indicators'].update(context_words)
    
    # Convert sets to lists
    for key in keywords:
        keywords[key] = list(keywords[key])
    
    return keywords


def initialize_transcript_enhancement():
    """
    Initialize the transcript enhancement system
    """
    transcript_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'Scam transcripts', 'BETTER30.csv')
    transcripts = load_scam_transcripts(transcript_path)
    
    if not transcripts:
        print("Warning: Could not load scam transcripts. Using default patterns.")
        return {}, {}, {}
    
    print(f"Loaded {len(transcripts)} transcript records for analysis")
    
    # Extract patterns from transcripts
    scam_patterns = extract_scam_patterns(transcripts)
    regex_patterns = generate_regex_patterns(scam_patterns)
    conversation_analysis = analyze_conversation_flows(transcripts)
    training_keywords = get_training_keywords(transcripts)
    
    print(f"Extracted patterns from {conversation_analysis['total_conversations']} conversations")
    print(f"Identified {conversation_analysis['scam_conversations']} scam conversations")
    
    return {
        'scam_patterns': scam_patterns,
        'regex_patterns': regex_patterns,
        'conversation_analysis': conversation_analysis,
        'training_keywords': training_keywords
    }


if __name__ == "__main__":
    enhancement_data = initialize_transcript_enhancement()
    print(f"Scam indicators found: {len(enhancement_data.get('scam_patterns', {}).get('scam_indicators', []))}")