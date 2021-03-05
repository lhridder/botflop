import os
import discord
import logging
import sys
from discord.ext import commands
from discord.ext.commands import has_permissions
import configparser

bot = commands.Bot(command_prefix=".", intents=discord.Intents.default(),
                   case_insensitive=True)

logging.basicConfig(filename='console.log',
                    level=logging.INFO,
                    format='[%(asctime)s %(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

try:
    file = open("config.ini")
    file.close()
except IOError:
    config = configparser.ConfigParser()
    config['bot'] = {'token': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    print("Config created! stopping...")
    sys.exit(0)
print("Config exists. continuing...")

config = configparser.ConfigParser()
config.read("config.ini")
token = config["bot"]["token"]


@bot.event
async def on_ready():
    # Marks bot as running
    logging.info('I am running.')

@bot.event
async def on_message(message):
    timings = bot.get_cog('Timings')
    await timings.analyze_timings(message)
    await bot.process_commands(message)

@bot.command()
async def ping(ctx):
    await ctx.send(f'Birdflop bot ping is {round(bot.latency * 1000)}ms')

@has_permissions(administrator=True)
async def react(ctx, url, reaction):
    channel = await bot.fetch_channel(int(url.split("/")[5]))
    message = await channel.fetch_message(int(url.split("/")[6]))
    await message.add_reaction(reaction)
    logging.info('reacted to ' + url + ' with ' + reaction)

for file_name in os.listdir('./cogs'):
    if file_name.endswith('.py'):
        bot.load_extension(f'cogs.{file_name[:-3]}')


bot.run(token)