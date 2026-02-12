"""
Cybercrime Dataset Integration Module

This module loads and processes the cybercrime dataset to enhance
the intelligence graph and scam detection capabilities.
"""
import csv
import os
from typing import Dict, List, Tuple
import re
from collections import defaultdict

# Load the cybercrime dataset
def load_cybercrime_dataset(file_path: str) -> Dict:
    """
    Load the cybercrime dataset from CSV file
    """
    dataset = []
    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                dataset.append(row)
    except FileNotFoundError:
        print(f"Dataset file not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return {}
    
    return dataset


def analyze_cybercrime_trends(dataset: List[Dict]) -> Dict:
    """
    Analyze trends in the cybercrime dataset to identify patterns
    """
    if not dataset:
        return {}
    
    # Calculate totals by crime type across all cities
    crime_totals = defaultdict(float)
    city_crime_counts = defaultdict(lambda: defaultdict(float))
    
    for record in dataset:
        city = record.get('City', 'Unknown')
        for crime_type, count in record.items():
            if crime_type not in ['City', 'Total']:  # Skip non-crime columns
                try:
                    count_val = float(count) if count != '' else 0.0
                    crime_totals[crime_type] += count_val
                    city_crime_counts[city][crime_type] = count_val
                except ValueError:
                    continue  # Skip non-numeric values
    
    # Calculate percentages and identify high-incidence areas
    total_crimes = sum(crime_totals.values())
    crime_percentages = {k: (v / total_crimes * 100) if total_crimes > 0 else 0 for k, v in crime_totals.items()}
    
    # Identify cities with high fraud rates
    high_fraud_cities = []
    for city, crimes in city_crime_counts.items():
        fraud_rate = crimes.get('Fraud', 0)
        if fraud_rate > 50:  # Cities with more than 50 fraud cases
            high_fraud_cities.append((city, fraud_rate))
    
    # Sort by fraud rate
    high_fraud_cities.sort(key=lambda x: x[1], reverse=True)
    
    return {
        'crime_totals': dict(crime_totals),
        'crime_percentages': dict(crime_percentages),
        'high_fraud_cities': high_fraud_cities[:10],  # Top 10 cities
        'total_records': len(dataset)
    }


def get_fraud_keywords_from_dataset(dataset: List[Dict]) -> List[str]:
    """
    Extract potential fraud-related keywords from the dataset
    Based on crime categories that are related to fraud/scams
    """
    fraud_related_categories = [
        'Fraud', 'Extortion', 'Causing Disrepute', 'Sale purchase illegal drugs',
        'Spreading Piracy', 'Steal Information', 'Others'
    ]
    
    # Generate keywords based on high-frequency fraud-related terms
    keywords = []
    for category in fraud_related_categories:
        # Create variations of the category name for detection
        base_word = category.replace(' ', '').replace('-', '').lower()
        keywords.extend([
            base_word,
            category.lower(),
            category.replace(' ', '.*'),  # Regex pattern
        ])
    
    return list(set(keywords))  # Remove duplicates


def enhance_detection_patterns(base_patterns: Dict[str, List[str]], dataset_analysis: Dict) -> Dict[str, List[str]]:
    """
    Enhance the base detection patterns with insights from the dataset
    """
    enhanced_patterns = base_patterns.copy()
    
    # Add regional/city-specific patterns if certain areas have high fraud rates
    high_fraud_cities = dataset_analysis.get('high_fraud_cities', [])
    
    # Create patterns based on high-fraud regions (could be used for geo-targeting)
    if high_fraud_cities:
        region_specific_terms = []
        for city, fraud_count in high_fraud_cities[:5]:  # Top 5 high fraud cities
            # Add city names as potential indicators (for location-based scams)
            region_specific_terms.append(city.lower())
        
        # Add to verification patterns since location spoofing is common in scams
        if 'verification' in enhanced_patterns:
            enhanced_patterns['verification'].extend([f".*{city}.*" for city in region_specific_terms])
    
    # Enhance financial patterns based on fraud statistics
    fraud_percentage = dataset_analysis.get('crime_percentages', {}).get('Fraud', 0)
    if fraud_percentage > 30:  # If fraud is a major category (>30% of crimes)
        # Add more aggressive financial scam patterns
        if 'financial' in enhanced_patterns:
            enhanced_patterns['financial'].extend([
                r"urgent.*action.*required",
                r"verify.*within.*hours",
                r"immediate.*attention",
                r"unusual.*activity.*detected"
            ])
    
    return enhanced_patterns


def get_high_risk_indicators(dataset_analysis: Dict) -> Dict[str, float]:
    """
    Identify high-risk indicators based on the dataset analysis
    """
    crime_totals = dataset_analysis.get('crime_totals', {})
    crime_percentages = dataset_analysis.get('crime_percentages', {})
    
    # Define risk multipliers based on dataset insights
    risk_indicators = {}
    
    # Higher fraud percentage means more aggressive scoring
    fraud_percentage = crime_percentages.get('Fraud', 0)
    risk_indicators['fraud_multiplier'] = 1.0 + (fraud_percentage / 100.0)
    
    # Extortion often involves threats and urgency
    extortion_percentage = crime_percentages.get('Extortion', 0)
    risk_indicators['urgency_multiplier'] = 1.0 + (extortion_percentage / 150.0)
    
    # Information theft patterns
    steal_info_percentage = crime_percentages.get('Steal Information', 0)
    risk_indicators['info_theft_multiplier'] = 1.0 + (steal_info_percentage / 200.0)
    
    return risk_indicators


def initialize_dataset_enhancement():
    """
    Initialize the dataset enhancement system
    """
    dataset_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'archive', 'Dataset_CyberCrime_Sean.csv')
    dataset = load_cybercrime_dataset(dataset_path)
    
    if not dataset:
        print("Warning: Could not load cybercrime dataset. Using default patterns.")
        return {}, {}
    
    analysis = analyze_cybercrime_trends(dataset)
    risk_indicators = get_high_risk_indicators(analysis)
    
    print(f"Dataset loaded successfully: {analysis.get('total_records', 0)} records analyzed")
    print(f"Top fraud-related cities: {analysis.get('high_fraud_cities', [])[:3]}")
    print(f"Fraud represents {analysis.get('crime_percentages', {}).get('Fraud', 0):.2f}% of total crimes")
    
    return analysis, risk_indicators


# For testing purposes
if __name__ == "__main__":
    analysis, risk_indicators = initialize_dataset_enhancement()
    print("\nRisk Indicators:", risk_indicators)