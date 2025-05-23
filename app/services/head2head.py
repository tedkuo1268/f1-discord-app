import time
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

from app.services.openf1 import OpenF1

import logging
logger = logging.getLogger(__name__)
logger.info("Logging is configured.")

class Head2Head(BaseModel):
    driver_names: Optional[List[str]] = None
    driver_numbers: Optional[List[int]] = None
    driver_colors: Optional[List[str]] = None
    lap_times: Optional[List[List[str]]] = None
    sector_times: Optional[List[List[List[str]]]] = None
    current_interval: Optional[Union[str, float]] = None
    laps: Optional[List[int]] = None
    
    def to_image_bytes(self) -> BytesIO:
        logger.info("Converting head2head to image bytes...")

        data = {}
        
        # Add lap times and sector times with a hierarchical structure
        for i, lap_num in enumerate(self.laps):
            # Add sector times
            for sector_idx in range(3):
                data[(f"Lap {lap_num}", f"Sector {sector_idx+1}")] = [
                    self.sector_times[0][i][sector_idx],
                    self.sector_times[1][i][sector_idx]
                ]

            # Add total lap time
            data[(f"Lap {lap_num}", "Total")] = [
                self.lap_times[0][i],
                self.lap_times[1][i]
            ]
        
        # Create DataFrame with drivers as index and MultiIndex columns
        df = pd.DataFrame(data, index=self.driver_names)
        df.columns = pd.MultiIndex.from_tuples(df.columns, names=['Lap', ''])
        
        # Format numbers for better display
        #df = df.round(3)
        
        # Create a figure with appropriate size
        #fig_width = max(10, len(df.columns) * 0.8)
        #fig_height = max(5, len(df) * 1.0)
        fig, ax = plt.subplots(figsize=(15, 2))
        fig.patch.set_facecolor('#333333')  # Dark grey background
        ax.set_facecolor('#333333')
        ax.axis('tight')
        ax.axis('off')
        
        # Create flattened column headers
        flattened_columns = [f"{col[0]}\n{col[1]}" for col in df.columns]
        
        # Create the table
        table = ax.table(
            cellText=df.values,
            rowLabels=df.index,
            colLabels=flattened_columns,
            loc='center',
            cellLoc='center'
        )
        
        # Add grid lines
        for key, cell in table.get_celld().items():
            cell.set_linewidth(0.5)
            
        # Apply dark theme to all cells
        cells = table.get_celld()
        for key, cell in cells.items():
            #print(key)
            #print(cell)
            #print(cell.get_text().get_text())
            if key[0] == 2 and key[1] >= 0: # Second driver row
                try:
                    value = float(cell.get_text().get_text())
                    if value > 0:
                        cell.set_text_props(color='#FF3333')
                    else:
                        cell.set_text_props(color='#49FF33')
                except ValueError:
                    cell.set_text_props(color='white')
            else:
                cell.set_text_props(color='white')
            
            # Separate laps by different background colors
            if key[0] > 0 and key[1] % 8 <= 3:
                cell.set_facecolor('#444444')
            elif key[0] > 0 and key[1] % 8 > 3:
                cell.set_facecolor('#555555')
            
        # Style header cells
        for i in range(len(flattened_columns)):
            header_cell = table[(0, i)]

            # Separate laps by different background colors
            if i % 8 <= 3:
                header_cell.set_facecolor('#222222')
            else:
                header_cell.set_facecolor('#333333')
                
            header_cell.set_text_props(fontweight='bold')
        
        # Apply driver colors to index cells
        for i, color in enumerate(self.driver_colors):
            row_cell = table[(i+1, -1)]
            row_cell.set_facecolor(color)
            row_cell.set_text_props(color='white', fontweight='bold')
        
        # Adjust table appearance
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1.2, 1.6)

        # Save to BytesIO
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        logger.info("Finished converting head2head to image bytes.")
        
        return buf


