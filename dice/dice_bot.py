# main import for discord.py
import discord
from discord.ext import commands

# imports for other features
import os
from dotenv import load_dotenv
import random

################################################
#                     SETUP                    #
################################################

client = commands.Bot(command_prefix = '%')
@client.event
async def on_ready():
    print('Bot is ready to roll')

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

################################################
#                   COMMANDS                   #
################################################

@client.command(brief="Dice Roll Help")
async def commands(ctx):
    print("Commands:")
    command = "%dcommands prints Dice Roll instructions and commands\n \
    %droll chooses a random number from a default dice or size 6\n \
    more coming :)"
    await ctx.send(str(command)) #pog

@client.command(brief="Roles the dice!")
async def roll(ctx):
    # Default sides = 6
    number = random.randint(1,6)
    await ctx.send("Dice Result is: {}.".format(number))

@client.command(brief="Roles a n sided dice!")
async def rolln(ctx, n):
    # Sides will be n
    number = random.randint(1,int(n))
    await ctx.send("Dice Result is: {}.".format(number))

@client.command(brief="Tells you some Details! (Proof of Concept)")
async def details(ctx):
    guild = ctx.guild
    channel = ctx.channel
    author = ctx.author

    # to @ the author of the command, this is special markup
    response = f"<@{author.id}> \n"

    if guild != None: # when in DMs
        #stuff for guild
        response += "This server is:\n"
        response += f"Name: {guild.name}\n"
        response += f"ID: {guild.id}\n\n"

    if channel != None: # when the channel is None, possible DMs?
        response += "We are in Channel:\n"
        response += f"Name: {channel.name}\n"
        response += f"ID: {channel.id}\n\n"

    # generate rolls list
    rolelist = []
    for role in author.roles:
        if (role.name != "@everyone"):
            rolelist.append(role.name)
    
    rolestring = ", ".join(rolelist)

    response += "You are:\n"
    response += f"Name: {author.name}\n"
    response += f"Code: {author.discriminator}\n"
    response += f"ID: {author.id}\n"
    response += f"Nickname: {author.nick}\n"
    response += f"Roles: {rolestring}\n"

    await ctx.send(response)
    

################################################
#                     MAIN                     #
################################################

client.run(DISCORD_TOKEN)
