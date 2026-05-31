import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, jsonify, request
from legionhbt import LegionHBTOrchestrator, Config

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

orchestrator = None


def get_orchestrator():
    global orchestrator
    if orchestrator is None:
        config = Config.from_env()
        orchestrator = LegionHBTOrchestrator(config)
        orchestrator.start()
    return orchestrator


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    orch = get_orchestrator()
    return jsonify(orch.get_system_status())


@app.route('/api/engagements', methods=['GET'])
def list_engagements():
    orch = get_orchestrator()
    state = request.args.get('state')
    return jsonify(orch.list_engagements(state))


@app.route('/api/engagements', methods=['POST'])
def create_engagement():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    node_type = data.get('type', 'generic')
    payload = data.get('payload', {})
    priority = data.get('priority', 2)
    
    node_id = orch.submit_engagement(node_type, payload, priority)
    
    return jsonify({
        "success": True,
        "node_id": node_id,
        "message": f"Engagement {node_id} created"
    })


@app.route('/api/engagements/<node_id>')
def get_engagement(node_id):
    orch = get_orchestrator()
    engagement = orch.get_engagement(node_id)
    
    if engagement:
        return jsonify(engagement)
    
    return jsonify({"error": "Engagement not found"}), 404


@app.route('/api/components')
def list_components():
    return jsonify({
        "layer_1": {
            "c1_engagement_graph": "SQLite-based engagement tracking",
            "c2_audit_log": "Hash-chained immutable audit log",
            "c3_risk_layer": "Risk-classified action layer",
            "c4_self_monitor": "Self-monitor + deliberative gate"
        },
        "layer_2": {
            "c5_ultraplan": "Strategic planning coordinator",
            "c6_coordinator": "Worker swarm coordinator",
            "c7_corroboration": "Cross-model corroboration (2-of-3)",
            "c8_poc_verification": "Dynamic executable PoC verification",
            "c9_variant_hunter": "Variant hunter with deduplication"
        },
        "layer_3": {
            "c10_chain_builder": "Composite critical-path chain builder",
            "c11_fixer": "Fixer with chain-severance proof",
            "c12_speculation": "Speculation layer with COW overlay"
        }
    })


@app.route('/api/audit/recent')
def recent_audit():
    orch = get_orchestrator()
    count = request.args.get('count', 50, type=int)
    entries = orch.c2_audit.get_recent_entries(count)
    
    return jsonify([
        {
            "entry_id": e.entry_id,
            "timestamp": e.timestamp,
            "event_type": e.event_type.value,
            "component": e.component,
            "action": e.action,
            "node_id": e.node_id
        }
        for e in entries
    ])


@app.route('/api/audit/verify')
def verify_audit():
    orch = get_orchestrator()
    valid = orch.c2_audit.verify_chain()
    return jsonify({"valid": valid})


@app.route('/api/coordinator/workers')
def list_workers():
    orch = get_orchestrator()
    workers = orch.c6_coordinator.get_all_workers()
    
    return jsonify([
        {
            "worker_id": w.worker_id,
            "role": w.role.value,
            "state": w.state.value,
            "capabilities": w.capabilities,
            "current_task": w.current_task,
            "performance_score": w.performance_score
        }
        for w in workers
    ])


@app.route('/api/coordinator/workers', methods=['POST'])
def spawn_worker():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    from legionhbt.components.c6_coordinator import WorkerRole
    
    role_str = data.get('role', 'general')
    role = WorkerRole(role_str)
    capabilities = data.get('capabilities', [])
    
    worker_id = orch.c6_coordinator.spawn_worker(role, capabilities)
    
    return jsonify({
        "success": True,
        "worker_id": worker_id,
        "role": role.value
    })


@app.route('/api/coordinator/tasks')
def list_tasks():
    orch = get_orchestrator()
    tasks = orch.c6_coordinator.get_active_tasks()
    
    return jsonify([
        {
            "task_id": t.task_id,
            "task_type": t.task_type,
            "status": t.status.value,
            "priority": t.priority,
            "assigned_worker": t.assigned_worker,
            "created_at": t.created_at
        }
        for t in tasks
    ])


@app.route('/api/coordinator/stats')
def coordinator_stats():
    orch = get_orchestrator()
    return jsonify(orch.c6_coordinator.get_stats())


@app.route('/api/ultraplan/plans')
def list_plans():
    orch = get_orchestrator()
    return jsonify(orch.c5_ultraplan.list_plans())


@app.route('/api/ultraplan/plans', methods=['POST'])
def create_plan():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    name = data.get('name', 'Unnamed Plan')
    objective = data.get('objective', '')
    tasks = data.get('tasks', [])
    
    plan_id = orch.c5_ultraplan.create_plan(name, objective, tasks)
    
    return jsonify({
        "success": True,
        "plan_id": plan_id
    })


@app.route('/api/ultraplan/plans/<plan_id>')
def get_plan(plan_id):
    orch = get_orchestrator()
    status = orch.c5_ultraplan.get_plan_status(plan_id)
    
    if status:
        return jsonify(status)
    
    return jsonify({"error": "Plan not found"}), 404


