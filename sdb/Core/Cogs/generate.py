import disnake
from disnake.ext import commands
from diffusers import StableDiffusionPipeline
import torch
from Core import make_collage, SDB
import io


class Generate(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot
        # TODO: make these configurable with a config file or slash command
        self.width = 512
        self.height = 512
        self.sample_steps = 50
        self.guidance_scale = 7
        self.images_per_promt = 1
        self.negtive_prompts = "(worst quality:1.4), (low quality:1.4), (monochrome:1.1)"
        self.model_id = "runwayml/stable-diffusion-v1-5"
        self.pipeline = StableDiffusionPipeline.from_pretrained(self.model_id, torch_dtype=torch.float16)
        self.pipeline.safety_checker = lambda images, clip_input: (images, False) # temporarily disable safety checker so we can manually run it later
        self.pipeline.to("cuda")


    # FIXME: when too many people use this command it will error out, because we cant defer fast enough since generating the image is blocking
    # if we dont defer 3 seconds after the command is sent discord will error out
    # could be fixed by using a queue system that is executed in the background on a worker thread
    @commands.slash_command(name="generate", description="generate a image using provided promts")
    async def Generate(self, interaction: disnake.CommandInteraction, prompt: str):
        await interaction.response.defer(ephemeral=False)
        images = self.pipeline(
            prompt,
            width=self.width,
            height=self.height,
            guidance_scale=self.guidance_scale,
            negative_prompt=self.negtive_prompts,
            num_inference_steps=self.sample_steps,
            num_images_per_prompt=self.images_per_promt,
        ).images
        
        if len(images) > 1:
            # TODO: dont hardcode this
            image = make_collage(images, 3, 3)
        else:
            image = images[0]


        with io.BytesIO() as image_binary:
            image.save(image_binary, 'PNG')
            image_binary.seek(0)
            await interaction.edit_original_response(file=disnake.File(fp=image_binary, filename=f"{interaction.id}.png"))
            

    @commands.command(name="generate")
    async def GenerateCTX(self, ctx: commands.Context):
        await ctx.reply(content=f"Use the slash command!")


def setup(bot: SDB):
    bot.add_cog(Generate(bot))
