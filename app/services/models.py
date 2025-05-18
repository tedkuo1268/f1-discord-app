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


class Location(BaseModel):
    year: int = Field(...)
    meeting_key: int = Field(...)
    meeting_name: str = Field(...)
    location: str = Field(...)
    date_start: str = Field(...)   # Query need to be sorted by date_start