from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import random
import string

class WithdrawalStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class WithdrawalType(Enum):
    INDIVIDUAL_SAVINGS = "individual_savings"
    STOKVEL_PAYOUT = "stokvel_payout"

class PaymentPIN:
    """Manages a withdrawal PIN"""
    
    def __init__(self, pin_id: str, user_id: str, phone_number: str, 
                 amount: float, withdrawal_type: WithdrawalType, 
                 source_id: str = None):
        self.pin_id = pin_id
        self.user_id = user_id
        self.phone_number = phone_number
        self.amount = amount
        self.withdrawal_type = withdrawal_type
        self.source_id = source_id  # stokvel_id or savings account id
        self.pin_code = self._generate_pin()
        self.created_at = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=24)  # 24 hour expiry
        self.status = WithdrawalStatus.PENDING
        self.redeemed_at = None
    
    def _generate_pin(self) -> str:
        """Generate a unique 5-digit PIN"""
        return ''.join(random.choices(string.digits, k=5))
    
    def is_valid(self) -> bool:
        """Check if PIN is still valid"""
        return (self.status == WithdrawalStatus.PENDING and 
                datetime.now() < self.expires_at)
    
    def mark_expired(self) -> bool:
        """Mark PIN as expired"""
        if datetime.now() >= self.expires_at and self.status == WithdrawalStatus.PENDING:
            self.status = WithdrawalStatus.EXPIRED
            return True
        return False
    
    def redeem(self) -> bool:
        """Redeem the PIN (mark as completed)"""
        if not self.is_valid():
            raise ValueError("PIN is not valid or has expired.")
        
        self.status = WithdrawalStatus.COMPLETED
        self.redeemed_at = datetime.now()
        return True
    
    def cancel(self) -> bool:
        """Cancel the withdrawal"""
        if self.status != WithdrawalStatus.PENDING:
            raise ValueError("Can only cancel pending withdrawals.")
        
        self.status = WithdrawalStatus.CANCELLED
        return True
    
    def get_pin_info(self) -> dict:
        """Get PIN information"""
        return {
            'pin_id': self.pin_id,
            'pin_code': self.pin_code,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'amount': self.amount,
            'withdrawal_type': self.withdrawal_type.value,
            'source_id': self.source_id,
            'status': self.status.value,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'redeemed_at': self.redeemed_at,
            'is_valid': self.is_valid(),
            'time_remaining': str(self.expires_at - datetime.now()) if self.is_valid() else "Expired"
        }

class StokvelPayoutSchedule:
    """Manages the payout schedule for a stokvel"""
    
    def __init__(self, stokvel_id: str):
        self.stokvel_id = stokvel_id
        self.payout_history: List[dict] = []
        self.current_cycle_members: List[str] = []
        self.upcoming_payouts: List[str] = []
    
    def initialize_payout_order(self, member_ids: List[str]) -> List[str]:
        """Initialize random payout order for all members"""
        if not member_ids:
            raise ValueError("No members to initialize payout order.")
        
        # Create a shuffled copy of members
        self.current_cycle_members = member_ids.copy()
        random.shuffle(self.current_cycle_members)
        self.upcoming_payouts = self.current_cycle_members.copy()
        
        return self.upcoming_payouts
    
    def get_next_payout_recipient(self) -> Optional[str]:
        """Get the next member due for payout"""
        if not self.upcoming_payouts:
            return None
        return self.upcoming_payouts[0]
    
    def complete_payout(self, member_id: str, amount: float) -> dict:
        """Record a completed payout"""
        if not self.upcoming_payouts:
            raise ValueError("No upcoming payouts scheduled.")
        
        if self.upcoming_payouts[0] != member_id:
            raise ValueError(f"It's not {member_id}'s turn for payout yet.")
        
        # Remove from upcoming
        self.upcoming_payouts.pop(0)
        
        # Record in history
        payout_record = {
            'member_id': member_id,
            'amount': amount,
            'date': datetime.now(),
            'cycle_position': len(self.current_cycle_members) - len(self.upcoming_payouts)
        }
        self.payout_history.append(payout_record)
        
        # If all members have been paid, start new cycle
        if not self.upcoming_payouts:
            self.initialize_payout_order(self.current_cycle_members)
        
        return payout_record
    
    def is_member_next(self, member_id: str) -> bool:
        """Check if it's a specific member's turn for payout"""
        return self.upcoming_payouts and self.upcoming_payouts[0] == member_id
    
    def get_member_position(self, member_id: str) -> Optional[int]:
        """Get member's position in payout queue (1-indexed)"""
        try:
            return self.upcoming_payouts.index(member_id) + 1
        except ValueError:
            return None
    
    def get_schedule_info(self) -> dict:
        """Get complete schedule information"""
        return {
            'stokvel_id': self.stokvel_id,
            'next_recipient': self.get_next_payout_recipient(),
            'upcoming_order': self.upcoming_payouts,
            'total_payouts_completed': len(self.payout_history),
            'current_cycle_size': len(self.current_cycle_members)
        }

