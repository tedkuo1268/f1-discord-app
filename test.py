import asyncio

from app.services.leaderboard import LeaderboardBuilder


async def main():
    builder = LeaderboardBuilder(2025, "Suzuka")
    leaderboard = await builder.add_position()
    leaderboard = leaderboard.build()
    table = leaderboard.to_markdown_table()
    print(table)
    

if __name__ == "__main__":
    asyncio.run(main())