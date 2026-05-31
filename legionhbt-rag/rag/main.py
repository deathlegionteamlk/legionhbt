import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

from rag.vector_store import SecurityVectorStore
from rag.rag_engine import RAGEngine
from rag.ingest import ingest_all_data

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
socketio = SocketIO(app, cors_allowed_origins="*")

rag_engine = None

def init_rag():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/query', methods=['POST'])
def query():
    engine = init_rag()
    data = request.json
    question = data.get('question')
    category = data.get('category')
    
    if not question:
        return jsonify({'error': 'Question is required'}), 400
    
    result = engine.query(question, category=category)
    return jsonify(result)

@app.route('/api/search/cve/<cve_id>', methods=['GET'])
def search_cve(cve_id):
    engine = init_rag()
    result = engine.search_cve(cve_id)
    return jsonify(result)

@app.route('/api/search/exploit', methods=['POST'])
def search_exploit():
    engine = init_rag()
    data = request.json
    keyword = data.get('keyword')
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    result = engine.search_exploit(keyword)
    return jsonify(result)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    engine = init_rag()
    return jsonify(engine.get_stats())

@app.route('/api/ingest', methods=['POST'])
def trigger_ingest():
    engine = init_rag()
    stats = ingest_all_data(engine.vector_store)
    return jsonify({'status': 'completed', 'stats': stats})

@app.route('/api/tools/nmap', methods=['POST'])
def tool_nmap():
    from rag.tools import NmapTool
    data = request.json
    target = data.get('target')
    
    if not target:
        return jsonify({'error': 'Target is required'}), 400
    
    tool = NmapTool()
    result = tool.execute(target)
    return jsonify({
        'success': result.success,
        'output': result.output,
        'error': result.error
    })

@app.route('/api/tools/webscan', methods=['POST'])
def tool_webscan():
    from rag.tools import WebScannerTool
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    tool = WebScannerTool()
    result = tool.execute(url)
    return jsonify({
        'success': result.success,
        'output': result.output,
        'error': result.error
    })

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to LEGIONHBT RAG'})

@socketio.on('query')
def handle_query(data):
    engine = init_rag()
    question = data.get('question')
    category = data.get('category')
    
    if question:
        result = engine.query(question, category=category)
        emit('query_response', result)

def main():
    init_rag()
    socketio.run(app, host='0.0.0.0', port=8082, debug=False)

if __name__ == '__main__':
    main()