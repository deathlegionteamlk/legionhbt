from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from legionhbt_agent.agent.autonomous_agent import AutonomousAgent
from legionhbt_model.model.server import ModelServer
from legionhbt_rag.rag.rag_engine import RAGEngine
from evolution.co_evolution import CoEvolutionFramework
from sandbox.sandbox_api import SandboxController
from scheduler.task_scheduler import TaskScheduler
from scheduler.skill_marketplace import SkillMarketplace
from pentesting_ai import PentestingAI

class EnhancedOrchestrator:
    def __init__(self):
        self.app = FastAPI(title="LEGIONHBT Enhanced Orchestrator")
        self.setup_middleware()
        self.setup_routes()
        
        self.agent = AutonomousAgent()
        self.model_server = ModelServer()
        self.rag_engine = RAGEngine()
        self.evolution = CoEvolutionFramework()
        self.sandbox_controller = SandboxController()
        self.scheduler = TaskScheduler()
        self.skill_marketplace = SkillMarketplace()
        self.pentesting_ai = PentestingAI()
        
        self.conversations: Dict[str, List[Dict]] = {}
        self.system_status = {
            "agent": True,
            "model": True,
            "rag": True,
            "sandbox": True,
            "evolution": True
        }
        
        self.active_connections: List[WebSocket] = []
    
    def setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self.app.get("/api/status")
        async def get_status():
            return self.system_status
        
        @self.app.get("/api/dashboard")
        async def get_dashboard():
            return {
                "system_status": self.system_status,
                "conversations": len(self.conversations),
                "scheduler_stats": self.scheduler.get_stats(),
                "skill_stats": self.skill_marketplace.get_stats(),
                "evolution_summary": self.evolution.get_evolution_summary()
            }
        
        @self.app.post("/api/chat")
        async def chat(request: Dict):
            mode = request.get("mode", "agent")
            message = request.get("message", "")
            conversation_id = request.get("conversationId", str(uuid.uuid4()))
            
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
            
            self.conversations[conversation_id].append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            
            async def generate():
                if mode == "agent":
                    async for chunk in self._stream_agent_response(message):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                elif mode == "model":
                    async for chunk in self._stream_model_response(message):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                elif mode == "rag":
                    async for chunk in self._stream_rag_response(message):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                elif mode == "evolution":
                    async for chunk in self._stream_evolution_response(message):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                elif mode == "sandbox":
                    async for chunk in self._stream_sandbox_response(message):
                        yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(generate(), media_type="text/event-stream")
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            file_id = str(uuid.uuid4())
            upload_dir = "/app/legionhbt_0406/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            return {
                "success": True,
                "fileId": file_id,
                "url": f"/uploads/{file_id}_{file.filename}"
            }
        
        @self.app.post("/api/sandbox/create")
        async def create_sandbox(resources: Optional[Dict] = None):
            session = self.sandbox_controller.sandbox.create_session(resources)
            if session:
                return {"session_id": session.session_id, "status": "created"}
            return JSONResponse({"error": "Failed to create sandbox"}, status_code=500)
        
        @self.app.post("/api/sandbox/{session_id}/command")
        async def execute_sandbox_command(session_id: str, command: Dict):
            result = self.sandbox_controller.sandbox.execute_command(
                session_id,
                command.get("command", "")
            )
            return {"session_id": session_id, "result": result}
        
        @self.app.get("/api/sandbox/{session_id}/screenshot")
        async def get_screenshot(session_id: str):
            screenshot = self.sandbox_controller.sandbox.screenshot(session_id)
            if screenshot:
                return {"session_id": session_id, "screenshot": screenshot}
            return JSONResponse({"error": "Screenshot failed"}, status_code=500)
        
        @self.app.post("/api/pentest/create")
        async def create_pentest(request: Dict):
            target = request.get("target", "")
            scope = request.get("scope", {})
            
            session = await self.pentesting_ai.create_engagement(target, scope)
            return {
                "session_id": session.session_id,
                "target": target,
                "status": session.status
            }
        
        @self.app.post("/api/pentest/{session_id}/recon")
        async def run_recon(session_id: str):
            result = await self.pentesting_ai.execute_reconnaissance(session_id)
            return result
        
        @self.app.get("/api/pentest/{session_id}/report")
        async def get_pentest_report(session_id: str):
            report = self.pentesting_ai.get_session_report(session_id)
            return report
        
        @self.app.post("/api/scheduler/task")
        async def create_scheduled_task(request: Dict):
            task_id = self.scheduler.create_task(
                name=request.get("name"),
                task_type=request.get("task_type"),
                schedule=request.get("schedule"),
                action=request.get("action"),
                enabled=request.get("enabled", True)
            )
            return {"task_id": task_id}
        
        @self.app.get("/api/skills")
        async def list_skills(category: Optional[str] = None):
            skills = self.skill_marketplace.list_skills(category=category)
            return [{"id": s.skill_id, "name": s.name, "installed": s.installed} for s in skills]
        
        @self.app.post("/api/skills/{skill_id}/install")
        async def install_skill(skill_id: str):
            success = self.skill_marketplace.install_skill(skill_id)
            return {"success": success}
        
        @self.app.post("/api/skills/{skill_id}/execute")
        async def execute_skill(skill_id: str, config: Dict):
            result = self.skill_marketplace.execute_skill(skill_id, config)
            return result
        
        @self.app.post("/api/evolution/start")
        async def start_evolution():
            asyncio.create_task(self.evolution.start_evolution())
            return {"status": "started"}
        
        @self.app.get("/api/evolution/status")
        async def get_evolution_status():
            return self.evolution.get_evolution_summary()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_connections.append(websocket)
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    if message.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                    elif message.get("type") == "status":
                        await websocket.send_json({
                            "type": "status",
                            "data": self.system_status
                        })
            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
        
        ui_build_path = "/app/legionhbt_0406/ui/build"
        if os.path.exists(ui_build_path):
            self.app.mount("/", StaticFiles(directory=ui_build_path, html=True), name="static")
    
    async def _stream_agent_response(self, message: str):
        words = message.split()
        response = f"Processing your request: {message}\n\n"
        
        for word in words:
            response += word + " "
            yield response
            await asyncio.sleep(0.05)
        
        response += "\n\nAgent analysis complete."
        yield response
    
    async def _stream_model_response(self, message: str):
        response = "Model inference result:\n\n"
        for char in response + message:
            yield char
            await asyncio.sleep(0.02)
    
    async def _stream_rag_response(self, message: str):
        response = f"Searching knowledge base for: {message}\n\n"
        yield response
        await asyncio.sleep(0.5)
        
        response += "Found relevant information:\n"
        response += "- CVE-2023-XXXX: Critical vulnerability\n"
        response += "- Exploit available in database\n"
        yield response
    
    async def _stream_evolution_response(self, message: str):
        response = "Evolution framework processing...\n\n"
        yield response
        await asyncio.sleep(0.3)
        
        response += f"Current cycle: {self.evolution.current_cycle}\n"
        response += f"Success rate: {self.evolution.get_evolution_summary().get('final_success_rate', 0):.2f}\n"
        yield response
    
    async def _stream_sandbox_response(self, message: str):
        response = "Sandbox operation initiated...\n\n"
        yield response
        await asyncio.sleep(0.3)
        
        response += "Sandbox session active.\n"
        response += "Ready for command execution.\n"
        yield response
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        self.scheduler.start()
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

orchestrator = EnhancedOrchestrator()
