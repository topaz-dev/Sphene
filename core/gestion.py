import discord
from discord.ext import commands
from discord.ext.commands import Bot

PREFIX = open("core/prefix.txt", "r").read().replace("\n", "")
client = Bot(command_prefix = "{0}".format(PREFIX))

rolesID = [[417451897729843223], [417451897729843223, 417451604141277185], [417451897729843223, 417451604141277185, 423606460908306433]]
guildID = [634317171496976395, 417445502641111051, 640507787494948865, 478003352551030796, 129364058901053440] # Get Gems | Bastion | Bastion Twitch | Test | TopazDev


def permission(ctx):
    roles = ctx.author.roles
    for role in roles :
        if ctx.guild.id in guildID and role.permissions.administrator:
            return True
    return False


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
