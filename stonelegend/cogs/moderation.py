from discord.ext.commands import Context, Cog, command, has_permissions
from discord import utils
from discord import Role, Embed
from datetime import datetime

from ..bot import StoneLegendBot


class Moderation(Cog):

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot

    @has_permissions(administrator=True)
    @command(name='announce', alias=('annoucement',))
    async def make_announcement(self, ctx: Context, *, announcement: str):

        async def report_role():
            await ctx.send("Announcement ping role not set, use `annoucerole` to set one")

        role_id = await self.bot.db.get_announcement_role(ctx.guild.id)
        if role_id is None:
            await report_role()
            return

        role = utils.get(ctx.guild.roles, id=role_id)
        if role is None:
            await report_role()
            return

        await ctx.send(role.mention, embed=Embed(
            title="Annoucement",
            description=announcement,
            timestamp=datetime.utcnow()
        ))

    @has_permissions(administrator=True)
    @command(name='announcerole')
    async def update_annoucement_role(self, ctx: Context, role: Role):
        """Updates annoucement role for the server"""

        await self.bot.db.update_annouce_role(ctx.guild.id, role.id)
        await ctx.send('Updated.')


def setup(bot: StoneLegendBot):
    bot.add_cog(Moderation(bot))