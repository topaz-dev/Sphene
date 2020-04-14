import discord
from discord.ext import commands
from discord.ext.commands import bot

from core import roles, gestion as ge
from database import SQLite as sql
from languages import lang


async def memberjoin(member, channel):
    ID = member.guild.id
    param = sql.valueAtNumber(ID, "Param_WelcomeMsg", "Guild")
    # print(wmsg)
    # print(wrole)
    if param != 0 and param != None:
        langue = sql.valueAtNumber(ID, "Lang", "Guild")
        wmsg = sql.valueAtNumber(ID, "WelcomeMsg", "Guild")
        wrole = sql.valueAtNumber(ID, "WelcomeRole", "Guild")
        if wmsg == 0 or wmsg == None:
            msg = lang.forge_msg(langue, "DefaultMsg", [member.mention, member.guild.name], False, 0)
        else:
            msg = ge.MEFI(wmsg, member)
        if wrole != 0 and wrole != None:
            try:
                await roles.addrole(member, wrole)
            except:
                await roles.createrole(member, wrole)
                await roles.addrole(member, wrole)
        print("Welcome >> {0} a rejoint le serveur {1}".format(member.name, member.guild.name))
        await channel.send(msg)


def memberremove(member):
    ID = member.guild.id
    param = sql.valueAtNumber(ID, "Param_QuitMsg", "Guild")
    # print(qmsg)
    if param != 0 and param != None:
        langue = sql.valueAtNumber(ID, "Lang", "Guild")
        qmsg = sql.valueAtNumber(ID, "QuitMsg", "Guild")
        if qmsg == 0 or qmsg == None:
            msg = "**{0}** nous a quitté, pourtant si jeune...".format(member.name)
            msg = lang.forge_msg(langue, "DefaultMsg", [member.name], False, 1)
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
