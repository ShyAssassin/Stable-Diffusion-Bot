import disnake
from disnake.ext import commands
from diffusers import StableDiffusionPipeline
import torch
from Core import make_collage, SDB
import math
import io
import os
import asyncio


class Text2Img(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot = bot
        self.base_config = self.bot.config
        self.config = self.base_config.DiffusionPipeline
        # config stuff
        self.model_id = self.config.current_model
        self.width = self.config.width
        self.height = self.config.height
        self.sample_steps = self.config.sample_steps
        self.batch_size = self.config.batch_size
        self.guidance_scale = self.config.guidance_scale
        self.images_per_prompt = self.config.images_per_prompt
        self.negative_prompts = ", ".join(self.config.negative_prompts)
        self.base_prompts = ", ".join(self.config.base_prompts)
        self.banned_prompts = self.config.banned_prompts
        # setup pipelines
        self.pipelines = []
        # god, forgive me for this
        self.queue_size = 0
        for _ in range(self.batch_size):
            pipeline = StableDiffusionPipeline.from_pretrained(self.model_id, torch_dtype=torch.float16)
            pipeline.safety_checker = self.safety_checker
            # we need to do this because it isn't possible to enable / disable the safety checker in the pipeline constructor
            pipeline.to(self.config.device)
            self.pipelines.append(pipeline)

    def generate_images(self, prompt, images):
        try:
            pipeline = self.pipelines.pop()
        except IndexError:
            return
        images += pipeline(
            prompt,
            width=self.width,
            height=self.height,
            guidance_scale=self.guidance_scale,
            negative_prompt=self.negative_prompts,
            num_inference_steps=self.sample_steps,
            num_images_per_prompt=self.images_per_prompt,
        ).images
        # after we are done with the pipeline we can add it back to the free pipelines
        self.pipelines.append(pipeline)
        self.queue_size -= 1

    def safety_checker(self, images, clip_input):
        # TODO: implement this
        if self.config.safety_checker:
            print("!!! Safety Checker is currently not implemented !!!")
        return images, False

    @commands.slash_command(name="generate", description="generate a image using provided prompts")
    async def Generate(self, interaction: disnake.CommandInteraction, prompt: str):
        await interaction.response.defer(ephemeral=False)
 
        if self.base_prompts != "":
            prompt = f"{self.base_prompts}, {prompt}"

        # search for banned prompts
        if self.banned_prompts != "":
            for banned_prompt in self.banned_prompts:
                if banned_prompt in prompt.lower():
                    await interaction.edit_original_message(content=f"Error: banned prompt '{banned_prompt}' found in input")
                    return

        self.queue_size += 1
        images = []
        while True:
            if self.pipelines != []:
                await interaction.edit_original_message(content="Generating...")
                # generate images in a asyncio thread so we don't block the event loop
                await asyncio.to_thread(self.generate_images, prompt, images)
                # sometimes two different threads can try to pop the same pipeline from the list
                # this can cause a index error, so we just try again
                if len(images) > 0:
                    break
            else:
                await interaction.edit_original_message(
                    content=f"Waiting for a free pipeline... (this can take a while)\nQueue size: {self.queue_size}"
                )
                await asyncio.sleep(5)

        if len(images) > 1:
            if self.config.stack_horizontally:
                cols = math.ceil(math.sqrt(len(images)))
                rows = math.ceil(len(images) / cols)
            else:
                rows = math.ceil(math.sqrt(len(images)))
                cols = math.ceil(len(images) / rows)
            image = make_collage(images, rows, cols)
        else:
            image = images[0]

        if self.base_config.save_images:
            os.makedirs(f"cache/{interaction.guild_id}", exist_ok=True)
            image.save(f"cache/{interaction.guild_id}/{interaction.id}.png")

        with io.BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            await interaction.edit_original_response(content="", file=disnake.File(fp=image_binary, filename=f"{interaction.id}.png"))

    @commands.command(name="generate")
    async def GenerateCTX(self, ctx: commands.Context):
        await ctx.reply(content="Use the slash command!")


def setup(bot: SDB):
    bot.add_cog(Text2Img(bot))
