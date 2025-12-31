import discord
from discord.ext import commands

WEBHOOK_URL = "https://discord.com/api/webhooks/1444491754194604062/GBqfIpj83KeWIi72ALx9p2RUrnBJ5Jt-Xb6_93vcRntVMWunnAPliqmWnBnVWRWJHj4m"

class WebhookActionLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.webhook = None

    async def get_webhook(self):
        if self.webhook is None:
            session = self.bot.http._HTTPClient__session
            self.webhook = discord.Webhook.from_url(
                WEBHOOK_URL,
                client=self.bot,
                session=session
            )
        return self.webhook

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        webhook = await self.get_webhook()
        embed = discord.Embed(
            title="Member Banned",
            description=f"{user} has been banned from **{guild.name}**.",
            color=discord.Color.red()
        )
        await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        webhook = await self.get_webhook()
        embed = discord.Embed(
            title="Member Unbanned",
            description=f"{user} has been unbanned from **{guild.name}**.",
            color=discord.Color.green()
        )
        await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # You can't know if they were kicked VS left.
        webhook = await self.get_webhook()
        embed = discord.Embed(
            title="Member Left / Possibly Kicked",
            description=f"{member} left the server.",
            color=discord.Color.orange()
        )
        await webhook.send(embed=embed)

    # Timeout is handled through member update
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Detect timeout start
        if before.timed_out_until != after.timed_out_until and after.timed_out_until is not None:
            until = after.timed_out_until
            webhook = await self.get_webhook()
            embed = discord.Embed(
                title="Member Timed Out",
                description=f"{after} has been timed out until `{until}`.",
                color=discord.Color.dark_orange()
            )
            await webhook.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WebhookActionLogger(bot))
