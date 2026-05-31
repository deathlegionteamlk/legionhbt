import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from agent.llm_clients import LLMRouter, LLMResponse
from agent.tools import ToolRegistry, ToolResult
from agent.session_manager import SessionManager, Session


class AgentState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    ANALYZING = "analyzing"
    REPORTING = "reporting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class Action:
    tool: str
    parameters: Dict[str, Any]
    reasoning: str
    risk_level: str


@dataclass
class Observation:
    action: Action
    result: ToolResult
    timestamp: str


class AutonomousPentestingAgent:
    def __init__(self, session_manager: SessionManager = None):
        self.llm_router = LLMRouter()
        self.tool_registry = ToolRegistry()
        self.session_manager = session_manager or SessionManager()
        self.state = AgentState.IDLE
        self.current_session = None
        self.plan = []
        self.observations = []
        self.findings = []
    
    def create_session(self, name: str, target: str, scope: Dict = None) -> Session:
        self.current_session = self.session_manager.create_session(
            name=name,
            target=target,
            metadata={"scope": scope or {}, "agent_version": "1.0.0"}
        )
        return self.current_session
    
    def _build_system_prompt(self) -> str:
        tools_desc = "\n".join([
            f"- {t['name']}: {t['description']} (Risk: {t['risk_level']})"
            for t in self.tool_registry.list_tools()
        ])
        
        return f"""You are LEGIONHBT, an autonomous AI penetration testing agent. Your goal is to discover and analyze security vulnerabilities in target systems.

Available Tools:
{tools_desc}

You operate in a ReAct pattern (Reasoning + Acting):
1. Analyze the current situation and previous observations
2. Reason about what to do next
3. Select the appropriate tool and parameters
4. Wait for the observation, then repeat

Risk Classification:
- LOW: Information gathering, passive reconnaissance
- MEDIUM: Active scanning, service enumeration
- HIGH: Exploitation, brute force, payload delivery

You must respond in this exact format:
REASONING: <your detailed reasoning about the next step>
ACTION: <tool_name>
PARAMETERS: <JSON object with parameters>

If you have completed the assessment, respond with:
REASONING: <summary of findings>
ACTION: COMPLETE
FINDINGS: <JSON array of discovered vulnerabilities>"""
    
    def _parse_llm_response(self, response: str) -> Optional[Action]:
        reasoning_match = re.search(r'REASONING:\s*(.+?)(?=ACTION:|FINDINGS:|$)', response, re.DOTALL)
        action_match = re.search(r'ACTION:\s*(\w+)', response)
        params_match = re.search(r'PARAMETERS:\s*(\{.+\})', response, re.DOTALL)
        
        if not action_match:
            return None
        
        tool_name = action_match.group(1).strip()
        
        if tool_name == "COMPLETE":
            return Action(tool="COMPLETE", parameters={}, reasoning="", risk_level="NONE")
        
        reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
        params = {}
        if params_match:
            try:
                params = json.loads(params_match.group(1))
            except json.JSONDecodeError:
                pass
        
        tool = self.tool_registry.get_tool(tool_name)
        risk_level = tool.risk_level if tool else "UNKNOWN"
        
        return Action(
            tool=tool_name,
            parameters=params,
            reasoning=reasoning,
            risk_level=risk_level
        )
    
    def _build_prompt(self, objective: str, iteration: int) -> str:
        history = "\n\n".join([
            f"Step {i+1}:\nAction: {obs.action.tool}\nParameters: {obs.action.parameters}\nResult: {obs.result.output if obs.result.success else obs.result.error}"
            for i, obs in enumerate(self.observations[-5:])
        ])
        
        return f"""Objective: {objective}
Target: {self.current_session.target if self.current_session else 'Unknown'}
Iteration: {iteration}

Previous Actions:
{history}

Based on the previous actions and their results, determine the next step.
Respond in the required format."""
    
    def run(self, objective: str, max_iterations: int = 20) -> Dict:
        if not self.current_session:
            raise ValueError("No active session. Call create_session() first.")
        
        self.state = AgentState.PLANNING
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            prompt = self._build_prompt(objective, iteration)
            system_prompt = self._build_system_prompt()
            
            try:
                llm_response = self.llm_router.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    temperature=0.7
                )
                
                action = self._parse_llm_response(llm_response.content)
                
                if not action:
                    self.observations.append(Observation(
                        action=Action(tool="ERROR", parameters={}, reasoning="Parse error", risk_level="NONE"),
                        result=ToolResult(success=False, output="", error="Failed to parse LLM response"),
                        timestamp=""
                    ))
                    continue
                
                if action.tool == "COMPLETE":
                    self.state = AgentState.COMPLETED
                    findings_match = re.search(r'FINDINGS:\s*(\[.+\])', llm_response.content, re.DOTALL)
                    if findings_match:
                        try:
                            self.findings = json.loads(findings_match.group(1))
                        except:
                            pass
                    break
                
                self.state = AgentState.EXECUTING
                
                result = self.tool_registry.execute(action.tool, **action.parameters)
                
                observation = Observation(
                    action=action,
                    result=result,
                    timestamp=""
                )
                self.observations.append(observation)
                
                self.session_manager.add_action(
                    self.current_session.id,
                    {
                        "tool": action.tool,
                        "parameters": action.parameters,
                        "reasoning": action.reasoning,
                        "success": result.success,
                        "output": result.output[:1000] if result.success else result.error
                    }
                )
                
                self.session_manager.log_audit(
                    session_id=self.current_session.id,
                    action_type="tool_execution",
                    tool_name=action.tool,
                    input_data=json.dumps(action.parameters),
                    output_data=result.output[:2000] if result.success else result.error
                )
                
                if result.success and result.data:
                    if "findings" in result.data:
                        for finding in result.data["findings"]:
                            self.session_manager.add_finding(
                                self.current_session.id,
                                finding
                            )
                
                self.state = AgentState.ANALYZING
                
            except Exception as e:
                self.state = AgentState.ERROR
                self.session_manager.add_action(
                    self.current_session.id,
                    {
                        "tool": "error",
                        "error": str(e),
                        "success": False
                    }
                )
                break
        
        self.session_manager.update_session(
            self.current_session.id,
            status="completed" if self.state == AgentState.COMPLETED else "error",
            findings=self.findings
        )
        
        return {
            "session_id": self.current_session.id,
            "status": self.state.value,
            "iterations": iteration,
            "findings": self.findings,
            "observations_count": len(self.observations)
        }
    
    def get_status(self) -> Dict:
        return {
            "state": self.state.value,
            "session": self.current_session.id if self.current_session else None,
            "iterations": len(self.observations),
            "findings": len(self.findings)
        }