class PaymentsManager:
    """Main manager for all payment and withdrawal operations"""
    
    def __init__(self, savings_manager):
        self.savings_manager = savings_manager
        self.pins: Dict[str, PaymentPIN] = {}
        self.stokvel_schedules: Dict[str, StokvelPayoutSchedule] = {}
        self.pin_counter = 0
    
    def _generate_pin_id(self) -> str:
        """Generate unique PIN ID"""
        self.pin_counter += 1
        return f"PIN_{datetime.now().strftime('%Y%m%d')}_{self.pin_counter:06d}"
    
    def _cleanup_expired_pins(self):
        """Mark expired PINs"""
        for pin in self.pins.values():
            pin.mark_expired()
    
    def get_or_create_schedule(self, stokvel_id: str) -> StokvelPayoutSchedule:
        """Get or create payout schedule for a stokvel"""
        if stokvel_id not in self.stokvel_schedules:
            schedule = StokvelPayoutSchedule(stokvel_id)
            stokvel = self.savings_manager.get_stokvel(stokvel_id)
            accepted_members = stokvel.get_accepted_members()
            
            if accepted_members:
                schedule.initialize_payout_order(accepted_members)
            
            self.stokvel_schedules[stokvel_id] = schedule
        
        return self.stokvel_schedules[stokvel_id]
    
    def request_individual_withdrawal(self, user_id: str, phone_number: str, 
                                     amount: float) -> PaymentPIN:
        """Request withdrawal from individual savings"""
        self._cleanup_expired_pins()
        
        if amount <= 0 or amount > 5000:
            raise ValueError("Withdrawal amount must be between R0 and R5,000.")
        
        # Verify user has savings account and sufficient funds
        savings = self.savings_manager.get_individual_savings(user_id)
        available_balance = savings.get_total_savings()
        
        if amount > available_balance:
            raise ValueError(f"Insufficient funds. Available: R{available_balance:.2f}")
        
        # Create PIN
        pin_id = self._generate_pin_id()
        pin = PaymentPIN(
            pin_id=pin_id,
            user_id=user_id,
            phone_number=phone_number,
            amount=amount,
            withdrawal_type=WithdrawalType.INDIVIDUAL_SAVINGS,
            source_id=user_id
        )
        
        self.pins[pin_id] = pin
        return pin
    
    def request_stokvel_withdrawal(self, user_id: str, stokvel_id: str, 
                                  phone_number: str, amount: float = None) -> PaymentPIN:
        """Request withdrawal from stokvel (must be user's turn)"""
        self._cleanup_expired_pins()
        
        # Verify stokvel exists
        stokvel = self.savings_manager.get_stokvel(stokvel_id)
        
        # Verify user is accepted member
        if user_id not in stokvel.get_accepted_members():
            raise ValueError("You are not an accepted member of this stokvel.")
        
        # Get or create payout schedule
        schedule = self.get_or_create_schedule(stokvel_id)
        
        # Check if it's user's turn
        if not schedule.is_member_next(user_id):
            position = schedule.get_member_position(user_id)
            next_recipient = schedule.get_next_payout_recipient()
            raise ValueError(
                f"It's not your turn yet. You are #{position} in queue. "
                f"Next payout: {next_recipient}"
            )
        
        # Calculate total payout amount available
        total_payout = stokvel.get_stokvel_total()
        
        if total_payout <= 0:
            raise ValueError("No funds available for payout.")
        
        # If amount not specified, use total (but capped at R5000)
        if amount is None:
            amount = min(total_payout, 5000.0)
        
        # Validate withdrawal amount
        if amount < 10.0:
            raise ValueError("Minimum withdrawal amount is R10.")
        
        if amount > 5000.0:
            raise ValueError("Maximum withdrawal amount per transaction is R5,000.")
        
        if amount > total_payout:
            raise ValueError(f"Requested amount exceeds available payout (R{total_payout:.2f}).")
        
        # Create PIN
        pin_id = self._generate_pin_id()
        pin = PaymentPIN(
            pin_id=pin_id,
            user_id=user_id,
            phone_number=phone_number,
            amount=amount,
            withdrawal_type=WithdrawalType.STOKVEL_PAYOUT,
            source_id=stokvel_id
        )
        
        self.pins[pin_id] = pin
        
        # Only mark payout as complete if withdrawing full amount
        # This allows multiple withdrawals for large payouts
        if amount >= total_payout:
            schedule.complete_payout(user_id, amount)
        
        return pin
    
    def get_remaining_payout_amount(self, user_id: str, stokvel_id: str) -> float:
        """Get remaining amount user can withdraw from their stokvel payout"""
        stokvel = self.savings_manager.get_stokvel(stokvel_id)
        schedule = self.get_or_create_schedule(stokvel_id)
        
        if not schedule.is_member_next(user_id):
            return 0.0
        
        total_available = stokvel.get_stokvel_total()
        
        # Get all pending/completed stokvel withdrawals for this user
        user_stokvel_pins = [
            pin for pin in self.pins.values()
            if pin.user_id == user_id 
            and pin.source_id == stokvel_id
            and pin.withdrawal_type == WithdrawalType.STOKVEL_PAYOUT
            and pin.status in [WithdrawalStatus.PENDING, WithdrawalStatus.COMPLETED]
        ]
        
        withdrawn_amount = sum(pin.amount for pin in user_stokvel_pins)
        remaining = total_available - withdrawn_amount
        
        return round(max(0, remaining), 2)
    
    def verify_and_redeem_pin(self, pin_code: str, phone_number: str) -> dict:
        """Verify PIN and process withdrawal (for store partners)"""
        self._cleanup_expired_pins()
        
        # Find PIN by code
        matching_pin = None
        for pin in self.pins.values():
            if pin.pin_code == pin_code and pin.phone_number == phone_number:
                matching_pin = pin
                break
        
        if not matching_pin:
            raise ValueError("Invalid PIN or phone number.")
        
        if not matching_pin.is_valid():
            raise ValueError(f"PIN has expired or already been used. Status: {matching_pin.status.value}")
        
        # Redeem PIN
        matching_pin.redeem()
        
        return {
            'success': True,
            'amount': matching_pin.amount,
            'user_id': matching_pin.user_id,
            'withdrawal_type': matching_pin.withdrawal_type.value,
            'redeemed_at': matching_pin.redeemed_at
        }
    
    def cancel_withdrawal(self, pin_id: str, user_id: str) -> bool:
        """Cancel a pending withdrawal"""
        if pin_id not in self.pins:
            raise ValueError("PIN not found.")
        
        pin = self.pins[pin_id]
        
        if pin.user_id != user_id:
            raise ValueError("You can only cancel your own withdrawals.")
        
        pin.cancel()
        return True
    
    def get_user_pins(self, user_id: str, include_expired: bool = False) -> List[dict]:
        """Get all PINs for a user"""
        self._cleanup_expired_pins()
        
        user_pins = []
        for pin in self.pins.values():
            if pin.user_id == user_id:
                if include_expired or pin.is_valid():
                    user_pins.append(pin.get_pin_info())
        
        return sorted(user_pins, key=lambda x: x['created_at'], reverse=True)
    
    def get_stokvel_payout_info(self, stokvel_id: str) -> dict:
        """Get payout information for a stokvel"""
        schedule = self.get_or_create_schedule(stokvel_id)
        stokvel = self.savings_manager.get_stokvel(stokvel_id)
        
        return {
            'stokvel_id': stokvel_id,
            'stokvel_name': stokvel.name,
            'total_pool': stokvel.get_stokvel_total(),
            'next_recipient': schedule.get_next_payout_recipient(),
            'payout_queue': schedule.upcoming_payouts,
            'completed_payouts': len(schedule.payout_history),
            'schedule_info': schedule.get_schedule_info()
        }
    
    def get_user_stokvel_position(self, user_id: str, stokvel_id: str) -> dict:
        """Get user's position in stokvel payout queue"""
        schedule = self.get_or_create_schedule(stokvel_id)
        position = schedule.get_member_position(user_id)
        is_next = schedule.is_member_next(user_id)
        
        return {
            'user_id': user_id,
            'stokvel_id': stokvel_id,
            'position': position,
            'is_next': is_next,
            'total_in_queue': len(schedule.upcoming_payouts),
            'next_recipient': schedule.get_next_payout_recipient()
        }