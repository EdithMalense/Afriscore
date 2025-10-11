from datetime import datetime
from typing import Dict
from enum import Enum

class AccountType(Enum):
    CURRENT = "current"
    SAVINGS = "savings"
    STOKVEL = "stokvel"

class Transaction:
    """Represents a transaction"""
    
    def __init__(self, transaction_id: str, user_id: str, amount: float,
                 transaction_type: str, account_type: AccountType, timestamp: datetime = None):
        self.transaction_id = transaction_id
        self.user_id = user_id
        self.amount = amount
        self.transaction_type = transaction_type
        self.account_type = account_type
        self.timestamp = timestamp or datetime.now()
    
    def get_info(self) -> dict:
        return {
            'transaction_id': self.transaction_id,
            'user_id': self.user_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'account_type': self.account_type.value,
            'timestamp': self.timestamp
        }

class UserAccount:
    """Manages a user's account with current balance and transaction history"""
    
    def __init__(self, user_id: str, name: str):
        self.user_id = user_id
        self.name = name
        self.current_balance = 0.0
        self.transactions: list = []
        self.transaction_counter = 0
        self.created_at = datetime.now()
    
    def _generate_transaction_id(self) -> str:
        self.transaction_counter += 1
        return f"TXN_{self.user_id}_{datetime.now().strftime('%Y%m%d')}_{self.transaction_counter:06d}"
    
    def deposit(self, amount: float) -> Transaction:
        if amount <= 0:
            raise ValueError("Deposit amount must be positive.")
        self.current_balance += amount
        transaction = Transaction(
            self._generate_transaction_id(),
            self.user_id,
            amount,
            "deposit",
            AccountType.CURRENT
        )
        self.transactions.append(transaction)
        return transaction
    
    def transfer_to_savings(self, amount: float) -> Transaction:
        if amount <= 0:
            raise ValueError("Transfer amount must be positive.")
        if amount > self.current_balance:
            raise ValueError(f"Insufficient funds. Available: R{self.current_balance:.2f}")
        self.current_balance -= amount
        transaction = Transaction(
            self._generate_transaction_id(),
            self.user_id,
            amount,
            "transfer_to_savings",
            AccountType.SAVINGS
        )
        self.transactions.append(transaction)
        return transaction
    
    def transfer_to_stokvel(self, amount: float, stokvel_id: str) -> Transaction:
        if amount < 10:
            raise ValueError("Minimum stokvel contribution is R10.")
        if amount > self.current_balance:
            raise ValueError(f"Insufficient funds. Available: R{self.current_balance:.2f}")
        self.current_balance -= amount
        transaction = Transaction(
            self._generate_transaction_id(),
            self.user_id,
            amount,
            f"transfer_to_stokvel_{stokvel_id}",
            AccountType.STOKVEL
        )
        self.transactions.append(transaction)
        return transaction
    
    def process_withdrawal(self, amount: float) -> Transaction:
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive.")
        self.current_balance -= amount
        transaction = Transaction(
            self._generate_transaction_id(),
            self.user_id,
            amount,
            "withdrawal",
            AccountType.CURRENT
        )
        self.transactions.append(transaction)
        return transaction
    
    def get_balance(self) -> float:
        return round(self.current_balance, 2)
    
    def get_transaction_history(self, limit: int = 50) -> list:
        return [t.get_info() for t in sorted(
            self.transactions, 
            key=lambda x: x.timestamp, 
            reverse=True
        )[:limit]]
    
    def get_account_summary(self) -> dict:
        return {
            'user_id': self.user_id,
            'name': self.name,
            'current_balance': self.get_balance(),
            'total_transactions': len(self.transactions),
            'created_at': self.created_at
        }

class AccountManager:
    """Manages all user accounts"""
    
    def __init__(self):
        self.accounts: Dict[str, UserAccount] = {}
    
    def create_account(self, user_id: str, name: str) -> UserAccount:
        if user_id in self.accounts:
            raise ValueError("Account already exists for this user.")
        account = UserAccount(user_id, name)
        self.accounts[user_id] = account
        return account
    
    def get_account(self, user_id: str) -> UserAccount:
        if user_id not in self.accounts:
            raise ValueError("Account not found.")
        return self.accounts[user_id]
    
    def deposit_to_account(self, user_id: str, amount: float) -> Transaction:
        account = self.get_account(user_id)
        return account.deposit(amount)