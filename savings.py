from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

class MemberStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"

class Stokvel:
    """Manages a stokvel group and its members"""
    
    def __init__(self, stokvel_id: str, name: str, creator_id: str, monthly_amount: float):
        if monthly_amount <= 0 or monthly_amount > 5000:
            raise ValueError("Monthly amount must be between R0 and R5,000.")
        
        self.stokvel_id = stokvel_id
        self.name = name
        self.creator_id = creator_id
        self.monthly_amount = monthly_amount
        self.members: Dict[str, dict] = {}
        self.contributions: Dict[str, List[dict]] = {}
        self.created_at = datetime.now()
        
        # Automatically add creator as accepted member
        self.members[creator_id] = {
            'status': MemberStatus.ACCEPTED,
            'joined_at': self.created_at
        }
        self.contributions[creator_id] = []
    
    def invite_member(self, member_id: str) -> bool:
        """Invite a member to the stokvel"""
        if member_id in self.members:
            raise ValueError("Member already invited or is part of the stokvel.")
        
        self.members[member_id] = {
            'status': MemberStatus.PENDING,
            'invited_at': datetime.now()
        }
        return True
    
    def accept_invitation(self, member_id: str) -> bool:
        """Member accepts invitation to join stokvel"""
        if member_id not in self.members:
            raise ValueError("No invitation found for this member.")
        
        if self.members[member_id]['status'] != MemberStatus.PENDING:
            raise ValueError("Invitation has already been processed.")
        
        self.members[member_id]['status'] = MemberStatus.ACCEPTED
        self.members[member_id]['joined_at'] = datetime.now()
        self.contributions[member_id] = []
        return True
    
    def reject_invitation(self, member_id: str) -> bool:
        """Member rejects invitation to join stokvel"""
        if member_id not in self.members:
            raise ValueError("No invitation found for this member.")
        
        if self.members[member_id]['status'] != MemberStatus.PENDING:
            raise ValueError("Invitation has already been processed.")
        
        self.members[member_id]['status'] = MemberStatus.REJECTED
        return True
    
    def add_contribution(self, member_id: str, amount: float) -> dict:
        """Add a contribution from a member"""
        if member_id not in self.members:
            raise ValueError("Member not part of this stokvel.")
        
        if self.members[member_id]['status'] != MemberStatus.ACCEPTED:
            raise ValueError("Member has not accepted the invitation.")
        
        if amount <= 0 or amount > 5000:
            raise ValueError("Contribution must be between R0 and R5,000.")
        
        contribution = {
            'amount': amount,
            'date': datetime.now(),
            'member_id': member_id
        }
        
        self.contributions[member_id].append(contribution)
        return contribution
    
    def get_member_total(self, member_id: str) -> float:
        """Get total contributions for a specific member"""
        if member_id not in self.contributions:
            return 0.0
        
        return round(sum(c['amount'] for c in self.contributions[member_id]), 2)
    
    def get_stokvel_total(self) -> float:
        """Get total contributions for entire stokvel"""
        total = 0.0
        for member_contributions in self.contributions.values():
            total += sum(c['amount'] for c in member_contributions)
        return round(total, 2)
    
    def get_accepted_members(self) -> List[str]:
        """Get list of accepted member IDs"""
        return [
            member_id for member_id, data in self.members.items()
            if data['status'] == MemberStatus.ACCEPTED
        ]
    
    def get_stokvel_summary(self) -> dict:
        """Get complete summary of stokvel"""
        return {
            'stokvel_id': self.stokvel_id,
            'name': self.name,
            'monthly_amount': self.monthly_amount,
            'total_contributions': self.get_stokvel_total(),
            'member_count': len(self.get_accepted_members()),
            'members': {
                member_id: {
                    'status': data['status'].value,
                    'total_contributed': self.get_member_total(member_id)
                }
                for member_id, data in self.members.items()
            }
        }


