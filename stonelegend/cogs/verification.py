import discord
from discord.ext import commands
from captcha.image import ImageCaptcha
import os
import string
import random
import asyncio

from ..bot import StoneLegendBot


class Verification(commands.Cog):
    """Commands related to verification for new members"""

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        self.captcha_characters = string.ascii_letters

        font_files = [os.path.abspath(os.path.join(os.path.join('./fonts', f))) \
            for f in os.listdir('./fonts')]
        self._captcha_builder = ImageCaptcha(fonts=font_files)

    @commands.has_permissions(manage_guild=True)
    @commands.command('setup_verification', aliases=('setvr', 'verifrole'))
    async def select_role(self, ctx: commands.Context, role: discord.Role):
        """Select a verified role for your server"""

        await self.bot.db.update_verification_role(ctx.guild.id, role.id)
        await ctx.send("Updated.")

    @commands.command('verify')
    @commands.bot_has_permissions(manage_roles=True)
    async def verify(self, ctx: commands.Context):
        """Verifies you by sending a captcha in your DM"""

        await ctx.message.delete()

        target_role_id = await self.bot.db.get_verification_role(ctx.guild.id)
        if target_role_id is None or (target_role := ctx.guild.get_role(target_role_id)) is None:
            raise commands.CheckFailure("Verification role is not set."
                + f"Please use `{ctx.prefix}setup_verification` command")

        challenge = ''.join(random.sample(self.captcha_characters, 4))

        try:
            await ctx.author.send('Type the characters in the below image (case sensitive)',
                file=discord.File(self._captcha_builder.generate(challenge), 'challenge.png'))
        except discord.Forbidden:
            await ctx.send(f"{ctx.author.mention} I can't message you because your DMs are turned off\n" \
                + f"Please enable DMs from this server and try again!",
                delete_after=60)
            return

        def check(message: discord.Message):
            return isinstance(message.channel, discord.DMChannel) and \
                message.author == ctx.author

        try:
            message = await self.bot.wait_for("message", check=check, timeout=30)
        except asyncio.TimeoutError:
            await ctx.author.send('Timed out.')
            return

        if message.content == challenge:
            await ctx.author.add_roles(target_role)
            await ctx.author.send('Verified')
        else:
            await ctx.author.send("Incorrect captcha, can't verify you")

def setup(bot: StoneLegendBot):
    bot.add_cog(Verification(bot))