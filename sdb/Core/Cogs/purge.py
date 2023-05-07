import disnake
from disnake.ext import commands
from Core import SDB


# god this whole class is a mess but it works
# TODO: Clean this up, this entire thing was written in like 10 minutes at 2am
class Purge(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    def is_bot(self, message):
        return message.author == self.bot.user

    @commands.slash_command(name="purge", description="Purge a specified amount of messages from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def Purge(self, interaction: disnake.CommandInteraction, amount: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount)
        await interaction.edit_original_message(content=f"Purged {amount} messages from {interaction.channel.mention}")

    @commands.slash_command(name="purge-bot", description="Purge a specified amount of bot messages from the current channel")
    @commands.check_any(commands.is_owner(), commands.has_permissions(administrator=True, manage_messages=True))
    async def PurgeBot(self, interaction: disnake.CommandInteraction, amount: int):
        await interaction.response.defer(ephemeral=True)
        await interaction.channel.purge(limit=amount, check=self.is_bot)
        await interaction.edit_original_message(content=f"Purged {amount} messages from {interaction.channel.mention}")

    @commands.command(name="purge")
    async def PurgeCTX(self, ctx: commands.Context):
        await ctx.reply(content=f"Use the slash command!")


def setup(bot: SDB):
    bot.add_cog(Purge(bot))
