from aiogram.types import BotCommand
from bot.enums.roles import UserRole


def get_main_menu_commands(locales: dict[str, str], role: UserRole):
    if role == UserRole.USER:
        return [
            BotCommand(
                command='/start',
                description=locales.get('/start_description')
            ),
            BotCommand(
                command='/add',
                description=locales.get('/add_description')
            ),
            BotCommand(
                command='/remove',
                description=locales.get('/remove_description')
            ),
            BotCommand(
                command='/list',
                description=locales.get('/list_description')
            ),
            BotCommand(
                command='/summary',
                description=locales.get('/summary_description')
            ),
            BotCommand(
                command='/help',
                description=locales.get('/help_description')
            ),
        ]
    elif role == UserRole.ADMIN:
        return [
            BotCommand(
                command='/start',
                description=locales.get('/start_description')
            ),
            BotCommand(
                command='/add',
                description=locales.get('/add_description')
            ),
            BotCommand(
                command='/remove',
                description=locales.get('/remove_description')
            ),
            BotCommand(
                command='/list',
                description=locales.get('/list_description')
            ),
            BotCommand(
                command='/summary',
                description=locales.get('/summary_description')
            ),
            BotCommand(
                command='/help',
                description=locales.get('/help_description')
            ),
            BotCommand(
                command='/ban',
                description=locales.get('/ban_description')
            ),
            BotCommand(
                command='/unban',
                description=locales.get('/unban_description')
            ),
            BotCommand(
                command='/statistics',
                description=locales.get('/statistics_description')
            ),
        ]