import asyncio
import time

import discord
from discord.ext import commands

from app.services import live_timing as lt
from app.services.openf1 import OpenF1
from app.cogs.helpers import get_years, get_locations
from app.exceptions import OpenF1Error

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")


class LiveTiming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="live-timing")
    @discord.option(
        name="year",
        type=discord.SlashCommandOptionType.integer,
        choices=get_years()
    )
    @discord.option(
        name="location",
        type=discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_locations)
    )
    @discord.option(
        name="session_name",
        type=discord.SlashCommandOptionType.string,
        choices=["Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Qualifying", "Sprint", "Race"]
    )
    async def live_timing(
        self,
        ctx: discord.ApplicationContext,
        year: discord.SlashCommandOptionType.integer,
        location: discord.SlashCommandOptionType.string,
        session_name: discord.SlashCommandOptionType.string
    ):
        logger.info(f"Live Timing command invoked by user [{ctx.interaction.user.id}|{ctx.interaction.user.name}]")
        session_key = await OpenF1.get_session_key(year, location, session_name)
        if not session_key:
            await ctx.respond(f"{year} {location} doesn't have {session_name} or {session_name} hasn't started yet. Please select another session.")
            return
        await ctx.respond(f"Select the fields for the Live Timing for {year} {location} Grand Prix {session_name} session. Default: `[Driver Number, Position]`", view=LiveTimingView(year, location, session_name))


class LiveTimingView(discord.ui.View):
    def __init__(self, year: int, location: str, session_name: str):
        super().__init__()
        self.year = year
        self.location = location
        self.session_name = session_name
        self.selected_values = []
    
    @discord.ui.select(
        placeholder = "Select extra fields...",
        min_values = 0, 
        max_values = 3,
        options = [
            discord.SelectOption(
                label="Intervals",
            ),
            discord.SelectOption(
                label="Pit Stops",
            ),
            discord.SelectOption(
                label="Tyres",
            )
        ]
    )
    async def select_callback(self, select: discord.ui.Select, interaction: discord.Interaction): # the function called when the user is done selecting options
        self.selected_values = select.values
        await interaction.response.defer()
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            logger.info(f"Start processing live timing for {self.year} {self.location} Grand Prix {self.session_name} session for user [{interaction.user.id}|{interaction.user.name}]")
            logger.info(f"Selected fields: {self.selected_values}")
            t0 = time.time()
            await interaction.response.defer()
            builder = lt.LiveTimingBuilder(self.year, self.location, self.session_name)
            await builder.get_session_key()
            tasks = [
                builder.add_drivers(),
                builder.add_positions()
            ]
            if "Intervals" in self.selected_values:
                tasks.append(builder.add_intervals())
            if "Pit Stops" in self.selected_values:
                tasks.append(builder.add_pit_stops())
            if "Tyres" in self.selected_values:
                tasks.append(builder.add_tyres())
            
            await asyncio.gather(*tasks)
            live_timing = builder.build()
            t1 = time.time()
            building_time = t1 - t0
            logger.debug(f"Time taken to build live_timing: {building_time} seconds")
            t0 = time.time()
            image_bytes = live_timing.to_image_bytes()
            t1 = time.time()
            image_conversion_time = t1 - t0
            logger.debug(f"Time taken to convert to image bytes: {image_conversion_time} seconds")
            logger.debug(f"Total time: {building_time + image_conversion_time} seconds")
            await interaction.followup.send(file=discord.File(image_bytes, filename="live_timing.png"))
            image_bytes.close()
        except OpenF1Error as e:
            await interaction.followup.send(f"OpenF1 API timed out, please try it again.")
        except Exception as e:
            logger.exception(e)
            await interaction.followup.send(f"An error occurred, please try it again.")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(LiveTiming(bot)) # add the cog to the bot