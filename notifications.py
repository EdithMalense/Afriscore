from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import re

class NotificationType(Enum):
    PIN_GENERATED = "pin_generated"
    PIN_REDEEMED = "pin_redeemed"
    PIN_EXPIRED = "pin_expired"
    PIN_CANCELLED = "pin_cancelled"
    CONTRIBUTION_ADDED = "contribution_added"
    STOKVEL_INVITATION = "stokvel_invitation"
    PAYOUT_TURN = "payout_turn"
    GOAL_REACHED = "goal_reached"

class NotificationChannel(Enum):
    SMS = "sms"
    EMAIL = "email"
    IN_APP = "in_app"

class Notification:
    """Represents a single notification"""
    
    def __init__(self, notification_id: str, user_id: str, 
                 notification_type: NotificationType, message: str,
                 channel: NotificationChannel, recipient: str):
        self.notification_id = notification_id
        self.user_id = user_id
        self.notification_type = notification_type
        self.message = message
        self.channel = channel
        self.recipient = recipient  # phone number or email
        self.created_at = datetime.now()
        self.sent = False
        self.sent_at = None
        self.read = False
        self.read_at = None
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.sent = True
        self.sent_at = datetime.now()
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.read = True
        self.read_at = datetime.now()
    
    def get_info(self) -> dict:
        """Get notification information"""
        return {
            'notification_id': self.notification_id,
            'user_id': self.user_id,
            'type': self.notification_type.value,
            'message': self.message,
            'channel': self.channel.value,
            'recipient': self.recipient,
            'created_at': self.created_at,
            'sent': self.sent,
            'sent_at': self.sent_at,
            'read': self.read,
            'read_at': self.read_at
        }

