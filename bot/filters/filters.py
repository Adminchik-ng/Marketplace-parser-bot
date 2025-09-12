from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message
from enums.roles import UserRole


class UserRoleFilter(BaseFilter):
    def __init__(self, *roles: str | UserRole):
        if not roles:
            raise ValueError("At least one role must be provided to UserRoleFilter.")

        self.roles = frozenset(
            UserRole(role) if isinstance(role, str) else role
            for role in roles
            if isinstance(role, (str, UserRole))
        )

        if not self.roles:
            raise ValueError("No valid roles provided to `UserRoleFilter`.")

    async def __call__(
        self,
        event: Message | CallbackQuery,
        user_row: object | None = None  # сюда будет передан user_row из middleware
    ) -> bool:
        if user_row is None:
            # Если middleware не положил user_row в data — фильтр не пропустит
            return False

        user_role = getattr(user_row, 'role', None)
        if user_role is None:
            return False

        return user_role in self.roles
