"""
Action Recommendation Agent
Generates actionable recommendations with assigned owners and due dates.
"""
from datetime import datetime, timedelta
from pathlib import Path


class ActionRecommendationAgent:
    """Generate scenario-specific action recommendations."""
    
    # Scenario-specific templates with real organizational context
    SCENARIO_TEMPLATES = {
        "c1-northbridge": {
            "scenario_name": "Northbridge Health Network",
            "context": "Multi-clinic network managing CAPA tracking and credentialing compliance",
            "actions": [
                {
                    "action": "Complete CAPA audit for Q2 findings",
                    "description": "Review and validate all corrective actions from Q2 CAPA submissions",
                    "owner": "Maria Delgado",
                    "owner_role": "Quality Program Manager",
                    "due_date_offset": 7,
                    "priority": "high",
                    "category": "Quality"
                },
                {
                    "action": "Resolve EHR vendor credentialing delays",
                    "description": "Follow up with Lumina Health Systems on outstanding credentialing documentation",
                    "owner": "Sandra Okafor",
                    "owner_role": "Credentialing Manager",
                    "due_date_offset": 5,
                    "priority": "critical",
                    "category": "Compliance"
                },
                {
                    "action": "Review commercial terms with leadership",
                    "description": "Present vendor penalty and licensing cost analysis to operations leadership",
                    "owner": "James Whitaker",
                    "owner_role": "Director of Clinic Operations",
                    "due_date_offset": 14,
                    "priority": "medium",
                    "category": "Commercial"
                },
            ]
        },
        "c2-contoso": {
            "scenario_name": "Contoso Manufacturing",
            "context": "Program transition with quality and supplier risk management",
            "actions": [
                {
                    "action": "Complete supplier risk assessment",
                    "description": "Evaluate all critical suppliers for Q3 program continuation",
                    "owner": "Raj Patel",
                    "owner_role": "Senior Quality Engineer",
                    "due_date_offset": 10,
                    "priority": "high",
                    "category": "Quality"
                },
                {
                    "action": "Finalize customer escalation response",
                    "description": "Prepare executive summary of incident resolution for customer review",
                    "owner": "Sam Ortiz",
                    "owner_role": "Program Manager",
                    "due_date_offset": 3,
                    "priority": "critical",
                    "category": "Customer"
                },
                {
                    "action": "Negotiate supplier agreement updates",
                    "description": "Review and update commercial terms with key suppliers",
                    "owner": "Marcus Reed",
                    "owner_role": "Director (Escalation)",
                    "due_date_offset": 21,
                    "priority": "medium",
                    "category": "Commercial"
                },
            ]
        },
        "c3-meridian": {
            "scenario_name": "Meridian Energy Solutions",
            "context": "Professional services with engagement tracking and resource allocation",
            "actions": [
                {
                    "action": "Update engagement deliverables status",
                    "description": "Verify completion status and timeline for all active client engagements",
                    "owner": "Engagement Manager",
                    "owner_role": "Project Lead",
                    "due_date_offset": 4,
                    "priority": "high",
                    "category": "Delivery"
                },
                {
                    "action": "Review PSA resource utilization",
                    "description": "Analyze resource allocation vs. capacity for Q3 planning",
                    "owner": "Resource Director",
                    "owner_role": "Operations Manager",
                    "due_date_offset": 7,
                    "priority": "medium",
                    "category": "Operations"
                },
                {
                    "action": "Escalate resource conflict resolution",
                    "description": "Address competing resource demands between client engagements",
                    "owner": "Executive Sponsor",
                    "owner_role": "VP Operations",
                    "due_date_offset": 2,
                    "priority": "critical",
                    "category": "Escalation"
                },
            ]
        },
        "c4-arundel": {
            "scenario_name": "Arundel Municipal Services",
            "context": "Facilities maintenance with work order tracking and CMMS management",
            "actions": [
                {
                    "action": "Process pending work orders",
                    "description": "Review and prioritize backlog of maintenance requests",
                    "owner": "Maintenance Supervisor",
                    "owner_role": "Operations Lead",
                    "due_date_offset": 2,
                    "priority": "high",
                    "category": "Maintenance"
                },
                {
                    "action": "Update CMMS system records",
                    "description": "Ensure all completed maintenance activities are logged and tracked",
                    "owner": "Facilities Manager",
                    "owner_role": "System Administrator",
                    "due_date_offset": 5,
                    "priority": "medium",
                    "category": "Operations"
                },
                {
                    "action": "Schedule emergency repair assessment",
                    "description": "Evaluate critical facility infrastructure for preventive maintenance",
                    "owner": "Capital Projects Manager",
                    "owner_role": "Planning Director",
                    "due_date_offset": 3,
                    "priority": "critical",
                    "category": "Planning"
                },
            ]
        },
        "c5-westbrook": {
            "scenario_name": "Westbrook Education Group",
            "context": "Academic institution with accreditation tracking and AOL reporting",
            "actions": [
                {
                    "action": "Submit accreditation progress report",
                    "description": "Compile and submit Q2 accreditation compliance documentation",
                    "owner": "Accreditation Coordinator",
                    "owner_role": "Compliance Lead",
                    "due_date_offset": 6,
                    "priority": "critical",
                    "category": "Compliance"
                },
                {
                    "action": "Finalize AOL assessment results",
                    "description": "Complete assessment of learning outcomes and program effectiveness",
                    "owner": "Assessment Director",
                    "owner_role": "Academic Lead",
                    "due_date_offset": 10,
                    "priority": "high",
                    "category": "Academic"
                },
                {
                    "action": "Review budget allocations for next cycle",
                    "description": "Analyze departmental budgets and resource requests for next fiscal year",
                    "owner": "Finance Director",
                    "owner_role": "CFO",
                    "due_date_offset": 14,
                    "priority": "medium",
                    "category": "Finance"
                },
            ]
        },
        "c6-edkh": {
            "scenario_name": "EDKH Platform",
            "context": "On-call operations with action tracking and incident management",
            "actions": [
                {
                    "action": "Review and resolve open incidents",
                    "description": "Triage all open incidents and assign to on-call teams",
                    "owner": "On-Call Lead",
                    "owner_role": "SRE Lead",
                    "due_date_offset": 1,
                    "priority": "critical",
                    "category": "Operations"
                },
                {
                    "action": "Update run-book procedures",
                    "description": "Document lessons learned from recent incidents and update playbooks",
                    "owner": "Platform Engineer",
                    "owner_role": "SRE Engineer",
                    "due_date_offset": 7,
                    "priority": "high",
                    "category": "Knowledge"
                },
                {
                    "action": "Schedule architecture review",
                    "description": "Review platform scaling and reliability improvements for next quarter",
                    "owner": "Architecture Lead",
                    "owner_role": "Technical Director",
                    "due_date_offset": 14,
                    "priority": "medium",
                    "category": "Strategy"
                },
            ]
        }
    }
    
    @staticmethod
    def generate(scenario, persona_id: str = None, last_response: str = None, 
                conversation_history: list = None) -> dict:
        """
        Generate action recommendations for a scenario.
        
        Args:
            scenario: Loaded scenario object
            persona_id: Current persona (for filtering recommendations)
            last_response: Last AI response (for context)
            conversation_history: Full conversation history
            
        Returns:
            dict with action recommendations and metadata
        """
        # Get scenario name from object
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        template = ActionRecommendationAgent.SCENARIO_TEMPLATES.get(
            scenario_name,
            ActionRecommendationAgent._get_generic_template()
        )
        
        # Calculate due dates
        today = datetime.now()
        actions = []
        
        for action_template in template.get("actions", []):
            due_date = today + timedelta(days=action_template.get("due_date_offset", 7))
            
            actions.append({
                "action": action_template.get("action", ""),
                "description": action_template.get("description", ""),
                "owner": action_template.get("owner", ""),
                "owner_role": action_template.get("owner_role", ""),
                "due_date": due_date.isoformat(),
                "priority": action_template.get("priority", "medium"),
                "category": action_template.get("category", "General"),
                "status": "pending"
            })
        
        return {
            "success": True,
            "scenario": template.get("scenario_name", scenario_name),
            "context": template.get("context", ""),
            "actions": actions,
            "total_actions": len(actions),
            "critical_count": sum(1 for a in actions if a["priority"] == "critical"),
            "high_count": sum(1 for a in actions if a["priority"] == "high"),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def _get_generic_template() -> dict:
        """Return generic fallback template for unknown scenarios."""
        return {
            "scenario_name": "Unknown Scenario",
            "context": "Generic organizational context",
            "actions": [
                {
                    "action": "Review pending items",
                    "description": "Assess all pending work items and prioritize next steps",
                    "owner": "Team Lead",
                    "owner_role": "Manager",
                    "due_date_offset": 7,
                    "priority": "medium",
                    "category": "General"
                },
                {
                    "action": "Schedule stakeholder sync",
                    "description": "Align on priorities and resource needs with stakeholders",
                    "owner": "Project Manager",
                    "owner_role": "Coordinator",
                    "due_date_offset": 3,
                    "priority": "medium",
                    "category": "Communication"
                },
                {
                    "action": "Document process improvements",
                    "description": "Capture lessons learned and identify process optimization opportunities",
                    "owner": "Process Owner",
                    "owner_role": "Analyst",
                    "due_date_offset": 10,
                    "priority": "low",
                    "category": "Process"
                }
            ]
        }
