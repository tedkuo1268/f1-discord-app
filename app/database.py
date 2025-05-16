import os
from pathlib import Path
from pymongo import AsyncMongoClient

from app.app_config import AppConfig

app_config_path = os.getenv("APP_CONFIG_PATH", f"{Path(__file__).parent.parent.resolve()}/app_config.json")
app_config = AppConfig.from_json(app_config_path)

client = AsyncMongoClient(
    host=app_config.mongodb.host,
    port=app_config.mongodb.port,
    username=app_config.mongodb.username,
    password=app_config.mongodb.password
)
db = client["f1_discord_app"]