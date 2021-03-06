import discord
from discord.ext import commands
from discord.ext.commands import bot
from languages import lang
from database import SQLite as sql

client = discord.Client()
VERSION = open("core/version.txt").read().replace("\n", "")


class Utils(commands.Cog):

    def __init__(self, ctx):
        return(None)

    @commands.command(pass_context=True)
    async def version(self, ctx):
            """0"""
            langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
            msg = lang.forge_msg(langue, "Utils", [VERSION], False, 0)
            await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def site(self, ctx):
            """1"""
            langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
            msg = lang.forge_msg(langue, "Utils", ["http://sphene.topazdev.fr/"], False, 1)
            await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def ping(self, ctx):
            """2"""
            msg = "**PONG**."
            await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def github(self, ctx):
            """3"""
            langue = sql.valueAtNumber(ctx.guild.id, "Lang", "Guild")
            msg = lang.forge_msg(langue, "Utils", ["https://github.com/topaz-dev/Sphene"], False, 2)
            await ctx.channel.send(msg)


def setup(bot):
    bot.add_cog(Utils(bot))
    open("help/cogs.txt", "a").write("Utils\n")
