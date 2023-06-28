from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from Core import make_collage, SDB, Text2ImgConfig
from disnake.ext import commands
import asyncio
import disnake
import random
import torch
import math
import io
import os


class Text2Img(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot
        self.config: Text2ImgConfig = self.bot.config.Text2Img
        self.pipelines: list[StableDiffusionPipeline] = []
        self.configure_pipelines()
        self.queue_size = 0

    def configure_pipelines(self):
        if self.config.enabled:
            for _ in range(self.config.batch_size):
                pipeline: StableDiffusionPipeline = StableDiffusionPipeline.from_pretrained(
                    pretrained_model_name_or_path=self.config.model.id,
                    torch_dtype=torch.float16,
                    custom_pipeline=self.config.custom_pipeline,
                    custom_revision=self.config.custom_pipeline_revision,
                )  # type: ignore
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

    def generate_images(self, prompt, negative_prompt, images, seed, width, height, num_inference_steps):
        try:
            pipeline = self.pipelines.pop()
            generator = torch.Generator(device=self.config.device).manual_seed(seed)
            images += pipeline(
                prompt=prompt,
                generator=generator,
                width=width,
                height=height,
                negative_prompt=negative_prompt,
                guidance_scale=self.config.guidance_scale,
                num_inference_steps=num_inference_steps,
                num_images_per_prompt=self.config.images_per_prompt,
            ).images  # type: ignore
            self.pipelines.append(pipeline)
            self.queue_size -= 1
        # On very very very rare occasions two threads will pop the same pipeline, and not throw a IndexError
        # This should never happen because list operations are atomic (doesnt release the GIL), but it does happen, WTF?
        except (RuntimeError, IndexError):
            return

    @commands.slash_command(name="text2img", description="Generate a image using provided prompts")
    async def text2img(
        self,
        interaction: disnake.CommandInteraction,
        prompt: str,
        negative_prompt: str = "",
        seed: int = -1,
        width: int = 512,
        height: int = 512,
        num_inference_steps: int = 50,
    ):
        if not self.config.enabled:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_message(content="This command is currently disabled!")
            return

        await interaction.response.defer(ephemeral=False)

        # if we have a base prompt we should add it to the provided prompt
        if self.config.base_prompts != []:
            prompt = f"{str(self.config.base_prompts)}, {prompt}"

        # there are base negative prompts, append user provided negative prompts
        if negative_prompt and self.config.negative_prompts:
            negative_prompt = f"{', '.join(self.config.negative_prompts)}, {negative_prompt}"
        elif self.config.negative_prompts:  # User didn't provide negative prompts, use base negative prompts
            negative_prompt = ", ".join(self.config.negative_prompts)

        # search for banned prompts
        if self.bot.config.banned_prompts != "":
            for banned_prompt in self.bot.config.banned_prompts:
                if banned_prompt in prompt.lower():
                    await interaction.edit_original_message(content=f"Error: banned prompt '{banned_prompt}' found in input")
                    return

        self.queue_size += 1
        while True:
            if self.pipelines != []:
                if seed < 0:
                    seed = random.randint(0, 2**32)  # should we use 64 bit seeds?

                # generate images in a asyncio thread so we don't block the event loop
                images = []
                await asyncio.to_thread(self.generate_images, prompt, negative_prompt, images, seed, width, height, num_inference_steps)

                # no images were generated, try again
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

        if self.bot.config.save_images:
            os.makedirs(f"cache/{interaction.guild_id}", exist_ok=True)
            image.save(f"cache/{interaction.guild_id}/{interaction.id}.png")

        with io.BytesIO() as image_binary:
            image.save(image_binary, "PNG")
            image_binary.seek(0)
            image_file = disnake.File(fp=image_binary, filename=f"{interaction.id}.png")
            if self.bot.config.debug:
                embed = disnake.Embed.from_dict(
                    {
                        "title": "Debug Info",
                        "color": 0xFF00AA,
                        "timestamp": interaction.created_at.isoformat(),
                        "fields": [
                            {"name": "Model", "value": f"{self.config.model.name}", "inline": False},
                            {"name": "Seed", "value": f"{seed}", "inline": True},
                            {"name": "Sample Steps", "value": f"{num_inference_steps}", "inline": True},
                            {"name": "Guidance Scale", "value": f"{self.config.guidance_scale}", "inline": True},
                            {"name": "Batch Size", "value": f"{self.config.batch_size}", "inline": True},
                            {"name": "IPP", "value": f"{self.config.images_per_prompt}", "inline": True},
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


def setup(bot: SDB):
    bot.add_cog(Text2Img(bot))
