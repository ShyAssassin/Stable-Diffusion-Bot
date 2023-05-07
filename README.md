# Stable-Diffusion-Bot
![Example](./.github/assets/header.png)
<center>
<image src="https://img.shields.io/github/license/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/issues/ShyAssassin/Stable-Diffusion-Bot"/> 
<image src="https://img.shields.io/github/stars/ShyAssassin/Stable-Diffusion-Bot?style=social"/> 
</center>

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

## running
after completing the installation steps edit the .env file and add you discord bot token after that run `poetry run python sdb/main.py` to start the bot.
