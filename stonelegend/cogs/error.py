from discord.ext.commands import(Cog, Context, CommandError,
    BadArgument, MissingRequiredArgument)
from discord import Embed, Color


class ErrorHandler(Cog):
    """Handles global command errors"""

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):

        def error_embed(title: str) -> Embed:
            return Embed(title=title, description=str(error),
                color=Color.red())

        if isinstance(error, BadArgument):
            await ctx.send(embed=error_embed("Bad argument"))
            return

        if isinstance(error, MissingRequiredArgument):
            await ctx.send(embed=error_embed("Missing argument"))
            return

        raise error


def setup(bot):
    bot.add_cog(ErrorHandler())