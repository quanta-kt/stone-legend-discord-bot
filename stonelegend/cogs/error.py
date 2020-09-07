from discord.ext.commands import(Cog, Context, CommandError,
    BadArgument, MissingRequiredArgument, CheckFailure, UserInputError, CommandNotFound)
from discord import Embed, Color


class ErrorHandler(Cog):
    """Handles global command errors"""

    @Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):

        def error_embed(title: str = "Error") -> Embed:
            return Embed(title=title, description=str(error),
                color=Color.red())

        if isinstance(error, BadArgument):
            await ctx.send(embed=error_embed("Bad argument"))
            return

        if isinstance(error, MissingRequiredArgument):
            await ctx.send(embed=error_embed("Missing argument"))
            return

        if isinstance(error, UserInputError):
            await ctx.send(embed=error_embed())
            return

        if isinstance(error, CheckFailure):
            await ctx.send(embed=error_embed())
            return

        if isinstance(error, CommandNotFound):
            return

        await ctx.send('An unexpected error occured. Please report this to the '
            + 'developer or open an issue on GitHub.')
        raise error


def setup(bot):
    bot.add_cog(ErrorHandler())