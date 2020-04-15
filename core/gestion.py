import discord
from discord.ext import commands
from discord.ext.commands import Bot
from database import SQLite as sql
from languages import lang

PREFIX = open("core/prefix.txt", "r").read().replace("\n", "")
client = Bot(command_prefix = "{0}".format(PREFIX))


def permission(ctx):
    roles = ctx.author.roles
    for role in roles :
        if role.permissions.administrator:
            return True
    return False


def MEFI(msg, member):
    msg = MEF(msg, "{mention}", str(member.mention))
    msg = MEF(msg, "{name}", str(member.name))
    msg = MEF(msg, "{id}", str(member.id))
    msg = MEF(msg, "{guild}", str(member.guild.name))
    msg = MEF(msg, "{IDguild}", str(member.guild.id))
    msg = MEF(msg, "{everyone}", "@everyone")
    msg = MEF(msg, "{here}", "@here")
    msg = MEF(msg, "\\n", "\n")
    return msg


def MEF(msg, source, destination):
    if type(msg) is dict:
        for k in msg.keys():
            if type(msg[k]) is str:
                msg[k] = msg[k].replace(source, destination)
            else:
                MEF(msg[k], source, destination)
    elif type(msg) is list:
        for x in range(0, len(msg)):
            if type(msg[x]) is str:
                msg[x] = msg[x].replace(source, destination)
            else:
                MEF(msg[x], source, destination)
    elif type(msg) is int:
        pass
    else:
        msg = msg.replace(source, destination)
    return msg


class Gestion(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        return

    # @commands.command(pass_context=True)
    # async def show_perm(self, ctx):
    #     """0"""
    #     msg = "Voici tes roles :```"
    #     roles = ctx.author.roles
    #     for role in roles:
    #         msg += "~ {} à pour valeur :{}\n".format(role.name, role.permissions.value)
    #     msg += "```"
    #     await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def supp(self, ctx, nb):
        """1"""
        ID = ctx.guild.id
        langue = sql.valueAtNumber(ID, "Lang", "Guild")
        suppMax = 40
        if permission(ctx):
            try :
                nb = int(nb)
                if nb <= suppMax :
                    await ctx.channel.purge(limit =nb)
                    msg = lang.forge_msg(langue, "Gestion", [nb], False, 0)
                else:
                    msg = lang.forge_msg(langue, "Gestion", [suppMax], False, 0)
            except ValueError:
                msg = lang.forge_msg(langue, "WarningMsg", None, False, 2)
        else :
            msg = lang.forge_msg(langue, "WarningMsg", None, False, 1)
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def lang(self, ctx, change_lang = None):
        """2"""
        ID = ctx.guild.id
        langue = sql.valueAtNumber(ID, "Lang", "Guild")
        if permission(ctx):
            langlist = ["EN", "FR"]
            change_lang = change_lang.upper()

            if change_lang == "NONE":
                msg = lang.forge_msg(langue, "lang", None, False, 2)
            else:
                if change_lang in langlist:
                    msg = lang.forge_msg(change_lang, "lang", None, False, 0)
                else:
                    msg = lang.forge_msg(langue, "lang", None, False, 1)
        else :
            msg = lang.forge_msg(langue, "WarningMsg", None, False, 1)
        await ctx.channel.send(msg)


def setup(bot):
    bot.add_cog(Gestion(bot))
    open("help/cogs.txt", "a").write("Gestion\n")
