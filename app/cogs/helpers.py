import discord
import asyncio
from async_lru import alru_cache

from app.services.openf1 import OpenF1
from app.exceptions import DatabaseError

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")

def get_years():
    year_choices = [2023, 2024, 2025]
    return year_choices

@alru_cache(ttl=3600)
async def get_locations(ctx: discord.AutocompleteContext):
    year = ctx.options['year']
    locations = await OpenF1.get_grand_prix_locations(year)
    location_choices = [discord.OptionChoice(location.meeting_name, location.location) for location in locations]
    return location_choices

@alru_cache(ttl=3600)
async def get_drivers_choices(ctx: discord.AutocompleteContext):
    year = ctx.options['year']
    location = ctx.options['location']
    session_name = ctx.options['session_name']

    #session_key = await OpenF1.get_session_key(year, location, 'Race')
    drivers = await OpenF1.get_drivers(year, location, session_name)
    driver_choices = [discord.OptionChoice(driver.name_acronym, driver.driver_number) for driver in drivers]

    return driver_choices

@alru_cache(ttl=3600)
async def get_drivers_select_options(year: int, location: str, session_name: str):
    #session_key = await OpenF1.get_session_key(year, location, 'Race')
    drivers = await OpenF1.get_drivers(year, location, session_name)
    driver_options = [discord.SelectOption(label=driver.name_acronym, value=str(driver.driver_number)) for driver in drivers]

    return driver_options

    