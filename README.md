# Stable-Diffusion-Bot
![Example](./.github/assets/header.png)
<p align="center">
<image src="https://img.shields.io/github/license/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/issues/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/stars/ShyAssassin/Stable-Diffusion-Bot?style=social"/> 
</p>

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

### When i start the bot i get import errors
This is generally because you forgot to run `poetry install`, if you did run the install command and you are still encountering errors please [open a bug report!](https://github.com/ShyAssassin/Stable-Diffusion-Bot/issues/new)

### A black image is being output
A black image will be sent if the saftey checker has determined that the generated image contains unsafe elements, the saftey checker can be disabled in config.
