import logging

import os
from dotenv import load_dotenv

import discord
from discord.ext import commands
import asyncio

from youtubesearchpython.__future__ import VideosSearch
import youtube_dl

# Enable basic logging
logging.basicConfig(level=logging.INFO)

# Bot variables
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
BOT_PREFIX = "$"

# Bot initialisation
bot = commands.Bot(command_prefix=BOT_PREFIX)

# Stuff copy pasted from discord.py repo xd
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


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


@bot.command(brief="Searches YouTube for a video and plays the audio")
async def play(ctx, *words):
    search_terms = " ".join(words)
    video_search = VideosSearch(search_terms, limit = 1)
    video_result = await video_search.next()
    video_url = video_result["result"][0]["link"]

    voice_channel = ctx.author.voice.channel
    await voice_channel.connect()

    async with ctx.typing():
        player = await YTDLSource.from_url(video_url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f"Success! Now playing: {video_url}")


@bot.command(brief="Stops playing")
async def stop(ctx):
    await ctx.voice_client.disconnect()

    await ctx.send("Stopped playing.")


bot.run(BOT_TOKEN)
