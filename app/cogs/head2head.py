import asyncio
import time
from typing import List

import discord
from discord.ext import commands

from app.cogs.helpers import get_years, get_locations, get_drivers_select_options
from app.services import head2head as h2h
from app.services.openf1 import OpenF1
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
        name="session_name",
        type=discord.SlashCommandOptionType.string,
        choices=["Practice 1", "Practice 2", "Practice 3", "Sprint Qualifying", "Qualifying", "Sprint", "Race"]
    )
    async def head2head(
        self,
        ctx: discord.ApplicationContext,
        year: discord.SlashCommandOptionType.integer,
        location: discord.SlashCommandOptionType.string,
        session_name: discord.SlashCommandOptionType.string
    ):  
        logger.info(f"Head-to-head command invoked by user [{ctx.interaction.user.id}|{ctx.interaction.user.name}]")
        session_key = await OpenF1.get_session_key(year, location, session_name)
        if not session_key:
            await ctx.respond(f"{year} {location} doesn't have {session_name} or {session_name} hasn't started yet. Please select another session.")
            return
        
        driver_options = await get_drivers_select_options(year, location, session_name)
        await ctx.respond(
            f"Select drivers and number of laps to see the head-to-head result for {year} {location} Grand Prix {session_name} session.", 
            view=Head2HeadView(year, location, session_name, driver_options)
        )

class DriversSelect(discord.ui.Select):
    def __init__(self, placeholder: str, driver_options: List[discord.SelectOption]):
        super().__init__(
            placeholder=placeholder,
            min_values=1,
            max_values=1,
            options=driver_options
        )
    
    async def callback(self, interaction: discord.Interaction):
        #print(f"Selected values: {self.values}")
        await interaction.response.defer()


class NumLapsSelect(discord.ui.Select):
    def __init__(self):
        super().__init__(
            placeholder="Select number of laps...",
            min_values=1,
            max_values=1,
            options=[discord.SelectOption(label=str(i)) for i in range(1, 6)],
        )
    
    async def callback(self, interaction: discord.Interaction):
        #print(f"Selected values: {self.values}")
        await interaction.response.defer()


class Head2HeadView(discord.ui.View):
    def __init__(self, year: int, location: str, session_name: str, driver_options: List[discord.SelectOption]):
        super().__init__()
        self.year = year
        self.location = location
        self.session_name = session_name
        self.driver_options = driver_options
        self.driver1_select = DriversSelect("Select the first driver...", driver_options)
        self.driver2_select = DriversSelect("Select the second driver", driver_options)
        self.num_laps_select = NumLapsSelect()

        self.add_item(self.driver1_select)
        self.add_item(self.driver2_select)
        self.add_item(self.num_laps_select)

    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            driver1 = int(self.driver1_select.values[0])
            driver2 = int(self.driver2_select.values[0])
            num_of_laps = int(self.num_laps_select.values[0])
            if driver1 == driver2:
                await interaction.respond("Please select two different drivers.")
                return
        
            logger.info(f"Start processing head-to-head comparison between {driver1} and {driver2} for {self.year} {self.location} Grand Prix for user [{interaction.user.id}|{interaction.user.name}]")
            
            await interaction.response.defer()
            t0 = time.time()
            builder = h2h.Head2HeadBuilder(self.year, self.location, self.session_name)
            await builder.get_session_key()
            tasks = [
                builder.add_drivers(driver1, driver2),
                builder.add_laps_and_sectors_time(driver1, driver2, num_of_laps),
                builder.add_interval(driver1, driver2)
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

            if head2head.current_interval > 0:
                interval_message = f"{head2head.driver_names[1]}'s gap to {head2head.driver_names[0]}: {head2head.current_interval} seconds"
            else:
                interval_message = f"{head2head.driver_names[0]}'s gap to {head2head.driver_names[1]}: {-head2head.current_interval} seconds"
            await interaction.followup.send(interval_message)
            await interaction.followup.send(file=discord.File(image_bytes, filename="head2head.png"))
            image_bytes.close()
        except OpenF1Error as e:
            await interaction.followup.send(f"OpenF1 API timed out, please try it again.")
        except Exception as e:
            logger.exception(e)
            await interaction.followup.send(f"An error occurred.")
        
        

    """ async def select_driver_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        print(f"Selected values: {select.values}")
        self.selected_values = select.values
        await interaction.response.defer()

    async def select_num_laps_callback(self, select: discord.ui.Select, interaction: discord.Interaction):
        print(f"Selected values: {select.values}")
        self.selected_values = select.values
        await interaction.response.defer() """


def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Head2Head(bot)) # add the cog to the bot