class SMSProvider:
    """Mock SMS provider - Replace with actual provider (Twilio, Africa's Talking, etc.)"""
    
    @staticmethod
    def validate_phone_number(phone: str) -> bool:
        """Validate South African phone number"""
        # Accept formats: +27XXXXXXXXX, 27XXXXXXXXX, 0XXXXXXXXX
        pattern = r'^(\+27|27|0)[6-8][0-9]{8}$'
        return bool(re.match(pattern, phone))
    
    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Standardize phone number to +27XXXXXXXXX format"""
        phone = phone.strip().replace(' ', '').replace('-', '')
        
        if phone.startswith('0'):
            phone = '+27' + phone[1:]
        elif phone.startswith('27'):
            phone = '+' + phone
        elif not phone.startswith('+'):
            phone = '+27' + phone
        
        return phone
    
    @staticmethod
    def send_sms(phone: str, message: str) -> bool:
        """
        Send SMS via provider
        In production, integrate with:
        - Twilio: https://www.twilio.com/
        - Africa's Talking: https://africastalking.com/
        - Clickatell: https://www.clickatell.com/
        """
        try:
            # Validate and format phone number
            if not SMSProvider.validate_phone_number(phone):
                raise ValueError(f"Invalid phone number format: {phone}")
            
            formatted_phone = SMSProvider.format_phone_number(phone)
            
            # Mock sending - In production, replace with actual API call
            print(f"[SMS MOCK] Sending to {formatted_phone}")
            print(f"[SMS MOCK] Message: {message}")
            
            # Example Twilio integration (commented out):
            # from twilio.rest import Client
            # client = Client(account_sid, auth_token)
            # message = client.messages.create(
            #     body=message,
            #     from_='+27XXXXXXXXX',  # Your Twilio number
            #     to=formatted_phone
            # )
            
            return True
        except Exception as e:
            print(f"[SMS ERROR] Failed to send: {str(e)}")
            return False

class NotificationManager:
    """Manages all notifications and messaging"""
    
    def __init__(self):
        self.notifications: Dict[str, Notification] = {}
        self.notification_counter = 0
    
    def _generate_notification_id(self) -> str:
        """Generate unique notification ID"""
        self.notification_counter += 1
        return f"NOTIF_{datetime.now().strftime('%Y%m%d')}_{self.notification_counter:06d}"
    
    def send_pin_notification(self, user_id: str, phone: str, pin_code: str, 
                            amount: float, expires_at: datetime) -> Notification:
        """Send PIN generation notification"""
        message = (
            f"Your withdrawal PIN: {pin_code}\n"
            f"Amount: R{amount:,.2f}\n"
            f"Expires: {expires_at.strftime('%Y-%m-%d %H:%M')}\n"
            f"Show this PIN at any partnered store to collect your cash.\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.PIN_GENERATED,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        # Send SMS
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def send_pin_redeemed_notification(self, user_id: str, phone: str, 
                                      amount: float) -> Notification:
        """Notify user when their PIN is redeemed"""
        message = (
            f"Your withdrawal of R{amount:,.2f} has been processed.\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"If you didn't authorize this, contact support immediately.\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.PIN_REDEEMED,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def send_stokvel_invitation_notification(self, user_id: str, phone: str, 
                                           stokvel_name: str, inviter_name: str, recipient_name: str, monthly_amount: float,
                                           app_link: str = "https://bankingforall.com/app") -> Notification:
        """Notify user of stokvel invitation"""
        message = (
            f"Hey, {recipient_name}, {inviter_name} has invited you to join '{stokvel_name}' stokvel.\n"
            f"Monthly fee: R{monthly_amount:,.2f}\n"
            f"Click the link to go on the app: {app_link}\n"
            f"Log in to Banking for All to accept or decline.\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.STOKVEL_INVITATION,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def send_payout_turn_notification(self, user_id: str, phone: str, 
                                     stokvel_name: str, amount: float) -> Notification:
        """Notify user it's their turn for stokvel payout"""
        message = (
            f"It's your turn to receive the stokvel payout!\n"
            f"Stokvel: {stokvel_name}\n"
            f"Amount: R{amount:,.2f}\n"
            f"Log in to request your withdrawal PIN.\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.PAYOUT_TURN,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def send_contribution_notification(self, user_id: str, phone: str, 
                                      amount: float, account_type: str) -> Notification:
        """Notify user of successful contribution"""
        message = (
            f"Contribution received: R{amount:,.2f}\n"
            f"Account: {account_type}\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.CONTRIBUTION_ADDED,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def send_goal_reached_notification(self, user_id: str, phone: str, 
                                      goal_amount: float) -> Notification:
        """Notify user when savings goal is reached"""
        message = (
            f"Congratulations! You've reached your savings goal of R{goal_amount:,.2f}!\n"
            f"Keep up the great work!\n"
            f"- Banking for All"
        )
        
        notification = Notification(
            notification_id=self._generate_notification_id(),
            user_id=user_id,
            notification_type=NotificationType.GOAL_REACHED,
            message=message,
            channel=NotificationChannel.SMS,
            recipient=phone
        )
        
        if SMSProvider.send_sms(phone, message):
            notification.mark_as_sent()
        
        self.notifications[notification.notification_id] = notification
        return notification
    
    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[dict]:
        """Get notifications for a user"""
        user_notifications = []
        for notification in self.notifications.values():
            if notification.user_id == user_id:
                if unread_only and notification.read:
                    continue
                user_notifications.append(notification.get_info())
        
        return sorted(user_notifications, key=lambda x: x['created_at'], reverse=True)
    
    def mark_notification_read(self, notification_id: str, user_id: str) -> bool:
        """Mark a notification as read"""
        if notification_id not in self.notifications:
            raise ValueError("Notification not found")
        
        notification = self.notifications[notification_id]
        
        if notification.user_id != user_id:
            raise ValueError("Cannot mark another user's notification as read")
        
        notification.mark_as_read()
        return True
    
    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for user"""
        return len([n for n in self.notifications.values() 
                   if n.user_id == user_id and not n.read])
    
    def send_bulk_notification(self, user_ids: List[str], phone_numbers: List[str],
                              notification_type: NotificationType, message: str) -> List[Notification]:
        """Send notification to multiple users"""
        notifications = []
        
        for user_id, phone in zip(user_ids, phone_numbers):
            notification = Notification(
                notification_id=self._generate_notification_id(),
                user_id=user_id,
                notification_type=notification_type,
                message=message,
                channel=NotificationChannel.SMS,
                recipient=phone
            )
            
            if SMSProvider.send_sms(phone, message):
                notification.mark_as_sent()
            
            self.notifications[notification.notification_id] = notification
            notifications.append(notification)
        
        return notifications