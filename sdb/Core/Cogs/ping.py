import disnake
from disnake.ext import commands
from Core import SDB


class Ping(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    @commands.slash_command(name="ping", description="Get the bot's current latency")
    async def Ping(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_message(content=f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.command(name="ping")
    async def PingCTX(self, ctx: commands.Context):
        await ctx.reply(f"Pong! {round(self.bot.latency * 1000)}ms")


def setup(bot: SDB):
    bot.add_cog(Ping(bot))
