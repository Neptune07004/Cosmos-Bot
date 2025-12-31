import discord
from discord.ext import commands
import asyncio
import os
from typing import Optional
from discord import app_commands

class ChatModeration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

@app_commands.command(name="chat_lock", description="locks the channel the command is run in")
@app_commands.describe(reason="Reason for locking channel")
async def chat_lock(interaction: discord.Interaction, reason: Optional[str] = None):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = False
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
    await interaction.response.send_message(
        embed = discord.Embed(
            description = "This channel has been temporarily locked. Reason: {reason}"
            discord.color.Green()
        )
    )

@app_commands.command(name="chat_unlock", description="unlocks the channel the command is run in")
@app_commands.describe(reason="Reason for unlocking channel")
async def chat_unlock(interaction: discord.Interaction, reason: Optional[str] = None):
    overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
    overwrite.send_messages = None
    await interaction.channel.set_permissions(interaction.guild.default_role, overwrite=overwrite, reason=reason)
    await interaction.response.send_message(
        embed = discord.Embed(
            description = "This channel has been unlocked. Reason: {reason}"
            discord.color.Green()
        )
    )

@app_commands.command(name="chat_slowmode", description="sets slowmode delay for the channel the command is run in")
@app_commands.describe(delay="Delay in seconds for slowmode")
@app_commands.describe(reason="Reason for setting slowmode")
async def chat_slowmode(interaction: discord.Interaction, delay: int, reason: Optional[str] = None):
    await interaction.channel.edit(slowmode_delay=delay, reason=reason)
    await interaction.response.send_message(
        embed = discord.Embed(
            description = "Slowmode has been set to {delay} seconds. Reason: {reason}"
            discord.color.Green()
        )
    ) 

@app_commands.command(name="fake_ban", description="trolls a user from being banned")
@app_commands.describe(user="user to troll ban")
async def fake_ban(interaction: discord.Interaction, user: discord.Member):
    await interaction.response.send_message(
        embed = discord.Embed(
            description = f"{user.mention} has been banned from the server! Just kidding :)"
            discord.color.Green()
        )
    )

async def setup(bot: commands.Bot):
    await bot.add_cog(ChatModeration(bot))