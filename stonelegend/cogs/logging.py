import discord
from discord.ext import commands
import datetime

from ..bot import StoneLegendBot


class LoggingChannelCache():

    def __init__(self, bot: StoneLegendBot):
        self._cache = {}
        self.bot = bot

    async def get_logging_channel(self, guild_id: int) -> int:

        channel_id = self._cache.get(guild_id)
        if channel_id is None:
            channel_id = await self.bot.db.get_logging_channel(guild_id)
            self._cache[guild_id] = channel_id

        return channel_id

    async def update_logging_channel(self, guild_id: int, channel_id: int) -> None:
        await self.bot.db.update_logging_channel(guild_id, channel_id)
        self._cache[guild_id] = channel_id

class Logging(commands.Cog):
    """Logs server actions in a specified channel"""
    
    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        self.logging_channels_cache = LoggingChannelCache(bot)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        
        log_channel_id = await self.logging_channels_cache.get_logging_channel(member.guild.id)
        if log_channel_id is None:
            return

        log_channel = self.bot.get_channel(log_channel_id) or \
            await self.bot.fetch_channel(log_channel_id)

        embed = discord.Embed(title=str(member),
            description=f"Member joined\n{member.mention}",
            color=discord.Color.green(),
            timestamp=datetime.datetime.today()) \
                .set_footer(text=f"ID: {member.id}")

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):

        log_channel_id = await self.logging_channels_cache.get_logging_channel(member.guild.id)
        if log_channel_id is None:
            return

        log_channel = self.bot.get_channel(log_channel_id) or \
            await self.bot.fetch_channel(log_channel_id)

        embed = discord.Embed(title=str(member),
            description="Member left",
            color=discord.Color.red(),
            timestamp=datetime.datetime.today()) \
                .set_footer(text=f"ID: {member.id}")

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):

        log_channel_id = await self.logging_channels_cache.get_logging_channel(payload.guild_id)
        if log_channel_id is None:
            return

        message = payload.cached_message
        if message is not None and message.author == self.bot.user:
            return # Skip bot's messages where possible

        log_channel = self.bot.get_channel(log_channel_id) or \
            await self.bot.fetch_channel(log_channel_id)

        if message is not None:
            message_content = message.content
            if len(message_content) > 100:
                message_content = message_content[:100] + '...'
        else:
            message_content = '?'

        description = "Message sent by {} deleted in {}\n\n{}".format(
            message.author.mention if message is not None else "?",
            message.channel.mention if message is not None else "?",
            message_content)

        embed = discord.Embed(title= f"{message.author}" if message is not None \
            else discord.Embed.Empty,
            description=description)

        await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent):

        log_channel_id = await self.logging_channels_cache.get_logging_channel(payload.data['guild_id'])
        if log_channel_id is None:
            return

        new_message = payload.data.get('content')
        if new_message is None:
            return # Skip embed only edits

        log_channel = self.bot.get_channel(log_channel_id) or \
            await self.bot.fetch_channel(log_channel_id)

        old_message = payload.cached_message.content if payload.cached_message is not None \
            else '?'

        if len(old_message) > 100:
            old_message = old_message[:100] + '...'
        if len(new_message) > 100:
            new_message = new_message[:100] + '...'

        description = "Message sent by <@{}> edited in <#{}>\n\nBefore:\n{}\n\nAfter:\n{}".format(
            payload.data['author']['id'], payload.channel_id, old_message, new_message)

        await log_channel.send(embed = discord.Embed(
            title = payload.data['author']['username'] + '#' + payload.data['author']['discriminator'],
            description=description))

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):

        log_channel_id = await self.logging_channels_cache \
            .get_logging_channel(after.guild.id)
        if log_channel_id is None:
            return

        log_channel = self.bot.get_channel(log_channel_id) or \
            await self.bot.fetch_channel(log_channel_id)

        if before.nick != after.nick:
            await log_channel.send(embed=discord.Embed(title=str(after), 
                description="Nickname changed\n\n"
                    + f"**Before**: {before.nick or str(before)}\n"
                    + f"**After:** {after.nick or str(after)}",
                color=discord.Color.green()))

        old_roles = set(before.roles)
        new_roles = set(after.roles)
        removed_roles = old_roles - new_roles
        added_roles = new_roles - old_roles

        if removed_roles:
            await log_channel.send(embed=discord.Embed(title=str(after),
                description="Roles removed\n\n"
                    + ", ".join(role.mention for role in removed_roles),
                color=discord.Color.green()))

        if added_roles:
            await log_channel.send(embed=discord.Embed(title=str(after),
                description="Roles added\n\n"
                    + ", ".join(role.mention for role in added_roles),
                color=discord.Color.green()))

    @commands.command(name='enablelogs')
    @commands.has_permissions(manage_guild=True)
    async def enable_logs(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set logging channel for the server"""

        await self.logging_channels_cache.update_logging_channel(ctx.guild.id, channel.id)
        await ctx.send('Enabled logging features.\n'
            + f'Logs will now appear in {channel.mention}')

def setup(bot: StoneLegendBot):
    bot.add_cog(Logging(bot))