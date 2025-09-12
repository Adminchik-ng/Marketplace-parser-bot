import utility_functions
from database import db
import pytest


@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
]) 
async def test_add_user_activity(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await db.users.add_user(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)   
        # Вызываем функцию добавления активности — должна создать новую запись с actions=1
        await db.activity.add_user_activity(conn=connection, user_id=telegram_id)

        row = await utility_functions.get_user_activity_actions_test(conn=connection, user_id=telegram_id)
        assert row is not None
        assert row == 1

        # Вызовем функцию снова — должна обновиться существующая запись, actions += 1
        await db.activity.add_user_activity(conn=connection, user_id=telegram_id)

        row_updated = await utility_functions.get_user_activity_actions_test(conn=connection, user_id=telegram_id)
        assert row_updated is not None
        assert row_updated == 2
        
        
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned, actions",[
    (1, 11, "test_user", 'ru', "admin", True, False, 5),
]) 
async def test_get_statistics(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned, actions):
    async with db_pool.acquire() as connection:
        await db.users.add_user(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)   

        await utility_functions.insert_activity_test(conn=connection, user_id=telegram_id, actions=actions)

        statistics = await db.activity.get_statistics(conn=connection)

        assert statistics is not None
        assert statistics == [(telegram_id, actions)]
        
        
@pytest.mark.parametrize("users, expected_result",[
        (
        [
            (1, 11, "user1", "ru", "admin", True, False, 5),
            (2, 12, "user2", "ru", "admin", True, True, 10),
            (3, 13, "user3", "en", "user", True, False, 122),
            (4, 14, "user4", "en", "user", False, False, 55),
            (5, 15, "user5", "en", "user", True, True, 400),
        ],
        5,
        )
    ]
)      
async def test_get_active_users_today(db_pool, users, expected_result):
    async with db_pool.acquire() as connection:
        for user in users:
            await utility_functions.add_user_test(
                                conn=connection,
                                telegram_id=user[0],
                                chat_id=user[1],
                                username=user[2],
                                language=user[3],
                                role=user[4],
                                is_alive=user[5],
                                banned=user[6])
            await utility_functions.insert_activity_test(conn=connection, user_id=user[0], actions=user[7])
        
        actions_count = await db.activity.get_active_users_today(conn=connection)
        
        assert actions_count == expected_result