import discord
from discord.ext import commands

import logging
import os
from dotenv import load_dotenv

# Enable basic logging
logging.basicConfig(level=logging.INFO)

# Set variables
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = "$"
intents = discord.Intents.default()

# Specify extensions
enabled_extensions = ["music"]

# Initialise bot
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)


if __name__ == "__main__":
    for extension in enabled_extensions:
        bot.load_extension(f"extensions.{extension}")


# Bot startup messages
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(f"with Python | {BOT_PREFIX}help"))
    logging.info("---------------------------------------------")
    logging.info(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    logging.info("Connected to the following guilds:")
    for guild in bot.guilds:
        logging.info(f"{guild.name} (ID: {guild.id})")
    logging.info("---------------------------------------------")


bot.run(BOT_TOKEN)
