from discord.ext.commands import Bot

from .help import CustomHelpCommand
from .db import Database


class StoneLegendBot(Bot):
    
    def __init__(self, sql_config):
        super().__init__(command_prefix='/', help_command=CustomHelpCommand())
        self.sql_config = sql_config
        self.db = None

    # Overriden to make a db connection on start-up
    async def start(self, *args, **kwargs):
        self.db = Database(self.sql_config)
        await self.db.connect()        
        await super().start(*args, **kwargs)

    async def close(self, *args, **kwargs):
        await self.db.close()
        await super().close()