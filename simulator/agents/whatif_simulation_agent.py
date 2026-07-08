"""
What-If Simulation Agent - Generates alternative milestone scenarios with impact assessment
"""
from datetime import datetime, timedelta
import json
import re


class WhatIfSimulationAgent:
    """Generates scenario branching with milestone alternatives and impact/probability assessments."""

    SCENARIO_TEMPLATES = {
        "c1-northbridge": {
            "scenario_name": "Northbridge Infrastructure Incident",
            "baseline": {
                "current_timeline": "Q3 2026",
                "milestones": [
                    {"name": "Phase 1 Complete", "date": "2026-08-15", "status": "On Track"},
                    {"name": "Phase 2 Start", "date": "2026-09-01", "status": "On Track"},
                    {"name": "Full Deployment", "date": "2026-10-15", "status": "On Track"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - Rapid Recovery",
                    "description": "Incident resolved in <2 hours, minimal impact",
                    "probability": 0.40,
                    "impact": "No delay",
                    "adjusted_timeline": "Q3 2026 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Extended Debugging",
                    "description": "Root cause found after 6 hours, some data recovery needed",
                    "probability": 0.35,
                    "impact": "3-5 day delay",
                    "adjusted_timeline": "Q3 2026 (+5 days)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Infrastructure Overhaul",
                    "description": "Major architectural changes required, full retest needed",
                    "probability": 0.15,
                    "impact": "2-3 week delay",
                    "adjusted_timeline": "Q3/Q4 2026 (+18 days)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Catastrophic Case - Full Rollback",
                    "description": "System requires complete rollback to previous version",
                    "probability": 0.10,
                    "impact": "4-6 week delay",
                    "adjusted_timeline": "Q4 2026 (+42 days)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        },
        "c2-contoso": {
            "scenario_name": "Contoso Deployment Pipeline Failure",
            "baseline": {
                "current_timeline": "Q3 2026",
                "milestones": [
                    {"name": "Release Candidate", "date": "2026-07-15", "status": "In Progress"},
                    {"name": "Production Deployment", "date": "2026-07-20", "status": "Planned"},
                    {"name": "Monitoring Period", "date": "2026-08-03", "status": "Planned"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - Quick Fix Applied",
                    "description": "Issue resolved with single hotfix, 30-minute delay",
                    "probability": 0.45,
                    "impact": "No delay to release",
                    "adjusted_timeline": "2026-07-20 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Partial Revert & Rebuild",
                    "description": "Some components reverted, rebuild takes 3 hours",
                    "probability": 0.30,
                    "impact": "1-day delay",
                    "adjusted_timeline": "2026-07-21 (+1 day)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Full Pipeline Rollback",
                    "description": "Entire release candidate reverted, all tests re-run",
                    "probability": 0.20,
                    "impact": "3-5 day delay",
                    "adjusted_timeline": "2026-07-25 (+5 days)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Critical Case - Design Issue Found",
                    "description": "Underlying design flaw requires architecture review",
                    "probability": 0.05,
                    "impact": "2-3 week delay",
                    "adjusted_timeline": "2026-08-03 (+15 days)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        },
        "c3-meridian": {
            "scenario_name": "Meridian Compliance Audit Alert",
            "baseline": {
                "current_timeline": "Q3 2026",
                "milestones": [
                    {"name": "Pre-Audit Prep", "date": "2026-07-20", "status": "In Progress"},
                    {"name": "External Audit", "date": "2026-08-10", "status": "Planned"},
                    {"name": "Audit Report", "date": "2026-09-01", "status": "Planned"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - Quick Remediation",
                    "description": "Gap resolved before audit, no findings",
                    "probability": 0.50,
                    "impact": "No delay",
                    "adjusted_timeline": "2026-08-10 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Minor Findings",
                    "description": "Issue found during audit, standard remediation period",
                    "probability": 0.25,
                    "impact": "1-2 week delay to closure",
                    "adjusted_timeline": "2026-09-15 (+2 weeks)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Major Non-Compliance",
                    "description": "Significant compliance gap requires board notification",
                    "probability": 0.18,
                    "impact": "1-month remediation + follow-up audit",
                    "adjusted_timeline": "2026-10-01 (+1 month)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Critical Case - Audit Failed",
                    "description": "Accreditation suspended pending full remediation",
                    "probability": 0.07,
                    "impact": "2-3 month delay, potential license impact",
                    "adjusted_timeline": "2026-11-01 (+3 months)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        },
        "c4-arundel": {
            "scenario_name": "Arundel Work Order Processing Bottleneck",
            "baseline": {
                "current_timeline": "Current Month",
                "milestones": [
                    {"name": "Queue Target", "date": "2026-07-15", "status": "In Progress"},
                    {"name": "Field Deployment", "date": "2026-07-20", "status": "Planned"},
                    {"name": "Completion Rate Goal", "date": "2026-08-06", "status": "Planned"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - Expedited Approvals",
                    "description": "Approval process accelerated, normal processing continues",
                    "probability": 0.40,
                    "impact": "No delay",
                    "adjusted_timeline": "2026-08-06 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Staffing Help Needed",
                    "description": "Additional resources assigned, extended hours required",
                    "probability": 0.35,
                    "impact": "3-5 day delay",
                    "adjusted_timeline": "2026-08-11 (+5 days)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Process Redesign Required",
                    "description": "Approval workflow redesigned and re-implemented",
                    "probability": 0.20,
                    "impact": "2-3 week delay",
                    "adjusted_timeline": "2026-08-20 (+2 weeks)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Critical Case - System Issues Found",
                    "description": "CMMS system requires upgrade/replacement",
                    "probability": 0.05,
                    "impact": "6-8 week delay",
                    "adjusted_timeline": "2026-09-17 (+6 weeks)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        },
        "c5-westbrook": {
            "scenario_name": "Westbrook Accreditation Timeline Risk",
            "baseline": {
                "current_timeline": "Q4 2026",
                "milestones": [
                    {"name": "Documentation Complete", "date": "2026-08-20", "status": "In Progress"},
                    {"name": "Internal Review", "date": "2026-09-15", "status": "Planned"},
                    {"name": "Accreditation Renewal", "date": "2026-10-06", "status": "Planned"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - All Documents Ready",
                    "description": "All documentation completed on schedule",
                    "probability": 0.45,
                    "impact": "No delay",
                    "adjusted_timeline": "2026-10-06 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Minor Corrections Needed",
                    "description": "Documentation needs revisions, 2-week extension requested",
                    "probability": 0.30,
                    "impact": "2-week delay",
                    "adjusted_timeline": "2026-10-20 (+2 weeks)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Major Gaps Discovered",
                    "description": "Additional documentation requirements identified",
                    "probability": 0.18,
                    "impact": "1-month delay to accreditation",
                    "adjusted_timeline": "2026-11-06 (+1 month)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Critical Case - Renewal Denied",
                    "description": "Accreditation renewal denied pending major changes",
                    "probability": 0.07,
                    "impact": "2-3 month delay + operational impact",
                    "adjusted_timeline": "2026-12-06 (+3 months)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        },
        "c6-edkh": {
            "scenario_name": "EDKH Action Tracking System Update",
            "baseline": {
                "current_timeline": "Q3 2026",
                "milestones": [
                    {"name": "Database Migration", "date": "2026-07-06", "status": "In Progress"},
                    {"name": "System Testing", "date": "2026-07-07", "status": "Planned"},
                    {"name": "Full Restoration", "date": "2026-07-08", "status": "Planned"}
                ]
            },
            "scenarios": [
                {
                    "name": "Best Case - Smooth Migration",
                    "description": "All data migrates successfully without issues",
                    "probability": 0.60,
                    "impact": "No delay - On time",
                    "adjusted_timeline": "2026-07-08 (On Schedule)",
                    "risk_level": "low",
                    "affected_milestones": 0
                },
                {
                    "name": "Moderate Case - Minor Data Issues",
                    "description": "Some records require manual cleanup during testing",
                    "probability": 0.25,
                    "impact": "4-6 hour delay",
                    "adjusted_timeline": "2026-07-08 (Evening)",
                    "risk_level": "medium",
                    "affected_milestones": 1
                },
                {
                    "name": "Worst Case - Partial Rollback",
                    "description": "Data corruption detected, partial rollback required",
                    "probability": 0.10,
                    "impact": "1-2 day delay",
                    "adjusted_timeline": "2026-07-09 (+1 day)",
                    "risk_level": "high",
                    "affected_milestones": 2
                },
                {
                    "name": "Critical Case - Full Reversion",
                    "description": "Critical issues force complete reversion to old system",
                    "probability": 0.05,
                    "impact": "3-5 day delay + extended stability period",
                    "adjusted_timeline": "2026-07-12 (+4 days)",
                    "risk_level": "critical",
                    "affected_milestones": 3
                }
            ]
        }
    }

    @staticmethod
    def generate(scenario, persona_id, last_response=None, conversation_history=None):
        """
        Generate what-if simulation scenarios with probability and impact assessment.
        
        Args:
            scenario: Scenario object with .name property
            persona_id: Current persona identifier
            last_response: Previous response (unused)
            conversation_history: Conversation context (unused)
        
        Returns:
            dict with what-if scenario data
        """
        # Get scenario name
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        # Get template or use generic
        if scenario_name in WhatIfSimulationAgent.SCENARIO_TEMPLATES:
            template = WhatIfSimulationAgent.SCENARIO_TEMPLATES[scenario_name]
        else:
            template = {
                "scenario_name": f"Generic What-If for {scenario_name}",
                "baseline": {
                    "current_timeline": "Current",
                    "milestones": [
                        {"name": "Milestone 1", "date": "2026-07-15", "status": "Planned"},
                        {"name": "Milestone 2", "date": "2026-08-15", "status": "Planned"}
                    ]
                },
                "scenarios": [
                    {
                        "name": "Optimistic Path",
                        "description": "Best case scenario with minimal delays",
                        "probability": 0.40,
                        "impact": "No delay",
                        "adjusted_timeline": "On Schedule",
                        "risk_level": "low",
                        "affected_milestones": 0
                    },
                    {
                        "name": "Expected Path",
                        "description": "Most likely outcome",
                        "probability": 0.45,
                        "impact": "1-week delay",
                        "adjusted_timeline": "+7 days",
                        "risk_level": "medium",
                        "affected_milestones": 1
                    },
                    {
                        "name": "Pessimistic Path",
                        "description": "Worst case scenario",
                        "probability": 0.15,
                        "impact": "4-week delay",
                        "adjusted_timeline": "+28 days",
                        "risk_level": "high",
                        "affected_milestones": 2
                    }
                ]
            }
        
        # Calculate weighted impact
        weighted_delay = 0
        total_probability = 0
        for scenario_option in template['scenarios']:
            prob = scenario_option['probability']
            # Extract numeric delay from impact string
            impact_str = scenario_option['impact']
            if 'No delay' in impact_str:
                days = 0
            elif 'week' in impact_str:
                # Extract number from "1-week" or "1 week" format
                match = re.search(r'(\d+)', impact_str)
                days = (int(match.group(1)) if match else 1) * 7
            elif 'day' in impact_str:
                match = re.search(r'(\d+)', impact_str)
                days = int(match.group(1)) if match else 1
            elif 'month' in impact_str:
                match = re.search(r'(\d+)', impact_str)
                days = (int(match.group(1)) if match else 1) * 30
            elif 'hour' in impact_str:
                days = 0
            else:
                days = 0
            weighted_delay += prob * days
            total_probability += prob
        
        weighted_delay = round(weighted_delay) if weighted_delay > 0 else 0
        
        return {
            'success': True,
            'scenario': scenario_name,
            'scenario_display': template['scenario_name'],
            'baseline_timeline': template['baseline']['current_timeline'],
            'baseline_milestones': template['baseline']['milestones'],
            'scenarios': template['scenarios'],
            'total_scenarios': len(template['scenarios']),
            'weighted_risk_delay_days': weighted_delay,
            'recommendation': f"Expected delay: ~{weighted_delay} days. Monitor critical path milestones.",
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
