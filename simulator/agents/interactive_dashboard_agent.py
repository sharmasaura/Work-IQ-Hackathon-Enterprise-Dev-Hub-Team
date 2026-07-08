"""
Interactive Dashboard Agent - Generates aggregated metrics and KPI snapshot
"""
from datetime import datetime
import json


class InteractiveDashboardAgent:
    """Generates comprehensive dashboard with health metrics, blockers, and KPIs."""

    SCENARIO_TEMPLATES = {
        "c1-northbridge": {
            "scenario_name": "Northbridge Infrastructure Dashboard",
            "health_status": "At Risk",
            "health_color": "yellow",
            "kpis": [
                {"label": "System Uptime", "value": "99.2%", "target": "99.9%", "status": "warning"},
                {"label": "Incident Response Time", "value": "8.3 min", "target": "<5 min", "status": "warning"},
                {"label": "Mean Time to Resolution", "value": "2.1 hrs", "target": "<1 hr", "status": "critical"},
                {"label": "Active Incidents", "value": "1", "target": "0", "status": "warning"}
            ],
            "top_blockers": [
                {"title": "Database Connection Pool", "severity": "high", "owner": "Infrastructure Team", "age_days": 2},
                {"title": "Performance Degradation", "severity": "medium", "owner": "SRE Lead", "age_days": 1}
            ],
            "top_actions": [
                {"action": "Implement connection pool monitoring", "owner": "Marcus", "due": "2026-07-08", "priority": "critical"},
                {"action": "Upgrade database driver", "owner": "Infrastructure", "due": "2026-07-10", "priority": "high"},
                {"action": "Capacity planning review", "owner": "Arch Team", "due": "2026-07-15", "priority": "medium"}
            ]
        },
        "c2-contoso": {
            "scenario_name": "Contoso Release Dashboard",
            "health_status": "Healthy",
            "health_color": "green",
            "kpis": [
                {"label": "Release Readiness", "value": "85%", "target": "90%", "status": "success"},
                {"label": "Test Coverage", "value": "92%", "target": ">85%", "status": "success"},
                {"label": "Critical Issues", "value": "0", "target": "0", "status": "success"},
                {"label": "Days to Release", "value": "3", "target": "5", "status": "success"}
            ],
            "top_blockers": [
                {"title": "Performance optimization pending", "severity": "low", "owner": "Performance Team", "age_days": 1}
            ],
            "top_actions": [
                {"action": "Final security review", "owner": "Security Team", "due": "2026-07-07", "priority": "high"},
                {"action": "Load testing validation", "owner": "QA", "due": "2026-07-08", "priority": "high"},
                {"action": "Release notes finalization", "owner": "Product", "due": "2026-07-10", "priority": "medium"}
            ]
        },
        "c3-meridian": {
            "scenario_name": "Meridian Compliance Dashboard",
            "health_status": "At Risk",
            "health_color": "yellow",
            "kpis": [
                {"label": "Compliance Score", "value": "95%", "target": "100%", "status": "warning"},
                {"label": "Documentation Complete", "value": "23/23", "target": "23/23", "status": "success"},
                {"label": "Days to Audit", "value": "35", "target": "45+", "status": "success"},
                {"label": "Critical Gaps", "value": "0", "target": "0", "status": "success"}
            ],
            "top_blockers": [
                {"title": "Data retention policy validation", "severity": "high", "owner": "Compliance", "age_days": 3},
                {"title": "Audit trail review", "severity": "medium", "owner": "Security", "age_days": 1}
            ],
            "top_actions": [
                {"action": "Complete data retention audit", "owner": "Compliance Officer", "due": "2026-07-10", "priority": "critical"},
                {"action": "Update audit logging", "owner": "Security Team", "due": "2026-07-12", "priority": "high"},
                {"action": "Document remediation", "owner": "Compliance", "due": "2026-07-15", "priority": "medium"}
            ]
        },
        "c4-arundel": {
            "scenario_name": "Arundel Operations Dashboard",
            "health_status": "Healthy",
            "health_color": "green",
            "kpis": [
                {"label": "Queue Processing Rate", "value": "98%", "target": ">90%", "status": "success"},
                {"label": "Average Resolution Time", "value": "2.1 days", "target": "<3 days", "status": "success"},
                {"label": "Pending Work Orders", "value": "243", "target": "<300", "status": "success"},
                {"label": "Team Utilization", "value": "87%", "target": "80-95%", "status": "success"}
            ],
            "top_blockers": [
                {"title": "Vendor response delays", "severity": "low", "owner": "Vendor Liaison", "age_days": 2}
            ],
            "top_actions": [
                {"action": "Review work order prioritization", "owner": "Ops Manager", "due": "2026-07-10", "priority": "medium"},
                {"action": "Team capacity planning", "owner": "HR", "due": "2026-07-15", "priority": "medium"},
                {"action": "Process optimization review", "owner": "Process Lead", "due": "2026-07-20", "priority": "low"}
            ]
        },
        "c5-westbrook": {
            "scenario_name": "Westbrook Accreditation Dashboard",
            "health_status": "On Track",
            "health_color": "green",
            "kpis": [
                {"label": "Accreditation Readiness", "value": "85%", "target": "100%", "status": "success"},
                {"label": "Documentation Progress", "value": "19/23", "target": "23/23", "status": "warning"},
                {"label": "Days Remaining", "value": "85", "target": ">30", "status": "success"},
                {"label": "Critical Gaps", "value": "0", "target": "0", "status": "success"}
            ],
            "top_blockers": [
                {"title": "Quality metrics documentation", "severity": "medium", "owner": "Quality Lead", "age_days": 3},
                {"title": "Training record compilation", "severity": "low", "owner": "HR", "age_days": 2}
            ],
            "top_actions": [
                {"action": "Complete quality documentation", "owner": "Quality Lead", "due": "2026-08-10", "priority": "high"},
                {"action": "Finalize training records", "owner": "HR Manager", "due": "2026-08-15", "priority": "high"},
                {"action": "Internal review preparation", "owner": "Accreditation Lead", "due": "2026-08-30", "priority": "medium"}
            ]
        },
        "c6-edkh": {
            "scenario_name": "EDKH System Dashboard",
            "health_status": "Healthy",
            "health_color": "green",
            "kpis": [
                {"label": "System Uptime", "value": "100%", "target": "99.9%", "status": "success"},
                {"label": "Migration Success", "value": "100%", "target": "100%", "status": "success"},
                {"label": "Data Integrity", "value": "100%", "target": "100%", "status": "success"},
                {"label": "Performance Baseline", "value": "Met", "target": "Met", "status": "success"}
            ],
            "top_blockers": [],
            "top_actions": [
                {"action": "Monitor system stability", "owner": "Operations", "due": "2026-07-13", "priority": "medium"},
                {"action": "Gather user feedback", "owner": "Product", "due": "2026-07-20", "priority": "medium"},
                {"action": "Performance optimization", "owner": "Platform Team", "due": "2026-07-30", "priority": "low"}
            ]
        }
    }

    @staticmethod
    def generate(scenario, persona_id, last_response=None, conversation_history=None):
        """
        Generate interactive dashboard with KPIs, blockers, and actions.
        
        Args:
            scenario: Scenario object with .name property
            persona_id: Current persona identifier
            last_response: Previous response (unused)
            conversation_history: Conversation context (unused)
        
        Returns:
            dict with dashboard metrics
        """
        # Get scenario name
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        # Get template or use generic
        if scenario_name in InteractiveDashboardAgent.SCENARIO_TEMPLATES:
            template = InteractiveDashboardAgent.SCENARIO_TEMPLATES[scenario_name]
        else:
            template = {
                "scenario_name": f"Generic Dashboard for {scenario_name}",
                "health_status": "On Track",
                "health_color": "green",
                "kpis": [
                    {"label": "Overall Progress", "value": "72%", "target": "80%", "status": "warning"},
                    {"label": "Active Metrics", "value": "8", "target": "10", "status": "warning"},
                    {"label": "Critical Issues", "value": "0", "target": "0", "status": "success"},
                    {"label": "Team Alignment", "value": "85%", "target": ">80%", "status": "success"}
                ],
                "top_blockers": [
                    {"title": "Generic blocker", "severity": "medium", "owner": "Team Lead", "age_days": 1}
                ],
                "top_actions": [
                    {"action": "Review metrics", "owner": "Manager", "due": "2026-07-10", "priority": "medium"},
                    {"action": "Team synchronization", "owner": "Lead", "due": "2026-07-15", "priority": "medium"}
                ]
            }
        
        # Count status indicators
        critical_count = sum(1 for kpi in template['kpis'] if kpi['status'] == 'critical')
        warning_count = sum(1 for kpi in template['kpis'] if kpi['status'] == 'warning')
        success_count = sum(1 for kpi in template['kpis'] if kpi['status'] == 'success')
        
        return {
            'success': True,
            'scenario': scenario_name,
            'scenario_display': template['scenario_name'],
            'health_status': template['health_status'],
            'health_color': template['health_color'],
            'kpis': template['kpis'],
            'kpi_summary': {
                'total': len(template['kpis']),
                'critical': critical_count,
                'warning': warning_count,
                'success': success_count
            },
            'top_blockers': template['top_blockers'],
            'blocker_count': len(template['top_blockers']),
            'top_actions': template['top_actions'],
            'action_count': len(template['top_actions']),
            'critical_action_count': sum(1 for a in template['top_actions'] if a['priority'] == 'critical'),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
