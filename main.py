import discord
from discord.ext import commands
from discord.ext.commands import Bot
import datetime as dt
from datetime import datetime

from database import SQLite as sql
from core import welcome as wel

# initialisation des variables.
DEFAUT_PREFIX = "!"

VERSION = open("core/version.txt").read().replace("\n", "")
TOKEN = open("token/token.txt", "r").read().replace("\n", "")
PREFIX = open("core/prefix.txt", "r").read().replace("\n", "")
client = commands.Bot(command_prefix = "{0}".format(PREFIX))
NONE = open("help/cogs.txt", "w")
NONE = open("help/help.txt", "w")

jour = dt.date.today()

#####################################################

client.remove_command("help")

# Au démarrage du Bot.
@client.event
async def on_ready():
    print('Connecté avec le nom : {c.user}'.format(c=client))
    print('PREFIX = {p}\n\nSPHENE {v}\n'.format(p=PREFIX, v=VERSION))
    print(sql.init())
    flag = sql.checkField()
    if flag == 0:
        print("SQL >> Aucun champ n'a été ajouté, supprimé ou modifié.")
    elif "add" in flag:
        print("SQL >> Un ou plusieurs champs ont été ajoutés à la DB.")
    elif "sup" in flag:
        print("SQL >> Un ou plusieurs champs ont été supprimés de la DB.")
    elif "type" in flag:
        print("SQL >> Un ou plusieurs type ont été modifié sur la DB.")
    print('------\n')

####################### Commande help.py #######################

client.load_extension('help.help')

################### Core ############################

client.load_extension('core.utils')


################### Welcome #################################

@client.event
async def on_guild_join(guild):
    if guild.system_channel != None:
        systemchannel = guild.system_channel
    else:
        systemchannel = 0
    sql.new(guild.id, "Guild")
    await systemchannel.send('Bonjour {}!'.format(guild.name))


@client.event
async def on_member_join(member):
    guild = client.get_guild(member.guild.id)
    if guild.system_channel != None:
        systemchannel = guild.system_channel
    else:
        systemchannel = 0
    await wel.memberjoin(member, systemchannel)


@client.event
async def on_member_remove(member):
    guild = client.get_guild(member.guild.id)
    if guild.system_channel != None:
        systemchannel = guild.system_channel
    else:
        systemchannel = 0
    await systemchannel.send(wel.memberremove(member))

###################### Commande gestion.py #####################

client.load_extension('core.gestion')

####################### Lancemement du bot ######################

client.run(TOKEN)
