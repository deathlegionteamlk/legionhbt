#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.enhanced_orchestrator import orchestrator

def main():
    print("=" * 60)
    print("LEGIONHBT - Enhanced Autonomous AI Pentesting Ecosystem")
    print("=" * 60)
    print()
    print("Features:")
    print("  - Capy.ai-like Browser Automation")
    print("  - Agent0-style Self-Evolving Agents")
    print("  - Desktop Sandbox with VNC")
    print("  - ChatGPT-like React UI")
    print("  - Task Scheduling & Skills Marketplace")
    print("  - Pentesting AI with Sandbox Control")
    print()
    print("Starting Enhanced Orchestrator on port 8080...")
    print()
    
    orchestrator.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
