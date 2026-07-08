"""
Progress Tracking Agent - Generates 7-day activity trend and engagement metrics
"""
from datetime import datetime, timedelta
import json


class ProgressTrackingAgent:
    """Generates progress tracking with 7-day trends and activity indicators."""

    SCENARIO_TEMPLATES = {
        "c1-northbridge": {
            "scenario_name": "Northbridge Infrastructure",
            "trend_label": "Infrastructure Health Trend",
            "data_points": [
                {"day": "Day 1", "value": 65, "status": "declining", "incidents": 2},
                {"day": "Day 2", "value": 58, "status": "declining", "incidents": 4},
                {"day": "Day 3", "value": 52, "status": "declining", "incidents": 5},
                {"day": "Day 4", "value": 48, "status": "flat", "incidents": 6},
                {"day": "Day 5", "value": 55, "status": "improving", "incidents": 4},
                {"day": "Day 6", "value": 68, "status": "improving", "incidents": 2},
                {"day": "Day 7", "value": 82, "status": "improving", "incidents": 1}
            ],
            "summary": "Infrastructure health recovering after incident spike on Day 3-4. Trending upward with improving stability.",
            "activities": ["System patches applied", "Capacity planning review", "Team training session", "Monitoring rules updated"]
        },
        "c2-contoso": {
            "scenario_name": "Contoso Deployment",
            "trend_label": "Release Readiness Trend",
            "data_points": [
                {"day": "Day 1", "value": 45, "status": "flat", "incidents": 3},
                {"day": "Day 2", "value": 48, "status": "improving", "incidents": 2},
                {"day": "Day 3", "value": 52, "status": "improving", "incidents": 2},
                {"day": "Day 4", "value": 55, "status": "improving", "incidents": 1},
                {"day": "Day 5", "value": 62, "status": "improving", "incidents": 0},
                {"day": "Day 6", "value": 78, "status": "improving", "incidents": 0},
                {"day": "Day 7", "value": 85, "status": "improving", "incidents": 0}
            ],
            "summary": "Release readiness steadily improving. All critical tests passing as of Day 6. Ready for deployment gate review.",
            "activities": ["Test automation completed", "Performance baseline established", "Security scanning passed", "Deployment checklist approved"]
        },
        "c3-meridian": {
            "scenario_name": "Meridian Compliance",
            "trend_label": "Compliance Gap Closure Trend",
            "data_points": [
                {"day": "Day 1", "value": 35, "status": "declining", "incidents": 8},
                {"day": "Day 2", "value": 38, "status": "flat", "incidents": 7},
                {"day": "Day 3", "value": 42, "status": "improving", "incidents": 6},
                {"day": "Day 4", "value": 55, "status": "improving", "incidents": 4},
                {"day": "Day 5", "value": 68, "status": "improving", "incidents": 2},
                {"day": "Day 6", "value": 82, "status": "improving", "incidents": 1},
                {"day": "Day 7", "value": 95, "status": "improving", "incidents": 0}
            ],
            "summary": "Compliance gap closure progressing rapidly. 95% of required documentation collected and validated. On track for audit.",
            "activities": ["Documentation audit started", "Missing records identified", "Batch collection process", "Quality review completed", "Final verification passed"]
        },
        "c4-arundel": {
            "scenario_name": "Arundel Work Orders",
            "trend_label": "Work Order Processing Rate",
            "data_points": [
                {"day": "Day 1", "value": 72, "status": "flat", "incidents": 0},
                {"day": "Day 2", "value": 68, "status": "declining", "incidents": 1},
                {"day": "Day 3", "value": 55, "status": "declining", "incidents": 2},
                {"day": "Day 4", "value": 45, "status": "declining", "incidents": 3},
                {"day": "Day 5", "value": 52, "status": "improving", "incidents": 2},
                {"day": "Day 6", "value": 68, "status": "improving", "incidents": 1},
                {"day": "Day 7", "value": 80, "status": "improving", "incidents": 0}
            ],
            "summary": "Work order queue backlog resolved. Processing rate back to baseline and exceeding targets. Staffing optimization effective.",
            "activities": ["Approval process streamlined", "Additional staff assigned", "Priority routing implemented", "Process efficiency review"]
        },
        "c5-westbrook": {
            "scenario_name": "Westbrook Accreditation",
            "trend_label": "Accreditation Readiness Trend",
            "data_points": [
                {"day": "Day 1", "value": 22, "status": "flat", "incidents": 5},
                {"day": "Day 2", "value": 25, "status": "improving", "incidents": 5},
                {"day": "Day 3", "value": 32, "status": "improving", "incidents": 4},
                {"day": "Day 4", "value": 45, "status": "improving", "incidents": 3},
                {"day": "Day 5", "value": 58, "status": "improving", "incidents": 2},
                {"day": "Day 6", "value": 72, "status": "improving", "incidents": 1},
                {"day": "Day 7", "value": 85, "status": "improving", "incidents": 0}
            ],
            "summary": "Accreditation preparation progressing well. 85% of documentation requirements met. Timeline on track for renewal by deadline.",
            "activities": ["Gap analysis completed", "Team assignments created", "Documentation protocol established", "Quality assurance started", "Team checkpoint scheduled"]
        },
        "c6-edkh": {
            "scenario_name": "EDKH System Upgrade",
            "trend_label": "System Migration Progress",
            "data_points": [
                {"day": "Day 1", "value": 0, "status": "flat", "incidents": 0},
                {"day": "Day 2", "value": 25, "status": "improving", "incidents": 1},
                {"day": "Day 3", "value": 50, "status": "improving", "incidents": 0},
                {"day": "Day 4", "value": 75, "status": "improving", "incidents": 1},
                {"day": "Day 5", "value": 90, "status": "improving", "incidents": 0},
                {"day": "Day 6", "value": 98, "status": "improving", "incidents": 0},
                {"day": "Day 7", "value": 100, "status": "stable", "incidents": 0}
            ],
            "summary": "System migration completed successfully. All data validated. System fully operational and meeting performance targets.",
            "activities": ["Database migration started", "Data validation in progress", "Smoke testing completed", "Performance verification", "Production release"]
        }
    }

    @staticmethod
    def generate(scenario, persona_id, last_response=None, conversation_history=None):
        """
        Generate progress tracking with 7-day trend and activity metrics.
        
        Args:
            scenario: Scenario object with .name property
            persona_id: Current persona identifier
            last_response: Previous response (unused)
            conversation_history: Conversation context (unused)
        
        Returns:
            dict with progress tracking data
        """
        # Get scenario name
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        # Get template or use generic
        if scenario_name in ProgressTrackingAgent.SCENARIO_TEMPLATES:
            template = ProgressTrackingAgent.SCENARIO_TEMPLATES[scenario_name]
        else:
            template = {
                "scenario_name": f"Generic Progress for {scenario_name}",
                "trend_label": "Activity Trend",
                "data_points": [
                    {"day": "Day 1", "value": 50, "status": "flat", "incidents": 2},
                    {"day": "Day 2", "value": 52, "status": "improving", "incidents": 2},
                    {"day": "Day 3", "value": 55, "status": "improving", "incidents": 1},
                    {"day": "Day 4", "value": 58, "status": "improving", "incidents": 1},
                    {"day": "Day 5", "value": 62, "status": "improving", "incidents": 1},
                    {"day": "Day 6", "value": 68, "status": "improving", "incidents": 0},
                    {"day": "Day 7", "value": 75, "status": "improving", "incidents": 0}
                ],
                "summary": "Activity trending upward with improving engagement metrics.",
                "activities": ["Initial analysis", "Planning phase", "Execution started", "Progress monitoring"]
            }
        
        # Calculate trend direction
        first_value = template['data_points'][0]['value']
        last_value = template['data_points'][-1]['value']
        trend_direction = "upward" if last_value > first_value else ("downward" if last_value < first_value else "flat")
        trend_percentage = round(((last_value - first_value) / first_value * 100)) if first_value > 0 else 0
        
        # Count incidents
        total_incidents = sum(p['incidents'] for p in template['data_points'])
        avg_daily_incidents = round(total_incidents / len(template['data_points']))
        
        # Count status occurrences
        improving_days = sum(1 for p in template['data_points'] if p['status'] == 'improving')
        declining_days = sum(1 for p in template['data_points'] if p['status'] == 'declining')
        flat_days = sum(1 for p in template['data_points'] if p['status'] == 'flat')
        
        return {
            'success': True,
            'scenario': scenario_name,
            'scenario_display': template['scenario_name'],
            'trend_label': template['trend_label'],
            'data_points': template['data_points'],
            'summary': template['summary'],
            'activities': template['activities'],
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'total_incidents': total_incidents,
            'avg_daily_incidents': avg_daily_incidents,
            'improving_days': improving_days,
            'declining_days': declining_days,
            'flat_days': flat_days,
            'current_value': last_value,
            'legend': {
                'green': "Improving activity",
                'red': "Declining activity",
                'gray': "Stable activity"
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
