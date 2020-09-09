import aiomysql
from functools import wraps
from typing import Dict, Iterable, Optional


SQL_CREATE_TABLE_POLLS = """
CREATE TABLE IF NOT EXISTS polls(
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    finish_time BIGINT NOT NULL,
    question VARCHAR(150) NOT NULL,
    emoji1 VARCHAR(35) NOT NULL,
    emoji2 VARCHAR(35) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;
"""

SQL_INSERT_POLL = """
INSERT INTO polls(channel_id, message_id, finish_time, question, emoji1, emoji2)
VALUES(%s, %s, %s, %s, %s, %s)
"""

SQL_SELECT_ALL_POLLS = """
SELECT id, channel_id, message_id, finish_time, question, emoji1, emoji2
FROM polls
"""

SQL_DELETE_POLL = """
DELETE FROM polls
WHERE id = %s
"""

SQL_CHECK_POLL = """
SELECT EXISTS (SELECT * FROM polls WHERE channel_id = %s AND message_id = %s) AS result
"""

SQL_CREATE_TABLE_GIVEAWAYS = """
CREATE TABLE IF NOT EXISTS giveaways(
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    prize VARCHAR(250) NOT NULL,
    finish_time BIGINT NOT NULL,
    author_id BIGINT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci;
"""

SQL_INSERT_GIVEAWAY = """
INSERT INTO giveaways(channel_id, message_id, prize, finish_time, author_id)
VALUES(%s, %s, %s, %s, %s)
"""

SQL_DELETE_GIVEAWAY = """
DELETE FROM giveaways
WHERE id = %s
"""

SQL_SELECT_ALL_GIVEAWAYS = """
SELECT id, channel_id, message_id, finish_time, prize, author_id
FROM giveaways
"""

SQL_CREATE_TABLE_ANNOUNCE_ROLES = """
CREATE TABLE IF NOT EXISTS annouceroles(
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT NOT NULL
)
"""

SQL_SELECT_ANNOUNCE_ROLE = """
SELECT role_id FROM annouceroles
WHERE guild_id = %s
"""

SQL_INSERT_ANNOUCE_ROLE = """
INSERT INTO annouceroles(guild_id, role_id)
VALUES(%(guild_id)s, %(role_id)s)
ON DUPLICATE KEY UPDATE role_id = %(role_id)s
"""

SQL_CREATE_TABLE_REACT_ROLES = """
CREATE TABLE IF NOT EXISTS reactroles(
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    emoji VARCHAR(40) COLLATE utf8mb4_unicode_ci NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE utf8mb4_general_ci
"""

SQL_INSERT_REACT_ROLE = """
INSERT INTO reactroles(guild_id, channel_id, message_id, role_id, emoji)
VALUES(%s, %s, %s, %s, %s)
"""

SQL_SELECT_ROLE_ID_FOR_REACTION = """
SELECT role_id FROM reactroles
WHERE guild_id = %s AND channel_id = %s AND message_id = %s AND emoji = %s COLLATE utf8mb4_bin
"""

SQL_CREATE_TABLE_WELCOME_CHANNELS = """
CREATE TABLE IF NOT EXISTS welcomechannels(
    guild_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    channel_id BIGINT NOT NULL
)
"""

SQL_INSERT_WELCOME_CHANNEL = """
INSERT INTO welcomechannels(guild_id, channel_id)
VALUES(%(guild_id)s, %(channel_id)s)
ON DUPLICATE KEY UPDATE channel_id = %(channel_id)s
"""

SQL_SELECT_WELCOME_CHANNEL = """
SELECT channel_id FROM welcomechannels WHERE guild_id = %s
"""

SQL_CREATE_TABLE_VERIFICATION_ROLES = """
CREATE TABLE IF NOT EXISTS verificationroles(
    guild_id BIGINT PRIMARY KEY,
    role_id BIGINT NOT NULL
)
"""

SQL_UPDATE_VERIFICATION_ROLE = """
INSERT INTO verificationroles(guild_id, role_id)
VALUES(%(guild_id)s, %(role_id)s)
ON DUPLICATE KEY UPDATE role_id = %(role_id)s
"""

SQL_SELECT_VERIFICATION_ROLE = """
SELECT role_id FROM verificationroles
WHERE guild_id = %s
LIMIT 1
"""

def requires_connection(decorated):
    """A decorator for Database methods which should not be called before calling Database.connect"""

    @wraps(decorated)
    def f(self, *args, **kwargs):
        if self._pool is None:
            raise ValueError("Tried to access database before connecting.\n"
                + "Please call Database.connect() before performing any DB operations"
            )

        return decorated(self, *args, **kwargs)

    return f


