import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import io
import random
from datetime import datetime, timedelta

from cogs.giveaway_db import get_db, setup_tables

ALLOWED_ROLE = 1443689224439070811


# ------------------------------
# Persistent Join Button
# ------------------------------
class JoinGiveawayButton(discord.ui.Button):
    def __init__(self, giveaway_id: int):
        super().__init__(
            label="🎉 Join Giveaway",
            style=discord.ButtonStyle.blurple,
            custom_id=f"join_g_{giveaway_id}"
        )
        self.giveaway_id = giveaway_id

    async def callback(self, interaction: discord.Interaction):
        db = await get_db()
        cur = await db.cursor()
        await cur.execute(
            "INSERT IGNORE INTO giveaway_entries (giveaway_id, user_id) VALUES (%s,%s)",
            (self.giveaway_id, interaction.user.id)
        )
        await cur.close()
        db.close()
        await interaction.response.send_message("🎉 You entered the giveaway!", ephemeral=True)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.add_item(JoinGiveawayButton(giveaway_id))


# ------------------------------
# Giveaway Cog
# ------------------------------
class GiveawayCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.loop.create_task(self.startup())

    async def startup(self):
        await self.bot.wait_until_ready()
        await setup_tables()
        await self.load_views()
        self.bot.loop.create_task(self.giveaway_scheduler())

    async def load_views(self):
        db = await get_db()
        cur = await db.cursor()
        await cur.execute("SELECT id FROM giveaways WHERE launched = 1 AND ended = 0")
        for (gid,) in await cur.fetchall():
            self.bot.add_view(GiveawayView(gid))
        await cur.close()
        db.close()

    async def giveaway_scheduler(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                db = await get_db()
                cur = await db.cursor()

                # End giveaways
                await cur.execute(
                    "SELECT id, channel_id, message_id, winners FROM giveaways "
                    "WHERE ended = 0 AND end_time <= NOW() AND launched = 1"
                )
                ending = await cur.fetchall()
                for gid, channel_id, msg_id, winners in ending:
                    await self.pick_winners(gid, channel_id, msg_id, winners)
                    await cur.execute("UPDATE giveaways SET ended = 1 WHERE id=%s", (gid,))

                await cur.close()
                db.close()
            except Exception as e:
                print("Scheduler error:", e)
            await asyncio.sleep(5)  # shorter interval

    async def pick_winners(self, gid, channel_id, msg_id, winners):
        db = await get_db()
        cur = await db.cursor()
        await cur.execute("SELECT user_id FROM giveaway_entries WHERE giveaway_id=%s", (gid,))
        entries = [r[0] for r in await cur.fetchall()]
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            return
        msg = await channel.fetch_message(msg_id)
        if len(entries) == 0:
            await msg.reply("Not enough participants to pick a winner.")
            await cur.close()
            db.close()
            return
        if len(entries) < winners:
            winners = len(entries)
        selected = random.sample(entries, winners)
        mentions = " ".join(f"<@{uid}>" for uid in selected)
        await msg.reply(f"**Winners for Giveaway ID {gid}:** {mentions}")
        await cur.close()
        db.close()

    @app_commands.command(
        name="make_giveaway",
        description="Start a giveaway immediately."
    )
    async def make_giveaway(
        self,
        interaction: discord.Interaction,
        sponsor: str,
        prize: str,
        description: str,
        duration_minutes: int,
        winners: int,
        image: discord.Attachment = None
    ):
        # Permission check
        if not any(r.id == ALLOWED_ROLE for r in interaction.user.roles):
            return await interaction.response.send_message(
                "Missing permissions.", ephemeral=True
            )

        start_dt = datetime.utcnow()
        end_dt = start_dt + timedelta(minutes=duration_minutes)

        img_bytes = await image.read() if image else None

        db = await get_db()
        cur = await db.cursor()
        await cur.execute(
            "INSERT INTO giveaways (channel_id, sponsor, prize, description, start_time, end_time, winners, image, launched) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)",
            (interaction.channel.id, sponsor, prize, description, start_dt, end_dt, winners, img_bytes)
        )
        gid = cur.lastrowid
        await cur.close()
        db.close()

        # Create embed with Discord timestamp for end time
        end_timestamp = int(end_dt.timestamp())
        embed = discord.Embed(
            title=f"🎉 GIVEAWAY — ID {gid}",
            description=(
                f"**Sponsor:** {sponsor}\n"
                f"**Prize:** {prize}\n"
                f"**Description:** {description}\n"
                f"**Ends:** <t:{end_timestamp}:R>\n"
                f"**Winners:** {winners}"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Reroll with `.reroll {gid}`")

        file = discord.File(io.BytesIO(img_bytes), filename="giveaway.png") if img_bytes else None
        msg = await interaction.channel.send(embed=embed, file=file, view=GiveawayView(gid))

        # Update message_id in DB
        db = await get_db()
        cur = await db.cursor()
        await cur.execute("UPDATE giveaways SET message_id=%s WHERE id=%s", (msg.id, gid))
        await cur.close()
        db.close()

        await interaction.response.send_message(
            f"Giveaway started! ID: `{gid}`", ephemeral=True
        )

    @commands.command(name="reroll")
    async def reroll_cmd(self, ctx, giveaway_id: int):
        db = await get_db()
        cur = await db.cursor()
        await cur.execute(
            "SELECT channel_id, message_id, winners FROM giveaways WHERE id=%s",
            (giveaway_id,)
        )
        row = await cur.fetchone()
        if not row:
            await ctx.send("Invalid giveaway ID.")
            await cur.close()
            db.close()
            return
        channel_id, msg_id, winners = row
        await self.pick_winners(giveaway_id, channel_id, msg_id, winners)
        await ctx.send(f"Rerolled Giveaway `{giveaway_id}`!")
        await cur.close()
        db.close()


async def setup(bot):
    await bot.add_cog(GiveawayCog(bot))