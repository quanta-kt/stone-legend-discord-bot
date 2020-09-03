from discord.ext.commands import Context, command, Cog
from discord.ext.tasks import loop
from discord import Embed, Color, Message, utils, NotFound, Emoji, Reaction, User, Member
import re
from datetime import timedelta, datetime
import aioscheduler
import asyncio
from typing import Union
import emoji
import random

from .. import StoneLegendBot
from ..db import Database


class Utility(Cog):

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        self._scheduler = aioscheduler.TimedScheduler()
        self.poll_countdown_updater.start()
        self.giveaway_countdown_updater.start()
        asyncio.ensure_future(self.schedule_from_db())

    async def _schedule_or_call(self, future, when):
        """Schedules the future to run at given datetime, awaits right away if
        when > currentdatetime"""

        if datetime.utcnow() > when:
            await future
        else:
            self._scheduler.schedule(future, when)

    @loop(seconds=5)
    async def poll_countdown_updater(self):
        """Updates countdown on all poll messages in the db"""

        await self.bot.wait_until_ready()

        for poll_row in await self.bot.db.get_all_polls():

            if datetime.utcnow().timestamp() > poll_row['finish_time']:
                continue

            duration_delta = timedelta(seconds=round(poll_row['finish_time'] - datetime.utcnow().timestamp()))

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

    @loop(seconds=5)
    async def giveaway_countdown_updater(self):
        """Updates countdown on all giveaway messages in the db"""

        await self.bot.wait_until_ready()

        for giveaway_row in await self.bot.db.get_all_giveaways():

            if datetime.utcnow().timestamp() > giveaway_row['finish_time']:
                continue

            try:
                channel = await self.bot.fetch_channel(giveaway_row['channel_id'])
                message = await channel.fetch_message(giveaway_row['message_id'])
            except NotFound:
                # No longer relevent
                await self.bot.db.delete_giveaway(giveaway_row['id'])
                continue

            duration_delta = timedelta(seconds=round(giveaway_row['finish_time'] - datetime.utcnow().timestamp()))

            embed = Embed(
                title="Giveaway!",
                description=f"{giveaway_row['prize']}\n\n"
                    + f"*Time left: {duration_delta}*\n"
                    + f"*Hosted by: <@{giveaway_row['author_id']}>*",
                color=Color.orange()
            ).set_footer(text="React with \N{party popper} to enter")

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
        self._scheduler.start() # Prepare scheduler
        await self.bot.wait_until_ready()

        for poll_row in await self.bot.db.get_all_polls():
            await self._schedule_or_call(
                self.finish_poll(poll_row), datetime.fromtimestamp(poll_row['finish_time']))

        for giveaway_row in await self.bot.db.get_all_giveaways():
            await self._schedule_or_call(
                self.finish_giveaway(giveaway_row), datetime.fromtimestamp(giveaway_row['finish_time']))

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

    async def finish_giveaway(self, giveaway_row):
        """Called when the giveaway finishes- i.e. when the giveaway time is up"""

        try:
            channel = await self.bot.fetch_channel(giveaway_row['channel_id'])
            message = await channel.fetch_message(giveaway_row['message_id'])
            reaction = utils.get(message.reactions, emoji='\N{party popper}')

            choices = tuple(user.mention for user in await reaction.users().flatten() if user != self.bot.user)
            if not choices:
                await channel.send(f"Oh no! Looks like nobody wants {giveaway_row['prize']}")
                return

            winner = random.choice(choices)
            await channel.send(f"\N{party popper} {winner} won {giveaway_row['prize']}!")

            await message.edit(embed=Embed(
                title="Giveaway!",
                description=f"{giveaway_row['prize']}\n\n"
                    + f"Winner: {winner}\n"
                    + f"Hosted by: <@{giveaway_row['author_id']}>",
                color=Color.green()
            ))

        finally:
            await self.bot.db.delete_giveaway(giveaway_row['id'])
            
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

        future = self.finish_poll({
            'id': poll_id,
            'channel_id': ctx.channel.id,
            'message_id': message.id,
            'question': question,
            'emoji1': emoji1,
            'emoji2': emoji2
        })

        await self._schedule_or_call(future, finish_time)

    @command(name='giveaway', aliases=('gw',))
    async def start_giveaway(self, ctx: Context, duration: str, *, prize):
        """Starts a give away"""

        # Parse and validate duration
        duration_delta = self.parse_duration(duration)
        if duration_delta is None:
            await ctx.send(embed=Embed(
                description='Invalid duration!',
                color=Color.orange()
            ))

            return

        finish_time = datetime.utcnow() + duration_delta
        
        embed = Embed(
            title="Giveaway!",
            description=f"{prize}\n\n"
                + f"*Time left: {duration_delta}*\n"
                + f"*Hosted by: {ctx.author.mention}*",
            color=Color.orange()
        ).set_footer(text="React with \N{party popper} to enter")

        message = await ctx.send(embed=embed)
        await message.add_reaction('\N{party popper}')

        giveaway_id = await self.bot.db.insert_giveaway(ctx.channel.id, message.id,
            prize, finish_time.timestamp(), ctx.author.id)
    
        future = self.finish_giveaway({
            'id': giveaway_id,
            'channel_id': ctx.channel.id,
            'message_id': message.id,
            'author_id': ctx.author.id,
            'prize': prize
        })

        await self._schedule_or_call(future, finish_time)

    @command(name='say', aliases=('echo',))
    async def say(self, ctx: Context, *, text):
        await ctx.send(text)

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