class Head2HeadBuilder:
    def __init__(self, year: int, location: str, session_name: str = 'Race'):
        self.h2h = Head2Head()
        self.year = year
        self.location = location
        self.session_name = session_name
        self.session_key = None   
        #self.leaderboard = Leaderboard()

    async def get_session_key(self) -> None:
        # Get session key from OpenF1 API
        logger.info("Getting session key...")
        session_key = await OpenF1.get_session_key(self.year, self.location, self.session_name)
        logger.info("Finished getting session key.")
        self.session_key = session_key

    async def add_drivers(self, driver_number_1: int, driver_number_2: int) -> "Head2HeadBuilder":
        logger.info("Adding driver numbers to the leaderboard...")
        drivers_data = await OpenF1.get_drivers(
            self.year, self.location, self.session_name
        )
        
        driver_numbers = [driver_number_1, driver_number_2]
        driver_names = [None, None]
        driver_colors = [None, None]
        for data in drivers_data:
            if data.driver_number == driver_number_1:
                driver_names[0] = data.name_acronym
                driver_colors[0] = f"#{data.team_colour}"
            elif data.driver_number == driver_number_2:
                driver_names[1] = data.name_acronym   
                driver_colors[1] = f"#{data.team_colour}"

        self.h2h.driver_numbers = driver_numbers
        self.h2h.driver_names = driver_names
        self.h2h.driver_colors = driver_colors
        logger.info("Finished adding driver numbers.")

        return self
    
    async def add_laps_and_sectors_time(self, driver_number_1: int, driver_number_2: int, num_of_laps: int) -> "Head2HeadBuilder":
        logger.info("Adding lap and sector times to the leaderboard...")
        lap_data = await OpenF1.get_lap_times(self.session_key)

        driver1_laps = []
        driver2_laps = []
        for data in lap_data:
            if data.get("driver_number") == driver_number_1:
                driver1_laps.append(data)
            elif data.get("driver_number") == driver_number_2:
                driver2_laps.append(data)
        
        last_lap = min(len(driver1_laps), len(driver2_laps))
        driver1_laps, driver2_laps = driver1_laps[max(0, last_lap - num_of_laps):last_lap], driver2_laps[max(0, last_lap - num_of_laps):last_lap]

        lap_times = [[], []]
        sector_times = [[], []]
        laps = []
        for d1_lap, d2_lap in zip(driver1_laps, driver2_laps):
            laps.append(d1_lap.get("lap_number"))

            try:
                lap_times[0].append(d1_lap.get("lap_duration"))
            except Exception as e:
                logger.warning(f"Error getting lap time for driver 1: {e}")
                lap_times[0].append("N/A")
            try:
                lap_times[1].append(round(d2_lap.get("lap_duration") - d1_lap.get("lap_duration"), 3)) # The lap time difference between driver 2 and driver 1
            except Exception as e:
                logger.warning(f"Error getting lap time difference between driver 1 and driver 2: {e}")
                lap_times[1].append("N/A")

            try:
                sector_times[0].append([
                    d1_lap.get("duration_sector_1"), 
                    d1_lap.get("duration_sector_2"), 
                    d1_lap.get("duration_sector_3")
                ])
            except Exception as e:
                logger.warning(f"Error getting sector times for driver 1: {e}")
                sector_times[0].append(["N/A", "N/A", "N/A"])
            try:
                sector_times[1].append([
                    round(d2_lap.get("duration_sector_1") - d1_lap.get("duration_sector_1"), 3), 
                    round(d2_lap.get("duration_sector_2") - d1_lap.get("duration_sector_2"), 3), 
                    round(d2_lap.get("duration_sector_3") - d1_lap.get("duration_sector_3"), 3)
                ])
            except Exception as e:
                logger.warning(f"Error getting sector times difference between driver 1 and driver 2: {e}")
                sector_times[1].append(["N/A", "N/A", "N/A"])

        self.h2h.lap_times = lap_times
        self.h2h.sector_times = sector_times
        self.h2h.laps = laps
        logger.info("Finished adding lap and sector times.")

        return self

    async def add_interval(self, driver_number_1: int, driver_number_2: int) -> "Head2HeadBuilder":
        logger.info("Adding intervals to the leaderboard...")
        intervals_data = await OpenF1.get_intervals(self.session_key)

        driver1_curr_gap_to_leader = 0
        driver2_curr_gap_to_leader = 0
        for data in intervals_data:
            if data.get("driver_number") == driver_number_1:
                driver1_curr_gap_to_leader = data.get("gap_to_leader")
            elif data.get("driver_number") == driver_number_2:
                driver2_curr_gap_to_leader = data.get("gap_to_leader")
        
        try:
            current_interval = round(driver2_curr_gap_to_leader - driver1_curr_gap_to_leader, 3)
        except TypeError:
            current_interval = "N.A."
        self.h2h.current_interval = current_interval

        logger.info("Finished adding intervals to the leaderboard.")

        return self
    
    def build(self) -> "Head2Head":
        return self.h2h