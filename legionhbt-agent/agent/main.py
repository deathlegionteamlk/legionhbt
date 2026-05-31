import os
import json
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session as flask_session
from flask_socketio import SocketIO, emit

from agent.autonomous_agent import AutonomousPentestingAgent
from agent.session_manager import SessionManager
from agent.llm_clients import LLMRouter

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(32)
socketio = SocketIO(app, cors_allowed_origins="*")

session_manager = SessionManager()
active_agents = {}
llm_router = LLMRouter()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/sessions', methods=['GET'])
def list_sessions():
    sessions = session_manager.list_sessions()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'target': s.target,
        'status': s.status,
        'created_at': s.created_at,
        'findings_count': len(s.findings)
    } for s in sessions])

@app.route('/api/sessions', methods=['POST'])
def create_session():
    data = request.json
    name = data.get('name', f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    target = data.get('target')
    scope = data.get('scope', {})
    
    if not target:
        return jsonify({'error': 'Target is required'}), 400
    
    agent = AutonomousPentestingAgent(session_manager)
    session = agent.create_session(name, target, scope)
    active_agents[session.id] = agent
    
    return jsonify({
        'id': session.id,
        'name': session.name,
        'target': session.target,
        'status': session.status,
        'created_at': session.created_at
    })

@app.route('/api/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    session = session_manager.get_session(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404
    
    return jsonify({
        'id': session.id,
        'name': session.name,
        'target': session.target,
        'status': session.status,
        'created_at': session.created_at,
        'updated_at': session.updated_at,
        'findings': session.findings,
        'actions': session.actions,
        'metadata': session.metadata
    })

@app.route('/api/sessions/<session_id>/start', methods=['POST'])
def start_scan(session_id):
    data = request.json or {}
    objective = data.get('objective', f"Perform comprehensive security assessment of target")
    max_iterations = data.get('max_iterations', 20)
    
    agent = active_agents.get(session_id)
    if not agent:
        agent = AutonomousPentestingAgent(session_manager)
        active_agents[session_id] = agent
    
    def run_agent():
        try:
            result = agent.run(objective, max_iterations)
            socketio.emit('scan_complete', {
                'session_id': session_id,
                'result': result
            }, namespace='/')
        except Exception as e:
            socketio.emit('scan_error', {
                'session_id': session_id,
                'error': str(e)
            }, namespace='/')
    
    socketio.start_background_task(run_agent)
    
    return jsonify({'status': 'started', 'session_id': session_id})

@app.route('/api/sessions/<session_id>/status', methods=['GET'])
def get_agent_status(session_id):
    agent = active_agents.get(session_id)
    if not agent:
        return jsonify({'error': 'Agent not found'}), 404
    
    return jsonify(agent.get_status())

@app.route('/api/tools', methods=['GET'])
def list_tools():
    from agent.tools import ToolRegistry
    registry = ToolRegistry()
    return jsonify(registry.list_tools())

@app.route('/api/tools/<tool_name>/execute', methods=['POST'])
def execute_tool(tool_name):
    from agent.tools import ToolRegistry
    registry = ToolRegistry()
    
    data = request.json or {}
    result = registry.execute(tool_name, **data)
    
    return jsonify({
        'success': result.success,
        'output': result.output,
        'error': result.error,
        'data': result.data
    })

@app.route('/api/llm/generate', methods=['POST'])
def llm_generate():
    data = request.json
    prompt = data.get('prompt')
    system_prompt = data.get('system_prompt', '')
    provider = data.get('provider', 'openai')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    try:
        response = llm_router.generate(prompt, system_prompt, provider)
        return jsonify({
            'content': response.content,
            'model': response.model,
            'tokens_used': response.tokens_used,
            'finish_reason': response.finish_reason
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/audit/<session_id>', methods=['GET'])
def get_audit_log(session_id):
    entries = session_manager.get_audit_log(session_id)
    return jsonify([{
        'id': e.id,
        'timestamp': e.timestamp,
        'action_type': e.action_type,
        'tool_name': e.tool_name,
        'hash_chain': e.hash_chain
    } for e in entries])

@socketio.on('connect')
def handle_connect():
    emit('connected', {'data': 'Connected to LEGIONHBT Agent'})

@socketio.on('disconnect')
def handle_disconnect():
    pass

def main():
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    main()