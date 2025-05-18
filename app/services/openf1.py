import os
from pathlib import Path
import aiohttp
from async_lru import alru_cache
from typing import Dict, Any

from app.app_config import AppConfig
from app.database import db
from app.services.models import Driver, Location
from app.exceptions import OpenF1Error, DatabaseError

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")

app_config_path = os.getenv("APP_CONFIG_PATH", f"{Path(__file__).parent.parent.parent.resolve()}/app_config.json")
app_config = AppConfig.from_json(app_config_path)

class OpenF1:

    @staticmethod
    @alru_cache(ttl=3600)
    async def get_session_key(year: int, location: str, session_name: str):
        url = f"{app_config.openf1.url}/sessions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"year": year, "location": location, "session_name": session_name}) as r:
                if r.status == 200:
                    result = await r.json()
                    return result[0].get("session_key")
                else:
                    logger.error(f"Error getting session key: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting session key: {r.status} - {await r.text()}")

    @staticmethod
    @alru_cache(ttl=3600)
    async def get_grand_prix_locations(year: int) -> list[Location]:
        location_repo = OpenF1LocationsRepository()
        locations = await location_repo.find({"year": int(year)})
        if len(locations) > 0:
            logger.info(f"Found {len(locations)} locations in the database.")
            return locations
        
        url = f"{app_config.openf1.url}/meetings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"year": year}) as r:
                if r.status == 200:
                    result = await r.json()
                    locations = []
                    for location in result:
                        if "Grand Prix" in location["meeting_name"] and "Testing" not in location["meeting_name"]:
                            locations.append(location)
                            await location_repo.insert(Location(**location))
                    return [Location(**location) for location in locations]
                else:
                    logger.error(f"Error getting grand prix locations: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting grand prix locations: {r.status} - {await r.text()}")

    @staticmethod
    async def upsert_grand_prix_locations(year: int) -> None:
        location_repo = OpenF1LocationsRepository()
        url = f"{app_config.openf1.url}/meetings"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"year": year}) as r:
                if r.status == 200:
                    result = await r.json()
                    locations = []
                    for location in result:
                        if "Grand Prix" in location["meeting_name"] and "Testing" not in location["meeting_name"]:
                            locations.append(location)
                            await location_repo.upsert(Location(**location))
                    return
                else:
                    logger.error(f"Error getting grand prix locations: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting grand prix locations: {r.status} - {await r.text()}")

    @staticmethod
    @alru_cache(ttl=3600)
    async def get_drivers(year: int, location: str, session_name: str) -> list[Driver]:
        driver_repo = OpenF1DriversRepository()
        drivers = await driver_repo.find({"year": int(year), "location": location, "session_name": session_name})  
        if len(drivers) > 0:
            logger.info(f"Found {len(drivers)} drivers in the database.")
            return drivers

        session_key = await OpenF1.get_session_key(year, location, session_name)
        url = f"{app_config.openf1.url}/drivers"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"session_key": session_key}) as r:
                if r.status == 200:
                    result = await r.json()
                    drivers = []
                    for driver in result:
                        driver["year"] = year
                        driver["location"] = location
                        driver["session_name"] = session_name
                        drivers.append(driver)
                        await driver_repo.insert(Driver(**driver))
                    return [Driver(**driver) for driver in drivers]
                else:
                    logger.error(f"Error getting drivers: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting drivers: {r.status} - {await r.text()}")

    @staticmethod
    @alru_cache(ttl=10)
    async def get_position(session_key: int):
        url = f"{app_config.openf1.url}/position"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"session_key": session_key}) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"Error getting positions: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting positions: {r.status} - {await r.text()}")
                
    @staticmethod
    @alru_cache(ttl=10)
    async def get_intervals(session_key: int, driver_number: int = None):
        url = f"{app_config.openf1.url}/intervals"
        params = {"session_key": session_key}
        if driver_number:
            params["driver_number"] = driver_number
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"Error getting intervals: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting intervals: {r.status} - {await r.text()}")
                
    @staticmethod
    @alru_cache(ttl=30)
    async def get_pit_stops(session_key: int):
        url = f"{app_config.openf1.url}/pit"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"session_key": session_key}) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"Error getting pit stops: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting pit stops: {r.status} - {await r.text()}")
                
    @staticmethod
    @alru_cache(ttl=30)
    async def get_tyres(session_key: int):
        url = f"{app_config.openf1.url}/stints"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"session_key": session_key}) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"Error getting tyres: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting tyres: {r.status} - {await r.text()}")
                
    @staticmethod
    @alru_cache(ttl=10)
    async def get_lap_times(session_key: int):
        url = f"{app_config.openf1.url}/laps"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params={"session_key": session_key}) as r:
                if r.status == 200:
                    return await r.json()
                else:
                    logger.error(f"Error getting lap times: {r.status} - {await r.text()}")
                    raise OpenF1Error(f"Error getting lap times: {r.status} - {await r.text()}")


class OpenF1DriversRepository:
    def __init__(self):
        self.collection = db["drivers"]

    async def find(self, query: Dict[str, Any]) -> list[Driver]:
        try:
            cursor = self.collection.find(query)
            drivers = await cursor.to_list()
        except Exception as e:
            logger.error(f"Error finding drivers: {e}")
            raise DatabaseError(f"Error finding drivers: {e}")
        return [Driver(**driver) for driver in drivers] if drivers else []
    
    async def insert(self, driver: Driver):
        try:
            await self.collection.insert_one(driver.model_dump())
        except Exception as e:
            logger.error(f"Error inserting driver: {e}")
            raise DatabaseError(f"Error inserting driver: {e}")
        

class OpenF1LocationsRepository:
    def __init__(self):
        self.collection = db["locations"]

    async def find(self, query: Dict[str, Any]) -> list[Location]:
        try:
            cursor = self.collection.find(query).sort("date_start", 1)
            locations = await cursor.to_list()
        except Exception as e:
            logger.error(f"Error finding locations: {e}")
            raise DatabaseError(f"Error finding locations: {e}")
        return [Location(**location) for location in locations] if locations else []
    
    async def insert(self, location: Location):
        try:
            await self.collection.insert_one(location.model_dump())
        except Exception as e:
            logger.error(f"Error inserting location: {e}")
            raise DatabaseError(f"Error inserting location: {e}")
        
    async def upsert(self, location: Location):
        try:
            await self.collection.update_one(
                {"meeting_key": location.meeting_key},
                {"$set": location.model_dump()},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error upserting location: {e}")
            raise DatabaseError(f"Error upserting location: {e}")