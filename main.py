import os
import discord
import dotenv
import logging.config

from logging_config import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()
bot.load_extension(name='app.cogs.leaderboard')
bot.load_extension(name='app.cogs.head2head')

# we need to limit the guilds for testing purposes
# so other users wouldn't see the command that we're testing

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")

bot.run(DISCORD_TOKEN)