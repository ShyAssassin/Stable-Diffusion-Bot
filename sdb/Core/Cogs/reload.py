import disnake
import os
from disnake.ext import commands
from Core import SDB


class Reload(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    @commands.slash_command(name="reload", description="reload all pipelines with the current config")
    @commands.check_any(commands.is_owner())  # should probably add a config option for trusted users / admins to use this
    async def Reload(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=False)
        await interaction.edit_original_message(content="Reloading pipelines, this may take a while...")
        # update config with the latest changes
        self.bot.config.load()
        # reload all cogs, this will regenerate all pipelines
        for cog in os.listdir(self.bot.CogPath):
            if not cog.startswith("_") and cog.endswith(".py") and cog != "reload.py":
                CurrentCogPath = str(os.path.join(self.bot.CogPath, cog))
                CurrentCogModule = CurrentCogPath.replace(os.path.sep, ".")[:-3]
                print(f"Reloading Extension: sdb.{CurrentCogModule}")
                self.bot.reload_extension(CurrentCogModule)
        await interaction.edit_original_message(content="All pipelines have been reloaded!")
        print("All pipelines have been reloaded!")

    @commands.command(name="reload")
    async def ReloadCTX(self, ctx: commands.Context):
        await ctx.reply(content="This is a Template")  # reply, send


def setup(bot: SDB):
    bot.add_cog(Reload(bot))
