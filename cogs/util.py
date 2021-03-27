import discord
import requests
import logging
import re
import configparser

from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option, create_choice


config = configparser.ConfigParser()
config.read("config.ini")
SLASH_GUILD_ID = int(config["bot"]["slash_commands_guild"])
DNS_TYPES = ["A", "AAAA", "CNAME", "NS", "SRV", "TXT", "CERT"]
DNS_TYPES_LOWER = [x.lower() for x in DNS_TYPES]
DNS_LONGEST = len(max(DNS_TYPES, key=len))

def dns_lookup(fqdn, record_type):
    r = requests.get("https://cloudflare-dns.com/dns-query", params={"name":fqdn, "type":record_type.lower()}, headers={"Accept": "application/dns-json"}).json()
    return [x["data"] for x in ([] if "Answer" not in r else r["Answer"])]

class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def online(self, exec_type, ctx, server):
        logging.info('Online {0} command execution from {1} for "{2}"'.format(exec_type, ctx.author, server))

        if server is None:
            await ctx.send("Please provide a server to check (`fqdn` or `ip:port`)")
            return
            
        if isinstance(ctx, SlashContext):
            await ctx.respond(False)

        r = requests.get("https://api.mcsrvstat.us/2/" + server)
        rjson = r.json()

        embed = discord.Embed(title="Server offline: " + server, color=0xFF0000)
        if rjson["online"]:
            embed = discord.Embed(title="Server online: " + server, color=0x00FF00)

            info = str(rjson["motd"]["clean"][0])
            if len(rjson["motd"]["clean"]) > 1:
                info += "\n" + str(rjson["motd"]["clean"][1])
            embed.add_field(name='Motd', value=info, inline=False)

            version = str(rjson["version"])
            if "software" in rjson:
                version += " (" + str(rjson["software"]) + ")"
            embed.add_field(name='Version', value=version, inline=False)

            count = str(rjson["players"]["online"]) + "/" + str(rjson["players"]["max"])
            embed.add_field(name='Players', value=count, inline=False)

        embed.add_field(name='Ip', value=str(rjson["ip"]) + ":" + str(rjson["port"]), inline=False)

        pingserver = ":red_circle:"
        if rjson["debug"]["ping"]:
            pingserver = ":white_check_mark:"

        query = ":red_circle:"
        if rjson["debug"]["query"]:
            query = ":white_check_mark:"

        srv = ":red_circle:"
        if rjson["debug"]["srv"]:
            srv = ":white_check_mark:"

        debug = pingserver + " Ping" + "\n" \
                    + query + " Query" + "\n" \
                    + srv + " SRV"
        if "hostname" in rjson:
            debug += "\n" \
                    + "Hostname: " + str(rjson["hostname"])

        embed.add_field(name='Debug', value=debug, inline=False)

        embed.set_footer(text="gh:lhridder/botflop - Data from mcsrvstat.us api")
        await ctx.send(embed=embed)
        logging.info("Sent response in channel")


    @cog_ext.cog_slash(name="online", description="Check whether a Minecraft server is online.", options=[
               create_option(
                 name="server",
                 description="Server to check.",
                 option_type=3,
                 required=True
               )
             ], guild_ids=[SLASH_GUILD_ID])
    async def online_slash(self, ctx, server=None):
        await self.online("slash", ctx, server)

    @commands.command(name="online")
    async def online_command(self, ctx, server=None):
        await self.online("default", ctx, server)
        
    
    
    async def ipinfo(self, exec_type, ctx, ip):
        logging.info('Ipinfo {0} command execution from {1} for ip "{2}"'.format(exec_type, ctx.author, ip))

        if ip is None:
            await ctx.send("Please provide an ip to look up! (`ip`)")
            return

        if re.match("^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$", ip) is None:
            await ctx.send("Invalid IP address!")
            return

        if isinstance(ctx, SlashContext):
            await ctx.respond(False)
            
        r = requests.get("https://ipinfo.io/" + ip + "?token=" + self.bot.ipinfo_apikey)
        rjson = r.json()
            
        if "bogon" in rjson and rjson["bogon"]:
            await ctx.send("This is a bogon IP Address!")
            return

        if "status" in rjson:
            await ctx.send("404 error while consulting the API")
            return

        embed = discord.Embed(title="Ip info", color=0x00FF00, description=rjson["ip"])
        if "hostname" in rjson:
            embed.add_field(name='Hostname', value=str(rjson["hostname"]), inline=False)
        if "org" in rjson:
            embed.add_field(name='Organization', value=str(rjson["org"]), inline=False)
        loc = "City: " + str(rjson["city"]) + "\n" \
              + "Region: " + str(rjson["region"]) + "\n" \
              + "Country: " + str(rjson["country"]) + "\n" \
              + "Location: " + str(rjson["loc"]) + "\n" \
              + "Postal code: " + str(rjson["postal"]) + "\n" \
              + "Timezone: " + str(rjson["timezone"])
        embed.add_field(name='Location', value=loc, inline=False)
        embed.set_footer(text="gh:lhridder/botflop - Data from ipinfo.io API")
        await ctx.send(embed=embed)
        logging.info("Sent ipinfo response in channel")


    @cog_ext.cog_slash(name="ipinfo", description="Retrieve information about an IP address.", options=[
               create_option(
                 name="ip",
                 description="IP address to look up.",
                 option_type=3,
                 required=True
               )
             ], guild_ids=[SLASH_GUILD_ID])
    async def ipinfo_slash(self, ctx, ip=None):
        await self.ipinfo("slash", ctx, ip)

    @commands.command(name="ipinfo")
    async def ipinfo_command(self, ctx, ip=None):
        await self.ipinfo("default", ctx, ip)
    


    async def dns(self, exec_type, ctx, fqdn, record_type):
        logging.info('DNS {0} command execution from {1} for fqdn "{2}" and record type "{3}"'.format(exec_type, ctx.author, fqdn, record_type))

        if fqdn is None:
            await ctx.send("Please provide a domain name to look up! (`fqdn`)")
            return
            
        if isinstance(ctx, SlashContext):
            await ctx.respond(False)
        
        embed = discord.Embed(title=("" if record_type is None else "Specific ")+"DNS Lookup", color=0x00FF00)
        def dns_result(record_type, fqdn=fqdn):
            result = dns_lookup(fqdn, record_type)
            if len(result) == 0:
                return ""
            return "{0}  {1}{2}".format(
                record_type.upper(),
                " "*(DNS_LONGEST - len(record_type)),
                "\n{0}  ".format(" "*DNS_LONGEST).join(result)
            )
        if record_type is None:
            # Look up about 4 of the most often used DNS record types and put them in an embed
            not_found = []
            result = ""
            for i in range(4):
                line = dns_result(DNS_TYPES[i])
                if line != "":
                    result += line + "\n"
                else:
                    not_found.append(DNS_TYPES[i])

            if result != "":
                result = "```\n{0}```".format(result)

            if len(not_found) > 0:
                result += "\n" + "(No record(s) was/were found of type(s) {0})".format(", ".join(["`"+x+"`" for x in not_found]))

            embed.add_field(name=fqdn, value=result, inline=False)

        else:
            # Look up a specific record_type
            if record_type.lower() not in DNS_TYPES_LOWER:
                await ctx.send("Invalid / unsupported DNS record type \"{0}\"! Available options (case insensitive):\n{1}".format(record_type, ", ".join(["`"+x+"`" for x in DNS_TYPES])))
                return
            
            result = dns_result(record_type)
            if result == "":
                result = "(No record was found of type `"+record_type.upper()+"`)"
            else:
                result = "```\n{0}\n```".format(result)
            embed.add_field(name=fqdn, value=result, inline=False)

        if not fqdn.startswith("_minecraft._tcp.") and (record_type is None or record_type.lower() == "srv"):
            result = dns_result("srv", "_minecraft._tcp."+fqdn)
            if result != "":
                result = "```\n{0}\n```".format(result)
            elif record_type is not None:
                result = "(No record was found of type `SRV`)"
            if result != "":
                embed.add_field(name="_minecraft._tcp."+fqdn, value=result, inline=False)
        
        embed.set_footer(text="gh:lhridder/botflop - Data from cloudflare-dns.com API")
        await ctx.send(embed=embed)


    @cog_ext.cog_slash(name="dns", description="Do a DNS lookup for a domain.", guild_ids=[SLASH_GUILD_ID], options=[
        create_option(
            name="FQDN",
            description="Domain to look up.",
            option_type=3,
            required=True
        ),
        create_option(
            name="type",
            description="DNS type to look up.",
            option_type=3,
            required=False,
            choices=[create_choice(x, x) for x in DNS_TYPES]
        )
    ])
    async def dns_slash(self, ctx, fqdn=None, record_type=None):
        await self.dns("slash", ctx, fqdn, record_type)

    @commands.command(name="dns")
    async def dns_command(self, ctx, fqdn=None, record_type=None):
        await self.dns("default", ctx, fqdn, record_type)



def setup(bot):
    bot.add_cog(Util(bot))
