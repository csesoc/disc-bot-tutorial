import discord
from discord.ext import commands

import asyncio
import youtube_dl
import validators
from youtubesearchpython.__future__ import VideosSearch

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''


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


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(brief="Joins a voice channel")
    async def join(self, ctx):
        await Music.ensure_voice(self, ctx)

    @commands.command(brief="Plays a video from YouTube search or URL")
    async def play(self, ctx, *, search_terms):
        if validators.url(search_terms):
            video_url = search_terms
            return await Music.playurl(self, ctx, video_url)

        videos_search = VideosSearch(search_terms, limit=10)
        videos_result = await videos_search.next()

        search_results = discord.Embed(title=f"🔎  {search_terms}")

        search_results.set_author(
            name="Search Results",
            icon_url="https://i.imgur.com/eRu4yM8.png")

        description = ""
        for idx, result in enumerate(videos_result['result']):
            description += f"`{idx}.` **[{result['title']}]({result['link']}) [{result['duration']}]**\n"
            description += f"{result['viewCount']['short']} | {result['publishedTime']}\n\n"

        search_results.description = description
        search_results.set_footer(text="Please type in a number to select a video")

        await ctx.send(embed=search_results)

        selection = await self.bot.wait_for("message", timeout=60.0)
        selection_num = int(selection.content)
        video_url = videos_result['result'][selection_num]['link']

        await Music.playurl(self, ctx, video_url)

    @commands.command(brief="Changes the volume")
    async def volume(self, ctx, volume: int=None):
        if volume is None:
            return await ctx.send(f"Current volume is {round(ctx.voice_client.source.volume * 100)}%")

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        elif ctx.voice_client.source is None:
            return await ctx.send("Not currently playing.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command(brief="Stops playing and disconnects the bot from voice")
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

        await ctx.send("Stopped playing.")

    async def playurl(self, ctx, url):
        await Music.ensure_voice(self, ctx)

        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f"Success! Now playing: {url}")

    async def ensure_voice(self, ctx):
        if ctx.author.voice:
            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.voice_client.move_to(ctx.author.voice.channel)
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
        else:
            await ctx.send("You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")


def setup(bot):
    bot.add_cog(Music(bot))
