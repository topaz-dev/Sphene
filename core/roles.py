import discord
from discord.ext import commands
from discord.ext.commands import bot
from discord.utils import get

async def addrole(member, role):
	setrole = get(member.guild.roles, name=role)
	await member.add_roles(setrole)

async def removerole(member, role):
	setrole = get(member.guild.roles, name=role)
	await member.remove_roles(setrole)

async def createrole(member, role):
	guild = member.guild
	await guild.create_role(name=role)
