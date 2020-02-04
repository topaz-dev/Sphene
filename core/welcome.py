import discord
from discord.ext import commands
from discord.ext.commands import bot

from core import roles
from database import SQLite as sql


async def memberjoin(member, channel):
    ID = member.guild.id
    wmsg = sql.valueAtNumber(ID, "WelcomeMsg", "Guild")
    wrole = sql.valueAtNumber(ID, "WelcomeRole", "Guild")
    msg = ""
    # print(wmsg)
    # print(wrole)
    if wmsg == 0 or wmsg == None:
        msg = "Bienvenue {} sur {}".format(member.mention, member.guild.name)
    else:
        wmsg = wmsg.replace("{mention}", str(member.mention))
        wmsg = wmsg.replace("{name}", str(member.name))
        wmsg = wmsg.replace("{id}", str(member.id))
        wmsg = wmsg.replace("{guild}", str(member.guild.name))
        wmsg = wmsg.replace("{IDguild}", str(member.guild.id))
        wmsg = wmsg.replace("\\n", "\n")
        msg = wmsg
    if wrole != 0 and wrole != None:
        try:
            await roles.addrole(member, wrole)
        except:
            await roles.createrole(member, wrole)
            await roles.addrole(member, wrole)
    print("Welcome >> {} a rejoint le serveur {}".format(member.name, member.guild.name))
    await channel.send(msg)


def memberremove(member):
    ID = member.guild.id
    qmsg = sql.valueAtNumber(ID, "QuitMsg", "Guild")
    # print(qmsg)
    if qmsg == 0 or qmsg == None:
        msg = "**{0}** nous a quitté, pourtant si jeune...".format(member.name)
    else:
        msg = qmsg
    print("Welcome >> {} a quitté le serveur {}".format(member.name, member.guild.name))
    return msg


class Welcome(commands.Cog):

    def __init__(self, ctx):
        return(None)


def setup(bot):
    bot.add_cog(Welcome(bot))
    open("help/cogs.txt", "a").write("Welcome\n")
