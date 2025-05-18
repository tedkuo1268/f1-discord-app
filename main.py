import os
from datetime import datetime
import time
import threading
import asyncio
import discord
import dotenv
import logging.config

from app.services.openf1 import OpenF1

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

# Background task for upserting locations
async def upsert_locations_task():
    while True:
        current_year = datetime.now().year
        try:
            await OpenF1.upsert_grand_prix_locations(current_year)
            logger.info(f"Upserted grand prix locations for {current_year}")
        except Exception as e:
            logger.error(f"Error upserting grand prix locations: {e}")
        await asyncio.sleep(3600)

@bot.event
async def on_ready():
    logger.info(f"Bot is ready as {bot.user}")
    # Start the background task
    bot.loop.create_task(upsert_locations_task())

# Run the bot
logger.info("Starting bot...")
bot.run(DISCORD_TOKEN)

logger.info("Done!")