from discord.ext.commands import Context, command, Cog
from discord.ext.tasks import loop
from discord import Embed, Color, Message, utils, NotFound, Emoji, Reaction, User, Member
import re
from datetime import timedelta, datetime
import aioscheduler
import asyncio
from typing import Union
import emoji

from .. import StoneLegendBot
from ..db import Database


class Utility(Cog):

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        self._scheduler = aioscheduler.TimedScheduler()
        self.poll_countdown_updater.start()
        asyncio.ensure_future(self.schedule_from_db())

    @loop(seconds=5)
    async def poll_countdown_updater(self):
        """Updates countdown on all poll messages in the db"""

        await self.bot.wait_until_ready()
        now = datetime.utcnow()

        for poll_row in await self.bot.db.get_all_polls():

            duration_delta = timedelta(seconds=round(poll_row['finish_time'] - now.timestamp()))

            try:
                channel = await self.bot.fetch_channel(poll_row['channel_id'])
                message = await channel.fetch_message(poll_row['message_id'])
            except NotFound:
                # No longer relevent
                await self.bot.db.delete_poll(poll_row['id'])
                continue

            emoji1, emoji2 = poll_row['emoji1'], poll_row['emoji2']

            embed = Embed(
                title="New Poll",
                description=poll_row['question']
                    + "\n\n"
                    + f"Time left: {duration_delta}",
                color=Color.green()
            ).set_footer(text=f"React with a {emoji1} or {emoji2}")

            try:
                await message.edit(embed=embed)
            except NotFound:
                pass

    @Cog.listener('on_reaction_add')
    async def on_reaction_add(self, reaction: Reaction, user: Union[User, Member]):
        """Listens on reactions to remove multiple poll entries from same user"""

        if user == self.bot.user:
            return

        if await self.bot.db.is_poll(reaction.message.channel.id, reaction.message.id):
            for other_reaction in reaction.message.reactions:
                if other_reaction != reaction:
                    await other_reaction.remove(user)

    async def schedule_from_db(self):
        self._scheduler.start()
        await self.bot.wait_until_ready()

        for poll_row in await self.bot.db.get_all_polls():
            
            # Trigger off tasks which finished in past
            if datetime.utcnow().timestamp() > poll_row['finish_time']:
                await self.finish_poll(poll_row)
                continue

            # Schedule upcoming tasks
            self._scheduler.schedule(
                self.finish_poll(poll_row),
                datetime.fromtimestamp(poll_row['finish_time'])
            )

    async def finish_poll(self, poll_row):
        """Called when the poll finishes- i.e. when the poll time is up"""

        try:
            channel = await self.bot.fetch_channel(poll_row['channel_id'])
            message = await channel.fetch_message(poll_row['message_id'])

            reaction1, reaction2, *_ = filter(
                lambda r: str(r.emoji) in (str(poll_row['emoji1']), str(poll_row['emoji2'])),
                message.reactions
            )

            try:
                await message.delete()
            except NotFound:
                pass # Ignored

            await channel.send(embed=Embed(
                title="Poll results",
                description=f"**Question:** {poll_row['question']}\n\n"
                    + f"{reaction1.count - 1} people reacted {reaction1.emoji}\n"
                    + f"{reaction2.count - 1} people reacted {reaction2.emoji}",
                color=Color.orange()
            ))
        finally:
            await self.bot.db.delete_poll(poll_row['id'])

    @command(name='poll')
    async def poll(self, ctx: Context, duration: str,
        emoji1: Union[Emoji, str], emoji2: Union[Emoji, str], *, question: str):
        """Posts a poll"""

        # Validate emojis
        async def ensure_emoji(*args):
            for emo in args:
                if not isinstance(emo, Emoji) and not emo in emoji.UNICODE_EMOJI:
                    await ctx.send(embed=Embed(
                        description=f"{emo} is not a valid emoji.",
                        color=Color.orange()
                    ))
                    return False
            return True

        if not await ensure_emoji(emoji1, emoji2):
            return

        # Parse and validate duration
        duration_delta = self.parse_duration(duration)
        if duration_delta is None:
            await ctx.send(embed=Embed(
                description='Invalid duration!',
                color=Color.orange()
            ))

            return

        await ctx.message.delete()

        finish_time = datetime.utcnow() + duration_delta
        
        embed = Embed(
            title="New Poll",
            description=question
                + "\n\n"
                + f"Time left: {duration_delta}",
            color=Color.orange()
        ).set_footer(text=f"React with a {emoji1} or {emoji2}")

        message = await ctx.send(embed=embed)
        await message.add_reaction(emoji1)
        await message.add_reaction(emoji2)

        poll_id = await self.bot.db.insert_poll(
            ctx.channel.id,
            message.id,
            round(finish_time.timestamp()),
            question,
            str(emoji1),
            str(emoji2)
        )

        async def trigger_poll():
            await self.finish_poll({
                'id': poll_id,
                'channel_id': ctx.channel.id,
                'message_id': message.id,
                'question': question,
                'emoji1': emoji1,
                'emoji2': emoji2
            })

        try:
            self._scheduler.schedule(trigger_poll, finish_time)
        except ValueError:
            # Cannot shedule, finish time already passed; trigger away
            await trigger_poll()


    def parse_duration(self, duration_string: str) -> timedelta:
        pattern = re.compile(r"^((?P<weeks>\d+)w)?((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?$", re.IGNORECASE)
        match = pattern.match(duration_string)
        if match is None:
            return None

        # Get groups and map None to 0
        duration_dict = {key: int(val) if val is not None else 0 for key, val in match.groupdict().items()}

        # Build and return timedelta
        return timedelta(**duration_dict)


def setup(bot: StoneLegendBot):
    bot.add_cog(Utility(bot))