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
intents = discord.Intents.default()

# Bot initialisation
bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

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


# Not actually sure why this is necessary
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


@bot.command(brief="Searches YouTube and allows you to select a video to play")
async def play(ctx, *, search_terms):
    videos_search = VideosSearch(search_terms, limit=10)
    videos_result = await videos_search.next()

    search_results = discord.Embed(title="Search Results")

    description = ""
    for idx, result in enumerate(videos_result['result']):
        description += f"`{idx}.` **[{result['title']}]({result['link']}) [{result['duration']}]**\n"
        description += f"{result['viewCount']['short']} | {result['publishedTime']}\n\n"

    search_results.description = description

    await ctx.send(embed=search_results)
    await ctx.send("Please type in a number to select a video.")

    selection = await bot.wait_for("message", timeout=60.0)
    selection_num = int(selection.content)
    video_url = videos_result['result'][selection_num]['link']

    # Not sure why the before_invoke doesn't do this automatically
    await ensure_voice(ctx)
    await ctx.invoke(bot.get_command("playurl"), url=video_url)


@bot.command(brief="Plays a video from a URL")
async def playurl(ctx, url):
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

    await ctx.send(f"Success! Now playing: {url}")


@bot.command(brief="Changes the player volume")
async def volume(ctx, volume: int):
    if ctx.voice_client is None:
        return await ctx.send("Not connected to a voice channel.")

    ctx.voice_client.source.volume = volume / 100
    await ctx.send(f"Changed volume to {volume}%")


@bot.command(brief="Stops playing")
async def stop(ctx):
    await ctx.voice_client.disconnect()

    await ctx.send("Stopped playing.")


@playurl.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()


bot.run(BOT_TOKEN)
