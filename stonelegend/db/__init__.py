import aiomysql
from functools import wraps
from typing import Dict, Iterable


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