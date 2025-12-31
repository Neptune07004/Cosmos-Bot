import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import os
import re

load_dotenv(".env")

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Remove prefix — slash commands don't need it
bot = commands.Bot(command_prefix=None, intents=intents)


async def load_cogs():
    folder_path = "cogs"
    for filename in os.listdir(folder_path):
        if filename.endswith(".py") and filename != "__init__.py":
            ext = f"cogs.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                print(f"✅ Loaded {ext}")
            except Exception as e:
                print(f"❌ Failed to load {ext}: {e}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())