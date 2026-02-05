
graph = {
    "nodes": {},
    "edges": []
}

def add_node(node_id, node_type):
    if node_id not in graph["nodes"]:
        graph["nodes"][node_id] = {
            "type": node_type,
            "count": 1
        }
    else:
        graph["nodes"][node_id]["count"] += 1


def add_edge(from_node, to_node, relation):
    graph["edges"].append({
        "from": from_node,
        "to": to_node,
        "relation": relation
    })

def process_case(case_data):
    case_id = case_data["case_id"]

    add_node(case_id, "case")

    for upi in case_data.get("entities", {}).get("upi", []):
        add_node(upi, "upi")
        add_edge(case_id, upi, "USED_IN")

    for phone in case_data.get("entities", {}).get("phone", []):
        add_node(phone, "phone")
        add_edge(case_id, phone, "CONTACTED_BY")

    for url in case_data.get("entities", {}).get("url", []):
        add_node(url, "url")
        add_edge(case_id, url, "USED_IN")

    for behavior in case_data.get("behavioral_tags", []):
        add_node(behavior, "behavior")
        add_edge(case_id, behavior, "EXPLOITS")


def get_risk_score(node_id):
    if node_id in graph["nodes"]:
        return graph["nodes"][node_id]["count"]
    return 0

def generate_case_report(case_id, use_enhanced_risk=False):
    linked_entities = []

    for edge in graph["edges"]:
        if edge["from"] == case_id:
            entity_id = edge["to"]
            entity_type = graph["nodes"][entity_id]["type"]

            if use_enhanced_risk:
                risk_score = get_enhanced_risk_score(entity_id)
            else:
                risk_score = get_risk_score(entity_id)

            linked_entities.append({
                "entity": entity_id,
                "type": entity_type,
                "risk_score": risk_score,
                "relation": edge["relation"]
            })

    # Adjust priority calculation based on enhanced risk if used
    if use_enhanced_risk:
        priority = "HIGH" if any(
            e["risk_score"] > 1.5 for e in linked_entities
        ) else "MEDIUM"
    else:
        priority = "HIGH" if any(
            e["risk_score"] > 1 for e in linked_entities
        ) else "MEDIUM"

    return {
        "case_id": case_id,
        "total_entities": len(linked_entities),
        "priority": priority,
        "linked_entities": linked_entities,
        "risk_model": "enhanced" if use_enhanced_risk else "standard"
    }


def get_visualization_data():
    """
    Generate visualization-friendly data for plotting the intelligence graph
    """
    nodes_for_viz = []
    edges_for_viz = []

    # Convert nodes to visualization format
    for node_id, node_data in graph["nodes"].items():
        nodes_for_viz.append({
            "id": node_id,
            "label": node_id,
            "type": node_data["type"],
            "size": max(10, node_data["count"] * 5),  # Size based on count
            "color": get_node_color(node_data["type"]),
            "title": f"{node_id}<br>Type: {node_data['type']}<br>Count: {node_data['count']}"
        })

    # Convert edges to visualization format
    for edge in graph["edges"]:
        edges_for_viz.append({
            "from": edge["from"],
            "to": edge["to"],
            "label": edge["relation"],
            "title": f"{edge['relation']}"
        })

    return {
        "nodes": nodes_for_viz,
        "edges": edges_for_viz
    }


def get_node_color(node_type):
    """
    Return color based on node type for visualization
    """
    colors = {
        "case": "#FF6B6B",      # Red for cases
        "upi": "#4ECDC4",       # Teal for UPI IDs
        "phone": "#45B7D1",     # Blue for phones
        "url": "#96CEB4",       # Green for URLs
        "behavior": "#FFEAA7",  # Yellow for behaviors
        "default": "#DDA0DD"    # Purple for others
    }
    return colors.get(node_type, colors["default"])


# Load dataset insights at module level
from .dataset_integration import initialize_dataset_enhancement
from .transcript_analysis import initialize_transcript_enhancement

# Initialize dataset enhancement
DATASET_ANALYSIS, RISK_INDICATORS = initialize_dataset_enhancement()

# Initialize transcript enhancement
TRANSCRIPT_ENHANCEMENT_DATA = initialize_transcript_enhancement()


def get_statistics():
    """
    Get statistics about the intelligence graph
    """
    stats = {
        "total_nodes": len(graph["nodes"]),
        "total_edges": len(graph["edges"]),
        "node_types": {},
        "high_risk_entities": [],
        "dataset_insights": DATASET_ANALYSIS,
        "risk_indicators": RISK_INDICATORS,
        "transcript_insights": TRANSCRIPT_ENHANCEMENT_DATA
    }

    # Count node types
    for node_id, node_data in graph["nodes"].items():
        node_type = node_data["type"]
        if node_type not in stats["node_types"]:
            stats["node_types"][node_type] = 0
        stats["node_types"][node_type] += 1

        # Track high-risk entities (those with count > 1)
        if node_data["count"] > 1:
            stats["high_risk_entities"].append({
                "id": node_id,
                "type": node_type,
                "count": node_data["count"]
            })

    # Sort high-risk entities by count
    stats["high_risk_entities"].sort(key=lambda x: x["count"], reverse=True)

    return stats


def get_enhanced_risk_score(node_id, base_score=None):
    """
    Get risk score enhanced with dataset insights
    """
    if node_id in graph["nodes"]:
        base_count = graph["nodes"][node_id]["count"]

        # Apply risk multipliers based on dataset analysis
        fraud_mult = RISK_INDICATORS.get('fraud_multiplier', 1.0)
        urgency_mult = RISK_INDICATORS.get('urgency_multiplier', 1.0)
        info_theft_mult = RISK_INDICATORS.get('info_theft_multiplier', 1.0)

        # Determine multiplier based on node type
        node_type = graph["nodes"][node_id]["type"]
        if node_type == "upi":
            multiplier = fraud_mult
        elif node_type == "url":
            multiplier = info_theft_mult
        elif node_type == "phone":
            multiplier = urgency_mult
        else:
            multiplier = (fraud_mult + urgency_mult + info_theft_mult) / 3

        enhanced_score = base_count * multiplier
        return min(enhanced_score, 10.0)  # Cap at reasonable value

    return 0


def get_regionally_adapted_threshold():
    """
    Get scam detection threshold adapted based on regional fraud statistics
    """
    fraud_percentage = DATASET_ANALYSIS.get('crime_percentages', {}).get('Fraud', 0)

    # Lower threshold in high-fraud regions (more sensitive detection)
    if fraud_percentage > 40:
        return 0.25  # Lower threshold for high-risk areas
    elif fraud_percentage > 25:
        return 0.30
    else:
        return 0.35  # Default threshold


if __name__ == "__main__":

    test_case_1 = {
        "case_id": "SCAM_001",
        "entities": {
            "upi": ["fraud@ybl"],
            "phone": ["+919876543210"],
            "url": ["fake-kyc.in"]
        },
        "behavioral_tags": ["urgency", "authority"]
    }

    test_case_2 = {
        "case_id": "SCAM_002",
        "entities": {
            "upi": ["fraud@ybl"],          # reused UPI
            "phone": ["+919876543210"],    # reused phone
            "url": ["fake-kyc.in"]         # reused URL
        },
        "behavioral_tags": ["urgency"]
    }

    process_case(test_case_1)
    process_case(test_case_2)

    print("\nCASE REPORT (LATEST CASE):")
    report = generate_case_report("SCAM_002")
    print(report)
