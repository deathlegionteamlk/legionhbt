import os
import json
import requests
from typing import Dict, List, Optional
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
socketio = SocketIO(app, cors_allowed_origins="*")

AGENT_URL = os.getenv("AGENT_URL", "http://localhost:8080")
MODEL_URL = os.getenv("MODEL_URL", "http://localhost:8081")
RAG_URL = os.getenv("RAG_URL", "http://localhost:8082")

class SystemOrchestrator:
    def __init__(self):
        self.systems = {
            "agent": {"url": AGENT_URL, "name": "LEGIONHBT Agent", "status": "unknown"},
            "model": {"url": MODEL_URL, "name": "LEGIONHBT Model", "status": "unknown"},
            "rag": {"url": RAG_URL, "name": "LEGIONHBT RAG", "status": "unknown"}
        }
    
    def health_check(self, system: str) -> Dict:
        try:
            url = self.systems[system]["url"]
            response = requests.get(f"{url}/health" if system == "model" else url, timeout=5)
            return {
                "system": system,
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            return {
                "system": system,
                "status": "offline",
                "error": str(e)
            }
    
    def health_check_all(self) -> List[Dict]:
        return [self.health_check(s) for s in self.systems.keys()]
    
    def route_query(self, query: str, query_type: str = "auto") -> Dict:
        if query_type == "auto":
            query_type = self._classify_query(query)
        
        if query_type == "pentest":
            return self._route_to_agent(query)
        elif query_type == "analysis":
            return self._route_to_model(query)
        elif query_type == "knowledge":
            return self._route_to_rag(query)
        else:
            return self._route_to_all(query)
    
    def _classify_query(self, query: str) -> str:
        pentest_keywords = ["scan", "exploit", "penetration test", "vulnerability scan", "nmap", "metasploit"]
        analysis_keywords = ["analyze", "cve", "exploit code", "vulnerability analysis", "security review"]
        
        query_lower = query.lower()
        
        for kw in pentest_keywords:
            if kw in query_lower:
                return "pentest"
        
        for kw in analysis_keywords:
            if kw in query_lower:
                return "analysis"
        
        return "knowledge"
    
    def _route_to_agent(self, query: str) -> Dict:
        try:
            response = requests.post(
                f"{AGENT_URL}/api/sessions",
                json={"name": f"Orchestrated_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "target": query},
                timeout=10
            )
            return {"system": "agent", "result": response.json()}
        except Exception as e:
            return {"system": "agent", "error": str(e)}
    
    def _route_to_model(self, query: str) -> Dict:
        try:
            response = requests.post(
                f"{MODEL_URL}/generate",
                json={"prompt": query, "max_tokens": 512},
                timeout=30
            )
            return {"system": "model", "result": response.json()}
        except Exception as e:
            return {"system": "model", "error": str(e)}
    
    def _route_to_rag(self, query: str) -> Dict:
        try:
            response = requests.post(
                f"{RAG_URL}/api/query",
                json={"question": query},
                timeout=30
            )
            return {"system": "rag", "result": response.json()}
        except Exception as e:
            return {"system": "rag", "error": str(e)}
    
    def _route_to_all(self, query: str) -> Dict:
        results = {}
        results["agent"] = self._route_to_agent(query)
        results["model"] = self._route_to_model(query)
        results["rag"] = self._route_to_rag(query)
        return results

orchestrator = SystemOrchestrator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify(orchestrator.health_check_all())

@app.route('/api/systems', methods=['GET'])
def list_systems():
    return jsonify(orchestrator.systems)

@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    query_text = data.get('query')
    query_type = data.get('type', 'auto')
    
    if not query_text:
        return jsonify({'error': 'Query is required'}), 400
    
    result = orchestrator.route_query(query_text, query_type)
    return jsonify(result)

@app.route('/api/agent/sessions', methods=['GET'])
def agent_sessions():
    try:
        response = requests.get(f"{AGENT_URL}/api/sessions", timeout=5)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 503

@app.route('/api/model/generate', methods=['POST'])
def model_generate():
    try:
        response = requests.post(f"{MODEL_URL}/generate", json=request.json, timeout=30)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 503

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    try:
        response = requests.post(f"{RAG_URL}/api/query", json=request.json, timeout=30)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 503

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to LEGIONHBT Orchestrator'})

def main():
    socketio.run(app, host='0.0.0.0', port=8083, debug=False)

if __name__ == '__main__':
    main()