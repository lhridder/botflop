import os
import discord
import logging
import sys
import configparser

from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord_slash import SlashCommand

bot = commands.Bot(command_prefix="-", intents=discord.Intents.default(),
                   case_insensitive=True, help_command=False)
slashbot = SlashCommand(bot, sync_commands=True)

logging.basicConfig(filename='console.log',
                    level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', )
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

try:
    file = open("config.ini")
    file.close()
except IOError:
    config = configparser.ConfigParser()
    config['bot'] = {'token': '', 'apikey': '', 'slash_commands_guild': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    print("Config created! stopping...")
    sys.exit(0)
print("Config exists. continuing...")

config = configparser.ConfigParser()
config.read("config.ini")
bot.bot_token = config["bot"]["token"]
bot.ipinfo_apikey = config["bot"]["apikey"]


@bot.event
async def on_ready():
    # Marks bot as running
    logging.info('I am running.')


@bot.event
async def on_message(message):
    timings = bot.get_cog('Timings')
    await timings.analyze_timings(message)
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error



for file_name in os.listdir('./cogs'):
    if file_name.endswith('.py'):
        bot.load_extension(f'cogs.{file_name[:-3]}')

bot.run(bot.bot_token)
