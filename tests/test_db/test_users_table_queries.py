import pytest
from datetime import datetime, timedelta
from database import db
import utility_functions


@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_add_user(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await db.users.add_user(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        res = await utility_functions.get_user_test(conn=connection, telegram_id=telegram_id)
        assert telegram_id == res.telegram_id
        assert chat_id == res.chat_id
        assert username == res.username
        assert language == res.language
        assert role == res.role
        assert is_alive == res.is_alive
        assert banned == res.banned

    

@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        res = await db.users.get_user(conn=connection, telegram_id=telegram_id)
        assert telegram_id == res.telegram_id
        assert chat_id == res.chat_id
        assert username == res.username
        assert language == res.language
        assert role == res.role
        assert is_alive == res.is_alive
        assert banned == res.banned

    

@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned, checked_is_alive",[
    (1, 11, "test_user", 'ru', "admin", True, False, False),
    (3, 333, "test_user_2", 'en', "user", False, True, True),
])      
async def test_change_user_alive_status(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned, checked_is_alive):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        await db.users.change_user_alive_status(conn=connection, is_alive=checked_is_alive, telegram_id=telegram_id)
        
        res = await utility_functions.get_user_test(conn=connection, telegram_id=telegram_id)
        
        assert checked_is_alive == res.is_alive 
        

@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned, checked_banned",[
    (1, 11, "test_user", 'ru', "admin", True, False, False),
    (3, 333, "test_user_2", 'en', "user", False, True, True),
])      
async def test_change_user_banned_status_by_id(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned, checked_banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        await db.users.change_user_banned_status_by_id(conn=connection, banned=checked_banned, user_id=telegram_id)
        
        res = await utility_functions.get_user_test(conn=connection, telegram_id=telegram_id)
        
        assert checked_banned == res.banned   
        
        
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned, checked_banned",[
    (1, 11, "test_user", 'ru', "admin", True, False, False),
    (3, 333, "test_user_2", 'en', "user", False, True, True),
])      
async def test_change_user_banned_status_by_username(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned, checked_banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        await db.users.change_user_banned_status_by_username(conn=connection, banned=checked_banned, username=username)
        
        res = await utility_functions.get_user_test(conn=connection, telegram_id=telegram_id)
        
        assert checked_banned == res.banned 
        
        
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user_alive_status(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        checked_is_alive = await db.users.get_user_alive_status(conn=connection, user_id=telegram_id)
        assert is_alive == checked_is_alive
        
        
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user_banned_status_by_id(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        checked_banned = await db.users.get_user_banned_status_by_id(conn=connection, user_id=telegram_id)
        assert banned == checked_banned
        
        
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user_banned_status_by_username(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        checked_banned = await db.users.get_user_banned_status_by_username(conn=connection, username=username)
        assert banned == checked_banned
    
    
    
@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user_role(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        checked_role = await db.users.get_user_role(conn=connection, user_id=telegram_id)
        assert role == checked_role
        

@pytest.mark.parametrize("telegram_id, chat_id, username, language, role, is_alive, banned",[
    (1, 11, "test_user", 'ru', "admin", True, False),
    (3, 333, "test_user_2", 'en', "user", False, True),
])      
async def test_get_user_chat_id(db_pool, telegram_id, chat_id, username, language, role, is_alive, banned):
    async with db_pool.acquire() as connection:
        await utility_functions.add_user_test(conn=connection,
                                telegram_id=telegram_id,
                                chat_id=chat_id,
                                username=username,
                                language=language,
                                role=role,
                                is_alive=is_alive,
                                banned=banned)
        checked_chat_id = await db.users.get_user_chat_id(conn=connection, user_id=telegram_id)
        assert chat_id == checked_chat_id
        
        
@pytest.mark.parametrize("users, expected_total", [
    ([
        (1, 11, "test_user", 'ru', "admin", True, False),
    ], 1),
    ([
        (1, 11, "test_user", 'ru', "admin", True, False),
        (3, 333, "test_user_2", 'en', "user", False, True),
    ], 2),
])
async def test_get_total_users_with_multiple(db_pool, users, expected_total):
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
                banned=user[6],
            )
        total_users = await db.users.get_total_users(conn=connection)
        assert total_users == expected_total
    
    
@pytest.mark.parametrize("users, expected_distribution", [
    (
        [
            (1, 11, "user1", "ru", "admin", True, False),
            (2, 12, "user2", "ru", "admin", True, True),
            (3, 13, "user3", "en", "user", True, False),
            (4, 14, "user4", "en", "user", False, False),
            (5, 15, "user5", "en", "user", True, True),
        ],
        [
            ("admin", False, 1),
            ("admin", True, 1),
            ("user", False, 2),
            ("user", True, 1),
        ]
    ),
    (
        [
            (10, 110, "another_user1", "en", "moderator", True, False),
            (11, 111, "another_user2", "en", "moderator", False, False),
        ],
        [
            ("moderator", False, 2),
        ]
    ),
])
async def test_get_users_role_distribution_parametrized(db_pool, users, expected_distribution):
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
                banned=user[6]
            )
        result = await db.users.get_users_role_distribution(conn=connection)
        assert sorted(result) == sorted(expected_distribution)
        

@pytest.mark.parametrize("users, expected_percent", [
    (
        [
            (1, 11, "user1", "ru", "admin", True, False, datetime.now()),
            (2, 12, "user2", "ru", "user", True, False, datetime.now() - timedelta(days=3)),
            (3, 13, "user3", "en", "user", True, False, datetime.now() - timedelta(days=10)),
        ],
        2/3 * 100.0
    ),
    (
        [
            (4, 14, "user4", "en", "user", True, False, datetime.now() - timedelta(days=20)),
            (5, 15, "user5", "en", "user", False, False, datetime.now() - timedelta(days=30)),
        ],
        0.0
    ),
    (
        [
            (6, 16, "user6", "ru", "admin", True, False, datetime.now()),
            (7, 17, "user7", "en", "user", True, False, datetime.now() - timedelta(days=1)),
        ],
        100.0
    ),
])
async def test_get_percent_new_users_week(db_pool, users, expected_percent):
    async with db_pool.acquire() as connection:
        for user in users:
            telegram_id, chat_id, username, language, role, is_alive, banned, created_at = user
            await utility_functions.add_user_test(
                conn=connection,
                telegram_id=telegram_id,
                chat_id=chat_id,
                username=username,
                language=language,
                role=role,
                is_alive=is_alive,
                banned=banned,
            )
            await utility_functions.update_user_created_at_test(connection, telegram_id, created_at)

        percent_new_users = await db.users.get_percent_new_users_week(conn=connection)
        assert float(percent_new_users) == pytest.approx(expected_percent, rel=1e-2)

