import discord
from discord.ext import commands

WEBHOOK_URL = "https://discord.com/api/webhooks/1444482996395708667/SBQN73HSxFvwzqrxj7OPgbGExxslu0kkVn2akyqkCpIT2lGUZk66zhcfyaG0ilx0el9B"


class WebhookLogger(commands.Cog):
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
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot:
            return
        if before.content == after.content:
            return

        webhook = await self.get_webhook()

        embed = discord.Embed(
            title="Message Edited",
            description=(
                f"**User:** {before.author.mention}\n"
                f"**Channel:** {before.channel.mention}\n\n"
                f"**Before:** {before.content}\n"
                f"**After:** {after.content}"
            ),
            color=discord.Color.orange()
        )

        embed.set_footer(text=f"Original Message Link: {before.jump_url}")

        await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return

        webhook = await self.get_webhook()

        embed = discord.Embed(
            title="Message Deleted",
            description=(
                f"**User:** {message.author.mention}\n"
                f"**Channel:** {message.channel.mention}\n\n"
                f"**Content:** {message.content}"
            ),
            color=discord.Color.red()
        )

        await webhook.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        webhook = await self.get_webhook()

        # Roles added
        added = [r for r in after.roles if r not in before.roles]
        if added:
            role_list = ", ".join([f"`{r.name}`" for r in added])
            embed = discord.Embed(
                title="Role Added",
                description=(
                    f"**User:** {after.mention}\n"
                    f"**Roles:** {role_list}"
                ),
                color=discord.Color.blue()
            )
            await webhook.send(embed=embed)

        # Roles removed
        removed = [r for r in before.roles if r not in after.roles]
        if removed:
            role_list = ", ".join([f"`{r.name}`" for r in removed])
            embed = discord.Embed(
                title="Role Removed",
                description=(
                    f"**User:** {after.mention}\n"
                    f"**Roles:** {role_list}"
                ),
                color=discord.Color.blue()
            )
            await webhook.send(embed=embed)


async def setup(bot):
    await bot.add_cog(WebhookLogger(bot))