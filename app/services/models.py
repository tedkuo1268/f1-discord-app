from pydantic import BaseModel, Field


class Driver(BaseModel):
    session_key: int = Field(...)
    year: int = Field(...)
    location: str = Field(...)
    session_name: str = Field(...)
    driver_number: int = Field(...)
    name_acronym: str = Field(...)
    team_colour: str = Field(...)
    team_name: str = Field(...)