import discord
from discord.ext import commands
from discord import app_commands
import json
import html
import os
import asyncio
from datetime import timedelta

WARN_FILE = "spam.json"


def load_warnings():
    if os.path.exists(WARN_FILE):
        try:
            with open(WARN_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_warnings(warnings):
    with open(WARN_FILE, "w") as f:
        json.dump(warnings, f, indent=4)


class SpamModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = load_warnings()

