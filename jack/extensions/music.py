import discord
from discord.ext import commands

import asyncio
import youtube_dl
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

    @commands.command(brief="Searches YouTube for a video to play")
    async def play(self, ctx, *, search_terms):
        videos_search = VideosSearch(search_terms, limit=10)
        videos_result = await videos_search.next()

        search_results = discord.Embed(title="Search Results")

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

        # Not sure why the before_invoke doesn't do this automatically
        await Music.ensure_voice(self, ctx)
        await ctx.invoke(self.bot.get_command("playurl"), url=video_url)

    @commands.command(brief="Plays a video from a URL")
    async def playurl(self, ctx, url):
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)

        await ctx.send(f"Success! Now playing: {url}")

    @commands.command(brief="Changes the player volume")
    async def volume(self, ctx, volume: int):
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        ctx.voice_client.source.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")

    @commands.command(brief="Stops playing")
    async def stop(self, ctx):
        await ctx.voice_client.disconnect()

        await ctx.send("Stopped playing.")

    @playurl.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Music(bot))
