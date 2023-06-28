from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
from Core import SDB, Img2ImgConfig, make_collage
from disnake.ext import commands
from io import BytesIO
from PIL import Image
import requests
import disnake
import asyncio
import random
import torch
import math
import os

# -------------------------------------------------------------
# FIXME: This is nearly identical to text2img.py, refactor this
# Maybe make a base class for img2img and text2img?
# -------------------------------------------------------------


class Img2Img(commands.Cog):
    def __init__(self, bot: SDB):
        self.bot: SDB = bot
        self.config: Img2ImgConfig = bot.config.Img2Img
        self.pipelines: list[StableDiffusionImg2ImgPipeline] = []
        self.configure_pipelines()
        self.queue_size = 0

    def configure_pipelines(self):
        if self.config.enabled:
            for _ in range(self.config.batch_size):
                pipeline: StableDiffusionImg2ImgPipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                    pretrained_model_name_or_path=self.config.model.id,
                    torch_dtype=torch.float16,
                )  # type: ignore
                pipeline.safety_checker = None
                pipeline.scheduler = DPMSolverMultistepScheduler.from_config(pipeline.scheduler.config, use_karras_sigmas=False)
                pipeline.to(self.config.device)
                self.pipelines.append(pipeline)

    def generate_images(self, image, strength, prompt, negative_prompt, images, seed):
        try:
            pipeline = self.pipelines.pop()
            generator = torch.Generator(device=self.config.device).manual_seed(seed)
            images += pipeline(
                image=image,
                prompt=prompt,
                strength=strength,
                generator=generator,
                negative_prompt=negative_prompt,
                guidance_scale=self.config.guidance_scale,
                num_inference_steps=self.config.num_inference_steps,
                num_images_per_prompt=self.config.images_per_prompt,
            ).images  # type: ignore
            self.pipelines.append(pipeline)
            self.queue_size -= 1
        # On very very very rare occasions two threads will pop the same pipeline, and not throw an IndexError
        # This should never happen because list operations are atomic (doesnt release the GIL), but it does happen, WTF?
        except (RuntimeError, IndexError):
            return

    @commands.slash_command(name="img2img", description="Generate a image from a image")
    async def img2img(
        self,
        interaction: disnake.CommandInteraction,
        image: disnake.Attachment,
        strength: float = -1,
        prompt: str = "",
        negative_prompt: str = "",
        seed: int = -1,
    ):
        if not self.config.enabled:
            await interaction.response.defer(ephemeral=True)
            await interaction.edit_original_message(content="This command is currently disabled!")
            return

        await interaction.response.defer(ephemeral=False)

        # Im dumb, make sure the image is a png
        if image.content_type != "image/png" and image.content_type != "image/jpeg":
            await interaction.edit_original_message(content="Error: input must be an image!")
            return

        # stength must be between 0 and 1
        if strength == -1:
            strength = self.config.strength
        elif strength < 0 or strength > 1:
            await interaction.edit_original_message(
                content="Error: strength must be between 0 and 1, falling back to default value\nGenerating..."
            )
            strength = self.config.strength

        if self.config.base_prompts != []:
            prompt = f"{str(self.config.base_prompts)}, {prompt}"

        # there are base negative prompts, append user provided negative prompts
        if negative_prompt and self.config.negative_prompts:
            negative_prompt = f"{', '.join(self.config.negative_prompts)}, {negative_prompt}"
        elif self.config.negative_prompts:  # User didn't provide negative prompts, use base negative prompts
            negative_prompt = ", ".join(self.config.negative_prompts)

        if self.bot.config.banned_prompts != "":
            for banned_prompt in self.bot.config.banned_prompts:
                if banned_prompt in prompt.lower():
                    await interaction.edit_original_message(content=f"Error: banned prompt '{banned_prompt}' found in input")
                    return

        self.queue_size += 1
        response = requests.get(image.url)
        init_image = Image.open(BytesIO(response.content)).convert("RGB")
        if self.config.resize_images:
            init_image = init_image.resize((self.config.width, self.config.height))
        while True:
            if self.pipelines != []:
                if seed < 0:
                    seed = random.randint(0, 2**32)

                images = []
                await asyncio.to_thread(self.generate_images, init_image, strength, prompt, negative_prompt, images, seed)

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
            output_image = make_collage(images, rows, cols)
        else:
            output_image = images[0]

        if self.bot.config.save_images:
            os.makedirs(f"cache/{interaction.guild_id}", exist_ok=True)
            output_image.save(f"cache/{interaction.guild_id}/{interaction.id}.png")

        with BytesIO() as image_binary:
            output_image.save(image_binary, "PNG")
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
                            {"name": "Strength", "value": f"{strength}", "inline": True},
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
    bot.add_cog(Img2Img(bot))
