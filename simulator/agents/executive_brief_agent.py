"""
Executive Brief Agent - Generates decision-ready executive briefs for leadership.
Provides status, risks, blockers, and next actions in a concise format.
"""


class ExecutiveBriefAgent:
    """Generates structured executive briefs for leadership decision-making."""

    @staticmethod
    def generate(scenario, persona_id: str = None, last_response: str = None, conversation_history: list = None) -> dict:
        """
        Generate an executive brief based on scenario context.
        
        Args:
            scenario: Loaded scenario object
            persona_id: Active persona ID
            last_response: Last assistant response text
            conversation_history: List of messages
            
        Returns:
            Dict with keys: summary, risks, blockers, next_actions, overall_health, timestamp
        """
        scenario_name = getattr(scenario, 'name', 'unknown')
        
        # Scenario-specific briefing templates
        briefs = {
            'c1-northbridge': {
                'summary': 'Northbridge CAPA & capacity program in progress. Key tracking items and resource allocation under review.',
                'risks': [
                    {'level': 'high', 'description': 'Timeline slippage on Phase 2 deliverables'},
                    {'level': 'medium', 'description': 'Resource availability constraints in Q3'},
                    {'level': 'low', 'description': 'Vendor dependency on critical components'},
                ],
                'blockers': [
                    {'description': 'Approval pending from steering committee', 'owner': 'Executive Sponsor', 'due': '2026-07-10'},
                    {'description': 'Budget allocation awaiting CFO sign-off', 'owner': 'Finance Director', 'due': '2026-07-12'},
                ],
                'next_actions': [
                    {'action': 'Schedule steering committee review', 'owner': 'Program Manager', 'due': '2026-07-08', 'priority': 'high'},
                    {'action': 'Update capacity forecasts for H2', 'owner': 'Resource Manager', 'due': '2026-07-15', 'priority': 'high'},
                    {'action': 'Confirm vendor SLAs', 'owner': 'Procurement', 'due': '2026-07-20', 'priority': 'medium'},
                ],
                'overall_health': 'At Risk',
            },
            'c2-contoso': {
                'summary': 'Contoso milestone qualification on track. Key stakeholder alignment achieved. Moving to final validation phase.',
                'risks': [
                    {'level': 'medium', 'description': 'Quality assurance findings may impact release timeline'},
                    {'level': 'low', 'description': 'Third-party integration dependencies'},
                ],
                'blockers': [
                    {'description': 'QA regression test completion', 'owner': 'QA Lead', 'due': '2026-07-14'},
                    {'description': 'Security audit final approval', 'owner': 'Security Officer', 'due': '2026-07-16'},
                ],
                'next_actions': [
                    {'action': 'Complete final stakeholder review', 'owner': 'Product Manager', 'due': '2026-07-09', 'priority': 'high'},
                    {'action': 'Execute Go-live readiness checklist', 'owner': 'Program Manager', 'due': '2026-07-18', 'priority': 'high'},
                    {'action': 'Prepare rollback plan', 'owner': 'Operations', 'due': '2026-07-17', 'priority': 'medium'},
                ],
                'overall_health': 'Healthy',
            },
            'c3-meridian': {
                'summary': 'Meridian engagement tracking active. Resource allocation and PSA metrics trending positively.',
                'risks': [
                    {'level': 'medium', 'description': 'Proposed resource redeployment may impact active engagements'},
                    {'level': 'medium', 'description': 'Utilization target variance in consulting practice'},
                ],
                'blockers': [
                    {'description': 'Approval for resource reallocation across practices', 'owner': 'Practice Lead', 'due': '2026-07-11'},
                    {'description': 'Client sign-off on extended engagement terms', 'owner': 'Account Manager', 'due': '2026-07-13'},
                ],
                'next_actions': [
                    {'action': 'Review Q3 engagement pipeline', 'owner': 'Sales Director', 'due': '2026-07-10', 'priority': 'high'},
                    {'action': 'Finalize resource utilization plan', 'owner': 'Resource Manager', 'due': '2026-07-15', 'priority': 'high'},
                    {'action': 'Update client engagement metrics', 'owner': 'Account Manager', 'due': '2026-07-19', 'priority': 'medium'},
                ],
                'overall_health': 'Healthy',
            },
            'c4-arundel': {
                'summary': 'Arundel maintenance and CMMS operations running smoothly. Work order backlog being processed on schedule.',
                'risks': [
                    {'level': 'high', 'description': 'Equipment age and deferred maintenance accumulation'},
                    {'level': 'medium', 'description': 'Preventive maintenance scheduling conflicts'},
                ],
                'blockers': [
                    {'description': 'Budget approval for emergency maintenance', 'owner': 'Facilities Director', 'due': '2026-07-12'},
                    {'description': 'Technician training completion', 'owner': 'Operations Manager', 'due': '2026-07-20'},
                ],
                'next_actions': [
                    {'action': 'Priority: Process critical work orders', 'owner': 'Maintenance Supervisor', 'due': '2026-07-09', 'priority': 'high'},
                    {'action': 'Schedule predictive maintenance audits', 'owner': 'Engineering', 'due': '2026-07-16', 'priority': 'high'},
                    {'action': 'Update CMMS with completed tasks', 'owner': 'Operations Analyst', 'due': '2026-07-21', 'priority': 'medium'},
                ],
                'overall_health': 'At Risk',
            },
            'c5-westbrook': {
                'summary': 'Westbrook accreditation program on track. Compliance items progressing. Audit readiness improving.',
                'risks': [
                    {'level': 'medium', 'description': 'Accreditation renewal deadline approaching (60 days)'},
                    {'level': 'medium', 'description': 'AOL policy interpretations may require clarification'},
                ],
                'blockers': [
                    {'description': 'Final accreditation body feedback', 'owner': 'Accreditation Manager', 'due': '2026-07-18'},
                    {'description': 'AOL compliance documentation completion', 'owner': 'Compliance Officer', 'due': '2026-07-25'},
                ],
                'next_actions': [
                    {'action': 'Conduct pre-audit review', 'owner': 'Quality Manager', 'due': '2026-07-10', 'priority': 'high'},
                    {'action': 'Address accreditation gaps', 'owner': 'Program Coordinator', 'due': '2026-07-17', 'priority': 'high'},
                    {'action': 'Update AOL procedures documentation', 'owner': 'Documentation Team', 'due': '2026-07-28', 'priority': 'medium'},
                ],
                'overall_health': 'At Risk',
            },
            'c6-edkh': {
                'summary': 'EDKH enterprise platform stabilizing. On-call operations nominal. Action tracking improving.',
                'risks': [
                    {'level': 'high', 'description': 'Platform availability SLA at risk (Q2 performance: 98.5% vs target 99.5%)'},
                    {'level': 'medium', 'description': 'Unresolved incident action items exceeding 30-day threshold'},
                ],
                'blockers': [
                    {'description': 'Infrastructure capacity planning approval', 'owner': 'Infrastructure Lead', 'due': '2026-07-14'},
                    {'description': 'On-call staffing model review', 'owner': 'HR Director', 'due': '2026-07-19'},
                ],
                'next_actions': [
                    {'action': 'Execute reliability improvement plan', 'owner': 'SRE Team Lead', 'due': '2026-07-11', 'priority': 'high'},
                    {'action': 'Complete overdue action items', 'owner': 'Incident Commander', 'due': '2026-07-09', 'priority': 'high'},
                    {'action': 'Finalize on-call rotation for Q3', 'owner': 'Operations Manager', 'due': '2026-07-15', 'priority': 'medium'},
                ],
                'overall_health': 'Critical',
            },
        }

        # Get scenario-specific brief or use generic template
        brief = briefs.get(scenario_name, {
            'summary': f'Status update for {scenario_name}. Monitoring key metrics and progress.',
            'risks': [
                {'level': 'medium', 'description': 'General project risks under review'},
            ],
            'blockers': [
                {'description': 'Stakeholder approvals pending', 'owner': 'TBD', 'due': '2026-07-15'},
            ],
            'next_actions': [
                {'action': 'Review project status', 'owner': 'Project Manager', 'due': '2026-07-10', 'priority': 'medium'},
            ],
            'overall_health': 'Healthy',
        })

        from datetime import datetime
        
        return {
            'summary': brief.get('summary', ''),
            'risks': brief.get('risks', []),
            'blockers': brief.get('blockers', []),
            'next_actions': brief.get('next_actions', []),
            'overall_health': brief.get('overall_health', 'Healthy'),
            'timestamp': datetime.now().isoformat(),
        }
