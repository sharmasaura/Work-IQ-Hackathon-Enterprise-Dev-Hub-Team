"""
Pre-mortem Generator Agent - predicts likely failure paths for active milestones
and proposes preventive actions before failure occurs.
"""

from datetime import datetime


class PreMortemGeneratorAgent:
    """Generates milestone pre-mortem analysis for hackathon demos."""

    TEMPLATES = {
        "c1-northbridge": {
            "scenario_display": "Northbridge Capacity Program",
            "active_milestone": "Phase 2 Readiness Gate",
            "target_date": "2026-08-15",
            "risk_window_days": 21,
            "failure_modes": [
                {
                    "name": "Vendor shipment variance",
                    "probability": 0.34,
                    "impact": "high",
                    "early_signal": "Lead times exceed plan by >4 days",
                    "blast_radius": "Delays integration and pushes go-live sequence"
                },
                {
                    "name": "Steering approval lag",
                    "probability": 0.27,
                    "impact": "medium",
                    "early_signal": "No decision after second review meeting",
                    "blast_radius": "Blocks budget release for downstream tasks"
                },
                {
                    "name": "Capacity model mismatch",
                    "probability": 0.22,
                    "impact": "medium",
                    "early_signal": "Forecast variance above 12% week-over-week",
                    "blast_radius": "Creates rework in staffing and sequencing"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Create alternate supplier trigger at +48h delay",
                    "owner": "Procurement Lead",
                    "due": "2026-07-10",
                    "priority": "high"
                },
                {
                    "action": "Pre-book steering escalation slot",
                    "owner": "Program Manager",
                    "due": "2026-07-09",
                    "priority": "high"
                },
                {
                    "action": "Lock weekly forecast variance review",
                    "owner": "Resource Manager",
                    "due": "2026-07-11",
                    "priority": "medium"
                }
            ]
        },
        "c2-contoso": {
            "scenario_display": "Contoso Release Program",
            "active_milestone": "Production Deployment",
            "target_date": "2026-07-20",
            "risk_window_days": 10,
            "failure_modes": [
                {
                    "name": "Late regression defect",
                    "probability": 0.31,
                    "impact": "high",
                    "early_signal": "Sev-2 defects in final test pass",
                    "blast_radius": "Forces release freeze and rollback prep"
                },
                {
                    "name": "Security sign-off delay",
                    "probability": 0.26,
                    "impact": "medium",
                    "early_signal": "Audit checklist unresolved >24h",
                    "blast_radius": "Blocks production approval window"
                },
                {
                    "name": "Pipeline instability",
                    "probability": 0.2,
                    "impact": "medium",
                    "early_signal": "Consecutive build failures on release branch",
                    "blast_radius": "Shifts cutover timing and support staffing"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Run focused regression war-room 72h pre-release",
                    "owner": "QA Lead",
                    "due": "2026-07-17",
                    "priority": "high"
                },
                {
                    "action": "Pre-approve conditional security waiver path",
                    "owner": "Security Officer",
                    "due": "2026-07-16",
                    "priority": "high"
                },
                {
                    "action": "Enable fallback deployment pipeline",
                    "owner": "DevOps Engineer",
                    "due": "2026-07-18",
                    "priority": "medium"
                }
            ]
        },
        "c3-meridian": {
            "scenario_display": "Meridian Engagement Delivery",
            "active_milestone": "Q3 Engagement Commit",
            "target_date": "2026-08-01",
            "risk_window_days": 18,
            "failure_modes": [
                {
                    "name": "Key consultant over-allocation",
                    "probability": 0.33,
                    "impact": "high",
                    "early_signal": "Utilization above 95% for two consecutive weeks",
                    "blast_radius": "Critical workstream slips and escalations increase"
                },
                {
                    "name": "Client scope growth without reset",
                    "probability": 0.25,
                    "impact": "medium",
                    "early_signal": "Scope delta accepted without timeline change",
                    "blast_radius": "Timeline compression and quality risk"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Add backup resource shadowing now",
                    "owner": "Practice Lead",
                    "due": "2026-07-12",
                    "priority": "high"
                },
                {
                    "action": "Enforce change-control gate for added scope",
                    "owner": "Account Manager",
                    "due": "2026-07-13",
                    "priority": "high"
                }
            ]
        },
        "c4-arundel": {
            "scenario_display": "Arundel CMMS Operations",
            "active_milestone": "Critical Work Order Clearance",
            "target_date": "2026-07-20",
            "risk_window_days": 14,
            "failure_modes": [
                {
                    "name": "Approval queue bottleneck",
                    "probability": 0.36,
                    "impact": "high",
                    "early_signal": "Work orders aging past SLA for 2 days",
                    "blast_radius": "Backlog compounds and safety checks slip"
                },
                {
                    "name": "Technician coverage gap",
                    "probability": 0.24,
                    "impact": "medium",
                    "early_signal": "Shift handoff unresolved for key locations",
                    "blast_radius": "Execution delays in preventive maintenance"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Introduce expedited path for high-criticality orders",
                    "owner": "Operations Manager",
                    "due": "2026-07-09",
                    "priority": "high"
                },
                {
                    "action": "Publish contingency roster for next 2 weeks",
                    "owner": "Maintenance Supervisor",
                    "due": "2026-07-10",
                    "priority": "medium"
                }
            ]
        },
        "c5-westbrook": {
            "scenario_display": "Westbrook Accreditation Program",
            "active_milestone": "Accreditation Renewal Submission",
            "target_date": "2026-10-06",
            "risk_window_days": 30,
            "failure_modes": [
                {
                    "name": "Documentation quality gap",
                    "probability": 0.29,
                    "impact": "high",
                    "early_signal": "Review findings remain open for more than one cycle",
                    "blast_radius": "Submission rejection and rework round"
                },
                {
                    "name": "Policy interpretation mismatch",
                    "probability": 0.21,
                    "impact": "medium",
                    "early_signal": "Conflicting interpretation across reviewers",
                    "blast_radius": "Late policy updates and delayed sign-off"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Schedule independent pre-audit review",
                    "owner": "Compliance Officer",
                    "due": "2026-07-15",
                    "priority": "high"
                },
                {
                    "action": "Create policy interpretation decision log",
                    "owner": "Accreditation Manager",
                    "due": "2026-07-16",
                    "priority": "medium"
                }
            ]
        },
        "c6-edkh": {
            "scenario_display": "EDKH Reliability Program",
            "active_milestone": "Platform Restoration Completion",
            "target_date": "2026-07-08",
            "risk_window_days": 5,
            "failure_modes": [
                {
                    "name": "Data migration regression",
                    "probability": 0.32,
                    "impact": "high",
                    "early_signal": "Validation failures after migration step",
                    "blast_radius": "Rollback requirement and extended outage"
                },
                {
                    "name": "On-call response fatigue",
                    "probability": 0.19,
                    "impact": "medium",
                    "early_signal": "Escalation latency increases over consecutive shifts",
                    "blast_radius": "Longer incident recovery and coordination gaps"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Run dry-run migration verification on sampled records",
                    "owner": "SRE Engineer",
                    "due": "2026-07-06",
                    "priority": "high"
                },
                {
                    "action": "Assign secondary incident commander for overlap window",
                    "owner": "On-call Lead",
                    "due": "2026-07-06",
                    "priority": "medium"
                }
            ]
        }
    }

    @staticmethod
    def _scenario_key(scenario) -> str:
        """Resolve stable scenario key from simulator scenario object."""
        root = getattr(scenario, "root", None)
        if root is not None:
            try:
                name = getattr(root, "name", "")
                if name:
                    return str(name)
            except Exception:
                pass

        for attr in ("name", "scenario", "scenario_id", "id"):
            value = getattr(scenario, attr, None)
            if isinstance(value, str) and value.strip():
                return value.strip()

        return "unknown"

    @staticmethod
    def _fallback_template(scenario_name: str) -> dict:
        return {
            "scenario_display": f"{scenario_name} Pre-mortem",
            "active_milestone": "Upcoming Milestone",
            "target_date": "2026-07-31",
            "risk_window_days": 14,
            "failure_modes": [
                {
                    "name": "Dependency delay",
                    "probability": 0.3,
                    "impact": "medium",
                    "early_signal": "Critical dependencies remain unconfirmed",
                    "blast_radius": "Milestone date likely to slip"
                }
            ],
            "preventive_actions": [
                {
                    "action": "Set contingency owner and fallback plan",
                    "owner": "Program Manager",
                    "due": "2026-07-10",
                    "priority": "high"
                }
            ]
        }

    @staticmethod
    def generate(scenario, persona_id=None, last_response=None, conversation_history=None):
        """Return pre-mortem package for the active scenario."""
        scenario_name = PreMortemGeneratorAgent._scenario_key(scenario)
        template = PreMortemGeneratorAgent.TEMPLATES.get(
            scenario_name, PreMortemGeneratorAgent._fallback_template(scenario_name)
        )

        risk_score = 0
        for fm in template.get("failure_modes", []):
            prob = float(fm.get("probability", 0))
            impact = str(fm.get("impact", "medium")).lower()
            impact_weight = {"low": 1, "medium": 2, "high": 3, "critical": 4}.get(impact, 2)
            risk_score += prob * impact_weight

        highest_mode = max(
            template.get("failure_modes", []),
            key=lambda x: float(x.get("probability", 0)),
            default={"name": "No significant failure mode found"},
        )

        return {
            "scenario_display": template.get("scenario_display"),
            "active_milestone": template.get("active_milestone"),
            "target_date": template.get("target_date"),
            "risk_window_days": template.get("risk_window_days", 14),
            "risk_score": round(risk_score, 2),
            "highest_risk_mode": highest_mode.get("name"),
            "failure_modes": template.get("failure_modes", []),
            "preventive_actions": template.get("preventive_actions", []),
            "recommendation": (
                "Execute high-priority preventive actions within 48 hours and verify early signals daily "
                "until milestone closure."
            ),
            "generated_for_persona": persona_id or "all",
            "timestamp": datetime.now().isoformat(),
        }
