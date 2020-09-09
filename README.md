# StoneLegend
Discord bot for StoneLegend Discord community/MineCraft server

## Note
This project is under development and needs a good amount of work. Code cleanup and refactoring is pending.

## Features
- [x] Get the Minecraft server status, online players
- [x] Create self-role menus which allow picking roles by reacting to messages
- [x] Make announcements with neat embeds while pinging a role of choice
- [x] Welcomes new members as they join with a clean image banner with thier username and profile picture
- [x] Create polls which end at the given time while also showing the results
- [x] Create giveaways which selects a random participant as winner
- [x] Captcha verification system for new users

## Planned features
- [ ] Push Minecraft server messages to Discord

# Installing

## Clone the repository
```bash
git clone https://github.com/quanta-kt/stone-legend-discord-bot
cd stone-legend-discord-bot
```
Or simply download and extract the zip file from GitHub

## Create and activate a virtual environment
On Linux:
```bash
python3 -m venv venv
source ./venv/bin/activate
```
On Windows:
```
python3 -m venv venv
.\env\Scripts\activate
```

## Install requirements
The module depends on a few modules from PyPi which can be installed with pip:
```bash
pip install -r requirements.txt
```

## Start the bot
```bash
python -m stonelegend
# Or alternatively
python bot.py
```
On Windows, using `py` instead:
```
py -m stonelegend
# Or alternatively
py bot.py
```

# LICENSE
This project is licensed under GNU GPL V3. Please check [LICENSE.md](LICENSE.md)
