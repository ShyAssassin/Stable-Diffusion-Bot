# Stable-Diffusion-Bot
![Example](./.github/assets/header.png)
<p align="center">
<image src="https://img.shields.io/github/license/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/issues/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/stars/ShyAssassin/Stable-Diffusion-Bot?style=social"/> 
</p>

## Features
* Text to Image generation
* Image to Image generation
* Runtime Model Switching
* Runtime Config Modification
* Multithreaded parallel image generation with queue system
* Config options to limit and moderate user generated content
* Slash commands with a lot of optional parameters to guide image generation

## Installation

### Prerequisites
* Python 3.10 or above
* Cuda 11.7 or above
* [poetry](https://python-poetry.org/)

```bash
git clone https://github.com/ShyAssassin/Stable-Diffusion-Bot.git
cd Stable-Diffusion-Bot
cp .env.example .env
poetry install
```
>**Note**: Make sure you fill out the .env file!

### Running
after completing the installation steps and editing the .env file to add you discord bot token, open a new terminal in the bot's root directory and run `poetry run python sdb/main.py` 

## Troubleshooting

### Nothing is generated but my GPU is at 100%
This is generally because you are generating too many images at once, try turning down `batch_size` and `images_per_prompt` in the config file.

### The Generated image does not look good
If the Generated image does not look good try adjusting the provided prompts and negative prompts or the `guidance_scale` / `sample_steps` in the config. if you are still not happy you can use a custom model by change `current_model` in the config.

### Generated Images look corrupted
If the Generated Images looks corrupted this is generally because you have too many or too few `sample_steps`, try messing around with the amount of `sample_steps` until the images look clear again.

### The Generated image contains "mutated" elements
If The Generated image contains mutated elements (extra arms, too many fingers, long necks, etc...) try adjusting the negative prompts provided or add base `negative_prompts` in the config.

### The Img2Img output image looks nothing like the input
This is expected because Img2Img uses the provided input image as a "base" for further generation [Read This for more info.](https://arxiv.org/pdf/2108.01073.pdf)      
Try adjusting the `stength` paramater provided when using the command or edit the base strength in the config. The higher the `strength` the more the "creative" the AI gets.

### When i start the bot i get import errors
This is generally because you forgot to run `poetry install`, if you did run the install command and you are still encountering errors please [open a bug report!](https://github.com/ShyAssassin/Stable-Diffusion-Bot/issues/new)

### A black image is being output
A black image will be sent if the saftey checker has determined that the generated image contains unsafe elements, the saftey checker can be disabled in config.
