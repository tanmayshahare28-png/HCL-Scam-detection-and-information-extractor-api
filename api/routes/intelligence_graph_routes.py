"""
Intelligence Graph Routes for Honeypot API

This module provides API endpoints for the intelligence graph functionality,
allowing retrieval of scam patterns, risk scores, and case reports.
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from intelligence_graph.graph_engine import (
    process_case,
    get_risk_score,
    get_enhanced_risk_score,
    generate_case_report,
    get_visualization_data,
    get_statistics,
    graph
)

intelligence_graph_bp = Blueprint('intelligence_graph', __name__)

@intelligence_graph_bp.route('/intelligence/graph', methods=['GET'])
def get_graph_info():
    """Get current graph statistics"""
    return jsonify({
        "status": "success",
        "graph_info": {
            "total_nodes": len(graph["nodes"]),
            "total_edges": len(graph["edges"]),
            "nodes": graph["nodes"]
        },
        "timestamp": datetime.now().isoformat()
    })

@intelligence_graph_bp.route('/intelligence/process-case', methods=['POST'])
def process_new_case():
    """Process a new case and add it to the intelligence graph"""
    try:
        data = request.get_json()
        
        if not data or "case_id" not in data:
            return jsonify({
                "status": "error",
                "message": "case_id is required in request body"
            }), 400
        
        # Process the case through the intelligence graph
        process_case(data)
        
        return jsonify({
            "status": "success",
            "message": f"Case {data['case_id']} processed and added to intelligence graph",
            "case_id": data["case_id"],
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to process case: {str(e)}"
        }), 500

@intelligence_graph_bp.route('/intelligence/risk-score/<node_id>', methods=['GET'])
def get_node_risk_score(node_id):
    """Get risk score for a specific node"""
    try:
        # Check if enhanced scoring is requested
        enhanced = request.args.get('enhanced', 'false').lower() == 'true'

        if enhanced:
            risk_score = get_enhanced_risk_score(node_id)
            score_type = "enhanced"
        else:
            risk_score = get_risk_score(node_id)
            score_type = "standard"

        return jsonify({
            "status": "success",
            "node_id": node_id,
            "risk_score": risk_score,
            "score_type": score_type,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get risk score: {str(e)}"
        }), 500

@intelligence_graph_bp.route('/intelligence/case-report/<case_id>', methods=['GET'])
def get_case_report(case_id):
    """Generate a detailed report for a specific case"""
    try:
        # Check if enhanced risk scoring is requested
        enhanced = request.args.get('enhanced', 'false').lower() == 'true'

        report = generate_case_report(case_id, use_enhanced_risk=enhanced)

        return jsonify({
            "status": "success",
            "report": report,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to generate case report: {str(e)}"
        }), 500


@intelligence_graph_bp.route('/intelligence/visualization-data', methods=['GET'])
def get_viz_data():
    """Get visualization data for plotting the intelligence graph"""
    try:
        viz_data = get_visualization_data()

        return jsonify({
            "status": "success",
            "visualization_data": viz_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get visualization data: {str(e)}"
        }), 500


@intelligence_graph_bp.route('/intelligence/statistics', methods=['GET'])
def get_stats():
    """Get statistics about the intelligence graph"""
    try:
        stats = get_statistics()

        return jsonify({
            "status": "success",
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get statistics: {str(e)}"
        }), 500


@intelligence_graph_bp.route('/intelligence/session-conversations/<session_id>', methods=['GET'])
def get_session_conversations(session_id):
    """Get conversation history for a specific session"""
    try:
        # Import the conversation history from main app
        from api.main import conversation_full_history

        if session_id not in conversation_full_history:
            return jsonify({
                "status": "error",
                "message": f"No conversation history found for session {session_id}"
            }), 404

        return jsonify({
            "status": "success",
            "session_id": session_id,
            "conversation_history": conversation_full_history[session_id],
            "message_count": len(conversation_full_history[session_id]),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to get session conversations: {str(e)}"
        }), 500