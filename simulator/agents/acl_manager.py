"""
ACL Manager - Central access control list for features based on personas.
Defines which roles/personas can access which features in the Work IQ UI.
"""


class FeatureACL:
    """Centralized feature access control based on persona roles."""
    
    # Define feature access rules: feature_name -> set of allowed persona IDs
    # 'admin' = All access (admin/unscoped)
    # 'leadership' = executive/leadership roles
    # 'engineer' = technical roles
    # 'oncall' = on-call roles
    # 'contractor' = limited external access
    
    FEATURE_ACCESS = {
        # Executive Brief - Only for admin and leadership
        'executive_brief': {
            'all',  # All access (admin/unscoped)
            'oncall_lead',  # On-Call Lead / SRE Lead
            'incident_commander',  # Incident Commander / Director (escalation)
        },
        
        # Progress Tracking - Available to all
        'progress_tracking': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # Next Steps - Available to all
        'next_steps': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # Timeline - Available to all
        'timeline': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # Data Duration Filter - Available to all
        'data_filters': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # FAQs - Available to all
        'faqs': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # Suggestions - Available to admin and leadership
        'suggestions': {
            'all',
            'oncall_lead',
            'incident_commander',
        },
        
        # Advanced Analytics - Only admin and leadership
        'advanced_analytics': {
            'all',
            'incident_commander',
        },
        
        # Risk Assessment - Only for on-call lead and director
        'risk_assessment': {
            'all',
            'oncall_lead',
            'incident_commander',
        },
        
        # Compliance Reporting - Only admin and director
        'compliance_reporting': {
            'all',
            'incident_commander',
        },
        
        # Action Recommendations - Available to all except contractors
        'action_recommendations': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'incident_commander',
        },
        
        # Scenario Timeline - Available to all
        'scenario_timeline': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # What-If Simulation - Available to leadership and engineers
        'whatif_simulation': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'incident_commander',
        },

        # Pre-mortem Generator - Available to all personas for planning
        'premortem_generator': {
            'all',
            'ops_director',
            'quality_pm',
            'credentialing_lead',
            'vendor_liaison',
            'new_pm',
            'quality_engineer',
            'director',
            'delivery_principal',
            'consultant',
            'duty_manager',
            'ops_engineer',
            'associate_dean',
            'committee_member',
            'adjunct',
            'provost',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
        
        # Interactive Dashboard - Available to all
        'interactive_dashboard': {
            'all',
            'oncall_lead',
            'sre_engineer',
            'contractor',
            'incident_commander',
        },
    }
    
    # Persona to ID mapping (for consistency)
    PERSONA_MAPPING = {
        'all': 'all',
        'admin': 'all',
        'Marco Reyes — On-Call Lead / SRE Lead': 'oncall_lead',
        'oncall_lead': 'oncall_lead',
        'Aisha Khan — SRE Engineer (on-call)': 'sre_engineer',
        'sre_engineer': 'sre_engineer',
        'Evan Cole — Contractor SRE (least privilege)': 'contractor',
        'contractor': 'contractor',
        'Helen Cho — Incident Commander / Director (escalation)': 'incident_commander',
        'incident_commander': 'incident_commander',
    }
    
    @staticmethod
    def normalize_persona_id(persona_id: str) -> str:
        """Normalize persona ID to standard internal format."""
        if not persona_id:
            return 'all'
        
        # Try direct mapping first
        normalized = FeatureACL.PERSONA_MAPPING.get(persona_id)
        if normalized:
            return normalized
        
        # Fallback to lowercase, replacing spaces and special chars
        normalized = persona_id.lower().replace(' ', '_').replace('-', '_')
        return normalized
    
    @staticmethod
    def can_access_feature(feature_name: str, persona_id: str) -> bool:
        """
        Check if a persona can access a feature.
        
        Args:
            feature_name: Name of the feature to check
            persona_id: Persona ID requesting access
            
        Returns:
            True if persona can access, False otherwise
        """
        if not feature_name:
            return False
        
        # Normalize the feature name
        feature_key = feature_name.lower().replace(' ', '_').replace('-', '_')
        
        # Get allowed personas for this feature
        allowed_personas = FeatureACL.FEATURE_ACCESS.get(feature_key, set())
        
        if not allowed_personas:
            # If feature not defined, deny access
            return False
        
        # Normalize persona ID
        normalized_persona = FeatureACL.normalize_persona_id(persona_id)
        
        # Check if persona is in allowed list
        return normalized_persona in allowed_personas
    
    @staticmethod
    def get_allowed_features(persona_id: str) -> list:
        """
        Get list of all features accessible to a persona.
        
        Args:
            persona_id: Persona ID
            
        Returns:
            List of feature names accessible to this persona
        """
        normalized_persona = FeatureACL.normalize_persona_id(persona_id)
        allowed_features = []
        
        for feature, allowed_personas in FeatureACL.FEATURE_ACCESS.items():
            if normalized_persona in allowed_personas:
                allowed_features.append(feature)
        
        return allowed_features
    
    @staticmethod
    def get_feature_details() -> dict:
        """
        Get complete feature access configuration.
        
        Returns:
            Dict mapping features to allowed personas
        """
        return {
            feature: list(personas)
            for feature, personas in FeatureACL.FEATURE_ACCESS.items()
        }
