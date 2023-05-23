import disnake
from disnake.ext import commands
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
import torch
import random
from Core import make_collage, SDB, Text2ImgConfig, SDBConfig
import math
import io
import os
import asyncio


class Text2Img(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot
        self.base_config: SDBConfig = self.bot.config
        self.config: Text2ImgConfig = self.base_config.Text2Img
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
        self.queue_size = 0
        print("Loading pipelines")
        for _ in range(self.batch_size):
            pipeline = StableDiffusionPipeline.from_pretrained(
                pretrained_model_name_or_path=self.model_id,
                torch_dtype=torch.float16,
                resume_download=True,
                custom_pipeline=self.config.custom_pipeline,
                custom_revision=self.config.custom_pipeline_revision,
            )
            pipeline.safety_checker = self.safety_checker
            # we set the scheduler to DPM++ because it is much faster and better than the default scheduler PNDM
            pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config, use_karras_sigmas=False)
            pipeline.to(self.config.device)
            self.pipelines.append(pipeline)

    def safety_checker(self, images, clip_input):
        # TODO: implement this
        if self.config.safety_checker:
            print("!!! Safety Checker is currently not implemented !!!")
        return images, False

    def generate_images(self, prompt, negative_prompt, images, seed):
        try:
            pipeline = self.pipelines.pop()
            generator = torch.Generator(device=self.config.device).manual_seed(seed)
            images += pipeline(
                prompt,
                generator=generator,
                width=self.width,
                height=self.height,
                guidance_scale=self.guidance_scale,
                negative_prompt=negative_prompt,
                num_inference_steps=self.sample_steps,
                num_images_per_prompt=self.images_per_prompt,
            ).images
            self.pipelines.append(pipeline)
            self.queue_size -= 1
        except IndexError:  # two threads tried to pop the same pipeline
            return

    @commands.slash_command(name="generate", description="generate a image using provided prompts")
    async def Generate(self, interaction: disnake.CommandInteraction, prompt: str, negative_prompt: str = None, seed: int = None):
        await interaction.response.defer(ephemeral=False)

        # if we have a base prompt we should add it to the provided prompt
        if self.base_prompts != "":
            prompt = f"{self.base_prompts}, {prompt}"

        # if the user provided negative prompts we should add them to the list of negative prompts
        # if the user didn't provide any negative prompts we should just use the default negative prompts
        if negative_prompt is not None and self.negative_prompts != "":
            negative_prompt = f"{self.negative_prompts}, {negative_prompt}"
        elif self.negative_prompts != "":
            negative_prompt = self.negative_prompts

        # search for banned prompts
        if self.banned_prompts != "":
            for banned_prompt in self.banned_prompts:
                if banned_prompt in prompt.lower():
                    await interaction.edit_original_message(content=f"Error: banned prompt '{banned_prompt}' found in input")
                    return

        self.queue_size += 1
        while True:
            if self.pipelines != []:
                await interaction.edit_original_message(content="Generating...")

                if seed is None:  # probably shouldn't regenerate the seed every time we fail to get a pipeline
                    seed = random.randint(0, 2**32)  # should we use 64 bit seeds?

                # generate images in a asyncio thread so we don't block the event loop
                images = []
                await asyncio.to_thread(self.generate_images, prompt, negative_prompt, images, seed)

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
            image_file = disnake.File(fp=image_binary, filename=f"{interaction.id}.png")
            if self.base_config.debug:
                embed = disnake.Embed.from_dict(
                    {
                        "title": "Debug Info",
                        "color": 0xFF00AA,
                        "timestamp": interaction.created_at.isoformat(),
                        "fields": [
                            {"name": "Model", "value": f"{self.model_id}", "inline": False},
                            {"name": "Seed", "value": f"{seed}", "inline": True},
                            {"name": "Sample Steps", "value": f"{self.sample_steps}", "inline": True},
                            {"name": "Guidance Scale", "value": f"{self.guidance_scale}", "inline": True},
                            {"name": "Batch Size", "value": f"{self.batch_size}", "inline": True},
                            {"name": "IPP", "value": f"{self.images_per_prompt}", "inline": True},
                            {"name": "Device", "value": f"{self.config.device}", "inline": True},
                            {"name": "Prompt", "value": f"{prompt}", "inline": False},
                            {"name": "Negative Prompt", "value": f"{negative_prompt}", "inline": False},
                        ],
                    }
                )
                embed.set_image(file=image_file)
                await interaction.edit_original_response(content="", embed=embed)
            else:
                await interaction.edit_original_response(content="", file=image_file)

    @commands.command(name="generate")
    async def GenerateCTX(self, ctx: commands.Context):
        await ctx.reply(content="Use the slash command!")


def setup(bot: SDB):
    bot.add_cog(Text2Img(bot))
