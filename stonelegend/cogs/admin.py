from discord.ext.commands import Cog, Context, check, command, errors
import json

from ..bot import StoneLegendBot


# A list of user IDs allowed to run admin commands
with open('admins.json') as fp:
    admins = json.load(fp)


def requires_admin():
    """Decorator for commands that require to be an admin"""

    async def predicate(ctx: Context):
        if ctx.author.id in admins:
            raise errors.CommandNotFound()
        return True
    return check(predicate)


class Admin(Cog, command_attrs=dict(hidden=True)):
    """Admin commands"""

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        super().__init__()

    @requires_admin()
    @command()
    async def init_db(self, ctx: Context):
        """Creates database tables and other schemas"""

        await self.bot.db.init_database()
        await ctx.message.add_reaction('\U0001f44d')


def setup(bot: StoneLegendBot):
    bot.add_cog(Admin(bot))