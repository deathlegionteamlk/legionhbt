import os
import sys
import unittest
import tempfile
import shutil
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from legionhbt.components.c1_engagement_graph import C1EngagementGraph, EngagementState, EngagementPriority
from legionhbt.components.c2_audit_log import C2AuditLog, AuditEventType
from legionhbt.components.c3_risk_layer import C3RiskLayer, RiskLevel, ActionType
from legionhbt.components.c4_self_monitor import C4SelfMonitor, GateDecision
from legionhbt.components.c5_ultraplan import C5ULTRAPLAN, PlanStatus
from legionhbt.components.c6_coordinator import C6Coordinator, WorkerRole, TaskStatus
from legionhbt.components.c7_corroboration import C7Corroboration, CorroborationStatus, ModelProvider
from legionhbt.components.c8_poc_verification import C8PoCVerification, PoCStatus, PoCType
from legionhbt.components.c9_variant_hunter import C9VariantHunter, VariantStatus
from legionhbt.components.c10_chain_builder import C10ChainBuilder, ChainStatus, LinkType
from legionhbt.components.c11_fixer import C11Fixer, FixStatus, FixType
from legionhbt.components.c12_speculation import C12SpeculationLayer, SpeculationStatus
from legionhbt.utils.safetensor_utils import SafetensorManager


