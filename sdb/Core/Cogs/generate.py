import disnake
from disnake.ext import commands
from Core import SDB
from Core.Cogs import *


# This COG just provides a common interface for all of the generative commands
# all of the actual commands are still accessible from their respective COGS
class Generate(commands.Cog):
    # we cant get the COGS in the constructor because they might not be loaded yet
    def __init__(self, bot: SDB):
        self.bot: SDB = bot

    @commands.slash_command(name="generate", description="Generate a image")
    async def Generate(self, interaction: disnake.CommandInteraction):
        pass

    @Generate.sub_command(name="text2img", description="Generate a image from a image")
    async def text2img(self, interaction: disnake.CommandInteraction, prompt: str, negative_prompt: str = "", seed: int = -1, width = 512, height = 512):
        try:
            cog: Text2Img = self.bot.get_cog("Text2Img")  # type: ignore
            await cog.text2img(interaction=interaction, prompt=prompt, negative_prompt=negative_prompt, seed=seed, width=width, height=height)
        except AttributeError:
            await interaction.response.defer(ephemeral=True)
            await interaction.response.send_message("This command is not available right now", ephemeral=True)
            print("Text2Img COG is not loaded")

    @Generate.sub_command(name="img2img", description="Generate a image from a image")
    async def img2img(
        self,
        interaction: disnake.CommandInteraction,
        image: disnake.Attachment,
        strength: float = -1,
        prompt: str = "",
        negative_prompt: str = "",
        seed: int = -1,
    ):
        try:
            cog: Img2Img = self.bot.get_cog("Img2Img")  # type: ignore
            await cog.img2img(
                interaction=interaction, image=image, strength=strength, prompt=prompt, negative_prompt=negative_prompt, seed=seed
            )
        except AttributeError:
            await interaction.response.defer(ephemeral=True)
            await interaction.response.send_message("This command is not available right now", ephemeral=True)
            print("Img2Img COG is not loaded")


def setup(bot: SDB):
    bot.add_cog(Generate(bot))
