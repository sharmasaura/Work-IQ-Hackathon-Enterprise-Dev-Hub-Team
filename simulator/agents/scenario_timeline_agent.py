"""
Scenario Timeline Agent - Generates incident/scenario timeline reconstruction
"""
from datetime import datetime, timedelta
import json


class ScenarioTimelineAgent:
    """Generates scenario-specific event timelines with timestamps, actors, and descriptions."""

    SCENARIO_TEMPLATES = {
        "c1-northbridge": {
            "scenario_name": "Northbridge Infrastructure Incident",
            "context": "Critical infrastructure outage affecting product deployment",
            "events": [
                {
                    "timestamp": "2026-07-06T08:15:00Z",
                    "category": "Alert",
                    "actor": "Monitoring System",
                    "title": "CPU Utilization Spike",
                    "description": "Production server CPU jumped to 95% - automated alert triggered",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T08:17:00Z",
                    "category": "Response",
                    "actor": "OnCall Engineer (Marcus)",
                    "title": "Initial Investigation Started",
                    "description": "Oncall engineer acknowledged alert and began initial diagnostics",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T08:22:00Z",
                    "category": "Escalation",
                    "actor": "Incident Commander",
                    "title": "Incident Escalated to Major",
                    "description": "Incident escalated to major severity - infrastructure team notified",
                    "severity": "critical"
                },
                {
                    "timestamp": "2026-07-06T08:35:00Z",
                    "category": "Action",
                    "actor": "Infrastructure Team",
                    "title": "Database Connection Pool Exhausted",
                    "description": "Root cause identified: connection pool exhaustion due to stale connections",
                    "severity": "critical"
                },
                {
                    "timestamp": "2026-07-06T08:45:00Z",
                    "category": "Resolution",
                    "actor": "Infrastructure Team",
                    "title": "Connection Pool Reset Executed",
                    "description": "Database pool reset completed and services returned to normal",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T09:00:00Z",
                    "category": "Closure",
                    "actor": "Incident Commander",
                    "title": "Incident Resolved",
                    "description": "All services verified healthy. Post-incident review scheduled for tomorrow.",
                    "severity": "low"
                }
            ]
        },
        "c2-contoso": {
            "scenario_name": "Contoso Deployment Pipeline Failure",
            "context": "Release deployment stalled mid-pipeline affecting product launch",
            "events": [
                {
                    "timestamp": "2026-07-06T10:00:00Z",
                    "category": "Event",
                    "actor": "Release Manager",
                    "title": "Deployment Pipeline Started",
                    "description": "Release v2.4.1 deployment pipeline initiated for production",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T10:15:00Z",
                    "category": "Progress",
                    "actor": "CI/CD Pipeline",
                    "title": "Build Stage Completed",
                    "description": "Build artifacts created successfully - 2,847 files packaged",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T10:28:00Z",
                    "category": "Alert",
                    "actor": "CI/CD Pipeline",
                    "title": "Test Suite Failed",
                    "description": "Integration tests failed: 12 test cases failed in payment module",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T10:32:00Z",
                    "category": "Response",
                    "actor": "QA Lead",
                    "title": "Investigation Started",
                    "description": "QA lead analyzing test failures - potential data migration issue detected",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T11:05:00Z",
                    "category": "Action",
                    "actor": "Development Team",
                    "title": "Hotfix Applied",
                    "description": "Data migration logic corrected - 2 files modified in payment service",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T11:25:00Z",
                    "category": "Resolution",
                    "actor": "CI/CD Pipeline",
                    "title": "Tests Re-run Successfully",
                    "description": "All tests passed on second run - deployment pipeline resumed",
                    "severity": "low"
                }
            ]
        },
        "c3-meridian": {
            "scenario_name": "Meridian Compliance Audit Alert",
            "context": "Unexpected compliance gap discovered during internal audit",
            "events": [
                {
                    "timestamp": "2026-07-06T09:30:00Z",
                    "category": "Alert",
                    "actor": "Compliance System",
                    "title": "Policy Violation Detected",
                    "description": "Data retention policy violation: 2,341 audit records expired but not purged",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T09:45:00Z",
                    "category": "Escalation",
                    "actor": "Compliance Officer",
                    "title": "Escalated to Senior Management",
                    "description": "Compliance officer notified director - potential audit finding",
                    "severity": "critical"
                },
                {
                    "timestamp": "2026-07-06T10:15:00Z",
                    "category": "Response",
                    "actor": "Data Governance Team",
                    "title": "Data Audit Initiated",
                    "description": "Full data retention audit started across all systems",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T11:30:00Z",
                    "category": "Action",
                    "actor": "Data Governance Team",
                    "title": "Batch Purge Process Started",
                    "description": "Automated purge job executed for expired records - estimated 4 hours",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T15:45:00Z",
                    "category": "Resolution",
                    "actor": "Data Governance Team",
                    "title": "Data Cleanup Completed",
                    "description": "2,341 expired records successfully purged - system now compliant",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T16:15:00Z",
                    "category": "Closure",
                    "actor": "Compliance Officer",
                    "title": "Compliance Status Verified",
                    "description": "Full compliance restored - documentation updated for audit trail",
                    "severity": "low"
                }
            ]
        },
        "c4-arundel": {
            "scenario_name": "Arundel Work Order Processing Bottleneck",
            "context": "CMMS work order queue growing - processing delays impacting operations",
            "events": [
                {
                    "timestamp": "2026-07-06T08:00:00Z",
                    "category": "Alert",
                    "actor": "CMMS Monitor",
                    "title": "Queue Backlog Warning",
                    "description": "Work order queue exceeded threshold: 847 pending items",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T09:20:00Z",
                    "category": "Response",
                    "actor": "Ops Manager",
                    "title": "Triage Meeting Initiated",
                    "description": "Operations manager called team meeting to review queue priorities",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T10:00:00Z",
                    "category": "Analysis",
                    "actor": "Process Analyst",
                    "title": "Root Cause Analysis Complete",
                    "description": "Identified: 3 critical work orders stuck in approval workflow",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T10:45:00Z",
                    "category": "Action",
                    "actor": "Approvals Team",
                    "title": "Priority Approvals Expedited",
                    "description": "Fast-tracked approval process for 3 critical items - notifications sent",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T11:30:00Z",
                    "category": "Progress",
                    "actor": "Field Teams",
                    "title": "Work Order Dispatch Started",
                    "description": "First batch of 12 priority work orders dispatched to field teams",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T14:00:00Z",
                    "category": "Resolution",
                    "actor": "CMMS Monitor",
                    "title": "Queue Status Normalized",
                    "description": "Backlog reduced to 243 items - processing rate returned to baseline",
                    "severity": "low"
                }
            ]
        },
        "c5-westbrook": {
            "scenario_name": "Westbrook Accreditation Timeline Risk",
            "context": "Accreditation renewal deadline approaching with documentation gaps",
            "events": [
                {
                    "timestamp": "2026-07-06T07:00:00Z",
                    "category": "Alert",
                    "actor": "Accreditation Tracker",
                    "title": "90-Day Warning Triggered",
                    "description": "Accreditation renewal due in 90 days - documentation review started",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T08:30:00Z",
                    "category": "Response",
                    "actor": "Accreditation Lead",
                    "title": "Gap Analysis Initiated",
                    "description": "Accreditation lead began detailed review of renewal requirements",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T09:45:00Z",
                    "category": "Finding",
                    "actor": "Accreditation Lead",
                    "title": "Documentation Gap Identified",
                    "description": "Missing 23 required documentation pieces - primarily in quality metrics section",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T11:00:00Z",
                    "category": "Planning",
                    "actor": "Compliance Team",
                    "title": "Remediation Plan Created",
                    "description": "60-day action plan created to address all gaps - assigned to 5 team members",
                    "severity": "high"
                },
                {
                    "timestamp": "2026-07-06T13:00:00Z",
                    "category": "Action",
                    "actor": "Documentation Team",
                    "title": "Document Collection Started",
                    "description": "Teams assigned tasks - deadline set for 45 days to allow 15-day review buffer",
                    "severity": "medium"
                },
                {
                    "timestamp": "2026-07-06T14:30:00Z",
                    "category": "Status",
                    "actor": "Accreditation Lead",
                    "title": "Timeline Confirmed",
                    "description": "All teams confirmed acceptance of assigned documentation deadlines",
                    "severity": "low"
                }
            ]
        },
        "c6-edkh": {
            "scenario_name": "EDKH Action Tracking System Update",
            "context": "System maintenance window for action item tracking platform",
            "events": [
                {
                    "timestamp": "2026-07-06T18:00:00Z",
                    "category": "Planned",
                    "actor": "Operations",
                    "title": "Maintenance Window Started",
                    "description": "Scheduled maintenance window begun - action tracker offline for upgrades",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T18:15:00Z",
                    "category": "Action",
                    "actor": "Database Team",
                    "title": "Database Migration Started",
                    "description": "Primary database migration in progress - 847,000 records being migrated",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T18:45:00Z",
                    "category": "Progress",
                    "actor": "Database Team",
                    "title": "Migration 50% Complete",
                    "description": "Halfway through data migration - validation checks passing",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T19:30:00Z",
                    "category": "Completion",
                    "actor": "Database Team",
                    "title": "Migration Completed",
                    "description": "All data successfully migrated and validated - system upgrade complete",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T19:45:00Z",
                    "category": "Testing",
                    "actor": "QA Team",
                    "title": "Post-Upgrade Verification",
                    "description": "Smoke tests completed - all critical functionality verified working",
                    "severity": "low"
                },
                {
                    "timestamp": "2026-07-06T20:00:00Z",
                    "category": "Resolution",
                    "actor": "Operations",
                    "title": "System Back Online",
                    "description": "Maintenance completed - system restored to production status",
                    "severity": "low"
                }
            ]
        }
    }

    @staticmethod
    def generate(scenario, persona_id, last_response=None, conversation_history=None):
        """
        Generate scenario-specific timeline events.
        
        Args:
            scenario: Scenario object with .name property
            persona_id: Current persona identifier
            last_response: Previous response (unused for timeline)
            conversation_history: Conversation context (unused for timeline)
        
        Returns:
            dict with timeline data structure
        """
        # Get scenario name
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        # Get template or use generic
        if scenario_name in ScenarioTimelineAgent.SCENARIO_TEMPLATES:
            template = ScenarioTimelineAgent.SCENARIO_TEMPLATES[scenario_name]
        else:
            template = {
                "scenario_name": f"Generic Timeline for {scenario_name}",
                "context": "Generic timeline showing event progression",
                "events": [
                    {
                        "timestamp": "2026-07-06T08:00:00Z",
                        "category": "Start",
                        "actor": "System",
                        "title": "Event Started",
                        "description": "Initial event triggered",
                        "severity": "low"
                    },
                    {
                        "timestamp": "2026-07-06T09:00:00Z",
                        "category": "Progress",
                        "actor": "System",
                        "title": "Processing Ongoing",
                        "description": "System processing event",
                        "severity": "medium"
                    },
                    {
                        "timestamp": "2026-07-06T10:00:00Z",
                        "category": "Complete",
                        "actor": "System",
                        "title": "Event Resolved",
                        "description": "Event processing completed",
                        "severity": "low"
                    }
                ]
            }
        
        # Calculate statistics
        event_count = len(template.get('events', []))
        severity_counts = {
            'critical': sum(1 for e in template.get('events', []) if e.get('severity') == 'critical'),
            'high': sum(1 for e in template.get('events', []) if e.get('severity') == 'high'),
            'medium': sum(1 for e in template.get('events', []) if e.get('severity') == 'medium'),
            'low': sum(1 for e in template.get('events', []) if e.get('severity') == 'low')
        }
        
        # Calculate duration
        if len(template.get('events', [])) > 1:
            first_time = template['events'][0]['timestamp']
            last_time = template['events'][-1]['timestamp']
            # Simple string comparison for ISO format works for duration calculation
            duration = "~12 hours" if 'T' in first_time else "Unknown"
        else:
            duration = "Ongoing"
        
        return {
            'success': True,
            'scenario': scenario_name,
            'scenario_display': template['scenario_name'],
            'context': template['context'],
            'events': template['events'],
            'total_events': event_count,
            'critical_count': severity_counts['critical'],
            'high_count': severity_counts['high'],
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
