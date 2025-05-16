import asyncio
import time

import discord
from discord.ext import commands

from app.services import leaderboard as lb
from app.cogs.helpers import get_years, get_locations

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")


class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="leaderboard")
    @discord.option(
        name="year",
        type=discord.SlashCommandOptionType.string,
        choices=get_years()
    )
    @discord.option(
        name="location",
        type=discord.SlashCommandOptionType.string,
        autocomplete=discord.utils.basic_autocomplete(get_locations)
    )
    async def leaderboard(
        self,
        ctx: discord.ApplicationContext,
        year: discord.SlashCommandOptionType.string,
        location: discord.SlashCommandOptionType.string
    ):
        await ctx.respond(f"Select the fields for the leaderboard for {year} {location} Grand Prix. Default: `[Driver Number, Position]`", view=LeaderboardView(year, location))


    @commands.Cog.listener() # we can add event listeners to our cog
    async def on_member_join(self, member): # this is called when a member joins the server
    # you must enable the proper intents
    # to access this event.
    # See the Popular-Topics/Intents page for more info
        await member.send('Welcome to the server!')


class LeaderboardView(discord.ui.View):
    def __init__(self, year: int, location: str):
        super().__init__()
        self.year = year
        self.location = location
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
    async def select_callback(self, select, interaction: discord.Interaction): # the function called when the user is done selecting options
        self.selected_values = select.values
        await interaction.response.defer()
    
    @discord.ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def button_callback(self, button: discord.ui.Button, interaction: discord.Interaction):
        try:
            t0 = time.time()
            await interaction.response.defer()
            builder = lb.LeaderboardBuilder(self.year, self.location)
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
            leaderboard = builder.build()
            t1 = time.time()
            building_time = t1 - t0
            logger.info(f"Time taken to build leaderboard: {building_time} seconds")
            t0 = time.time()
            image_bytes = leaderboard.to_image_bytes()
            t1 = time.time()
            image_conversion_time = t1 - t0
            logger.info(f"Time taken to convert to image bytes: {image_conversion_time} seconds")
            logger.info(f"Total time: {building_time + image_conversion_time} seconds")
            #await interaction.response.send_message(table)
            await interaction.followup.send(file=discord.File(image_bytes, filename="leaderboard.png"))
        except Exception as e:
            logger.exception(e)
            await interaction.followup.send(f"An error occurred, please try it again.")

def setup(bot): # this is called by Pycord to setup the cog
    bot.add_cog(Leaderboard(bot)) # add the cog to the bot