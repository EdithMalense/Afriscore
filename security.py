from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum
import hashlib
import secrets

class SecurityEventType(Enum):
    LOGIN_ATTEMPT = "login_attempt"
    WITHDRAWAL_REQUEST = "withdrawal_request"
    PIN_VERIFICATION = "pin_verification"
    FAILED_PIN_ATTEMPT = "failed_pin_attempt"
    ACCOUNT_LOCKED = "account_locked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SecurityEvent:
    """Records security-related events"""
    
    def __init__(self, event_id: str, user_id: str, event_type: SecurityEventType,
                 risk_level: RiskLevel, details: dict):
        self.event_id = event_id
        self.user_id = user_id
        self.event_type = event_type
        self.risk_level = risk_level
        self.details = details
        self.timestamp = datetime.now()
        self.ip_address = details.get('ip_address', 'unknown')
    
    def get_info(self) -> dict:
        return {
            'event_id': self.event_id,
            'user_id': self.user_id,
            'event_type': self.event_type.value,
            'risk_level': self.risk_level.value,
            'details': self.details,
            'timestamp': self.timestamp,
            'ip_address': self.ip_address
        }

class RateLimiter:
    """Rate limiting for API calls and actions"""
    
    def __init__(self):
        self.action_counts: Dict[str, List[datetime]] = {}
    
    def check_rate_limit(self, key: str, max_attempts: int, 
                        time_window_minutes: int) -> Tuple[bool, int]:
        """
        Check if action is within rate limit
        Returns: (is_allowed, remaining_attempts)
        """
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(minutes=time_window_minutes)
        
        # Initialize or clean old attempts
        if key not in self.action_counts:
            self.action_counts[key] = []
        
        # Remove old attempts outside time window
        self.action_counts[key] = [
            timestamp for timestamp in self.action_counts[key]
            if timestamp > cutoff_time
        ]
        
        current_count = len(self.action_counts[key])
        
        if current_count >= max_attempts:
            return False, 0
        
        return True, max_attempts - current_count
    
    def record_attempt(self, key: str):
        """Record an attempt"""
        if key not in self.action_counts:
            self.action_counts[key] = []
        self.action_counts[key].append(datetime.now())
    
    def reset_counter(self, key: str):
        """Reset rate limit counter for a key"""
        if key in self.action_counts:
            del self.action_counts[key]

