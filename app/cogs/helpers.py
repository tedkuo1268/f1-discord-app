import discord
from async_lru import alru_cache

from app.services.openf1 import OpenF1
from app.database import db

def get_years():
    year_choices = ["2024", "2025"]
    return year_choices

@alru_cache(ttl=3600)
async def get_locations(ctx: discord.AutocompleteContext):
    year = ctx.options['year']
    result = await db["locations"].find_one({"year": year}) 
    return result["locations"]

@alru_cache(ttl=3600)
async def get_drivers(ctx: discord.AutocompleteContext):
    year = ctx.options['year']
    location = ctx.options['location']

    #session_key = await OpenF1.get_session_key(year, location, 'Race')
    drivers_data = await OpenF1.get_drivers(year, location, 'Race')
    driver_choices = [discord.OptionChoice(data.name_acronym, data.driver_number) for data in drivers_data]

    return driver_choices
    