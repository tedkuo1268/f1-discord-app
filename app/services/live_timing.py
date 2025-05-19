import time
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from app.services.openf1 import OpenF1

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")


class LiveTiming(BaseModel):
    driver_numbers: Optional[List[int]] = None
    driver_names: Optional[Dict[int, str]] = None
    driver_colors: Optional[Dict[int, str]] = None
    team_names: Optional[Dict[int, str]] = None
    positions: Optional[Dict[int, int]] = None
    intervals: Optional[Dict[int, float]] = None
    gaps_to_leader: Optional[Dict[int, float]] = None
    pit_stops: Optional[Dict[int, int]] = None
    tyres_compound: Optional[Dict[int, str]] = None
    tyres_age: Optional[Dict[int, int]] = None


    def to_image_bytes(self) -> BytesIO:
        logger.info("Converting live timing to image bytes...")
        drivers_data = []
        for driver in self.driver_numbers:
            driver_data = {
            "Position": self.positions.get(driver) if self.positions else None,
            "Driver No.": driver,
            "Driver Name": self.driver_names.get(driver) if self.driver_names else None,
            "Driver Color": self.driver_colors.get(driver) if self.driver_colors else None,
            "Team Name": self.team_names.get(driver) if self.team_names else None,
            "Interval": self.intervals.get(driver) if self.intervals else None,
            "Gap to Leader": self.gaps_to_leader.get(driver) if self.gaps_to_leader else None,
            "Pit Stops": self.pit_stops.get(driver) if self.pit_stops else None,
            "Tyre Compound": self.tyres_compound.get(driver) if self.tyres_compound else None,
            "Tyre Age": self.tyres_age.get(driver) if self.tyres_age else None
            }
            drivers_data.append(driver_data)
        
        # Convert the data to Pandas DataFrame
        df = pd.DataFrame(drivers_data)
        df = df.dropna(axis=1, how='all')
        df = df.sort_values(by="Position")
        
        # Extract driver colors and then remove the column
        driver_colors = df["Driver Color"].tolist()
        df = df.drop(columns=["Driver Color"])
        
        # Insert empty column at the beginning
        df.insert(0, "", [""] * len(df))
        
        # Create a table figure with dark background
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#333333')  # Dark grey background
        ax.set_facecolor('#333333')
        ax.axis('tight')
        ax.axis('off')
        
        # Create the table
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')
        
        # Define custom column widths
        col_widths = {
            0: 0.02,  # Color column
            1: 0.08,  # Position
            2: 0.1,  # Driver No.
            3: 0.12,  # Driver Name
            4: 0.14,  # Team Name
            5: 0.1,  # Interval
            6: 0.14,  # Gap to Leader
            7: 0.08,  # Pit Stops
            8: 0.14,  # Tyre Compound
            9: 0.08   # Tyre Age
        }
        
        # Apply custom widths to each column
        for col in range(len(df.columns)):
            width = col_widths.get(col, 0.1)  # Default width of 0.1 if not specified
            for row in range(len(df) + 1):  # +1 for header row
                cell = table.get_celld().get((row, col))
                if cell:
                    cell.set_width(width)
        
        # Apply dark theme to all cells
        cells = table.get_celld()
        for key, cell in cells.items():
            cell.set_text_props(color='white')
            cell.set_facecolor('#333333')
            
        # Set header row style
        for col in range(len(df.columns)):
            cells[(0, col)].set_facecolor('#222222')
            cells[(0, col)].set_text_props(fontweight='bold')
            
        # Color the cells in the first column with driver colors
        for row_idx in range(len(df)):
            color = driver_colors[row_idx] if row_idx < len(driver_colors) and driver_colors[row_idx] else '#333333'
            cells[(row_idx+1, 0)].set_facecolor(color)
        
        # Adjust table appearance
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.2)

        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        #plt.show()
        logger.info("Finished converting live timing to image bytes.")

        return buf
    

class LiveTimingBuilder:
    def __init__(self, year: int, location: str, session_name: str = 'Race'):
        self.live_timing = LiveTiming()
        self.year = year
        self.location = location
        self.session_name = session_name
        self.session_key = None   

    async def get_session_key(self) -> None:
        # Get session key from OpenF1 API
        logger.info("Getting session key...")
        session_key = await OpenF1.get_session_key(self.year, self.location, self.session_name)
        logger.info("Finished getting session key.")
        self.session_key = session_key

    async def add_drivers(self) -> "LiveTimingBuilder":
        logger.info("Adding driver numbers to the live timing...")
        drivers_data = await OpenF1.get_drivers(
            self.year, self.location, self.session_name
        )
        
        driver_numbers = []
        driver_names = {}
        driver_colors = {}
        team_names = {}
        for data in drivers_data:
            driver_number = data.driver_number
            driver_numbers.append(driver_number)
            driver_names[driver_number] = data.name_acronym
            driver_colors[driver_number] = f"#{data.team_colour}"
            team_names[driver_number] = data.team_name

        self.live_timing.driver_numbers = driver_numbers
        self.live_timing.driver_names = driver_names
        self.live_timing.driver_colors = driver_colors
        self.live_timing.team_names = team_names
        logger.info("Finished adding driver numbers.")

        return self

    async def add_positions(self):
        logger.info("Adding position data to the live timing...")
        position_data = await OpenF1.get_position(self.session_key)

        processed_data = {}
        #position_data.sort(key=lambda x: x.get("date"))
        for data in position_data:
            driver_number = data.get("driver_number")
            processed_data[driver_number] = data.get("position")

        self.live_timing.positions = processed_data
        logger.info("Finished adding position data.")

        return self

    async def add_intervals(self):
        logger.info("Adding intervals to the live timing...")
        intervals_data = await OpenF1.get_intervals(self.session_key)

        intervals = {}
        gaps_to_leader = {}
        for data in intervals_data:
            driver_number = data.get("driver_number")
            intervals[driver_number] = data.get("interval")
            gaps_to_leader[driver_number] = data.get("gap_to_leader")

        self.live_timing.intervals = intervals 
        self.live_timing.gaps_to_leader = gaps_to_leader
        logger.info("Finished adding intervals.")

        return self

    async def add_pit_stops(self):
        logger.info("Adding pit stops data to the live timing...")
        pit_stops_data = await OpenF1.get_pit_stops(self.session_key)

        pit_stops = {}
        for data in pit_stops_data:
            driver_number = data.get("driver_number")
            pit_stops[driver_number] = int(pit_stops.get(driver_number, 0) + 1)

        self.live_timing.pit_stops = pit_stops
        logger.info("Finished adding pit stops data.")

        return self

    async def add_tyres(self):
        logger.info("Adding tyres data to the live timing...")
        tyres_data = await OpenF1.get_tyres(self.session_key)

        tyres_compound = {}
        tyres_age = {}
        for data in tyres_data:
            driver_number = data.get("driver_number")
            tyres_compound[driver_number] = data.get("compound")
            tyres_age[driver_number] = int(data.get("tyre_age_at_start") + data.get("lap_end") - data.get("lap_start"))

        self.live_timing.tyres_compound = tyres_compound
        self.live_timing.tyres_age = tyres_age
        logger.info("Finished adding tyres data.")

        return self

    def build(self) -> "LiveTiming":
        return self.live_timing