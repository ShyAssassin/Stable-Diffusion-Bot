import disnake
from disnake.ext import commands
from Core import SDB


class Config(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    @commands.slash_command(name="config", description="Send the current config")
    @commands.check_any(commands.is_owner())  # type: ignore
    async def Config(self, interaction: disnake.CommandInteraction):
        await interaction.response.defer(ephemeral=True)
        await interaction.edit_original_message(content=f"```json\n{self.bot.config.json(indent=4)}```")


def setup(bot: SDB):
    bot.add_cog(Config(bot))
