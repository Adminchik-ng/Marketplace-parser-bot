from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    
@dataclass
class UserRow:
    id: int
    telegram_id: int
    chat_id: int
    username: Optional[str]
    language: Optional[str]
    role: UserRole
    is_alive: bool
    banned: bool
    created_at: datetime
    updated_at: datetime