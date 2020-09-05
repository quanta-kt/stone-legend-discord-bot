from discord import Member, File
from discord.ext.commands import Cog, command
import aiohttp
from concurrent.futures import ProcessPoolExecutor
from io import BytesIO
from base64 import b64encode
import cairosvg

from .. import StoneLegendBot


class Welcome(Cog):

    def __init__(self, bot: StoneLegendBot):
        self.bot = bot
        with open('welcome_template.svg') as fp:
            self.template_svg = fp.read()

        self.process_pool = ProcessPoolExecutor(max_workers=3)
        self.http_session = aiohttp.ClientSession()

    def __del__(self):
        self.process_pool.shutdown()
        self.http_session.close()

    async def generate_welcome_image(self, pfp_data: bytes, username: str) -> BytesIO:
        """Build and return the png image from svg template as BytesIO object"""

        def generate():
            svg = self.template_svg % (b64encode(pfp_data).decode('utf-8'), username)
            result = BytesIO()
            cairosvg.svg2png(svg, write_to=result)
            return result

        return await self.bot.loop.run_in_executor(self.process_pool, generate)

    @command(name="_shh")
    async def on_member_join(self, ctx: Context, member: Member):
        """Listen to member join event to welcome them"""

        if member.guild.id != 670907730155798548:
            return

        async with http_session.get(member.avatar_url_as('png')) as resp:
            pfp = await resp.content.read()

        image = await generate_welcome_image(pfp, str(member))
        del pfp

        await member.guild.get_channel(738086034809683999).send(member.mention, file=File(image))


def setup(bot: StoneLegendBot):
    bot.add_cog(Welcome(bot))