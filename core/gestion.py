import discord
from discord.ext import commands
from discord.ext.commands import Bot

PREFIX = open("core/prefix.txt", "r").read().replace("\n", "")
client = Bot(command_prefix = "{0}".format(PREFIX))

rolesID = [[417451897729843223], [417451897729843223, 417451604141277185], [417451897729843223, 417451604141277185, 423606460908306433]]
guildID = [690939984399827024, 417445502641111051, 129364058901053440] # Get Gems | Bastion | TopazDev


def permission(ctx):
    roles = ctx.author.roles
    for role in roles :
        if ctx.guild.id in guildID and role.permissions.administrator:
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

    @commands.command(pass_context=True)
    async def show_perm(self, ctx):
        """Montre les permissions et leur valeurs"""
        msg = "Voici tes roles :```"
        roles = ctx.author.roles
        for role in roles:
            msg += "~ {} à pour valeur :{}\n".format(role.name, role.permissions.value)
        msg += "```"
        await ctx.channel.send(msg)

    @commands.command(pass_context=True)
    async def supp(self, ctx, nb):
        """**[nombre]** | Supprime [nombre] de message dans le channel """
        suppMax = 40
        if permission(ctx):
            try :
                nb = int(nb)
                if nb <= suppMax :
                    await ctx.channel.purge(limit =nb)
                    msg = '{0} messages on été éffacé !'.format(nb)
                else:
                    msg = "On ne peut pas supprimer plus de {} messages à la fois".format(suppMax)
            except ValueError:
                msg = "Commande mal remplis"
        else :
            msg = "Tu ne remplis pas les conditions"
        await ctx.channel.send(msg)


def setup(bot):
    bot.add_cog(Gestion(bot))
    open("help/cogs.txt", "a").write("Gestion\n")
