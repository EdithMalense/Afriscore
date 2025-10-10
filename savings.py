from datetime import datetime, timedelta
from typing import Dict, List, Optional
from enum import Enum
import random

class MemberStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    LEFT = "left"

class VoteType(Enum):
    MANAGER_CHANGE = "manager_change"
    MONTHLY_AMOUNT_CHANGE = "monthly_amount_change"

class Vote:
    """Represents a vote in the stokvel"""
    
    def __init__(self, vote_id: str, stokvel_id: str, vote_type: VoteType,
                 proposal: dict, initiated_by: str):
        self.vote_id = vote_id
        self.stokvel_id = stokvel_id
        self.vote_type = vote_type
        self.proposal = proposal  # e.g., {'new_manager': 'user002'} or {'new_amount': 600.0}
        self.initiated_by = initiated_by
        self.votes: Dict[str, bool] = {}  # member_id: True/False
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=24)
        self.is_active = True
        self.passed = False
    
    def cast_vote(self, member_id: str, vote_yes: bool):
        """Cast a vote"""
        self.votes[member_id] = vote_yes
    
    def check_if_passed(self, total_members: int) -> bool:
        """Check if vote has passed (simple majority)"""
        if not self.is_active:
            return self.passed
        
        yes_votes = sum(1 for v in self.votes.values() if v)
        total_votes = len(self.votes)
        
        # Need majority of total members to vote yes
        required_votes = (total_members // 2) + 1
        
        if yes_votes >= required_votes:
            self.passed = True
            self.is_active = False
            return True
        
        # Check if expired
        if datetime.now() >= self.expires_at:
            self.is_active = False
            return False
        
        return False
    
    def get_vote_info(self) -> dict:
        """Get vote information"""
        yes_votes = sum(1 for v in self.votes.values() if v)
        no_votes = sum(1 for v in self.votes.values() if not v)
        
        return {
            'vote_id': self.vote_id,
            'type': self.vote_type.value,
            'proposal': self.proposal,
            'initiated_by': self.initiated_by,
            'yes_votes': yes_votes,
            'no_votes': no_votes,
            'total_votes': len(self.votes),
            'is_active': self.is_active,
            'passed': self.passed,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'time_remaining': str(self.expires_at - datetime.now()) if self.is_active else "Expired"
        }

class Stokvel:
    """Manages a stokvel group and its members"""
    
    MIN_MEMBERS = 2
    MAX_MEMBERS = 10
    
    def __init__(self, stokvel_id: str, name: str, creator_id: str, monthly_amount: float):
        if monthly_amount <= 0 or monthly_amount > 5000:
            raise ValueError("Monthly amount must be between R0 and R5,000.")
        
        self.stokvel_id = stokvel_id
        self.name = name
        self.manager_id = creator_id  # Current manager
        self.monthly_amount = monthly_amount
        self.members: Dict[str, dict] = {}
        self.contributions: Dict[str, List[dict]] = {}
        self.payout_schedule: List[tuple] = []  # [(member_id, date)]
        self.votes: Dict[str, Vote] = {}
        self.created_at = datetime.now()
        self.vote_counter = 0
        
        # Automatically add creator as accepted member and manager
        self.members[creator_id] = {
            'status': MemberStatus.ACCEPTED,
            'joined_at': self.created_at,
            'is_manager': True
        }
        self.contributions[creator_id] = []
    
    def _generate_vote_id(self) -> str:
        """Generate unique vote ID"""
        self.vote_counter += 1
        return f"VOTE_{self.stokvel_id}_{self.vote_counter:04d}"
    
    def _calculate_payout_dates(self):
        """Calculate payout dates for all members (monthly cycle)"""
        accepted_members = self.get_accepted_members()
        if not accepted_members:
            return
        
        # Shuffle members randomly
        shuffled_members = accepted_members.copy()
        random.shuffle(shuffled_members)
        
        # Assign monthly payout dates
        self.payout_schedule = []
        base_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Start from next month
        if datetime.now().day > 1:
            if base_date.month == 12:
                base_date = base_date.replace(year=base_date.year + 1, month=1)
            else:
                base_date = base_date.replace(month=base_date.month + 1)
        
        for idx, member_id in enumerate(shuffled_members):
            # Each member gets payout in consecutive months
            payout_date = base_date
            if idx > 0:
                months_to_add = idx
                new_month = base_date.month + months_to_add
                new_year = base_date.year + (new_month - 1) // 12
                new_month = ((new_month - 1) % 12) + 1
                payout_date = base_date.replace(year=new_year, month=new_month)
            
            self.payout_schedule.append((member_id, payout_date))
    
    def get_payout_schedule(self) -> List[dict]:
        """Get the payout schedule with dates"""
        if not self.payout_schedule:
            self._calculate_payout_dates()
        
        schedule = []
        for member_id, payout_date in self.payout_schedule:
            schedule.append({
                'member_id': member_id,
                'payout_date': payout_date,
                'is_past': payout_date < datetime.now(),
                'expected_amount': self.monthly_amount * len(self.get_accepted_members())
            })
        
        return schedule
    
    def can_add_member(self) -> bool:
        """Check if stokvel can accept more members"""
        accepted_count = len(self.get_accepted_members())
        return accepted_count < self.MAX_MEMBERS
    
    def invite_member(self, member_id: str, phone_number: str) -> bool:
        """Invite a member to the stokvel"""
        if member_id in self.members:
            raise ValueError("Member already invited or is part of the stokvel.")
        
        if not self.can_add_member():
            raise ValueError(f"Stokvel is full (maximum {self.MAX_MEMBERS} members).")
        
        self.members[member_id] = {
            'status': MemberStatus.PENDING,
            'invited_at': datetime.now(),
            'phone_number': phone_number,
            'is_manager': False
        }
        return True
    
    def accept_invitation(self, member_id: str) -> bool:
        """Member accepts invitation to join stokvel"""
        if member_id not in self.members:
            raise ValueError("No invitation found for this member.")
        
        if self.members[member_id]['status'] != MemberStatus.PENDING:
            raise ValueError("Invitation has already been processed.")
        
        if not self.can_add_member():
            raise ValueError(f"Stokvel is full (maximum {self.MAX_MEMBERS} members).")
        
        self.members[member_id]['status'] = MemberStatus.ACCEPTED
        self.members[member_id]['joined_at'] = datetime.now()
        self.contributions[member_id] = []
        
        # Recalculate payout schedule
        self._calculate_payout_dates()
        
        return True
    
    def reject_invitation(self, member_id: str) -> bool:
        """Member rejects invitation to join stokvel"""
        if member_id not in self.members:
            raise ValueError("No invitation found for this member.")
        
        if self.members[member_id]['status'] != MemberStatus.PENDING:
            raise ValueError("Invitation has already been processed.")
        
        self.members[member_id]['status'] = MemberStatus.REJECTED
        return True
    
    def leave_stokvel(self, member_id: str) -> bool:
        """Member leaves the stokvel"""
        if member_id not in self.members:
            raise ValueError("Member not part of this stokvel.")
        
        if self.members[member_id]['status'] != MemberStatus.ACCEPTED:
            raise ValueError("Only accepted members can leave.")
        
        # Check if member is manager
        if self.members[member_id].get('is_manager', False):
            # If manager is leaving, initiate manager vote
            if len(self.get_accepted_members()) <= 1:
                raise ValueError("Cannot leave - you are the last member. Delete the stokvel instead.")
            
            # Manager must transfer ownership before leaving
            raise ValueError("As manager, you must transfer ownership before leaving or demote yourself to member.")
        
        # Mark as left
        self.members[member_id]['status'] = MemberStatus.LEFT
        self.members[member_id]['left_at'] = datetime.now()
        
        # Check minimum members
        if len(self.get_accepted_members()) < self.MIN_MEMBERS:
            raise ValueError(f"Cannot leave - stokvel needs minimum {self.MIN_MEMBERS} members.")
        
        # Recalculate payout schedule
        self._calculate_payout_dates()
        
        return True
    
    def initiate_manager_vote(self, initiated_by: str, proposed_manager: str) -> Vote:
        """Initiate a vote to change manager"""
        if initiated_by not in self.get_accepted_members():
            raise ValueError("Only accepted members can initiate votes.")
        
        if proposed_manager not in self.get_accepted_members():
            raise ValueError("Proposed manager must be an accepted member.")
        
        # Check for active manager votes
        for vote in self.votes.values():
            if vote.is_active and vote.vote_type == VoteType.MANAGER_CHANGE:
                raise ValueError("There is already an active manager vote.")
        
        vote_id = self._generate_vote_id()
        vote = Vote(
            vote_id,
            self.stokvel_id,
            VoteType.MANAGER_CHANGE,
            {'new_manager': proposed_manager},
            initiated_by
        )
        
        self.votes[vote_id] = vote
        return vote
    
    def initiate_amount_change_vote(self, initiated_by: str, new_amount: float) -> Vote:
        """Initiate a vote to change monthly amount"""
        if initiated_by not in self.get_accepted_members():
            raise ValueError("Only accepted members can initiate votes.")
        
        if new_amount <= 0 or new_amount > 5000:
            raise ValueError("Monthly amount must be between R0 and R5,000.")
        
        # Check for active amount change votes
        for vote in self.votes.values():
            if vote.is_active and vote.vote_type == VoteType.MONTHLY_AMOUNT_CHANGE:
                raise ValueError("There is already an active amount change vote.")
        
        vote_id = self._generate_vote_id()
        vote = Vote(
            vote_id,
            self.stokvel_id,
            VoteType.MONTHLY_AMOUNT_CHANGE,
            {'new_amount': new_amount},
            initiated_by
        )
        
        self.votes[vote_id] = vote
        return vote
    
    def cast_vote(self, vote_id: str, member_id: str, vote_yes: bool) -> bool:
        """Member casts a vote"""
        if vote_id not in self.votes:
            raise ValueError("Vote not found.")
        
        if member_id not in self.get_accepted_members():
            raise ValueError("Only accepted members can vote.")
        
        vote = self.votes[vote_id]
        if not vote.is_active:
            raise ValueError("This vote is no longer active.")
        
        vote.cast_vote(member_id, vote_yes)
        
        # Check if vote passed
        total_members = len(self.get_accepted_members())
        if vote.check_if_passed(total_members):
            # Apply the change
            if vote.vote_type == VoteType.MANAGER_CHANGE:
                self._change_manager(vote.proposal['new_manager'])
            elif vote.vote_type == VoteType.MONTHLY_AMOUNT_CHANGE:
                self.monthly_amount = vote.proposal['new_amount']
                self._calculate_payout_dates()  # Recalculate with new amount
            
            return True
        
        return False
    
    def _change_manager(self, new_manager_id: str):
        """Change the stokvel manager"""
        # Remove manager status from old manager
        for member_id in self.members:
            if self.members[member_id].get('is_manager', False):
                self.members[member_id]['is_manager'] = False
        
        # Set new manager
        self.manager_id = new_manager_id
        self.members[new_manager_id]['is_manager'] = True
    
    def manager_demote_self(self, new_manager_id: str) -> bool:
        """Manager demotes themselves and appoints new manager"""
        if new_manager_id not in self.get_accepted_members():
            raise ValueError("New manager must be an accepted member.")
        
        self._change_manager(new_manager_id)
        return True
    
    def manager_change_amount(self, new_amount: float) -> bool:
        """Manager directly changes monthly amount (without vote)"""
        if new_amount <= 0 or new_amount > 5000:
            raise ValueError("Monthly amount must be between R0 and R5,000.")
        
        self.monthly_amount = new_amount
        self._calculate_payout_dates()
        return True
    
    def get_active_votes(self) -> List[dict]:
        """Get all active votes"""
        active_votes = []
        for vote in self.votes.values():
            if vote.is_active:
                active_votes.append(vote.get_vote_info())
        return active_votes
    
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
        for member_id in self.get_accepted_members():
            if member_id in self.contributions:
                total += sum(c['amount'] for c in self.contributions[member_id])
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
            'manager_id': self.manager_id,
            'monthly_amount': self.monthly_amount,
            'total_contributions': self.get_stokvel_total(),
            'member_count': len(self.get_accepted_members()),
            'min_members': self.MIN_MEMBERS,
            'max_members': self.MAX_MEMBERS,
            'can_add_members': self.can_add_member(),
            'payout_schedule': self.get_payout_schedule(),
            'active_votes': self.get_active_votes(),
            'members': {
                member_id: {
                    'status': data['status'].value,
                    'total_contributed': self.get_member_total(member_id),
                    'is_manager': data.get('is_manager', False)
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
            months_elapsed = (
                (current_date.year - contribution['date'].year) * 12 +
                current_date.month - contribution['date'].month
            )
            
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
        self.user_registry: Dict[str, dict] = {}  # user_id: {phone, name, etc}
    
    def register_user(self, user_id: str, phone_number: str, name: str = None) -> dict:
        """Register a new user"""
        if user_id in self.user_registry:
            return self.user_registry[user_id]
        
        self.user_registry[user_id] = {
            'user_id': user_id,
            'phone_number': phone_number,
            'name': name,
            'registered_at': datetime.now()
        }
        return self.user_registry[user_id]
    
    def get_user_info(self, user_id: str) -> Optional[dict]:
        """Get user information"""
        return self.user_registry.get(user_id)
    
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
        
    
    