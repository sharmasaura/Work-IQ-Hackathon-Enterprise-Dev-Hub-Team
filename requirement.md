# Work IQ Hackathon Requirements

## Objective
Create a high-impact Work IQ demonstration for hackathon judging with clear business value, explainable outputs, and actionable outcomes.

## Backlog (Prioritized by Impact Weightage)
Move items from this section to "Active Development List" as implementation starts.

| Rank | Feature | Impact (1-10) | Why It Matters for Hackathon | Status |
|---|---|---:|---|---|
| 1 | Cross-app Single Answer Copilot (Email + Teams + Files + Notes + Tables) | 10.0 | Strongest Work IQ story: one trusted answer from fragmented enterprise context. | Implemented |
| 2 | Decision-Ready Executive Briefs (status, risks, blockers, next actions) | 9.7 | Immediate business value and leadership-facing outcomes. | Approved |
| 3 | Risk/Delay Early Warning with confidence indicators | 9.4 | Demonstrates proactive intelligence, not just reactive search. | Pending |
| 4 | Natural language query to structured insights | 9.2 | Shows intuitive UX and reasoning across mixed data types. | Pending |
| 5 | Persona-aware responses (PM vs Executive vs Engineer) | 8.9 | Highlights context personalization and relevance. | Pending |
| 6 | Action recommendation engine (owner + due date suggestions) | 8.7 | Converts insights into execution-ready recommendations. | Approved |
| 7 | Source traceability and explainability (citations) | 8.5 | Builds trust with verifiable evidence from source artifacts. | Implemented |
| 8 | Scenario playback / incident timeline reconstruction | 8.3 | Excellent storytelling mechanism for live demos. | Approved |
| 9 | Meeting intelligence (minutes, decisions, owners, follow-ups) | 8.1 | Universally relatable productivity value. | Pending |
| 10 | Cross-scenario benchmarking and prioritization | 7.8 | Shows portfolio-level intelligence and comparative reasoning. | Pending |
| 11 | What-if simulation for milestone impact | 7.6 | Adds advanced planning and decision-support capability. | Approved |
| 12 | Policy/compliance guardrails in responses | 7.3 | Improves enterprise readiness and responsible AI posture. | Pending |
| 13 | Role-based data access-aware responses | 7.1 | Demonstrates secure, audience-appropriate answer shaping. | Pending |
| 14 | Automated worklog/status mail drafting | 6.8 | Practical time-saver for day-to-day teams. | Pending |
| 15 | Interactive dashboard snapshot (health, blockers, actions) | 6.5 | Good visual support when paired with strong AI reasoning. | Approved |
| 16 | Progress Tracking (7-day trend, activity indicators) | 7.2 | Shows activity patterns and engagement trends over time. | Approved |

### Differentiation Backlog (Not In Standard M365 Copilot Workflows)
Use this list to prioritize unique Work IQ capabilities for hackathon differentiation.

| Rank | Feature | Impact (1-10) | Why It Matters for Hackathon | Status |
|---|---|---:|---|---|
| 1 | Causal Decision Graph | 9.8 | Explains chain of decisions and downstream impact, beyond summaries. | Pending-Approval |
| 2 | Confidence-Calibrated Answer Contracts | 9.6 | Communicates confidence and missing evidence for trusted enterprise usage. | Pending-Approval |
| 3 | Contradiction Radar Across Channels | 9.5 | Detects conflicts across email, Teams, meeting notes, and trackers. | Pending-Approval |
| 4 | Decision Debt Score | 9.3 | Quantifies unresolved decisions and ownership ambiguity into a risk metric. | Pending-Approval |
| 5 | Pre-mortem Generator for Active Milestones | 9.2 | Proactively identifies likely failure paths and prevention actions. | Approved |
| 6 | Accountability Drift Detector | 9.0 | Identifies reassigned, dropped, or stalled tasks and escalation needs. | Pending-Approval |
| 7 | Silent Stakeholder Detector | 8.8 | Highlights critical but missing voices in active decision threads. | Pending-Approval |
| 8 | Evidence-to-Action Auto-Chain | 8.7 | Converts detected risk into owner-ready action packs quickly. | Pending-Approval |
| 9 | Knowledge Decay Alarm | 8.5 | Flags playbooks that no longer match real team behavior. | Pending-Approval |
| 10 | What-If Shock Simulator | 8.4 | Simulates operational shocks and impact propagation for planning. | Pending-Approval |
| 11 | Multi-Persona Truth Views | 8.2 | Shows alignment/misalignment across executive, PM, and engineering lenses. | Pending-Approval |
| 12 | Signal Spoof Protection | 8.0 | Detects green-reporting patterns masking true execution risk. | Pending-Approval |
| 13 | Human-in-the-Loop Reasoning Replay | 7.8 | Improves transparency by showing evidence used and rejected paths. | Pending-Approval |
| 14 | Workload Fairness and Burnout Forecast | 7.6 | Predicts overload risk with intervention-ready signals. | Pending-Approval |
| 15 | Decision Memory for New Joiners | 7.4 | Preserves rationale and assumptions for continuity and onboarding. | Pending-Approval |

## Active Development List
Manually move selected features here when development starts.

### Active Item Template
Copy this block for each feature moved from backlog.

Feature:
Owner:
Status: Planned | In Progress | Blocked | Demo Ready | Done
ETA:
Demo Prompt:
Expected Output:
Dependencies:
Notes:

### Active Items Tracker
| Feature | Owner | Status | ETA | Demo Prompt |
|---|---|---|---|---|
| (Add first feature from backlog) | (Name) | Planned | (YYYY-MM-DD) | (Prompt to run in demo) |

## Development Topics (Pick and Plan)
Use this section to choose implementation tracks and define scope.

### 1) Data and Context Layer
- [ ] Multi-source ingestion contract (emails, meetings, files, notes, tables)
- [ ] Unified context schema and entity normalization
- [ ] Scenario-specific adapters and test fixtures
- [ ] Data freshness and retrieval strategy

### 2) Intelligence and Reasoning Layer
- [ ] Prompt orchestration for synthesis and summarization
- [ ] Risk scoring heuristic and confidence scoring
- [ ] Persona-aware response shaping logic
- [ ] Action recommendation generation and ranking

### 3) Trust, Safety, and Governance
- [ ] Source citation formatting and traceability rules
- [ ] Hallucination containment patterns (grounded answer requirements)
- [ ] Compliance guardrails and safe-answer policy checks
- [ ] Role-based visibility filters

### 4) Product and UX Demonstration
- [ ] Demo flow design (7-minute and 12-minute variants)
- [ ] Narrative states: question -> insight -> evidence -> action
- [ ] Output templates (executive brief, risk report, meeting digest)
- [ ] Fail-safe demo fallback responses

### 5) Engineering and Delivery
- [ ] API contracts and endpoint design
- [ ] Evaluation harness updates (quality, grounding, usefulness)
- [ ] Automated test coverage for high-impact scenarios
- [ ] Performance and latency budget for live demo

### 6) Hackathon Readiness
- [ ] Judge-facing value proposition (problem, differentiation, ROI)
- [ ] Demo script with expected outputs per step
- [ ] Backup scenarios if primary scenario fails
- [ ] Final checklist: reliability, clarity, and reproducibility

## Notes
- Keep backlog priority order stable unless scoring criteria change.
- If needed, add columns for effort, risk, and owner to improve sprint planning.
