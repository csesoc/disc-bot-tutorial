import discord
from discord.ext import commands

import logging
import os
import yaml
from dotenv import load_dotenv

# Enable basic logging
logging.basicConfig(level=logging.INFO)

# Load settings file and set variables
with open('./config/settings.yml') as file:
    settings = yaml.full_load(file)

BOT_PREFIX = settings['prefix']

# Set token
if settings['token_env_enabled']:
    load_dotenv()
    BOT_TOKEN = os.getenv(settings['token_env_key'])
else:
    BOT_TOKEN = settings['token']

# TODO: Move this to config file
intents = discord.Intents.default()

# Initialise bot
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Load extensions
if __name__ == "__main__":
    for extension in settings['enabled_extensions']:
        bot.load_extension(f"extensions.{extension}")


# Bot startup messages
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(f"with Python | {BOT_PREFIX}help"))

    logging.info("---------------------------------------------")
    logging.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logging.info("Loaded extensions:")
    for extension in bot.extensions:
        logging.info(f"- {extension}")
    logging.info("Connected to the following guilds:")
    for guild in bot.guilds:
        logging.info(f"- {guild.name} (ID: {guild.id})")
    logging.info("---------------------------------------------")


@bot.command(brief="Changes the command prefix")
@commands.is_owner()
async def prefix(ctx, prefix):
    bot.command_prefix = prefix

    settings['prefix'] = prefix
    save_settings()

    await ctx.send(f"Prefix set to `{prefix}`")


def save_settings():
    with open('./config/settings.yml', 'w') as file:
        yaml.dump(settings, file)


bot.run(BOT_TOKEN)
