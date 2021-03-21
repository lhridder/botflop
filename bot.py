import os
import discord
import logging
import sys

import requests
from discord.ext import commands
from discord.ext.commands import has_permissions
import configparser

bot = commands.Bot(command_prefix=".", intents=discord.Intents.default(),
                   case_insensitive=True)

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
    config['bot'] = {'token': '', 'apikey': ''}
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    print("Config created! stopping...")
    sys.exit(0)
print("Config exists. continuing...")

config = configparser.ConfigParser()
config.read("config.ini")
token = config["bot"]["token"]
apikey = config["bot"]["apikey"]


@bot.event
async def on_ready():
    # Marks bot as running
    logging.info('I am running.')


@bot.event
async def on_message(message):
    timings = bot.get_cog('Timings')
    await timings.analyze_timings(message)
    await bot.process_commands(message)
    msg = message.content

    # Server status checker based on mcsrvstat.us api
    if msg == "-online":
        print('Message from {0.author}: {0.content}'.format(message))
        await message.channel.send("Please give an ip to check (-online ip:port)")
    if msg.startswith("-online "):
        print('Message from {0.author}: {0.content}'.format(message))

        arg = msg.replace("-online ", "")
        r = requests.get("https://api.mcsrvstat.us/2/" + arg)
        rjson = r.json()

        if rjson["online"]:
            embed = discord.Embed(title="Server online: " + arg, color=0x00FF00)

            if len(rjson["motd"]["clean"]) > 1:
                info = str(rjson["motd"]["clean"][0]) + "\n" + str(rjson["motd"]["clean"][1])
            else:
                info = str(rjson["motd"]["clean"][0])
            embed.add_field(name='Motd', value=info, inline=False)

            if "software" in rjson:
                version = str(rjson["version"]) + " (" + str(rjson["software"]) + ")"
            else:
                version = str(rjson["version"]) + "\n"
            embed.add_field(name='Version', value=version, inline=False)

            count = str(rjson["players"]["online"]) + "/" + str(rjson["players"]["max"])
            embed.add_field(name='Players', value=count, inline=False)

        else:
            embed = discord.Embed(title="Server offline: " + arg, color=0xFF0000)

        embed.add_field(name='Ip', value=str(rjson["ip"]) + ":" + str(rjson["port"]), inline=False)

        if rjson["debug"]["ping"]:
            pingserver = ":white_check_mark:"
        else:
            pingserver = ":red_circle:"

        if rjson["debug"]["query"]:
            query = ":white_check_mark:"
        else:
            query = ":red_circle:"

        if rjson["debug"]["srv"]:
            srv = ":white_check_mark:"
        else:
            srv = ":red_circle:"

        if "hostname" not in rjson:
            debug = pingserver + " Ping" + "\n" \
                    + query + " Query" + "\n" \
                    + srv + " SRV"
        else:
            debug = pingserver + " Ping" + "\n" \
                    + query + " Query" + "\n" \
                    + srv + " SRV" + "\n" \
                    + "Hostname: " + str(rjson["hostname"])

        embed.add_field(name='Debug', value=debug, inline=False)

        embed.set_footer(text="Data from mcsrvstat.us api",
                         icon_url="https://feroxhosting.nl/img/fhlogosmall.png")
        await message.channel.send(embed=embed)
        print("Sent response in channel")

    # Server status checker based on mcsrvstat.us api
    if msg == "-ipinfo":
        print('Message from {0.author}: {0.content}'.format(message))
        await message.channel.send("Please give an ip to check (-ipinfo (ip))")
    if msg.startswith("-ipinfo "):
        print('Message from {0.author}: {0.content}'.format(message))
        arg = msg.replace("-ipinfo ", "")
        if " " in arg:
            await message.channel.send("No spaces allowed")
        else:
            r = requests.get("https://ipinfo.io/" + arg + "?token=" + apikey)
            rjson = r.json()
            if "status" in rjson:
                await message.channel.send("404 error while consulting the API")
            else:
                embed = discord.Embed(title="Ip info", color=0x00FF00, description=rjson["ip"])
                embed.add_field(name='Hostname', value=str(rjson["hostname"]), inline=False)
                embed.add_field(name='Organization', value=str(rjson["org"]), inline=False)
                loc = "City: " + str(rjson["city"]) + "\n" \
                      + "Region: " + str(rjson["region"]) + "\n" \
                      + "Country: " + str(rjson["country"]) + "\n" \
                      + "Location: " + str(rjson["loc"]) + "\n" \
                      + "Postal code: " + str(rjson["postal"]) + "\n" \
                      + "Timezone: " + str(rjson["timezone"])
                embed.add_field(name='Location', value=loc, inline=False)
                embed.set_footer(text="Data from ipinfo.io api",
                                 icon_url="https://feroxhosting.nl/img/fhlogosmall.png")
                await message.channel.send(embed=embed)
                print("Sent response in channel")


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