@app.route('/api/poc/results')
def poc_results():
    orch = get_orchestrator()
    return jsonify(orch.c8_poc.get_verification_summary())


@app.route('/api/variant/stats')
def variant_stats():
    orch = get_orchestrator()
    return jsonify(orch.c9_variant.get_deduplication_stats())


@app.route('/api/chain/list')
def list_chains():
    orch = get_orchestrator()
    return jsonify(orch.c10_chain.list_chains())


@app.route('/api/chain/build', methods=['POST'])
def build_chain():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    name = data.get('name', 'Unnamed Chain')
    description = data.get('description', '')
    links = data.get('links', [])
    
    chain_id = orch.c10_chain.create_chain(name, description, links)
    
    return jsonify({
        "success": True,
        "chain_id": chain_id
    })


@app.route('/api/chain/execute/<chain_id>', methods=['POST'])
def execute_chain(chain_id):
    orch = get_orchestrator()
    data = request.get_json() or {}
    context = data.get('context', {})
    
    result = orch.execute_chain(chain_id, context)
    
    return jsonify(result)


@app.route('/api/chain/status/<chain_id>')
def chain_status(chain_id):
    orch = get_orchestrator()
    status = orch.c10_chain.get_chain_status(chain_id)
    
    if status:
        return jsonify(status)
    
    return jsonify({"error": "Chain not found"}), 404


@app.route('/api/speculation/layers')
def list_speculation_layers():
    orch = get_orchestrator()
    return jsonify({
        "active_layer": orch.c12_speculation.get_active_layer(),
        "layers": orch.c12_speculation.list_layers(),
        "stack": orch.c12_speculation.get_layer_stack()
    })


@app.route('/api/speculation/create', methods=['POST'])
def create_speculation():
    orch = get_orchestrator()
    data = request.get_json() or {}
    name = data.get('name', 'Speculation Layer')
    
    layer_id = orch.create_speculation(name)
    
    return jsonify({
        "success": True,
        "layer_id": layer_id
    })


@app.route('/api/speculation/commit/<layer_id>', methods=['POST'])
def commit_speculation(layer_id):
    orch = get_orchestrator()
    success = orch.commit_speculation(layer_id)
    
    return jsonify({"success": success})


@app.route('/api/fix/create', methods=['POST'])
def create_fix():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    target_id = data.get('target_id', '')
    issue = data.get('issue', '')
    fix_type = data.get('fix_type', 'code_patch')
    context = data.get('context', {})
    
    fix_id = orch.create_fix(target_id, issue, fix_type, context)
    
    return jsonify({
        "success": True,
        "fix_id": fix_id
    })


@app.route('/api/fix/apply/<fix_id>', methods=['POST'])
def apply_fix(fix_id):
    orch = get_orchestrator()
    success = orch.apply_fix(fix_id)
    
    return jsonify({"success": success})


@app.route('/api/safetensor/models')
def list_safetensor_models():
    orch = get_orchestrator()
    models = orch.safetensor.list_loaded_models()
    
    return jsonify({
        "loaded_models": models,
        "available_models": orch.safetensor.scan_models_directory()
    })


@app.route('/api/safetensor/stats/<model_id>')
def safetensor_stats(model_id):
    orch = get_orchestrator()
    stats = orch.safetensor.get_model_stats(model_id)
    
    if stats:
        return jsonify(stats)
    
    return jsonify({"error": "Model not found"}), 404


@app.route('/api/risk/assess', methods=['POST'])
def assess_risk():
    orch = get_orchestrator()
    data = request.get_json() or {}
    
    action_id = data.get('action_id', 'temp_action')
    action_type = data.get('action_type', 'read')
    context = data.get('context', {})
    
    from legionhbt.components.c3_risk_layer import ActionType
    
    action_enum = ActionType.READ
    for at in ActionType:
        if at.value == action_type:
            action_enum = at
            break
    
    orch.c3_risk.register_action(action_id, action_enum)
    assessment = orch.c3_risk.assess_risk(action_id, context)
    
    return jsonify({
        "action_id": assessment.action_id,
        "risk_level": assessment.risk_level.value,
        "risk_score": assessment.risk_score,
        "requires_approval": assessment.requires_approval,
        "mitigation": assessment.mitigation
    })


@app.route('/api/monitor/health')
def monitor_health():
    orch = get_orchestrator()
    return jsonify(orch.c4_monitor.get_health_report())


@app.route('/api/monitor/gate-history')
def gate_history():
    orch = get_orchestrator()
    count = request.args.get('count', 50, type=int)
    history = orch.c4_monitor.get_gate_history(count)
    
    return jsonify([
        {
            "check_id": h.check_id,
            "timestamp": h.timestamp,
            "node_id": h.node_id,
            "decision": h.decision.value,
            "confidence": h.confidence,
            "reasoning": h.reasoning
        }
        for h in history
    ])


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    
    orch = get_orchestrator()
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    finally:
        orch.stop()
