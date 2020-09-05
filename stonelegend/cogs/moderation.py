from discord.ext.commands import(Context, Cog, command, has_permissions,
    BadArgument, RoleConverter, EmojiConverter, MissingRequiredArgument, CommandError)
from discord import Role, Embed, Color, TextChannel, Reaction, User, Member, Emoji
from discord import utils
from datetime import datetime
from typing import Tuple, Union
import emoji
import re

from ..bot import StoneLegendBot


class ParseError(CommandError):
    """Exception thrown when a custom Parser fails"""

    def __init__(self, readable_error):
        self.readable_error = readable_error

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
    async def create_self_roles(self, ctx: Context, channel: TextChannel, *, entries):
        """Creates a self roles message
        entries must be triplets of role, emoji, description separated by space
        Example: selfroles #RolesChannel @CoolRole \N{smiling face with sunglasses} A cool role
        @Evil \N{smiling face with horns} Evil role"""

        mapping = await self.parse_self_roles_list(ctx, entries)

        # Build and send message
        roles_list = "\n\n".join(f"{reactable} {role.mention}\n{desc}" \
            for role, reactable, desc in mapping)
        target_message = await channel.send(embed=Embed(title="Role Menu",
            description=roles_list))

        await ctx.send('Creating...')

        for role, reactable, _ in mapping:
            await self.bot.db.insert_reaction_role(ctx.guild.id,
                target_message.channel.id, target_message.id, role.id, str(reactable))
            await target_message.add_reaction(reactable)

        await ctx.send('Reaction roles set-up!')

    async def parse_self_roles_list(self, ctx: Context, raw_list: str) -> Tuple[Tuple[Role, Union[str, Emoji], str], ...]:
        """Parses and returns the user inputed list from `selfroles` command.
        Raises ParseError on failure."""

        async def convert_to_emoji(emoji_str) -> Union[Emoji, str]:
            try:
                return await EmojiConverter().convert(ctx, emoji_str)
            except BadArgument:
                if emoji_str in emoji.UNICODE_EMOJI:
                    return emoji_str
            raise ParseError(f"{emoji_str} is not a valid emoji")

        async def convert_to_role(role_str) -> Role:
            try:
                return await RoleConverter().convert(ctx, role_str)
            except BadArgument:
                raise ParseError(f"{role_str} is not a valid role")

        async def parse_row(line):
            row = re.split(' +', line.strip(), maxsplit=2)
            try:
                role_str, emoji_str, desc = row
            except ValueError:
                raise ParseError(f"{' '.join(row)} is not a valid pair of role-emoji-description")
            return (await convert_to_role(role_str), await convert_to_emoji(emoji_str), desc)

        return tuple([await parse_row(line) for line in raw_list.splitlines() if line])

    @create_self_roles.error
    async def create_self_roles_error(self, ctx: Context, error: Exception):

        if isinstance(error, ParseError):
            await ctx.send(embed=Embed(
                title="Invalid arguments",
                description=error.readable_error,
                color=Color.orange()))
            return

        if isinstance(error, MissingRequiredArgument):
            await ctx.send(embed=Embed(title="Missing argument",
                description=f"Missing required argument: **{error.param.name}**"))
            return

        if isinstance(error, BadArgument):
            await ctx.send(embed=Embed(description="Can't find the specified channel",
                color=Color.orange))
            return

        raise error

    @has_permissions(administrator=True)
    @command(name='welcome', aliases=('wc',))
    async def set_welcome_channel(self, ctx: Context, channel: TextChannel):
        """Sets the channel where welcome messages are sent"""

        await self.bot.db.insert_welcome_channel(ctx.guild.id, channel.id)
        await ctx.send('Updated')
    
    @set_welcome_channel.error
    async def set_welcome_channel_error(self, ctx: Context, error: CommandError):
        
        if isinstance(error, BadArgument):
            await ctx.send(embed=Embed(description="Can't find the specified channel",
                color=Color.orange()))

            return

        if isinstance(error, MissingRequiredArgument):
            await ctx.send(embed=Embed(title="Missing argument",
                description=f"Missing required argument: **{error.param.name}**"))
            return

        raise error


def setup(bot: StoneLegendBot):
    bot.add_cog(Moderation(bot))