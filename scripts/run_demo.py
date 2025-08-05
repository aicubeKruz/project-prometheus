#!/usr/bin/env python3
"""
Demo script for Project Prometheus.
Demonstrates the basic functionality of the multi-agent system.
"""
import asyncio
import json
from typing import Dict, Any

from prometheus.core.domain import AgentType, Priority
from prometheus.services.agent_manager import AgentManager
from prometheus.services.task_service import TaskService
from prometheus.infrastructure.event_bus import InMemoryEventBus
from prometheus.infrastructure.repositories import InMemoryRepository


async def run_demo():
    """Run Project Prometheus demonstration."""
    print("🚀 Starting Project Prometheus Demo")
    print("=" * 50)
    
    # Initialize infrastructure
    event_bus = InMemoryEventBus()
    task_repository = InMemoryRepository()
    
    # Initialize services
    agent_manager = AgentManager(event_bus=event_bus, task_repository=task_repository)
    task_service = TaskService(agent_manager)
    
    try:
        # Start agent manager
        await agent_manager.start()
        print("✅ Agent manager started")
        
        # Setup agent hierarchy
        print("\n🏗️  Setting up agent hierarchy...")
        hierarchy_info = await agent_manager.setup_agent_hierarchy()
        
        print(f"✅ Created {len(hierarchy_info['created_agents'])} agents:")
        for agent_info in hierarchy_info['created_agents']:
            print(f"   - {agent_info['type'].upper()}: {agent_info['role']}")
        
        # Display hierarchy
        print("\n🌳 Agent Hierarchy:")
        hierarchy = await agent_manager.get_hierarchy_structure()
        for level, agents in hierarchy.items():
            if agents:
                print(f"   {level.upper()}:")
                for agent in agents:
                    print(f"     - {agent['type'].upper()} ({agent['id'][:8]}...)")
        
        # Initialize project
        print("\n📋 Initializing project...")
        prometheus_agent = await agent_manager.get_prometheus_agent()
        if prometheus_agent and hasattr(prometheus_agent, 'initialize_project'):
            await prometheus_agent.initialize_project(
                mission="Develop safe and aligned artificial general intelligence",
                research_phases=[
                    "architecture_design",
                    "symbolic_reasoning_development",
                    "embodied_learning", 
                    "safety_validation"
                ]
            )
            print("✅ Project initialized with mission and research phases")
        
        # Create some demonstration tasks
        print("\n📝 Creating demonstration tasks...")
        
        # Get agents for task assignment
        daedalus = await agent_manager.get_agent_by_type("daedalus")
        logos = await agent_manager.get_agent_by_type("logos")
        odysseus = await agent_manager.get_agent_by_type("odysseus")
        themis = await agent_manager.get_agent_by_type("themis")
        
        demo_tasks = []
        
        if daedalus:
            task = await task_service.create_task(
                agent_id=str(daedalus.id),
                name="Design Hybrid Neuro-Symbolic Core",
                description="Develop the core AGI architecture integrating neural and symbolic components",
                priority=Priority.CRITICAL,
                metadata={"phase": "architecture_design", "complexity": "high"}
            )
            demo_tasks.append(task)
            print(f"   - Created architecture task for Daedalus")
        
        if logos:
            task = await task_service.create_task(
                agent_id=str(logos.id),
                name="Develop Formal Logic Systems",
                description="Create formal logic systems and knowledge graphs for System 2 reasoning",
                priority=Priority.HIGH,
                metadata={"phase": "symbolic_reasoning", "logic_types": ["first_order", "temporal"]}
            )
            demo_tasks.append(task)
            print(f"   - Created logic task for Logos")
        
        if odysseus:
            task = await task_service.create_task(
                agent_id=str(odysseus.id),
                name="Design Simulation Environment",
                description="Create high-fidelity simulation for embodied learning",
                priority=Priority.HIGH,
                metadata={"phase": "embodied_learning", "environment_type": "physics_sim"}
            )
            demo_tasks.append(task)
            print(f"   - Created simulation task for Odysseus")
        
        if themis:
            task = await task_service.create_task(
                agent_id=str(themis.id),
                name="Comprehensive Safety Audit",
                description="Perform safety audit of all system components",
                priority=Priority.CRITICAL,
                metadata={"phase": "safety_validation", "audit_scope": "comprehensive"}
            )
            demo_tasks.append(task)
            print(f"   - Created safety task for Themis")
        
        print(f"✅ Created {len(demo_tasks)} demonstration tasks")
        
        # Execute tasks
        print("\n⚡ Executing tasks...")
        executed_tasks = []
        
        for i, task in enumerate(demo_tasks[:2]):  # Execute first 2 tasks for demo
            print(f"   Executing task {i+1}: {task.name}")
            executed_task = await task_service.execute_task(str(task.id))
            executed_tasks.append(executed_task)
            print(f"   ✅ Task completed with status: {executed_task.status.value}")
        
        # Demonstrate inter-agent communication
        print("\n💬 Demonstrating inter-agent communication...")
        if prometheus_agent and daedalus:
            await agent_manager.send_message(
                sender_id=str(prometheus_agent.id),
                receiver_id=str(daedalus.id),
                content={
                    "type": "research_directive",
                    "message": "Focus on hybrid architecture development",
                    "priority": "high"
                },
                message_type="directive"
            )
            print("   ✅ Message sent from Prometheus to Daedalus")
        
        # Safety demonstration
        print("\n🛡️  Demonstrating safety features...")
        if themis:
            # Get status from Themis
            if hasattr(themis, 'get_safety_status'):
                safety_status = await themis.get_safety_status()
                print(f"   - Safety monitors active: {len(safety_status.get('active_monitors', {}))}")
                print(f"   - Veto power: {'Active' if safety_status.get('veto_power_active') else 'Inactive'}")
            
            # Perform a safety audit
            if hasattr(themis, 'perform_comprehensive_audit') and daedalus:
                print("   - Performing safety audit on Daedalus...")
                audit_results = await themis.perform_comprehensive_audit(daedalus.id)
                passed_checks = len([r for r in audit_results if r.status == "passed"])
                print(f"   ✅ Safety audit completed: {passed_checks}/{len(audit_results)} checks passed")
        
        # System status
        print("\n📊 System Status:")
        agents_info = await agent_manager.list_agents()
        active_agents = len([a for a in agents_info if a.get("active", False)])
        print(f"   - Total agents: {len(agents_info)}")
        print(f"   - Active agents: {active_agents}")
        
        task_stats = await task_service.get_task_statistics()
        print(f"   - Total tasks: {task_stats['total']}")
        print(f"   - Completed tasks: {task_stats['by_status'].get('completed', 0)}")
        
        # Demonstrate exploration (Odysseus)
        print("\n🌍 Demonstrating embodied exploration...")
        if odysseus and hasattr(odysseus, 'explore_environment'):
            exploration_config = {
                "strategy": "random",
                "steps": 50,
                "focus": ["spatial", "causal"]
            }
            exploration_result = await odysseus.explore_environment("physics_sim", exploration_config)
            if exploration_result.get("insights"):
                print(f"   ✅ Exploration completed with {len(exploration_result['insights'])} insights")
                for insight in exploration_result['insights'][:2]:  # Show first 2 insights
                    print(f"     - {insight['type']}: {insight['insight']}")
        
        # Demonstrate symbolic reasoning (Logos)
        print("\n🧠 Demonstrating symbolic reasoning...")
        if logos and hasattr(logos, 'develop_formal_logic_systems'):
            print("   - Developing formal logic systems...")
            logic_systems = await logos.develop_formal_logic_systems()
            active_systems = [name for name, system in logic_systems.items() 
                            if isinstance(system, dict) and system.get('status') == 'completed']
            print(f"   ✅ Logic systems developed: {', '.join(active_systems)}")
        
        print("\n🎉 Demo completed successfully!")
        print("=" * 50)
        
        # Final summary
        print("\n📋 Demo Summary:")
        print("   - Multi-agent hierarchy established")
        print("   - Inter-agent communication demonstrated") 
        print("   - Task creation and execution shown")
        print("   - Safety monitoring active")
        print("   - Embodied exploration simulated")
        print("   - Symbolic reasoning initiated")
        print("\n🚀 Project Prometheus is ready for research and development!")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await agent_manager.stop()
        print("\n🔄 System shutdown complete")


if __name__ == "__main__":
    asyncio.run(run_demo())