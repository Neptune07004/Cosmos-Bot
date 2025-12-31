import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
from datetime import timedelta

WARN_FILE = "warnings.json"


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


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = load_warnings()

    @app_commands.command(name="warn", description="Warn a server member.")
    @app_commands.default_permissions(discord.Permissions(manage_messages=True))
    @app_commands.describe(member="Member to warn", reason="Reason for the warning")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        user_id = str(member.id)

        if user_id not in self.warnings:
            self.warnings[user_id] = []

        self.warnings[user_id].append(reason)
        save_warnings(self.warnings)

        try:
            embed = discord.Embed(
                description=f"You were warned in {interaction.guild.name}.\n\nReason: {reason}",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        except discord.Forbidden:
            pass

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{member.mention} has been warned.\nReason: {reason}",
                color=discord.Color.green()
            )
        )

        if len(self.warnings[user_id]) >= 5:
            try:
                await member.send(
                    embed=discord.Embed(
                        description=f"You have received 5 warnings in {interaction.guild.name}.",
                        color=discord.Color.red(),
                    )
                )
            except:
                pass

            await member.kick(reason="Exceeded 5 warnings")

            await interaction.followup.send(
                f"{member.mention} has been auto-kicked.",
            )

    @app_commands.command(name="warnings", description="Show warnings for a member.")
    @app_commands.describe(member="Member to check warnings for")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)

        if user_id not in self.warnings or len(self.warnings[user_id]) == 0:
            await interaction.response.send_message(
                f"{member.mention} has no warnings.",
                ephemeral=True
            )
            return

        reasons = "\n".join([f"{i+1}. {reason}" for i, reason in enumerate(self.warnings[user_id])])

        embed = discord.Embed(
            title=f"Warnings for {member}",
            description=reasons,
            color=discord.Color.red()
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="clearwarnings", description="Clear a member's warnings.")
    @app_commands.default_permissions(discord.Permissions(manage_messages=True))
    @app_commands.describe(member="Member whose warnings will be cleared")
    async def clearwarnings(self, interaction: discord.Interaction, member: discord.Member):
        user_id = str(member.id)

        if user_id in self.warnings:
            del self.warnings[user_id]
            save_warnings(self.warnings)
            await interaction.response.send_message(
                f"Cleared all warnings for {member.mention}.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"{member.mention} has no warnings.",
                ephemeral=True
            )

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.default_permissions(discord.Permissions(ban_members=True))
    @app_commands.describe(member="Member to ban", reason="Reason", appeal="Appeal status")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", appeal: str = "You may appeal in the appeals channel."):

        try:
            embed = discord.Embed(
                description=f"You were banned from {interaction.guild.name}.\n\nReason: {reason}\nAppeal Status: {appeal}",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        except:
            pass

        await member.ban(reason=reason)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{member.mention} has been banned.\nReason: {reason}. Appeal Status: {appeal}",
                color=discord.Color.green()
            )
        )

    @app_commands.command(name="unban", description="Unban a banned user.")
    @app_commands.default_permissions(discord.Permissions(ban_members=True))
    @app_commands.describe(user_id="ID of the banned user", reason="Reason for unban")
    async def unban(self, interaction: discord.Interaction, user_id: int, reason: str):
        try:
            user = await self.bot.fetch_user(user_id)
            await interaction.guild.unban(user, reason=reason)

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{user.mention} has been unbanned.\nReason: {reason}",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Error: `{e}`",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="kick", description="Kick a member.")
    @app_commands.default_permissions(discord.Permissions(kick_members=True))
    @app_commands.describe(member="Member to kick", reason="Reason")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):

        try:
            embed = discord.Embed(
                description=f"You were kicked from {interaction.guild.name}.\n\nReason: {reason}",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        except:
            pass

        await member.kick(reason=reason)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{member.mention} has been kicked.\nReason: {reason}",
                color=discord.Color.green()
            )
        )

    @app_commands.command(name="softban", description="Softban (ban + unban) a member.")
    @app_commands.default_permissions(discord.Permissions(ban_members=True))
    @app_commands.describe(member="Member", reason="Reason")
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):

        try:
            embed = discord.Embed(
                description=f"You were softbanned from {interaction.guild.name}.\n\nReason: {reason}",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        except:
            pass

        await interaction.guild.ban(member, reason=reason)
        await interaction.guild.unban(member, reason="Softban unban")

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{member.mention} has been softbanned.\nReason: {reason}",
                color=discord.Color.green()
            )
        )

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.default_permissions(discord.Permissions(moderate_members=True))
    @app_commands.describe(member="Member", duration="Minutes", reason="Reason")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):

        if duration < 1 or duration > 40320:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="Timeout duration must be **1–40320 minutes**.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        try:
            await member.timeout(timedelta(minutes=duration), reason=reason)

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"{member.mention} has been timed out for **{duration} minutes**.\nReason: **{reason}**",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Error: `{e}`",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="untimeout", description="Remove a timeout.")
    @app_commands.default_permissions(discord.Permissions(moderate_members=True))
    @app_commands.describe(member="Member", reason="Reason")
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):

        try:
            await member.timeout(None, reason=reason)

            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Timeout removed from {member.mention}.\nReason: **{reason}**",
                    color=discord.Color.green()
                )
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    description=f"Error: `{e}`",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @app_commands.command(name="purge", description="Purge messages.")
    @app_commands.default_permissions(discord.Permissions(manage_messages=True))
    @app_commands.describe(amount="Number to purge", user="Filter by user (optional)")
    async def purge(self, interaction: discord.Interaction, amount: int, user: discord.Member = None):

        if amount < 1 or amount > 1000:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="Amount must be **1–1000**.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        def check(msg):
            return user is None or msg.author.id == user.id

        deleted = await interaction.channel.purge(limit=amount, check=check)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"Deleted **{len(deleted)}** messages.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @app_commands.command(name="tempban", description="Temporarily ban a member.")
    @app_commands.default_permissions(discord.Permissions(ban_members=True))
    @app_commands.describe(member="Member", duration="Minutes", reason="Reason")
    async def tempban(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = "No reason provided"):

        if duration < 1 or duration > 43200:
            return await interaction.response.send_message(
                embed=discord.Embed(
                    description="Tempban duration must be **1–43200 minutes**.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

        try:
            embed = discord.Embed(
                description=f"You were temporarily banned from {interaction.guild.name} for **{duration} minutes**.\n\nReason: {reason}",
                color=discord.Color.red(),
            )
            await member.send(embed=embed)
        except:
            pass

        await member.ban(reason=reason)

        await interaction.response.send_message(
            embed=discord.Embed(
                description=f"{member.mention} has been temporarily banned for **{duration} minutes**.\nReason: {reason}",
                color=discord.Color.green()
            )
        )

        # wait for expiration
        await asyncio.sleep(duration * 60)

        try:
            await interaction.guild.unban(member, reason="Temporary ban expired")
        except:
            pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))