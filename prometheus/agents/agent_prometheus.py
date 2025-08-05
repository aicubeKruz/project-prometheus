"""
Agent Prometheus - Master Control & Strategy
The highest-level agent, serving as the project director.
"""
from typing import Any, Dict, List, Optional

import structlog

from ..core.base_agent import BaseAgent
from ..core.domain import (
    AgentId,
    AgentType,
    EventBus,
    Message,
    Repository,
    SafetyCheck,
    Task,
    TaskId,
    Priority,
)

logger = structlog.get_logger()


class AgentPrometheus(BaseAgent):
    """
    Master Control & Strategy Agent.
    
    Responsibilities:
    - Interpret the constitutional mission
    - Decompose into strategic research phases
    - Allocate computational resources
    - Synthesize findings from subordinate agents
    - Overall project planning and coordination
    """

    def __init__(
        self,
        agent_id: Optional[AgentId] = None,
        event_bus: Optional[EventBus] = None,
        task_repository: Optional[Repository] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.PROMETHEUS,
            event_bus=event_bus,
            task_repository=task_repository,
        )
        self._project_state: Dict[str, Any] = {
            "mission": "",
            "current_phase": "initialization",
            "research_phases": [],
            "resource_allocation": {},
            "agent_reports": {},
        }
        self._strategic_priorities: List[str] = []

    async def initialize_project(self, mission: str, research_phases: List[str]) -> None:
        """Initialize project with mission and research phases."""
        self._project_state["mission"] = mission
        self._project_state["research_phases"] = research_phases
        self._project_state["current_phase"] = research_phases[0] if research_phases else "initialization"
        
        self._logger.info("Project initialized", 
                         mission=mission, 
                         phases=research_phases)
        
        # Notify all subordinates of project initialization
        await self.broadcast_to_subordinates({
            "type": "project_initialization",
            "mission": mission,
            "current_phase": self._project_state["current_phase"],
            "research_phases": research_phases,
        }, "project_update")

    async def decompose_research_phase(self, phase: str) -> List[Task]:
        """Decompose a research phase into specific tasks for subordinate agents."""
        tasks = []
        
        if phase == "architecture_design":
            # Tasks for Daedalus (Cognitive Architect)
            tasks.append(Task(
                name="Design Hybrid Neuro-Symbolic Core",
                description="Develop the core AGI architecture integrating neural and symbolic components",
                priority=Priority.CRITICAL,
                metadata={"target_agent": "daedalus", "phase": phase}
            ))
            
            # Tasks for Logos (Symbolic Reasoner)
            tasks.append(Task(
                name="Develop Formal Logic Systems",
                description="Create formal logic systems and knowledge graphs for System 2 reasoning",
                priority=Priority.HIGH,
                metadata={"target_agent": "logos", "phase": phase}
            ))
            
        elif phase == "embodied_learning":
            # Tasks for Odysseus (Embodied Explorer)
            tasks.append(Task(
                name="Design Simulation Environment",
                description="Create high-fidelity simulation environment for embodied learning",
                priority=Priority.HIGH,
                metadata={"target_agent": "odysseus", "phase": phase}
            ))
            
        elif phase == "safety_validation":
            # Tasks for Themis (Safety Overseer)
            tasks.append(Task(
                name="Comprehensive Safety Audit",
                description="Perform comprehensive safety audit of all system components",
                priority=Priority.CRITICAL,
                metadata={"target_agent": "themis", "phase": phase}
            ))

        self._logger.info("Decomposed research phase", phase=phase, task_count=len(tasks))
        return tasks

    async def allocate_resources(self, agent_id: AgentId, resources: Dict[str, Any]) -> None:
        """Allocate computational resources to an agent."""
        self._project_state["resource_allocation"][str(agent_id)] = resources
        
        await self.send_message(agent_id, {
            "type": "resource_allocation",
            "resources": resources,
        }, "resource_management")
        
        self._logger.info("Resources allocated", 
                         agent_id=str(agent_id), 
                         resources=resources)

    async def synthesize_findings(self) -> Dict[str, Any]:
        """Synthesize findings from all subordinate agents."""
        synthesis = {
            "phase": self._project_state["current_phase"],
            "agent_contributions": {},
            "key_insights": [],
            "next_steps": [],
            "challenges": [],
        }
        
        # Collect reports from all agents
        for agent_id, reports in self._project_state["agent_reports"].items():
            if reports:
                latest_report = reports[-1]  # Get most recent report
                synthesis["agent_contributions"][agent_id] = latest_report
                
                # Extract key insights
                if "insights" in latest_report:
                    synthesis["key_insights"].extend(latest_report["insights"])
                
                # Extract challenges
                if "challenges" in latest_report:
                    synthesis["challenges"].extend(latest_report["challenges"])

        self._logger.info("Synthesized findings", synthesis=synthesis)
        return synthesis

    async def advance_to_next_phase(self) -> bool:
        """Advance project to the next research phase."""
        current_idx = self._project_state["research_phases"].index(
            self._project_state["current_phase"]
        )
        
        if current_idx < len(self._project_state["research_phases"]) - 1:
            next_phase = self._project_state["research_phases"][current_idx + 1]
            self._project_state["current_phase"] = next_phase
            
            # Notify all subordinates
            await self.broadcast_to_subordinates({
                "type": "phase_transition",
                "new_phase": next_phase,
            }, "project_update")
            
            self._logger.info("Advanced to next phase", phase=next_phase)
            return True
        
        self._logger.info("Project completed - no more phases")
        return False

    async def _process_message_internal(self, message: Message) -> Optional[Message]:
        """Process incoming messages from subordinate agents."""
        content = message.content
        message_type = message.message_type
        
        if message_type == "agent_report":
            # Store agent report
            agent_id = str(message.sender_id)
            if agent_id not in self._project_state["agent_reports"]:
                self._project_state["agent_reports"][agent_id] = []
            
            self._project_state["agent_reports"][agent_id].append(content)
            self._logger.info("Received agent report", agent_id=agent_id)
            
            # Check if we have reports from all active subordinates
            if len(self._project_state["agent_reports"]) >= len(self._subordinates):
                synthesis = await self.synthesize_findings()
                # Consider advancing to next phase
                await self._evaluate_phase_completion()
        
        elif message_type == "safety_alert":
            # Handle safety alerts from Themis with highest priority
            self._logger.warning("Safety alert received", alert=content)
            
            # Broadcast safety alert to all agents
            await self.broadcast_to_subordinates({
                "type": "safety_alert",
                "alert": content,
                "action_required": True,
            }, "safety_alert")
        
        elif message_type == "resource_request":
            # Handle resource requests from subordinates
            requested_resources = content.get("resources", {})
            await self.allocate_resources(message.sender_id, requested_resources)
        
        return None

    async def _execute_task_internal(self, task: Task) -> Dict[str, Any]:
        """Execute strategic planning and coordination tasks."""
        task_name = task.name
        
        if "strategic_planning" in task_name.lower():
            return await self._perform_strategic_planning(task)
        elif "resource_optimization" in task_name.lower():
            return await self._optimize_resource_allocation(task)
        elif "progress_evaluation" in task_name.lower():
            return await self._evaluate_project_progress(task)
        else:
            return {"status": "completed", "message": f"Generic task {task_name} completed"}

    async def _perform_strategic_planning(self, task: Task) -> Dict[str, Any]:
        """Perform strategic planning for the project."""
        current_phase = self._project_state["current_phase"]
        
        # Generate tasks for current phase
        phase_tasks = await self.decompose_research_phase(current_phase)
        
        # Assign tasks to appropriate agents
        for task_item in phase_tasks:
            target_agent = task_item.metadata.get("target_agent")
            if target_agent and target_agent in [str(sub) for sub in self._subordinates]:
                # Send task assignment to target agent
                await self.send_message(
                    AgentId(target_agent), 
                    {"type": "task_assignment", "task": task_item}, 
                    "task_assignment"
                )
        
        return {
            "status": "completed",
            "tasks_generated": len(phase_tasks),
            "current_phase": current_phase,
        }

    async def _optimize_resource_allocation(self, task: Task) -> Dict[str, Any]:
        """Optimize resource allocation across agents."""
        # Simple resource optimization logic
        total_resources = 100  # Example: 100 units of computational resources
        agent_count = len(self._subordinates)
        
        if agent_count > 0:
            base_allocation = total_resources // agent_count
            
            for agent_id in self._subordinates:
                await self.allocate_resources(agent_id, {
                    "compute_units": base_allocation,
                    "memory_gb": base_allocation * 2,
                    "priority_level": "normal",
                })
        
        return {
            "status": "completed",
            "total_resources": total_resources,
            "agents_allocated": agent_count,
        }

    async def _evaluate_project_progress(self, task: Task) -> Dict[str, Any]:
        """Evaluate overall project progress."""
        synthesis = await self.synthesize_findings()
        
        # Simple progress evaluation
        completed_tasks = len([
            report for reports in self._project_state["agent_reports"].values()
            for report in reports if report.get("status") == "completed"
        ])
        
        progress_score = min(completed_tasks * 20, 100)  # Simple scoring
        
        return {
            "status": "completed",
            "progress_score": progress_score,
            "synthesis": synthesis,
            "current_phase": self._project_state["current_phase"],
        }

    async def _evaluate_phase_completion(self) -> None:
        """Evaluate if current phase is ready for completion."""
        # Simple completion criteria - all subordinates have reported
        if len(self._project_state["agent_reports"]) >= len(self._subordinates):
            synthesis = await self.synthesize_findings()
            
            # Check if phase objectives are met
            if self._phase_objectives_met(synthesis):
                await self.advance_to_next_phase()

    def _phase_objectives_met(self, synthesis: Dict[str, Any]) -> bool:
        """Check if current phase objectives are met."""
        # Simple criteria - no critical challenges reported
        critical_challenges = [
            challenge for challenge in synthesis.get("challenges", [])
            if challenge.get("severity") == "critical"
        ]
        
        return len(critical_challenges) == 0

    async def get_project_status(self) -> Dict[str, Any]:
        """Get comprehensive project status."""
        return {
            "project_state": self._project_state,
            "agent_status": await self.get_status(),
            "synthesis": await self.synthesize_findings(),
        }