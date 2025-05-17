# F1 Discord Bot

A Discord bot that provides real-time Formula 1 race information using the OpenF1 API. The bot enables users to view live race standings, compare drivers head-to-head, and get detailed information about F1 race sessions. The data for this project is sourced from [OpenF1](https://openf1.org). Please visit the website for more details. 

## Install the F1 Discord App

To install the production F1 Discord App, please click this [link](https://discord.com/oauth2/authorize?client_id=1372934394687524874) and install it to your server or your user account.

## Features

- **Live Timing** (`/live-timing`): View current and historical race standings with customizable data including:
  - Driver positions
  - Intervals between drivers
  - Pit stop counts
  - Current tire compounds and age

- **Head-to-Head** (`/h2h`): Compare two drivers' performance with:
  - Lap time differences
  - Sector time comparisons
  - Current interval between drivers
  - Up to 5 most recent laps

## Develop with your own Discord app

If you would like to test and develop with your own Discord app, please follow the steps below.

### Local Development

1. Create your bot:

    Follow the instuction [here](https://guide.pycord.dev/getting-started/creating-your-first-bot) to build the bot application.

2. Clone the repository:
    ```bash
    git clone https://github.com/tedkuo1268/f1-discord-app.git
    cd f1-discord-app
    ```

3. Set up environment with `uv`:
    ```bash
    # If you haven't have uv installed
    pip install uv

    # Installing packages from lockfile
    uv sync
    ```

4. Set up environment variables and config file:
    ```bash
    # Add the Discord token you got from Step 1 here.
    # 
    cp .env.example .env
    cp app_config.json.example app_config.json
    ```


## Docker Deployment