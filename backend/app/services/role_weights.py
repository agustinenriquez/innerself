from typing import Dict
from app.models.user import UserRole

class RoleWeights:
    """Define essence calculation weights based on user roles"""
    
    # Base weights for different essence metrics by role
    ROLE_WEIGHTS = {
        UserRole.DEVELOPER: {
            "pr_quality": 0.35,           # Developers should excel at PR quality
            "commit_activity": 0.30,      # And consistent commits
            "team_collaboration": 0.20,   # Moderate collaboration weight
            "communication_score": 0.15,  # Lower communication weight
        },
        UserRole.PM: {
            "communication_score": 0.40,  # PMs should excel at communication
            "team_collaboration": 0.35,   # And team coordination
            "pr_quality": 0.15,          # Lower code quality weight
            "commit_activity": 0.10,     # Minimal commit weight
        },
        UserRole.QA: {
            "team_collaboration": 0.30,   # QA works closely with team
            "communication_score": 0.30,  # Good communication for bug reports
            "pr_quality": 0.25,          # Code review skills important
            "commit_activity": 0.15,     # Some automation/test commits
        },
        UserRole.DESIGNER: {
            "team_collaboration": 0.35,   # Design requires collaboration
            "communication_score": 0.30,  # Presenting design decisions
            "pr_quality": 0.20,          # Some code/asset contributions
            "commit_activity": 0.15,     # Asset commits
        },
        UserRole.ADMIN: {
            "team_collaboration": 0.30,   # Balanced admin role
            "communication_score": 0.25,
            "pr_quality": 0.25,
            "commit_activity": 0.20,
        }
    }
    
    # Essence multipliers for actions based on role
    ACTION_MULTIPLIERS = {
        UserRole.DEVELOPER: {
            "pr_merged": 1.2,            # Bonus for developers
            "code_review": 1.1,
            "helpful_comment": 0.9,      # Slightly less for non-code help
            "micromanagement": 1.5,      # Penalty multiplier
        },
        UserRole.PM: {
            "pr_merged": 0.8,            # Less bonus for PMs doing code
            "code_review": 0.9,
            "helpful_comment": 1.3,      # Bonus for PM guidance
            "micromanagement": 2.0,      # Higher penalty for PM micromanagement
            "team_coordination": 1.5,    # Bonus for coordination activities
        },
        UserRole.QA: {
            "pr_merged": 0.9,
            "code_review": 1.3,          # QA should be good at reviews
            "helpful_comment": 1.1,
            "micromanagement": 1.2,
            "bug_report": 1.4,           # Bonus for quality bug reports
        },
        UserRole.DESIGNER: {
            "pr_merged": 0.7,            # Rare for designers
            "code_review": 0.8,
            "helpful_comment": 1.2,      # Design feedback valuable
            "micromanagement": 1.0,      # Standard penalty
            "design_feedback": 1.5,      # Bonus for design reviews
        },
        UserRole.ADMIN: {
            "pr_merged": 1.0,            # Standard weights
            "code_review": 1.0,
            "helpful_comment": 1.0,
            "micromanagement": 1.8,      # Higher penalty for admin micromanagement
        }
    }
    
    @classmethod
    def get_role_weights(cls, role: UserRole) -> Dict[str, float]:
        """Get essence metric weights for a role"""
        return cls.ROLE_WEIGHTS.get(role, cls.ROLE_WEIGHTS[UserRole.DEVELOPER])
    
    @classmethod
    def get_action_multiplier(cls, role: UserRole, action: str) -> float:
        """Get action multiplier for a role"""
        role_multipliers = cls.ACTION_MULTIPLIERS.get(role, {})
        return role_multipliers.get(action, 1.0)
    
    @classmethod
    def calculate_weighted_essence(cls, role: UserRole, essence_metrics: Dict[str, float]) -> float:
        """Calculate overall essence using role-specific weights"""
        weights = cls.get_role_weights(role)
        
        weighted_sum = 0.0
        for metric, weight in weights.items():
            metric_value = essence_metrics.get(metric, 50.0)  # Default to 50
            weighted_sum += metric_value * weight
        
        return weighted_sum
    
    @classmethod
    def apply_role_bonus(cls, role: UserRole, base_essence: float, action: str) -> float:
        """Apply role-specific bonus/penalty to essence gain"""
        multiplier = cls.get_action_multiplier(role, action)
        return base_essence * multiplier
    
    @classmethod
    def get_role_expectations(cls, role: UserRole) -> Dict[str, str]:
        """Get role-specific expectations for essence metrics"""
        expectations = {
            UserRole.DEVELOPER: {
                "pr_quality": "Create high-quality, well-documented PRs with good test coverage",
                "commit_activity": "Maintain consistent, meaningful commit patterns",
                "team_collaboration": "Participate in code reviews and technical discussions",
                "communication_score": "Provide clear technical communication and updates"
            },
            UserRole.PM: {
                "communication_score": "Facilitate clear team communication and coordination",
                "team_collaboration": "Enable effective collaboration across team members",
                "pr_quality": "Understand technical decisions and provide product guidance",
                "commit_activity": "Minimal direct code contributions expected"
            },
            UserRole.QA: {
                "team_collaboration": "Work closely with developers to improve quality",
                "communication_score": "Provide clear, actionable bug reports and feedback",
                "pr_quality": "Review code changes for potential quality issues",
                "commit_activity": "Contribute test automation and quality improvements"
            },
            UserRole.DESIGNER: {
                "team_collaboration": "Collaborate on design decisions and user experience",
                "communication_score": "Present and explain design decisions effectively",
                "pr_quality": "Contribute design assets and front-end improvements",
                "commit_activity": "Update design assets and documentation"
            },
            UserRole.ADMIN: {
                "team_collaboration": "Facilitate team processes and remove blockers",
                "communication_score": "Provide clear direction and team updates",
                "pr_quality": "Review and approve technical decisions",
                "commit_activity": "Contribute to infrastructure and tooling"
            }
        }
        
        return expectations.get(role, expectations[UserRole.DEVELOPER])