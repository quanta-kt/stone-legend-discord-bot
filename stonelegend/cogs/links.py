from discord.ext.commands import Bot, Cog, command, Context
from discord import Embed, Color


WEBSITE_URL = "https://stonelegend.net/"
DISCORD_INVITE_URL = "https://stonelegend.net/discord"
VOTE_URL = "https://www.example.com/"

class Links(Cog):
    """Some links related to us"""

    @command(name='web', aliases=('website',))
    async def website_link(self, ctx: Context):
        """Sends a link to our website"""

        await ctx.send(embed=Embed(
            title="StoneLegend Official Website",
            description=f"Click [here]({WEBSITE_URL}) to visit our website.",
            color=Color.green()
        ))

    @command(name='discord', aliases=('invite', 'server'))
    async def discord_invite(self, ctx: Context):
        """Sends an invite link to our discord server"""

        await ctx.send(embed=Embed(
            title="StoneLegend Official Discord Server",
            description=f"Click [here]({DISCORD_INVITE_URL}) to join our server.",
            color=Color.green()
        ))

    @command(name='vote', aliases=('upvote',))
    async def vote_link(self, ctx: Context):
        """Sends a link for voting"""

        await ctx.send(embed=Embed(
            title="Vote us",
            description=f"Click [here]({VOTE_URL}) to submit your vote",
            color=Color.green()
        ))


def setup(bot: Bot):
    bot.add_cog(Links())
