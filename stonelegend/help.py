from discord import Embed, Color
from discord.ext.commands import HelpCommand, Group, Command


class CustomHelpCommand(HelpCommand):

    def get_embed(self, **kwargs):
        """Returns an embed with preset color and thumbnail"""
        return Embed(color=Color.green(), **kwargs) \
            .set_thumbnail(url="https://stonelegend.net/img/logo.png")

    def get_command_signature(self, command: Command, group: str = '') -> str:
        sig = (' ' + command.signature).rstrip()
        group = group + ' ' if group else ''
        return f'/{group}{command.name}{sig}'

    def get_group_signature(self, group: Group) -> str:
        sig = (' ' + group.signature).rstrip()
        return f"/{group.name}{sig}"

    async def command_not_found(self, string):
        await self.get_destination().send(embed=Embed(
            description=f"No command called {string}!",
            color=Color.orange()
        ))

    async def send_bot_help(self, mapping):
        embed = self.get_embed().set_author(name='List of categories and commands')

        for cog, commands in mapping.items():
            if cog is not None and (commands := [c for c in commands if not c.hidden]):
                embed.add_field(
                    name=cog.qualified_name,
                    value=', '.join(command.qualified_name for command in commands),
                    inline=False
                )

        await self.get_destination().send(embed=embed)

    async def send_cog_help(self, cog):
        commands = cog.get_commands()

        embed = self.get_embed() \
            .set_author(name=f'{cog.qualified_name} category') \
            .add_field(name='Usage', value=cog.description, inline=False) \
            .add_field(name='Commands',
                value=', '.join([command.name for command in commands]) if commands else '*No commands to show*',
                inline=True)
        await self.get_destination().send(embed=embed)

    async def send_group_help(self, group: Group):
        embed = self.get_embed(title=self.get_group_signature(group),
            description=group.help)

        for command in group.commands:
            embed.add_field(name=self.get_command_signature(command, group.name),
                value=command.help)

        await self.get_destination().send(embed=embed)

    async def send_command_help(self, command: Command):
        embed = self.get_embed(title=self.get_command_signature(command),
            description=command.help) \
            .add_field(
                name='This command belongs to',
                value=f'{command.cog_name} cog',
                inline=False
            )
        
        if command.aliases:
            embed.add_field(
                name='Aliases',
                value=', '.join(alias for alias in command.aliases),
                inline=False
            )

        await self.get_destination().send(embed=embed)