class Database:

    def __init__(self, sql_config: Dict[str, str]):
        self._pool = None
        self._config = sql_config

    def __del__(self):
        """Closes the connection
        Note: Do not rely on this and call Database.close instead"""

        if self._pool is not None:
            self._pool.close()

    async def connect(self) -> None:
        """Aquire a connection pool to the database.
        This should be called before any database operation is performed."""

        self._pool = await aiomysql.create_pool(
            cursorclass=aiomysql.cursors.DictCursor,
            **self._config
        )

    @requires_connection
    async def init_database(self):
        """Initialize database- create required tables and schemas"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_CREATE_TABLE_POLLS)
                await cur.execute(SQL_CREATE_TABLE_GIVEAWAYS)
                await cur.execute(SQL_CREATE_TABLE_ANNOUNCE_ROLES)
                await cur.execute(SQL_CREATE_TABLE_REACT_ROLES)
                await cur.execute(SQL_CREATE_TABLE_WELCOME_CHANNELS)
                await cur.execute(SQL_CREATE_TABLE_VERIFICATION_ROLES)
                await conn.commit()

    async def close(self) -> None:
        """Closes connection pool to the database and waits for it to close completely"""

        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()

    @requires_connection
    async def insert_poll(self, channel_id: int, message_id: int,
        finish_time: int, question: str,
        emoji1: str, emoji2: str) -> int:
        """Insert a poll into DB and return the row id inserted to"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_INSERT_POLL, (
                    channel_id,
                    message_id,
                    finish_time,
                    question,
                    emoji1,
                    emoji2
                ))

            await conn.commit()

        return cur.lastrowid

    @requires_connection
    async def is_poll(self, channel_id, message_id):
        """Returns True if the message of given ID in the given channel is a poll,
        False otherwise"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_CHECK_POLL, (channel_id, message_id))
                return bool((await cur.fetchone())['result'])


    @requires_connection
    async def get_all_polls(self):
        """Fetches and returns all active polls from db"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_ALL_POLLS)
                return await cur.fetchall()

    @requires_connection
    async def delete_poll(self, poll_id):
        """Deletes the poll with given id"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_DELETE_POLL, (poll_id,))
                await conn.commit()

    @requires_connection
    async def insert_giveaway(self, channel_id, message_id, prize, finish_time, author_id):
        """Inserts giveaway to the db"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_INSERT_GIVEAWAY, (channel_id, message_id, prize, finish_time, author_id))
                await conn.commit()

        return cur.lastrowid

    @requires_connection
    async def get_all_giveaways(self):
        """Fetches and returns all active giveaways from db"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_ALL_GIVEAWAYS)
                return await cur.fetchall()

    @requires_connection
    async def delete_giveaway(self, giveaway_id):
        """Deletes the giveaway belonging to passed giveaway ID"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_DELETE_GIVEAWAY, (giveaway_id,))
                await conn.commit()

    @requires_connection
    async def update_annouce_role(self, guild_id, role_id):
        """Inserts or updates annoucement role id for the guild"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_INSERT_ANNOUCE_ROLE,
                    dict(guild_id=guild_id, role_id=role_id))
                await conn.commit()

    @requires_connection
    async def get_announcement_role(self, guild_id):
        """Fetches and returns the annoucement role ID for given guild ID"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_ANNOUNCE_ROLE, (guild_id,))
                return None if cur.rowcount < 1 else (await cur.fetchone())['role_id']

    @requires_connection
    async def insert_reaction_role(self, guild_id: int, channel_id: int,
        message_id: int, role_id: int, emoji_str: str):
        """Inserts a reaction role into db"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:        
                await cur.execute(SQL_INSERT_REACT_ROLE,
                    (guild_id, channel_id, message_id, role_id, emoji_str))
                await conn.commit()

    @requires_connection
    async def get_role_for_reaction(self, guild_id, channel_id, message_id, emoji_str) -> Optional[int]:
        """Fetches and returns role id for given reaction parameters
        Returns None if the reaction has no role registered"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_ROLE_ID_FOR_REACTION,
                    (guild_id, channel_id, message_id, emoji_str))
                return (await cur.fetchone())['role_id'] if cur.rowcount > 0 else None

    @requires_connection
    async def update_welcome_channel(self, guild_id: int, channel_id: int):
        """Inserts a welcome channel into db"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:        
                await cur.execute(SQL_INSERT_WELCOME_CHANNEL,
                    dict(guild_id=guild_id, channel_id=channel_id))
                await conn.commit()

    @requires_connection
    async def get_welcome_channel(self, guild_id):
        """Fetches and returns the welcome channel ID for given guild ID.
        Returns None if not set"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_WELCOME_CHANNEL, (guild_id,))
                return None if cur.rowcount < 1 else (await cur.fetchone())['channel_id']

    @requires_connection
    async def update_verification_role(self, guild_id, role_id):
        """Updates verification role id for given guild"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_UPDATE_VERIFICATION_ROLE, dict(guild_id=guild_id, role_id=role_id))
                await conn.commit()
                

    async def get_verification_role(self, guild_id):
        """Fetches and returns the role id set as verification role.
        Returns None if not set"""

        async with self._pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(SQL_SELECT_VERIFICATION_ROLE, (guild_id,))
                return (await cur.fetchone())['role_id'] if cur.rowcount > 0 else None