class AccountSecurity:
    """Manages account security for a user"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.failed_pin_attempts = 0
        self.last_failed_attempt = None
        self.is_locked = False
        self.locked_until = None
        self.lockout_duration_minutes = 30
        self.max_failed_attempts = 3
    
    def record_failed_pin_attempt(self):
        """Record a failed PIN verification attempt"""
        self.failed_pin_attempts += 1
        self.last_failed_attempt = datetime.now()
        
        if self.failed_pin_attempts >= self.max_failed_attempts:
            self.lock_account()
    
    def lock_account(self):
        """Lock the account due to suspicious activity"""
        self.is_locked = True
        self.locked_until = datetime.now() + timedelta(minutes=self.lockout_duration_minutes)
    
    def unlock_account(self):
        """Manually unlock account"""
        self.is_locked = False
        self.locked_until = None
        self.failed_pin_attempts = 0
    
    def check_if_locked(self) -> bool:
        """Check if account is currently locked"""
        if not self.is_locked:
            return False
        
        # Auto-unlock if lockout period has passed
        if self.locked_until and datetime.now() >= self.locked_until:
            self.unlock_account()
            return False
        
        return True
    
    def reset_failed_attempts(self):
        """Reset failed attempt counter after successful verification"""
        self.failed_pin_attempts = 0
        self.last_failed_attempt = None
    
    def get_lockout_time_remaining(self) -> Optional[timedelta]:
        """Get remaining lockout time"""
        if not self.is_locked or not self.locked_until:
            return None
        
        remaining = self.locked_until - datetime.now()
        return remaining if remaining.total_seconds() > 0 else None

class FraudDetection:
    """Detects potentially fraudulent activities"""
    
    @staticmethod
    def check_withdrawal_pattern(user_id: str, amount: float, 
                                 recent_withdrawals: List[dict]) -> Tuple[bool, RiskLevel, str]:
        """
        Analyze withdrawal patterns for suspicious activity
        Returns: (is_suspicious, risk_level, reason)
        """
        # Check for multiple withdrawals in short time
        if len(recent_withdrawals) >= 3:
            time_span = recent_withdrawals[0]['timestamp'] - recent_withdrawals[-1]['timestamp']
            if time_span < timedelta(hours=1):
                return True, RiskLevel.HIGH, "Multiple withdrawals in short time period"
        
        # Check for unusually large withdrawal
        if recent_withdrawals:
            avg_amount = sum(w['amount'] for w in recent_withdrawals) / len(recent_withdrawals)
            if amount > avg_amount * 3:
                return True, RiskLevel.MEDIUM, "Withdrawal amount significantly higher than usual"
        
        # Check for maximum limit abuse
        if amount >= 4500:  # Close to R5000 limit
            return True, RiskLevel.MEDIUM, "Withdrawal near maximum limit"
        
        return False, RiskLevel.LOW, "No suspicious patterns detected"
    
    @staticmethod
    def check_phone_number_change(user_id: str, new_phone: str, 
                                  old_phone: str) -> Tuple[bool, RiskLevel, str]:
        """Check if phone number change is suspicious"""
        if not old_phone:
            return False, RiskLevel.LOW, "First time phone number registration"
        
        if old_phone != new_phone:
            return True, RiskLevel.HIGH, "Phone number changed - requires verification"
        
        return False, RiskLevel.LOW, "Phone number unchanged"
    
    @staticmethod
    def check_stokvel_payout_integrity(stokvel_id: str, member_id: str,
                                      expected_next: str) -> Tuple[bool, RiskLevel, str]:
        """Verify stokvel payout is legitimate"""
        if member_id != expected_next:
            return True, RiskLevel.CRITICAL, "Attempted payout out of turn"
        
        return False, RiskLevel.LOW, "Payout order is correct"

class SecurityManager:
    """Main security manager"""
    
    def __init__(self):
        self.security_events: Dict[str, SecurityEvent] = {}
        self.account_security: Dict[str, AccountSecurity] = {}
        self.rate_limiter = RateLimiter()
        self.event_counter = 0
    
    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        self.event_counter += 1
        return f"SEC_{datetime.now().strftime('%Y%m%d')}_{self.event_counter:06d}"
    
    def get_or_create_account_security(self, user_id: str) -> AccountSecurity:
        """Get or create account security object"""
        if user_id not in self.account_security:
            self.account_security[user_id] = AccountSecurity(user_id)
        return self.account_security[user_id]
    
    def log_security_event(self, user_id: str, event_type: SecurityEventType,
                          risk_level: RiskLevel, details: dict) -> SecurityEvent:
        """Log a security event"""
        event_id = self._generate_event_id()
        event = SecurityEvent(event_id, user_id, event_type, risk_level, details)
        self.security_events[event_id] = event
        return event
    
    def verify_withdrawal_request(self, user_id: str, amount: float,
                                 phone: str) -> Tuple[bool, str]:
        """
        Verify if withdrawal request is allowed
        Returns: (is_allowed, reason)
        """
        # Check if account is locked
        account_sec = self.get_or_create_account_security(user_id)
        if account_sec.check_if_locked():
            remaining = account_sec.get_lockout_time_remaining()
            minutes = int(remaining.total_seconds() / 60) if remaining else 0
            self.log_security_event(
                user_id,
                SecurityEventType.ACCOUNT_LOCKED,
                RiskLevel.CRITICAL,
                {'reason': 'Account locked due to failed attempts'}
            )
            return False, f"Account locked. Try again in {minutes} minutes."
        
        # Check rate limit (max 5 withdrawal requests per hour)
        rate_key = f"withdrawal_{user_id}"
        is_allowed, remaining = self.rate_limiter.check_rate_limit(rate_key, 5, 60)
        
        if not is_allowed:
            self.log_security_event(
                user_id,
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                RiskLevel.HIGH,
                {'action': 'withdrawal_request', 'limit': 5}
            )
            return False, "Too many withdrawal requests. Please wait before trying again."
        
        # Record the attempt
        self.rate_limiter.record_attempt(rate_key)
        
        self.log_security_event(
            user_id,
            SecurityEventType.WITHDRAWAL_REQUEST,
            RiskLevel.LOW,
            {'amount': amount, 'phone': phone}
        )
        
        return True, "Request allowed"
    
    def verify_pin_attempt(self, pin_code: str, phone: str, 
                          actual_pin: str, actual_phone: str,
                          user_id: str) -> Tuple[bool, str]:
        """
        Verify PIN attempt with security checks
        Returns: (is_valid, message)
        """
        account_sec = self.get_or_create_account_security(user_id)
        
        # Check if account is locked
        if account_sec.check_if_locked():
            remaining = account_sec.get_lockout_time_remaining()
            minutes = int(remaining.total_seconds() / 60) if remaining else 0
            return False, f"Account locked. Try again in {minutes} minutes."
        
        # Check rate limit for PIN verification (max 10 attempts per hour)
        rate_key = f"pin_verify_{user_id}"
        is_allowed, remaining = self.rate_limiter.check_rate_limit(rate_key, 10, 60)
        
        if not is_allowed:
            self.log_security_event(
                user_id,
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                RiskLevel.CRITICAL,
                {'action': 'pin_verification'}
            )
            return False, "Too many PIN attempts. Please wait before trying again."
        
        self.rate_limiter.record_attempt(rate_key)
        
        # Verify PIN and phone
        if pin_code == actual_pin and phone == actual_phone:
            # Success - reset failed attempts
            account_sec.reset_failed_attempts()
            self.log_security_event(
                user_id,
                SecurityEventType.PIN_VERIFICATION,
                RiskLevel.LOW,
                {'status': 'success'}
            )
            return True, "PIN verified successfully"
        else:
            # Failed attempt
            account_sec.record_failed_pin_attempt()
            
            self.log_security_event(
                user_id,
                SecurityEventType.FAILED_PIN_ATTEMPT,
                RiskLevel.HIGH,
                {'attempts': account_sec.failed_pin_attempts}
            )
            
            remaining_attempts = account_sec.max_failed_attempts - account_sec.failed_pin_attempts
            
            if account_sec.check_if_locked():
                return False, f"Too many failed attempts. Account locked for {account_sec.lockout_duration_minutes} minutes."
            
            return False, f"Invalid PIN or phone number. {remaining_attempts} attempts remaining."
    
    def analyze_fraud_risk(self, user_id: str, action: str, 
                          details: dict) -> Tuple[RiskLevel, List[str]]:
        """
        Analyze overall fraud risk for an action
        Returns: (risk_level, risk_factors)
        """
        risk_factors = []
        max_risk = RiskLevel.LOW
        
        # Check recent security events
        recent_events = self.get_user_security_events(user_id, hours=24)
        failed_attempts = len([e for e in recent_events 
                              if e['event_type'] == SecurityEventType.FAILED_PIN_ATTEMPT.value])
        
        if failed_attempts > 2:
            risk_factors.append(f"{failed_attempts} failed PIN attempts in last 24 hours")
            max_risk = RiskLevel.MEDIUM
        
        if failed_attempts > 5:
            max_risk = RiskLevel.HIGH
        
        # Check suspicious activity flags
        suspicious_events = [e for e in recent_events 
                           if e['event_type'] == SecurityEventType.SUSPICIOUS_ACTIVITY.value]
        if suspicious_events:
            risk_factors.append("Previous suspicious activity detected")
            max_risk = RiskLevel.HIGH
        
        return max_risk, risk_factors
    
    def get_user_security_events(self, user_id: str, hours: int = 24) -> List[dict]:
        """Get security events for a user within time period"""
        cutoff = datetime.now() - timedelta(hours=hours)
        events = []
        
        for event in self.security_events.values():
            if event.user_id == user_id and event.timestamp > cutoff:
                events.append(event.get_info())
        
        return sorted(events, key=lambda x: x['timestamp'], reverse=True)
    
    def unlock_user_account(self, user_id: str, admin_id: str) -> bool:
        """Manually unlock a user account (admin function)"""
        if user_id not in self.account_security:
            return False
        
        account_sec = self.account_security[user_id]
        account_sec.unlock_account()
        
        self.log_security_event(
            user_id,
            SecurityEventType.ACCOUNT_LOCKED,
            RiskLevel.LOW,
            {'action': 'manual_unlock', 'admin': admin_id}
        )
        
        return True
    
    def get_security_summary(self, user_id: str) -> dict:
        """Get security summary for a user"""
        account_sec = self.get_or_create_account_security(user_id)
        recent_events = self.get_user_security_events(user_id, hours=24)
        risk_level, risk_factors = self.analyze_fraud_risk(user_id, "summary", {})
        
        return {
            'user_id': user_id,
            'is_locked': account_sec.check_if_locked(),
            'failed_attempts': account_sec.failed_pin_attempts,
            'lockout_time_remaining': account_sec.get_lockout_time_remaining(),
            'recent_events_count': len(recent_events),
            'risk_level': risk_level.value,
            'risk_factors': risk_factors,
            'last_activity': recent_events[0]['timestamp'] if recent_events else None
        }

# Utility functions for password hashing (if needed for future authentication)
def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${pwd_hash}"

def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    try:
        salt, pwd_hash = hashed.split('$')
        return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
    except:
        return False

def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)