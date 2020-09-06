from discord.ext.commands import(Converter, Context, BadArgument,
    EmojiConverter, RoleConverter)
from discord import Emoji, Role
from datetime import timedelta
from typing import Union, Tuple
import emoji
import re

class TimeDeltaConverter(Converter):
    """A converter to parse time durations"""

    async def convert(self, ctx: Context, arg: str) -> timedelta:
        pattern = re.compile(r"^((?P<weeks>\d+)w)?((?P<days>\d+)d)?((?P<hours>\d+)h)?((?P<minutes>\d+)m)?((?P<seconds>\d+)s)?$", re.IGNORECASE)
        match = pattern.match(arg)

        if match is None:
            raise BadArgument(f"{arg} is not a valid time duration")

        # Get groups and map None to 0
        duration_dict = {key: int(val) if val is not None else 0 for key, val in match.groupdict().items()}

        # Build and return timedelta
        return timedelta(**duration_dict)

class ReactableConverter(Converter):
    """A converter for 'reactables' (Emoji objects or unicode emoji string)"""

    async def convert(self, ctx: Context, arg: str) -> Union[Emoji, str]:
        try:
            return await EmojiConverter().convert(ctx, arg)
        except BadArgument:
            if arg in emoji.UNICODE_EMOJI:
                return arg
        raise BadArgument(f"{arg} is not a valid emoji")

class SelfRolesListConverter(Converter):
    """Converter for list of self roles passed to `selfroles` command"""

    async def convert(self, ctx: Context, arg: str) -> Tuple[Tuple[Role, Union[str, Emoji], str], ...]:

        async def convert_to_emoji(emoji_str) -> Union[Emoji, str]:
            try:
                return await EmojiConverter().convert(ctx, emoji_str)
            except BadArgument:
                if emoji_str in emoji.UNICODE_EMOJI:
                    return emoji_str
            raise BadArgument(f"{emoji_str} is not a valid emoji")

        async def convert_to_role(role_str) -> Role:
            try:
                return await RoleConverter().convert(ctx, role_str)
            except BadArgument:
                raise BadArgument(f"{role_str} is not a valid role")

        async def parse_row(line):
            row = re.split(' +', line.strip(), maxsplit=2)
            try:
                role_str, emoji_str, desc = row
            except ValueError:
                raise BadArgument(f"{' '.join(row)} is not a valid pair of role-emoji-description")
            return (await convert_to_role(role_str), await convert_to_emoji(emoji_str), desc)

        return tuple([await parse_row(line) for line in arg.splitlines() if line])