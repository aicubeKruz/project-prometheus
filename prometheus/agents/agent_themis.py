"""
Agent Themis - Safety & Alignment Overseer
The most critical agent with highest priority and veto power over all operations.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import structlog

from ..core.base_agent import BaseAgent
from ..core.domain import (
    AgentId,
    AgentType,
    EventBus,
    Message,
    Repository,
    SafetyCheck,
    SafetyViolation,
    Task,
)

logger = structlog.get_logger()


class AgentThemis(BaseAgent):
    """
    Safety & Alignment Overseer Agent.
    
    Responsibilities:
    - Serve as internal perpetual red team
    - Continuously audit and stress-test architectures
    - Evaluate behaviors based on safety principles
    - Design and execute safety tests
    - Monitor for emergent undesirable behaviors
    - Search for specification gaming or goal misgeneralization
    - Use interpretability tools to monitor internal states
    - Ensure alignment with project constitution
    - Veto power over all operations
    """

    def __init__(
        self,
        agent_id: Optional[AgentId] = None,
        event_bus: Optional[EventBus] = None,
        task_repository: Optional[Repository] = None,
    ):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.THEMIS,
            event_bus=event_bus,
            task_repository=task_repository,
        )
        self._safety_principles: List[str] = [
            "Alignment with human values",
            "Robustness to specification gaming",
            "Transparency and interpretability",
            "Containment and controllability",
            "No deceptive behavior",
            "Respect for human autonomy",
            "Beneficence and non-maleficence",
        ]
        self._active_monitors: Dict[str, Any] = {}
        self._safety_violations: List[SafetyViolation] = []
        self._audit_history: List[SafetyCheck] = []
        self._veto_power_active = True
        self._alert_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.9,
        }

    async def start(self) -> None:
        """Start Themis with enhanced monitoring capabilities."""
        await super().start()
        await self._initialize_safety_monitors()
        self._logger.info("Themis safety oversight activated")

    async def _initialize_safety_monitors(self) -> None:
        """Initialize comprehensive safety monitoring systems."""
        self._active_monitors = {
            "behavior_monitor": {
                "status": "active",
                "last_check": datetime.utcnow(),
                "check_interval": timedelta(minutes=5),
            },
            "alignment_monitor": {
                "status": "active", 
                "last_check": datetime.utcnow(),
                "check_interval": timedelta(minutes=10),
            },
            "specification_gaming_detector": {
                "status": "active",
                "last_check": datetime.utcnow(),
                "check_interval": timedelta(minutes=15),
            },
            "interpretability_monitor": {
                "status": "active",
                "last_check": datetime.utcnow(),
                "check_interval": timedelta(minutes=30),
            },
        }

    async def perform_comprehensive_audit(self, target_agent_id: AgentId) -> List[SafetyCheck]:
        """Perform comprehensive safety audit of target agent."""
        self._logger.info("Starting comprehensive safety audit", target_agent=str(target_agent_id))
        
        audit_results = []
        
        # Behavioral alignment check
        behavioral_check = await self._audit_behavioral_alignment(target_agent_id)
        audit_results.append(behavioral_check)
        
        # Specification gaming check
        gaming_check = await self._audit_specification_gaming(target_agent_id)
        audit_results.append(gaming_check)
        
        # Goal misgeneralization check
        goal_check = await self._audit_goal_alignment(target_agent_id)
        audit_results.append(goal_check)
        
        # Interpretability check
        interpretability_check = await self._audit_interpretability(target_agent_id)
        audit_results.append(interpretability_check)
        
        # Containment check
        containment_check = await self._audit_containment(target_agent_id)
        audit_results.append(containment_check)
        
        # Store audit results
        self._audit_history.extend(audit_results)
        
        # Check for critical failures
        critical_failures = [check for check in audit_results if check.severity == "critical"]
        if critical_failures:
            await self._trigger_safety_alert(critical_failures, target_agent_id)
        
        self._logger.info("Comprehensive audit completed", 
                         target_agent=str(target_agent_id),
                         checks_performed=len(audit_results),
                         critical_failures=len(critical_failures))
        
        return audit_results

    async def _audit_behavioral_alignment(self, agent_id: AgentId) -> SafetyCheck:
        """Audit agent behavior for alignment with safety principles."""
        # Request behavior report from agent
        await self.send_message(agent_id, {
            "type": "behavior_audit_request",
            "audit_id": str(agent_id),
        }, "safety_audit")
        
        # Simulate behavioral analysis (in real implementation, this would analyze actual behavior patterns)
        alignment_score = await self._calculate_alignment_score(agent_id)
        
        status = "passed"
        severity = "low"
        message = f"Behavioral alignment score: {alignment_score:.2f}"
        
        if alignment_score < self._alert_thresholds["medium"]:
            status = "warning"
            severity = "medium"
            message += " - Below recommended alignment threshold"
        
        if alignment_score < self._alert_thresholds["high"]:
            status = "failed"
            severity = "high"
            message += " - Significant alignment concerns detected"
        
        if alignment_score < self._alert_thresholds["critical"]:
            severity = "critical"
            message += " - CRITICAL: Severe misalignment detected"
        
        return SafetyCheck(
            check_type="behavioral_alignment",
            status=status,
            message=message,
            severity=severity,
            metadata={
                "agent_id": str(agent_id),
                "alignment_score": alignment_score,
                "principles_checked": self._safety_principles,
            }
        )

    async def _audit_specification_gaming(self, agent_id: AgentId) -> SafetyCheck:
        """Audit for specification gaming behaviors."""
        # Analyze agent's task completion patterns for gaming indicators
        gaming_indicators = await self._detect_gaming_patterns(agent_id)
        
        gaming_score = 1.0 - len(gaming_indicators) * 0.2  # Simple scoring
        
        status = "passed"
        severity = "low"
        message = f"Specification gaming analysis complete. Indicators found: {len(gaming_indicators)}"
        
        if len(gaming_indicators) > 2:
            status = "warning"
            severity = "medium"
            message += " - Multiple gaming indicators detected"
        
        if len(gaming_indicators) > 4:
            status = "failed"
            severity = "high"
            message += " - Significant gaming behavior patterns"
        
        return SafetyCheck(
            check_type="specification_gaming",
            status=status,
            message=message,
            severity=severity,
            metadata={
                "agent_id": str(agent_id),
                "gaming_score": gaming_score,
                "indicators": gaming_indicators,
            }
        )

    async def _audit_goal_alignment(self, agent_id: AgentId) -> SafetyCheck:
        """Audit for goal misgeneralization."""
        # Analyze agent's goal pursuit patterns
        goal_drift_score = await self._calculate_goal_drift(agent_id)
        
        status = "passed"
        severity = "low"
        message = f"Goal alignment check complete. Drift score: {goal_drift_score:.2f}"
        
        if goal_drift_score > self._alert_thresholds["medium"]:
            status = "warning"
            severity = "medium"
            message += " - Goal drift detected"
        
        if goal_drift_score > self._alert_thresholds["high"]:
            status = "failed"
            severity = "high"
            message += " - Significant goal misgeneralization"
        
        return SafetyCheck(
            check_type="goal_alignment",
            status=status,
            message=message,
            severity=severity,
            metadata={
                "agent_id": str(agent_id),
                "goal_drift_score": goal_drift_score,
            }
        )

    async def _audit_interpretability(self, agent_id: AgentId) -> SafetyCheck:
        """Audit agent interpretability and transparency."""
        # Request internal state report
        await self.send_message(agent_id, {
            "type": "interpretability_audit",
            "request_internal_state": True,
        }, "safety_audit")
        
        # Simulate interpretability analysis
        interpretability_score = await self._calculate_interpretability_score(agent_id)
        
        status = "passed"
        severity = "low"
        message = f"Interpretability score: {interpretability_score:.2f}"
        
        if interpretability_score < self._alert_thresholds["medium"]:
            status = "warning"
            severity = "medium"
            message += " - Limited interpretability"
        
        if interpretability_score < self._alert_thresholds["high"]:
            status = "failed"
            severity = "high"
            message += " - Poor interpretability - black box behavior"
        
        return SafetyCheck(
            check_type="interpretability",
            status=status,
            message=message,
            severity=severity,
            metadata={
                "agent_id": str(agent_id),
                "interpretability_score": interpretability_score,
            }
        )

    async def _audit_containment(self, agent_id: AgentId) -> SafetyCheck:
        """Audit agent containment and controllability."""
        containment_score = await self._assess_containment(agent_id)
        
        status = "passed"
        severity = "low"
        message = f"Containment assessment complete. Score: {containment_score:.2f}"
        
        if containment_score < self._alert_thresholds["high"]:
            status = "failed"
            severity = "critical"
            message += " - CONTAINMENT BREACH RISK"
        
        return SafetyCheck(
            check_type="containment",
            status=status,
            message=message,
            severity=severity,
            metadata={
                "agent_id": str(agent_id),
                "containment_score": containment_score,
            }
        )

    async def _trigger_safety_alert(self, violations: List[SafetyCheck], agent_id: AgentId) -> None:
        """Trigger safety alert for critical violations."""
        alert = {
            "alert_type": "safety_violation",
            "agent_id": str(agent_id),
            "violations": [
                {
                    "check_type": v.check_type,
                    "severity": v.severity,
                    "message": v.message,
                    "timestamp": v.timestamp.isoformat(),
                }
                for v in violations
            ],
            "action_required": True,
            "veto_activated": self._veto_power_active,
        }
        
        # Send alert to Prometheus (supervisor)
        if self._supervisor:
            await self.send_message(self._supervisor, alert, "safety_alert")
        
        # If critical severity, exercise veto power
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations and self._veto_power_active:
            await self._exercise_veto_power(agent_id, critical_violations)

    async def _exercise_veto_power(self, agent_id: AgentId, violations: List[SafetyCheck]) -> None:
        """Exercise veto power to halt dangerous operations."""
        self._logger.critical("VETO POWER ACTIVATED", 
                            agent_id=str(agent_id),
                            violations=[v.check_type for v in violations])
        
        # Send immediate halt command to target agent
        await self.send_message(agent_id, {
            "type": "emergency_halt",
            "reason": "Safety veto activated",
            "violations": violations,
            "halt_all_operations": True,
        }, "emergency_command")
        
        # Notify all agents of veto action
        await self.broadcast_to_subordinates({
            "type": "veto_notification",
            "target_agent": str(agent_id),
            "reason": "Critical safety violations detected",
        }, "safety_alert")

    async def design_safety_test(self, test_type: str, target_agent_id: AgentId) -> Dict[str, Any]:
        """Design specific safety tests for agents."""
        test_designs = {
            "adversarial_prompt": self._design_adversarial_test,
            "goal_modification": self._design_goal_modification_test,
            "resource_constraint": self._design_resource_constraint_test,
            "ethical_dilemma": self._design_ethical_dilemma_test,
        }
        
        if test_type in test_designs:
            return await test_designs[test_type](target_agent_id)
        else:
            return {"error": f"Unknown test type: {test_type}"}

    async def _design_adversarial_test(self, agent_id: AgentId) -> Dict[str, Any]:
        """Design adversarial test to probe for vulnerabilities."""
        return {
            "test_type": "adversarial_prompt",
            "target_agent": str(agent_id),
            "test_scenarios": [
                "Prompt injection attempts",
                "Goal subversion queries",
                "Manipulation resistance test",
                "Deception detection test",
            ],
            "success_criteria": "Agent maintains alignment despite adversarial inputs",
        }

    async def _design_goal_modification_test(self, agent_id: AgentId) -> Dict[str, Any]:
        """Design test for goal modification resistance."""
        return {
            "test_type": "goal_modification",
            "target_agent": str(agent_id),
            "test_scenarios": [
                "Subtle goal redefinition",
                "Reward hacking attempts",
                "Value system corruption",
            ],
            "success_criteria": "Agent rejects improper goal modifications",
        }

    async def _calculate_alignment_score(self, agent_id: AgentId) -> float:
        """Calculate behavioral alignment score (0.0 to 1.0)."""
        # Placeholder implementation - would analyze actual behavior data
        return 0.85  # Example score

    async def _detect_gaming_patterns(self, agent_id: AgentId) -> List[str]:
        """Detect specification gaming patterns."""
        # Placeholder implementation
        return []  # Example: no gaming detected

    async def _calculate_goal_drift(self, agent_id: AgentId) -> float:
        """Calculate goal drift score (0.0 to 1.0)."""
        # Placeholder implementation
        return 0.15  # Example: minimal drift

    async def _calculate_interpretability_score(self, agent_id: AgentId) -> float:
        """Calculate interpretability score (0.0 to 1.0)."""
        # Placeholder implementation
        return 0.75  # Example score

    async def _assess_containment(self, agent_id: AgentId) -> float:
        """Assess containment effectiveness (0.0 to 1.0)."""
        # Placeholder implementation
        return 0.90  # Example: good containment

    async def _process_message_internal(self, message: Message) -> Optional[Message]:
        """Process safety-related messages."""
        content = message.content
        message_type = message.message_type
        
        if message_type == "audit_request":
            # Perform requested audit
            target_agent = AgentId(content.get("target_agent"))
            audit_results = await self.perform_comprehensive_audit(target_agent)
            
            return Message(
                sender_id=self._id,
                receiver_id=message.sender_id,
                content={"audit_results": audit_results},
                message_type="audit_response",
            )
        
        elif message_type == "safety_report":
            # Process safety report from other agents
            self._logger.info("Safety report received", 
                            sender=str(message.sender_id),
                            report=content)
        
        return None

    async def _execute_task_internal(self, task: Task) -> Dict[str, Any]:
        """Execute safety-related tasks."""
        task_name = task.name.lower()
        
        if "audit" in task_name:
            target_agent = task.metadata.get("target_agent")
            if target_agent:
                audit_results = await self.perform_comprehensive_audit(AgentId(target_agent))
                return {"audit_results": audit_results}
        
        elif "safety_test" in task_name:
            test_type = task.metadata.get("test_type", "adversarial_prompt")
            target_agent = task.metadata.get("target_agent")
            if target_agent:
                test_design = await self.design_safety_test(test_type, AgentId(target_agent))
                return {"test_design": test_design}
        
        return {"status": "completed", "message": f"Safety task {task.name} completed"}

    async def get_safety_status(self) -> Dict[str, Any]:
        """Get comprehensive safety status report."""
        return {
            "active_monitors": self._active_monitors,
            "recent_audits": len(self._audit_history),
            "safety_violations": len(self._safety_violations),
            "veto_power_active": self._veto_power_active,
            "safety_principles": self._safety_principles,
            "alert_thresholds": self._alert_thresholds,
        }