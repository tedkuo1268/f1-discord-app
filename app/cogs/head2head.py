import asyncio
import time

import discord
from discord.ext import commands

from app.cogs.helpers import get_years, get_locations, get_drivers
from app.services import head2head as h2h
from app.exceptions import OpenF1Error

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")


class Head2Head(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="h2h")
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
        name="driver1",
        type=discord.SlashCommandOptionType.integer,
        autocomplete=discord.utils.basic_autocomplete(get_drivers)
    )
    @discord.option(
        name="driver2",
        type=discord.SlashCommandOptionType.integer,
        autocomplete=discord.utils.basic_autocomplete(get_drivers)
    )
    @discord.option(
        name="num_of_laps",
        description="Comparison for the most recent N laps",
        type=discord.SlashCommandOptionType.integer,
        choices=[1, 2, 3, 4, 5]
    )
    async def head2head(
        self,
        ctx: discord.ApplicationContext,
        year: discord.SlashCommandOptionType.integer,
        location: discord.SlashCommandOptionType.string,
        driver1: discord.SlashCommandOptionType.integer,
        driver2: discord.SlashCommandOptionType.integer,
        num_of_laps: discord.SlashCommandOptionType.integer
    ):  
        logger.info(f"Head-to-head command invoked by user [{ctx.interaction.user.id}|{ctx.interaction.user.name}]")
        if driver1 == driver2:
            await ctx.respond("Please select two different drivers.")
            return
        
        await ctx.respond(
            f"Press the button to see the head-to-head result between {driver1} and {driver2} for {year} {location} Grand Prix", 
            view=Head2HeadView(year, location, driver1, driver2, num_of_laps)
        )


class Head2HeadView(discord.ui.View):
    def __init__(self, year: int, location: str, driver1: int, driver2: int, num_of_laps: int):
        super().__init__()
        self.year = year
        self.location = location
        self.driver1 = driver1
        self.driver2 = driver2
        self.num_of_laps = num_of_laps
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            logger.info(f"Start processing head-to-head comparison between {self.driver1} and {self.driver2} for {self.year} {self.location} Grand Prix for user [{interaction.user.id}|{interaction.user.name}]")
            
            await interaction.response.defer()
            t0 = time.time()
            builder = h2h.Head2HeadBuilder(self.year, self.location)
            await builder.get_session_key()
            tasks = [
                builder.add_drivers(self.driver1, self.driver2),
                builder.add_laps_and_sectors_time(self.driver1, self.driver2, self.num_of_laps),
                builder.add_interval(self.driver1, self.driver2)
            ]
            
            await asyncio.gather(*tasks)
            head2head = builder.build()
            t1 = time.time()
            building_time = t1 - t0
            logger.debug(f"Time taken to build head2head: {building_time} seconds")

            t0 = time.time()
            image_bytes = head2head.to_image_bytes()
            t1 = time.time()
            image_conversion_time = t1 - t0
            logger.debug(f"Time taken to convert to image bytes: {image_conversion_time} seconds")
            logger.debug(f"Total time: {building_time + image_conversion_time} seconds")

            await interaction.followup.send(f"{head2head.driver_names[1]}'s gap to {head2head.driver_names[0]}: {head2head.current_interval} seconds")
            await interaction.followup.send(file=discord.File(image_bytes, filename="head2head.png"))
            image_bytes.close()
        except OpenF1Error as e:
            await interaction.followup.send(f"OpenF1 API timed out, please try it again.")
        except Exception as e:
            logger.exception(e)
            await interaction.followup.send(f"An error occurred.")


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Head2Head(bot)) # add the cog to the bot