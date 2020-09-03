from discord.ext.commands import Cog, command, Bot, Context
from discord import Embed, Color
import aiohttp


class Info(Cog):

    @command(name='store', aliases=('shop', 'market'))
    async def store(self, ctx: Context):
        """Links to buycraft store"""

        pass

    @command(name='features', aliases=('offers',))
    async def offers(self, ctx: Context):
        """Shows what we offer"""

        pass

    @command(name='status')
    async def minecraft_server_status(self, ctx: Context):
        """Shows the status of the MineCraft server"""

        embed = Embed(title="Minecraft Server Status", color=Color.green())
        embed.add_field(
            name="**IP**",
            value="play.stonelegend.net",
            inline=False
        )
        embed.add_field(
            name="**Port**",
            value="19145",
            inline=False
        )

        async with aiohttp.ClientSession() as client:
            resp = await client.get("https://api.mcsrvstat.us/2/play.stonelegend.net:19145")
            data = await resp.json()

        embed.add_field(
            name='**Status**',
            value='Online' if data['online'] else 'Offline',
            inline=False
        )

        if data['online']:
            embed.add_field(
                name='**Players**',
                value=f"{data['players']['online']}/{data['players']['max']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @command(name='players')
    async def players_list(self, ctx: Context):
        """Lists the online players in the MineCraft server"""

        async with aiohttp.ClientSession() as client:
            resp = await client.get("https://api.mcsrvstat.us/2/play.stonelegend.net:19145")
            data = await resp.json()

        if not data['online']:
            await ctx.send(embed=Embed(
                description='The server is offline at the moment!',
                color=Color.orange()
            ))

            return

        if data['players']['online'] < 1:
            description = '*No players online.*'
        else:
            description = '\n'.join(data['players']['list'])

        await ctx.send(embed=Embed(
            title="List of Players in the MineCraft Server",
            description=description,
            color=Color.green()
        ))


def setup(bot: Bot):
    bot.add_cog(Info())