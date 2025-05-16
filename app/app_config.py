import json
from typing import Optional, Dict, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

class OpenF1Settings(BaseSettings):
    url: str = Field(
        default="https://api.openf1.org/v1",
        description="Base URL for the OpenF1 API"
    )

class MongoDBSettings(BaseSettings):
    host: str = Field(default="localhost")
    port: int = Field(default=27017)
    username: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None)


class AppConfig(BaseSettings):
    openf1: OpenF1Settings = Field(
        default_factory=OpenF1Settings,
        description="Settings for the OpenF1 API"
    )

    mongodb: MongoDBSettings = Field(
        default_factory=MongoDBSettings,
        description="Settings for MongoDB connection"
    )

    @classmethod
    def from_json(cls, file_path: Union[str, Path]) -> "AppConfig":
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")
        
        with open(file_path, "r") as f:
            config_data = json.load(f)
            
        return cls(**config_data)
