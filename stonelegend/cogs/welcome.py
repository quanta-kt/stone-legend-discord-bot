from discord import Member, File
from discord.ext.commands import Cog, command, Context
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from base64 import b64encode
import cairosvg

from .. import StoneLegendBot


class Welcome(Cog):

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        with open('welcome_template.svg') as fp:
            self.template_svg = fp.read()

        self.thread_pool = ThreadPoolExecutor(max_workers=3)
        self.http_session = aiohttp.ClientSession()

    def __del__(self):
        self.thread_pool.shutdown()
        self.http_session.close()

    def _generate_welcome_image(self, pfp_data, bg_data, username):
        svg = self.template_svg % dict(pfp=b64encode(pfp_data).decode('utf-8'),
            bg=b64encode(bg_data).decode('utf-8'), username=username)
        result = BytesIO()
        cairosvg.svg2png(svg, write_to=result)
        result.seek(0)
        return result

    async def generate_welcome_image(self, pfp_data: bytes, bg_data: bytes, username: str) -> BytesIO:
        """Build and return the png image from svg template as BytesIO object"""

        return await self.bot.loop.run_in_executor(self.thread_pool, self._generate_welcome_image,
            pfp_data, bg_data, username)

    @Cog.listener()
    async def on_member_join(self, member: Member):
        """Listens to member join event to welcome them"""

        target_channel_id = await self.bot.db.get_welcome_channel(member.guild.id)
        if target_channel_id is None:
            return

        target_channel = member.guild.get_channel(target_channel_id)
        if target_channel is None:
            return

        async with self.http_session.get(str(member.avatar_url_as(format='png'))) as resp:
            pfp = await resp.content.read()

        async with self.http_session.get("https://source.unsplash.com/500x250/?universe") as resp:
            bg = await resp.content.read()

        image = await self.generate_welcome_image(pfp, bg, str(member))
        del pfp

        await target_channel.send(member.mention, file=File(image, filename='welcome.png'))


def setup(bot: StoneLegendBot):
    bot.add_cog(Welcome(bot))