class TestC1EngagementGraph(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test.db")
        self.graph = C1EngagementGraph(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_node(self):
        node_id = self.graph.create_node("test", {"key": "value"}, EngagementPriority.HIGH)
        self.assertIsNotNone(node_id)
        self.assertEqual(len(node_id), 16)
    
    def test_get_node(self):
        node_id = self.graph.create_node("test", {"key": "value"})
        node = self.graph.get_node(node_id)
        self.assertIsNotNone(node)
        self.assertEqual(node.node_type, "test")
        self.assertEqual(node.state, EngagementState.PENDING)
    
    def test_update_node_state(self):
        node_id = self.graph.create_node("test", {})
        success = self.graph.update_node_state(node_id, EngagementState.ACTIVE)
        self.assertTrue(success)
        node = self.graph.get_node(node_id)
        self.assertEqual(node.state, EngagementState.ACTIVE)
    
    def test_chain_integrity(self):
        parent_id = self.graph.create_node("parent", {})
        child_id = self.graph.create_node("child", {}, parent_id=parent_id)
        
        self.assertTrue(self.graph.verify_chain_integrity(parent_id))
        self.assertTrue(self.graph.verify_chain_integrity(child_id))


class TestC2AuditLog(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, "audit.log")
        self.audit = C2AuditLog(self.log_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_log_event(self):
        entry_id = self.audit.log(AuditEventType.NODE_CREATED, "test", "create", payload={"test": True})
        self.assertIsNotNone(entry_id)
        self.assertTrue(os.path.exists(self.log_path))
    
    def test_verify_chain(self):
        self.audit.log(AuditEventType.NODE_CREATED, "test", "create")
        self.audit.log(AuditEventType.NODE_UPDATED, "test", "update")
        self.assertTrue(self.audit.verify_chain())
    
    def test_get_recent_entries(self):
        for i in range(5):
            self.audit.log(AuditEventType.NODE_CREATED, "test", f"action_{i}")
        entries = self.audit.get_recent_entries(3)
        self.assertEqual(len(entries), 3)


class TestC3RiskLayer(unittest.TestCase):
    def setUp(self):
        self.risk = C3RiskLayer()
    
    def test_assess_risk_unknown_action(self):
        assessment = self.risk.assess_risk("unknown_action")
        self.assertEqual(assessment.risk_level, RiskLevel.HIGH)
        self.assertTrue(assessment.requires_approval)
    
    def test_assess_risk_read_action(self):
        self.risk.register_action("read_test", ActionType.READ, 0.1)
        assessment = self.risk.assess_risk("read_test")
        self.assertEqual(assessment.risk_level, RiskLevel.LOW)
        self.assertFalse(assessment.requires_approval)
    
    def test_assess_risk_execute_action(self):
        self.risk.register_action("exec_test", ActionType.EXECUTE, 0.3)
        assessment = self.risk.assess_risk("exec_test")
        self.assertIn(assessment.risk_level, [RiskLevel.MEDIUM, RiskLevel.HIGH])


class TestC4SelfMonitor(unittest.TestCase):
    def setUp(self):
        self.monitor = C4SelfMonitor(check_interval=0.1)
    
    def test_get_state(self):
        state = self.monitor.get_state()
        self.assertIsNotNone(state)
    
    def test_deliberative_gate_allow(self):
        check = self.monitor.deliberative_gate("test_node", {"risk_score": 0.1})
        self.assertEqual(check.decision, GateDecision.ALLOW)
    
    def test_deliberative_gate_deliberate(self):
        check = self.monitor.deliberative_gate("test_node", {"risk_score": 0.9})
        self.assertEqual(check.decision, GateDecision.DELIBERATE)
    
    def test_health_report(self):
        report = self.monitor.get_health_report()
        self.assertIn("state", report)


class TestC5ULTRAPLAN(unittest.TestCase):
    def setUp(self):
        self.plan = C5ULTRAPLAN()
    
    def test_create_plan(self):
        tasks = [{"name": "Task 1", "priority": 1}, {"name": "Task 2", "priority": 2}]
        plan_id = self.plan.create_plan("Test Plan", "Test objective", tasks)
        self.assertIsNotNone(plan_id)
    
    def test_decompose_objective(self):
        tasks = self.plan.decompose_objective("build a system")
        self.assertGreater(len(tasks), 0)
    
    def test_get_plan_status(self):
        tasks = [{"name": "Task 1"}]
        plan_id = self.plan.create_plan("Test", "Test", tasks)
        status = self.plan.get_plan_status(plan_id)
        self.assertEqual(status["name"], "Test")


class TestC6Coordinator(unittest.TestCase):
    def setUp(self):
        self.coord = C6Coordinator(max_workers=2)
    
    def test_spawn_worker(self):
        worker_id = self.coord.spawn_worker(WorkerRole.GENERAL)
        self.assertIsNotNone(worker_id)
    
    def test_submit_task(self):
        self.coord.register_task_handler("test_task", lambda p: {"result": "ok"})
        task_id = self.coord.submit_task("test_task", {"data": "test"})
        self.assertIsNotNone(task_id)


class TestC7Corroboration(unittest.TestCase):
    def setUp(self):
        self.corr = C7Corroboration(threshold=0.67)
    
    def test_register_model(self):
        def mock_interface(query):
            return {"response": "test", "confidence": 0.9}
        
        self.corr.register_model("model1", ModelProvider.PRIMARY, mock_interface)
        self.assertEqual(len(self.corr._model_interfaces), 1)


class TestC8PoCVerification(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.poc = C8PoCVerification(sandbox_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_create_poc(self):
        poc_id = self.poc.create_poc("Test", "Test desc", PoCType.CODE_EXECUTION, "print('hello')")
        self.assertIsNotNone(poc_id)
    
    def test_verify_poc_python(self):
        poc_id = self.poc.create_poc("Test", "Test", PoCType.CODE_EXECUTION, "print('hello')", "python")
        result = self.poc.verify_poc(poc_id)
        self.assertIn(result.status, [PoCStatus.VERIFIED, PoCStatus.FAILED])


class TestC9VariantHunter(unittest.TestCase):
    def setUp(self):
        self.hunter = C9VariantHunter()
    
    def test_hunt_variants(self):
        variants = self.hunter.hunt_variants("source1", {"param": 10, "method": "test"})
        self.assertIsInstance(variants, list)
    
    def test_get_deduplication_stats(self):
        stats = self.hunter.get_deduplication_stats()
        self.assertIn("total_variants", stats)


class TestC10ChainBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = C10ChainBuilder()
    
    def test_create_chain(self):
        links = [{"name": "Link1", "type": "sequential", "action": {}}]
        chain_id = self.builder.create_chain("Test", "Test chain", links)
        self.assertIsNotNone(chain_id)
    
    def test_validate_chain(self):
        links = [{"name": "Link1", "type": "sequential", "action": {}, "dependencies": []}]
        chain_id = self.builder.create_chain("Test", "Test", links)
        errors = self.builder.validate_chain(chain_id)
        self.assertEqual(len(errors), 0)


class TestC11Fixer(unittest.TestCase):
    def setUp(self):
        self.fixer = C11Fixer()
    
    def test_identify_fix(self):
        fix_id = self.fixer.identify_fix("target1", "Test issue", FixType.CODE_PATCH, {})
        self.assertIsNotNone(fix_id)
    
    def test_get_fix(self):
        fix_id = self.fixer.identify_fix("target1", "Test", FixType.CODE_PATCH, {})
        fix = self.fixer.get_fix(fix_id)
        self.assertIsNotNone(fix)
        self.assertEqual(fix.target_id, "target1")


class TestC12Speculation(unittest.TestCase):
    def setUp(self):
        self.spec = C12SpeculationLayer()
    
    def test_create_layer(self):
        layer_id = self.spec.create_layer("Test Layer")
        self.assertIsNotNone(layer_id)
        self.assertEqual(self.spec.get_active_layer(), layer_id)
    
    def test_set_get_state(self):
        self.spec.create_layer("Test")
        self.spec.set_state("key1", "value1")
        self.assertEqual(self.spec.get_state("key1"), "value1")
    
    def test_commit_layer(self):
        layer_id = self.spec.create_layer("Test")
        self.spec.set_state("key1", "value1")
        success = self.spec.commit_layer(layer_id)
        self.assertTrue(success)


class TestSafetensorManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SafetensorManager(self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_scan_models_directory(self):
        models = self.manager.scan_models_directory()
        self.assertIsInstance(models, list)
    
    def test_list_loaded_models(self):
        models = self.manager.list_loaded_models()
        self.assertEqual(len(models), 0)


if __name__ == '__main__':
    unittest.main()