class IndividualSavings:
    """Manages individual savings account"""
    
    def __init__(self, user_id: str, savings_goal: Optional[float] = None):
        self.user_id = user_id
        self.savings_goal = savings_goal
        self.contributions: List[dict] = []
        self.created_at = datetime.now()
    
    def add_contribution(self, amount: float) -> dict:
        """Add a savings contribution"""
        if amount <= 0 or amount > 5000:
            raise ValueError("Contribution must be between R0 and R5,000.")
        
        contribution = {
            'amount': amount,
            'date': datetime.now()
        }
        
        self.contributions.append(contribution)
        return contribution
    
    def get_total_savings(self) -> float:
        """Get total savings without interest"""
        return round(sum(c['amount'] for c in self.contributions), 2)
    
    def get_savings_with_interest(self, monthly_interest_rate: float = 0.05) -> float:
        """Calculate total savings with compound interest"""
        if monthly_interest_rate < 0 or monthly_interest_rate > 1:
            raise ValueError("Interest rate must be between 0 and 1.")
        
        total_savings = 0.0
        current_date = datetime.now()
        
        for contribution in self.contributions:
            # Calculate months since contribution
            months_elapsed = (
                (current_date.year - contribution['date'].year) * 12 +
                current_date.month - contribution['date'].month
            )
            
            # Apply compound interest
            amount_with_interest = contribution['amount'] * ((1 + monthly_interest_rate) ** months_elapsed)
            total_savings += amount_with_interest
        
        return round(total_savings, 2)
    
    def get_progress_percentage(self) -> Optional[float]:
        """Get savings progress as percentage of goal"""
        if self.savings_goal is None or self.savings_goal == 0:
            return None
        
        return round((self.get_total_savings() / self.savings_goal) * 100, 2)
    
    def set_savings_goal(self, goal: float) -> bool:
        """Set or update savings goal"""
        if goal <= 0:
            raise ValueError("Savings goal must be positive.")
        
        self.savings_goal = goal
        return True
    
    def get_savings_summary(self, include_interest: bool = False, 
                           interest_rate: float = 0.05) -> dict:
        """Get complete savings summary"""
        summary = {
            'user_id': self.user_id,
            'total_contributions': len(self.contributions),
            'total_saved': self.get_total_savings(),
            'savings_goal': self.savings_goal,
            'progress_percentage': self.get_progress_percentage()
        }
        
        if include_interest:
            summary['total_with_interest'] = self.get_savings_with_interest(interest_rate)
        
        return summary


class SavingsManager:
    """Main manager for all savings operations"""
    
    def __init__(self):
        self.stokvels: Dict[str, Stokvel] = {}
        self.individual_savings: Dict[str, IndividualSavings] = {}
    
    def create_stokvel(self, stokvel_id: str, name: str, creator_id: str, 
                      monthly_amount: float) -> Stokvel:
        """Create a new stokvel"""
        if stokvel_id in self.stokvels:
            raise ValueError("Stokvel ID already exists.")
        
        stokvel = Stokvel(stokvel_id, name, creator_id, monthly_amount)
        self.stokvels[stokvel_id] = stokvel
        return stokvel
    
    def get_stokvel(self, stokvel_id: str) -> Stokvel:
        """Get a stokvel by ID"""
        if stokvel_id not in self.stokvels:
            raise ValueError("Stokvel not found.")
        return self.stokvels[stokvel_id]
    
    def create_individual_savings(self, user_id: str, 
                                 savings_goal: Optional[float] = None) -> IndividualSavings:
        """Create individual savings account"""
        if user_id in self.individual_savings:
            raise ValueError("Savings account already exists for this user.")
        
        savings = IndividualSavings(user_id, savings_goal)
        self.individual_savings[user_id] = savings
        return savings
    
    def get_individual_savings(self, user_id: str) -> IndividualSavings:
        """Get individual savings account"""
        if user_id not in self.individual_savings:
            raise ValueError("Savings account not found for this user.")
        return self.individual_savings[user_id]
    
    def get_user_stokvels(self, user_id: str) -> List[dict]:
        """Get all stokvels a user is part of"""
        user_stokvels = []
        for stokvel in self.stokvels.values():
            if user_id in stokvel.members and stokvel.members[user_id]['status'] == MemberStatus.ACCEPTED:
                user_stokvels.append(stokvel.get_stokvel_summary())
        return user_stokvels
        
    
    