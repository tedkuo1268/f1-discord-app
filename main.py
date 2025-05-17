import os
import discord
import dotenv
import logging.config

import logging
from logging_config import LOGGING_CONFIG
logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")

dotenv.load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

bot = discord.Bot()
bot.load_extension(name='app.cogs.live_timing')
bot.load_extension(name='app.cogs.head2head')

@bot.command(description="Sends the bot's latency.") # this decorator makes a slash command
async def ping(ctx): # a slash command will be created with the name "ping"
    await ctx.respond(f"Pong! Latency is {bot.latency}")

bot.run(DISCORD_TOKEN)