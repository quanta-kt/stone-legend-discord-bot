from discord.ext.commands import(Context, Cog, command, has_permissions,
    BadArgument, RoleConverter, EmojiConverter, MissingRequiredArgument, CommandError,
    Converter, bot_has_permissions, group)
from discord import Role, Embed, Color, TextChannel, Reaction, User, Member, Emoji
from discord import utils
from datetime import datetime
from typing import Tuple, Union

from ..bot import StoneLegendBot
from ..converters import SelfRolesListConverter


class Moderation(Cog):
    """Server moderation and management commands"""

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

        await ctx.message.delete()
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

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):

        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        
        # Skip bots
        if member.bot:
            return

        role_id = await self.bot.db.get_role_for_reaction(payload.guild_id,
            payload.channel_id, payload.message_id, str(payload.emoji))
        if role_id is None:
            return # Not a reaction role

        role = guild.get_role(role_id)
        if role is None:
            guild.get_channel(payload.channel_id).send('Could not find that role!')
        else:
            await member.add_roles(role)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        
        # Skip bots
        if member.bot:
            return

        role_id = await self.bot.db.get_role_for_reaction(payload.guild_id,
            payload.channel_id, payload.message_id, str(payload.emoji))
        if role_id is None:
            return # Not a reaction role

        role = guild.get_role(role_id)
        if role is not None:
            await member.remove_roles(role)

    @has_permissions(administrator=True)
    @command(name='selfroles', aliases=('rr', 'reactionroles'))
    async def create_self_roles(self, ctx: Context, channel: TextChannel, *,
        entries: SelfRolesListConverter):
        """Creates a self roles message
        entries must be triplets of role, emoji, description separated by space
        Example: selfroles #RolesChannel @CoolRole \N{smiling face with sunglasses} A cool role
        @Evil \N{smiling face with horns} Evil role"""

        # Build and send message
        roles_list = "\n\n".join(f"{reactable} {role.mention}\n{desc}" \
            for role, reactable, desc in entries)
        target_message = await channel.send(embed=Embed(title="Role Menu",
            description=roles_list))

        await ctx.send('Creating...')

        for role, reactable, _ in entries:
            await self.bot.db.insert_reaction_role(ctx.guild.id,
                target_message.channel.id, target_message.id, role.id, str(reactable))
            await target_message.add_reaction(reactable)

        await ctx.send('Reaction roles set-up!')

    @has_permissions(administrator=True)
    @command(name='welcome', aliases=('wc',))
    async def set_welcome_channel(self, ctx: Context, channel: TextChannel):
        """Sets the channel where welcome messages are sent"""

        await self.bot.db.update_welcome_channel(ctx.guild.id, channel.id)
        await ctx.send('Updated')

    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    @group(name='purge')
    async def purge(self, ctx: Context, count: int = 10):
        """Deletes multiple messages from the current channel.
        You must have Manage messages permission."""

        if ctx.invoked_subcommand is None:
            async for message in ctx.channel.history(limit=count):
                await message.delete()

    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    @purge.command(name='user')
    async def purge_user(self, ctx: Context, user: Member, count: int = 10):
        """Delete messages from the specified user"""

        async for message in ctx.channel.history(limit=count):
            if message.author == user:
                await message.delete()

    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    @command(name='kick')
    async def kick_user(self, ctx: Context, user: Member, *, reason: str = None):
        """Kicks a member from the server.
        You must have kick members permission"""

        await user.kick(reason=reason)
        await ctx.channel.send(f'{user} has been kicked\nReason: {reason}')

    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @command(name='ban')
    async def ban_user(self, ctx: Context, user: Member, *, reason: str = None):
        """Kicks a member from the server.
        You must have kick members permission"""

        await user.ban(reason=reason)
        await ctx.channel.send(f'{user} has been banned\nReason: {reason}')


def setup(bot: StoneLegendBot):
    bot.add_cog(Moderation(bot))