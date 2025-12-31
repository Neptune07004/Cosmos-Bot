import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
import asyncio
import datetime
import io
import html
import json
import os
from typing import Optional, Dict, Any, List

# Configuration - set these appropriately
PANEL_CHANNEL_ID: Optional[int] = 1443615796512166050
TRANSCRIPT_LOG_CHANNEL_ID: Optional[int] = 1443780121134895115

TICKETS_JSON_PATH = "report.json"
PANEL_JSON_PATH = "panel2.json"
TICKET_COUNTER_KEY = "___counter"

AUTO_CLOSE_MINUTES = 15
TICKET_LOG_FOLDER = "report_logs"
os.makedirs(TICKET_LOG_FOLDER, exist_ok=True)

_ticket_file_lock = asyncio.Lock()


async def load_tickets() -> Dict[str, Any]:
    async with _ticket_file_lock:
        if not os.path.exists(TICKETS_JSON_PATH):
            with open(TICKETS_JSON_PATH, "w", encoding="utf-8") as f:
                json.dump({TICKET_COUNTER_KEY: 0}, f, indent=2)
            return {TICKET_COUNTER_KEY: 0}

        with open(TICKETS_JSON_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {TICKET_COUNTER_KEY: 0}


async def save_tickets(data: Dict[str, Any]) -> None:
    async with _ticket_file_lock:
        with open(TICKETS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def load_panel_record() -> Dict[str, Any]:
    if not os.path.exists(PANEL_JSON_PATH):
        return {}
    try:
        with open(PANEL_JSON_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_panel_record(data: Dict[str, Any]) -> None:
    with open(PANEL_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def make_ticket_id(ticket_type: str, username: str, counter: int) -> str:
    safe_user = "".join(ch for ch in username.lower() if ch.isalnum() or ch in ("-", "_"))[:16]
    return f"{ticket_type}-{safe_user}-{counter:04d}"


class CloseReasonModal(discord.ui.Modal, title="Close Ticket Reason"):
    reason = discord.ui.TextInput(
        label="Reason for closing the ticket",
        style=discord.TextStyle.long,
        required=False,
        max_length=1024,
    )

    def __init__(self, callback):
        super().__init__()
        self.callback_fn = callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_fn(interaction, self.reason.value)


async def build_readable_transcript(channel: discord.TextChannel, messages: List[discord.Message], ticket_meta: Dict[str, Any]) -> io.BytesIO:
    opener = ticket_meta.get("opener_name", f"<@{ticket_meta.get('opener_id')}>")
    claimed_by = ticket_meta.get("claimed_by_name", "None")
    closed_by = ticket_meta.get("closed_by_name", ticket_meta.get("closed_by", "Unknown"))
    reason = ticket_meta.get("close_reason", "")

    lines = []
    lines.append("**TOP OF TRANSCRIPT**")
    lines.append(f"Ticket creator: {html.escape(str(opener))}")
    lines.append(f"Admin handling the ticket: {html.escape(str(claimed_by))}")
    lines.append(f"Closed by: {html.escape(str(closed_by))}")
    lines.append(f"Reason: {html.escape(str(reason))}")
    lines.append("")

    for msg in messages:
        timestamp = msg.created_at.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        author = f"{msg.author.name}#{msg.author.discriminator}"
        content = msg.content or ""
        safe_content = html.escape(content)
        line = f"{timestamp}, {html.escape(author)}, {safe_content}"
        lines.append(line)

        for att in msg.attachments:
            lines.append(f"{timestamp}, {html.escape(author)}, [attachment] {html.escape(att.url)}")

    body = "\n".join(lines)

    html_doc = (
        "<html><head><meta charset='utf-8'><title>Ticket Transcript</title></head>"
        "<body><pre style='white-space:pre-wrap;font-family:monospace;'>"
    )
    html_doc += html.escape(body)
    html_doc += "</pre></body></html>"

    bio = io.BytesIO(html_doc.encode("utf-8"))
    bio.seek(0)
    return bio


class TicketView(discord.ui.View):
    COOLDOWN_SECONDS = 60
    cooldowns: Dict[int, float] = {}

    def __init__(self, panel_channel_id: Optional[int] = None, staff_role_id: Optional[int] = None):
        super().__init__(timeout=None)
        self.panel_channel_id = panel_channel_id
        self.staff_role_id = staff_role_id

    async def check_cooldown(self, interaction: discord.Interaction) -> bool:
        now = datetime.datetime.utcnow().timestamp()
        last = self.cooldowns.get(interaction.user.id, 0)
        if now - last < self.COOLDOWN_SECONDS:
            remaining = int(self.COOLDOWN_SECONDS - (now - last))
            await interaction.response.send_message(f"Please wait {remaining}s before opening another ticket.", ephemeral=True)
            return False
        self.cooldowns[interaction.user.id] = now
        return True

    async def create_ticket(self, interaction: discord.Interaction, ticket_type: str):
        if not await self.check_cooldown(interaction):
            return

        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("This command must be used in a server.", ephemeral=True)
            return

        panel_ch = None
        if self.panel_channel_id:
            panel_ch = guild.get_channel(self.panel_channel_id)
        category = panel_ch.category if panel_ch and isinstance(panel_ch, discord.TextChannel) else None

        tickets = await load_tickets()
        counter = tickets.get(TICKET_COUNTER_KEY, 0) + 1
        tickets[TICKET_COUNTER_KEY] = counter

        ticket_id = make_ticket_id(ticket_type, interaction.user.name, counter)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        if self.staff_role_id:
            role = guild.get_role(self.staff_role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=ticket_id,
            category=category,
            overwrites=overwrites,
            topic=f"TicketOpenerID:{interaction.user.id}",
            reason=f"Ticket opened by {interaction.user}"
        )

        created_ts = int(datetime.datetime.utcnow().timestamp())

        tickets[ticket_id] = {
            "ticket_id": ticket_id,
            "channel_id": channel.id,
            "opener_id": interaction.user.id,
            "opener_name": f"{interaction.user.name}#{interaction.user.discriminator}",
            "ticket_type": ticket_type,
            "created_at": created_ts,
            "auto_close_at": None,
            "closed": False,
            "claimed_by": None,
            "claimed_by_name": None
        }

        await save_tickets(tickets)

        await interaction.response.send_message(
            f"Your **{ticket_type}** ticket has been created: {channel.mention}",
            ephemeral=True
        )

        staff_mention = f"<@&{1443751370065707141}> <@&{1443751453142290442}>"

        embed = discord.Embed(
            title="Cosmos Report Ticket",
            description=(
                f"Hello {interaction.user.mention}, welcome to the Cosmos Report Program, or CRP. \n\n"
                ""
                f"Our moderation will be with you shortly.\n"
                ""
                f"While waiting, please describe your issue, who you would like to report, why your reporting them, and evidence.\n\n"
                ""
                f"Thank you!\n"
                f"**Ticket ID:** {ticket_id}"
            ),
            color=discord.Color.light_grey()
        )

        view = CloseTicketView(opener_id=interaction.user.id, ticket_id=ticket_id)

        await channel.send(content=staff_mention or "", embed=embed, view=view)

    @discord.ui.button(label="🚨 Report", style=discord.ButtonStyle.primary)
    async def appeal_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.create_ticket(interaction, "report")


class CloseTicketView(discord.ui.View):
    def __init__(self, opener_id: int, ticket_id: Optional[str] = None):
        super().__init__(timeout=None)
        self.opener_id = opener_id
        self.ticket_id = ticket_id
        self.closed = False

    @discord.ui.button(label="Claim Ticket", style=discord.ButtonStyle.secondary)
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Only moderation staff can claim tickets.", ephemeral=True)
            return

        tickets = await load_tickets()
        entry = tickets.get(self.ticket_id, {})

        if entry.get("claimed_by"):
            await interaction.response.send_message("This ticket is already claimed.", ephemeral=True)
            return

        entry["claimed_by"] = interaction.user.id
        entry["claimed_by_name"] = f"{interaction.user.name}#{interaction.user.discriminator}"
        tickets[self.ticket_id] = entry
        await save_tickets(tickets)

        button.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(f"{interaction.user.mention} has claimed this ticket.", ephemeral=False)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if channel is None or not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("This must be used within a ticket channel.", ephemeral=True)
            return

        if interaction.user.id == self.opener_id:

            async def opener_cb(inter: discord.Interaction, reason: str):
                confirm = ConfirmCloseView(
                    channel=channel,
                    opener_id=self.opener_id,
                    ticket_id=self.ticket_id,
                    opener_reason=reason,
                    skip_wait=True
                )
                await inter.response.defer(ephemeral=True)
                await confirm._finalize_close(closed_by=str(inter.user.id), auto_closed=False)

            modal = CloseReasonModal(opener_cb)
            await interaction.response.send_modal(modal)
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("Only moderation staff can request closure.", ephemeral=True)
            return

        async def staff_cb(inter: discord.Interaction, reason: str):
            staff_reason = reason or ""
            auto_close_dt = datetime.datetime.utcnow() + datetime.timedelta(minutes=AUTO_CLOSE_MINUTES)
            auto_close_ts = int(auto_close_dt.timestamp())
            rel_ts = f"<t:{auto_close_ts}:R>"

            embed = discord.Embed(
                title="Ticket Closure Requested",
                description=(
                    f"A staff member ({inter.user.mention}) has requested to close this ticket.\n\n"
                    f"Staff reason: {html.escape(staff_reason)}\n\n"
                    f"Opener must confirm within {AUTO_CLOSE_MINUTES} minutes: {rel_ts}\n\n"
                    "If the opener does not confirm, the ticket will be auto-closed."
                ),
                color=discord.Color.orange()
            )

            confirm_view = ConfirmCloseView(
                channel=channel,
                opener_id=self.opener_id,
                ticket_id=self.ticket_id,
                moderator_reason=staff_reason,
                auto_close_timestamp=auto_close_ts
            )

            await inter.response.send_message("Staff reason submitted. Waiting for opener confirmation...", ephemeral=True)
            await channel.send(embed=embed, view=confirm_view)

            try:
                asyncio.create_task(confirm_view.start_auto_close_timer())
            except Exception:
                pass

        modal = CloseReasonModal(staff_cb)
        await interaction.response.send_modal(modal)


class ConfirmCloseView(discord.ui.View):
    def __init__(
        self,
        channel: discord.TextChannel,
        opener_id: int,
        ticket_id: Optional[str] = None,
        initiator_id: Optional[int] = None,
        skip_wait: bool = False,
        moderator_reason: Optional[str] = None,
        opener_reason: Optional[str] = None,
        auto_close_timestamp: Optional[int] = None
    ):
        super().__init__(timeout=None)
        self.channel = channel
        self.opener_id = opener_id
        self.ticket_id = ticket_id
        self.skip_wait = skip_wait
        self.moderator_reason = moderator_reason or ""
        self.opener_reason = opener_reason
        self.auto_close_timestamp = auto_close_timestamp
        self._auto_task: Optional[asyncio.Task] = None
        self.closed = False

    async def start_auto_close_timer(self):
        if not self.auto_close_timestamp or self.skip_wait:
            return

        now = int(datetime.datetime.utcnow().timestamp())
        wait = max(0, self.auto_close_timestamp - now)
        if wait <= 0:
            wait = 1

        try:
            await asyncio.sleep(wait)
        except asyncio.CancelledError:
            return

        if not self.closed:
            try:
                await self.channel.send("No confirmation received from the ticket opener — auto-closing the ticket now.")
            except:
                pass

            self.opener_reason = self.opener_reason or "No opener confirmation (auto-closed)"
            self.moderator_reason = self.moderator_reason or "No moderator reason provided"

            await self._finalize_close(closed_by="system", auto_closed=True)

    @discord.ui.button(label="Confirm Close", style=discord.ButtonStyle.success)
    async def confirm_close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opener_id:
            await interaction.response.send_message("Only the ticket opener can confirm.", ephemeral=True)
            return

        if not self.opener_reason:

            async def opener_modal_cb(inter: discord.Interaction, reason: str):
                self.opener_reason = reason
                await inter_follow_close(inter, self)

            modal = CloseReasonModal(opener_modal_cb)
            await interaction.response.send_modal(modal)
            return

        await interaction.response.defer(ephemeral=True)
        await self._finalize_close(closed_by=str(interaction.user.id), auto_closed=False)

    async def _finalize_close(self, closed_by: str, auto_closed: bool = False):
        if self.closed:
            return

        self.closed = True

        if self._auto_task and not self._auto_task.done():
            self._auto_task.cancel()

        tickets = await load_tickets()
        entry = tickets.get(self.ticket_id, {})

        close_ts = int(datetime.datetime.utcnow().timestamp())
        close_reason = self.opener_reason or self.moderator_reason or "No reason provided"

        entry.update({
            "ticket_id": self.ticket_id,
            "channel_id": self.channel.id,
            "opener_id": entry.get("opener_id", self.opener_id),
            "ticket_type": entry.get("ticket_type", ""),
            "created_at": entry.get("created_at"),
            "closed": True,
            "closed_at": close_ts,
            "close_reason": close_reason,
            "closed_by": closed_by,
            "auto_closed": auto_closed
        })

        claimed_by = entry.get("claimed_by")
        if claimed_by and not entry.get("claimed_by_name"):
            member = self.channel.guild.get_member(claimed_by)
            if member:
                entry["claimed_by_name"] = f"{member.name}#{member.discriminator}"

        tickets[self.ticket_id] = entry
        await save_tickets(tickets)

        messages = [msg async for msg in self.channel.history(limit=None, oldest_first=True)]
        transcript_io = await build_readable_transcript(self.channel, messages, entry)
        transcript_fp = discord.File(
            fp=transcript_io,
            filename=f"{self.ticket_id or self.channel.name}_transcript.html"
        )

        try:
            filename = os.path.join(TICKET_LOG_FOLDER, f"{(self.ticket_id or self.channel.name)}_meta.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        except Exception:
            pass

        try:
            opener_member = self.channel.guild.get_member(entry.get("opener_id"))
            if opener_member:
                dm_embed = discord.Embed(
                    title="Report Ticket Closed",
                    description=(
                        f"Your ticket **{self.ticket_id or self.channel.name}** has been closed.\n"
                        f"Reason: {html.escape(close_reason)}\n\n"
                        f"If you are on the OperaGX browser, colors may appear differently.\n"
                        f"Thank you for using Cosmos Reporting System!"
                    ),
                    color=discord.Color.blue()
                )
                try:
                    transcript_io.seek(0)
                    await opener_member.send(embed=dm_embed, file=transcript_fp)
                except:
                    pass
        except Exception:
            pass

        if TRANSCRIPT_LOG_CHANNEL_ID:
            try:
                log_ch = self.channel.guild.get_channel(TRANSCRIPT_LOG_CHANNEL_ID)
                if log_ch:
                    transcript_io.seek(0)
                    meta_bytes = io.BytesIO(json.dumps(entry, indent=2).encode("utf-8"))

                    await log_ch.send(
                        embed=discord.Embed(
                            title="Ticket Closed",
                            description=(
                                f"Ticket: {self.ticket_id or self.channel.name}\n"
                                f"Channel: {self.channel.mention}\n"
                                f"Opened by: <@{entry.get('opener_id')}>\n"
                                f"Claimed by: {entry.get('claimed_by_name', 'None')}\n"
                                f"Closed by: {closed_by}\n"
                                f"Reason: {html.escape(close_reason)}"
                            ),
                            color=discord.Color.dark_blue()
                        ),
                        files=[
                            discord.File(
                                fp=io.BytesIO(transcript_io.read()),
                                filename=f"{self.ticket_id or self.channel.name}_transcript.html"
                            ),
                            discord.File(fp=meta_bytes, filename=f"{self.ticket_id or self.channel.name}_meta.json")
                        ]
                    )
            except Exception:
                pass

        try:
            await self.channel.send(f"Ticket closed. <@{entry.get('opener_id')}>")
        except:
            pass

        await asyncio.sleep(2)
        try:
            await self.channel.delete(reason=f"Ticket {(self.ticket_id or self.channel.name)} closed.")
        except:
            pass


async def inter_follow_close(interaction: discord.Interaction, view: ConfirmCloseView):
    try:
        await interaction.response.send_message("Thanks — closing ticket now.", ephemeral=True)
    except:
        pass
    await view._finalize_close(closed_by=str(interaction.user.id), auto_closed=False)


def create_ticket_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Cosmos Reporting System",
        description=(
            "To be able to report someone in our server, please make sure to review our rules before reporting them.\n\n"
            ""
            "- Make sure to include proof of what they are being blamed of\n\n"
            "- Do not spam ping our moderation staff, they will get with you shortly\n\n"
            "- Make sure not to have anything blured out, only sensitive data may be blured out\n\n"
            "- If we find out your report was made with bias, you will be temporarily banned from our reporting system.\n"
        ),
        color=discord.Color.dark_orange()
    )

    embed.set_footer(text="Click the button below to report!")
    return embed


class TicketReport(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self._ensure_panel_and_views())

    async def _ensure_panel_and_views(self):
        await self.bot.wait_until_ready()
        try:
            panel_record = load_panel_record()
            channel_id = panel_record.get("channel_id") or PANEL_CHANNEL_ID
            if not channel_id:
                print("[TicketReport] PANEL_CHANNEL_ID not configured.")
                return

            channel = None
            for g in self.bot.guilds:
                ch = g.get_channel(channel_id)
                if ch:
                    channel = ch
                    break

            if not channel:
                print(f"[TicketReport] Panel channel {channel_id} not found in any guilds the bot is in.")
                return

            message_id = panel_record.get("message_id")
            msg_found = None

            if message_id:
                try:
                    msg_found = await channel.fetch_message(message_id)
                except Exception:
                    msg_found = None

            if not msg_found:
                async for m in channel.history(limit=200):
                    if m.author == self.bot.user and m.embeds:
                        title = m.embeds[0].title or ""
                        if "Cosmos Report Program" in title:
                            msg_found = m
                            break

            if not msg_found:
                view = TicketView(panel_channel_id=channel.id, staff_role_id=panel_record.get("staff_role_id"))
                embed = create_ticket_embed()

                panel_msg = await channel.send(embed=embed, view=view)

                save_panel_record({
                    "message_id": panel_msg.id,
                    "channel_id": channel.id,
                    "staff_role_id": panel_record.get("staff_role_id")
                })

                try:
                    self.bot.add_view(view, message_id=panel_msg.id)
                except Exception:
                    self.bot.add_view(view)

                print(f"[TicketReport] Ticket panel sent to channel {channel.id} (message id {panel_msg.id}).")
                return

            try:
                self.bot.add_view(
                    TicketView(panel_channel_id=channel.id, staff_role_id=panel_record.get("staff_role_id")),
                    message_id=msg_found.id
                )
            except Exception:
                self.bot.add_view(
                    TicketView(panel_channel_id=channel.id, staff_role_id=panel_record.get("staff_role_id"))
                )

            save_panel_record({
                "message_id": msg_found.id,
                "channel_id": channel.id,
                "staff_role_id": panel_record.get("staff_role_id")
            })

            print(f"[TicketReport] Ticket panel is present in channel {channel.id} (message id {msg_found.id}).")

        except Exception as exc:
            print(f"[TicketReport] Error in _ensure_panel_and_views: {exc}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await asyncio.sleep(2)
        await self._ensure_panel_and_views()


async def setup(bot: commands.Bot):
    await bot.add_cog(TicketReport(bot))