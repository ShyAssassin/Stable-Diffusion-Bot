import disnake
from disnake.ext import commands
from diffusers import StableDiffusionPipeline
import torch
import io
from Core import SDB


class Generate(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot
        self.width = 512
        self.height = 512
        self.sample_steps = 50
        self.guidance_scale = 7
        self.images_per_promt = 1
        self.negtive_prompts = "(worst quality:1.4), (low quality:1.4), (monochrome:1.1)"
        self.model_id = "andite/anything-v4.0"
        self.pipeline = StableDiffusionPipeline.from_pretrained(self.model_id, torch_dtype=torch.float16)
        self.pipeline.safety_checker = lambda images, clip_input: (images, False)
        self.pipeline.to("cuda")


    @commands.slash_command(name="generate", description="generate a image using provided promts")
    async def Template(self, interaction: disnake.CommandInteraction, prompt: str):
        await interaction.response.defer(ephemeral=False)
        image = self.pipeline(
            prompt,
            # self.guidance_scale,
            width=self.width,
            height=self.height,
            negative_prompt=self.negtive_prompts,
            num_inference_steps=self.sample_steps,
            num_images_per_prompt=self.images_per_promt,
        ).images
        image[0].save("temp.png", format="PNG")
        await interaction.edit_original_message(files=[disnake.File("temp.png", filename="image.png")])

    @commands.command(name="generate")
    async def TemplateCTX(self, ctx: commands.Context):
        await ctx.reply(content=f"This is a Template")  # reply, send


def setup(bot: SDB):
    bot.add_cog(Generate(bot))
