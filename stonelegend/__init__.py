from os import environ, path
import json

from .bot import StoneLegendBot
from .cogs import all_extensions
from .help import CustomHelpCommand
from .db import Database


SQL_CONFIG_FILE = 'sql_config.json'


def run():

    token = environ.get('TOKEN')
    if token is None:
        raise ValueError('TOKEN environment variable is not set')

    if not path.exists(SQL_CONFIG_FILE):
        raise ValueError(f"{SQL_CONFIG_FILE} does not exist!")

    with open(SQL_CONFIG_FILE) as fp:
        sql_config = json.load(fp)

    bot = StoneLegendBot(sql_config)

    for ext in all_extensions:
        ext.setup(bot)

    bot.run(token)