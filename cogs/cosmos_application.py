import discord
from discord.ext import commands

class CosmosApplications(commands.Cog):

    @discord.command.commands(name="Applications", description="Shows the list of Cosmos applications.")
    async def applications(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(
            title="***Cosmos Department & Moderation Applications***",
            description=(
                "Hello! Thank you for your interest in joining the Cosmos team.\n"
                "To apply for a position, press one of the buttons below, which will then direct you to a different page.\n\n"
                "**Available Positions:**\n"
                "- Moderator Applications\n"
                "- Giveaway Staff Applications\n"
                "- Partnership Staff Applications \n"
                "- Event Staff Applications\n\n"
                "Good luck!"
            ),
            color=discord.Color.blue() empheral=True
            )
        @discord.ui.button(label="Moderation Applications", style=discord.ButtonStyle.primary)
        async def mod_app_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_message(
                embed = discord.Embed(
                    title="Moderator Application",
                    description=(
                    "Hello! Welcome to the Cosmos Moderation Application, otherwise known as CMA. \n"
                    "To apply for our moderation team, there are some requirements you need to meet: \n\n"
                    "- 1st. You must have a clean modlog, meaning no warnings, bans, or kicks in the last 30 days.\n"
                    "- 2nd. You must be somewhat active in our server, meaning you need atleast chatter level 25 or higher. \n"
                    "- 3rd. You must be able to dedicate atleast 4-5 hours a month to moderation. \n\n"
                    "If you meet these requirements, there is a very high chance you will be accepted into our moderation team!\n"
                )
                discord.color=discord.Color=blue()
                set.footer(text="Good luck!")
            )
            )
            @discord.ui.button(label="Apply to join the Moderation Team", style=discord.ButtonStyle.primary)
            async def apply_mod_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(
                    discord.ui.Modal(
                        title="Moderator Application Form",
                        components=[
                            discord.ui.InputText(
                                label="Why do you want to join our moderation team?",
                                style=discord.InputTextStyle.long,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="Do you have any moderation experince? If so, please list the servers you've moderated in.",
                                style=discord.InputTextStyle.long,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="What is your chatter level?",
                                style=discord.InputTextStyle.short,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="What will you contribute to the server as a moderator?",
                                style=discord.InputTextStyle.long,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="Why should we choose you over other applicants?",
                                style=discord.InputTextStyle.long,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                        ],
                    )
                )
            await ctx.respond(embed=embed, view=self)
            self.add_item(mod_app_button)
            self.add_item(apply_mod_button)

        @discord.ui.button(label="Giveaway Staff Applications", style=discord.ButtonStyle.success)
        async def giveaway_app_button(self, interaction: discord.Interaction, button: discord.ui.Button)
            await interaction.response.send_message(
                embed = discord.Embed(
                    title = "Giveaway Staff Application",
                    description=(
                        "Hello! Welcome to the Cosmos Giveaway Staff Applications, otherwise known as CGSA. \n"
                        "To apply for our giveaway staff team, there are some requirements you need to understand and meet:\n\n"
                        "- 1st. You must be active in our server, meaning you need atleast chatter level 15 or higher.\n"
                        "- 2nd. You must have Legendary Sponsor, meaning you must have sponsored 25 giveaways.\n"
                        "- 3rd. You must have a clean modlog, meaning no warnings, bans, or kicks in the last 30 days.\n"
                        "- 4th. You must have basic knowledge of how giveaways work in our server.\n\n"
                        "If you meet these requirements, there is a very high chance you will be accepted into our giveaway staff team, good luck!"
                    )
                    discord.Color=Green()
                    set.footer(text="Good luck!")
                )
            )
            @discord.ui.button(label="Giveaway Staff Application Form", style=discord.ButtonStyle.success)
            async def apply_giveaway_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.send_modal(
                    discord.ui.Modal(
                        title="Giveaway Staff Application Form",
                        components=[
                            discord.ui.InputText(
                                label="Why do you want to join our giveaway staff team?",
                                style=discord.InputTextStyle.long,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="What is your chatter level?",
                                style=discord.InputTextStyle.short,
                                placeholder="Type your answer here...",
                                required=True,
                            ),
                            discord.ui.InputText(
                                label="Would you say your good at using bots?",
                                style=discord.InputTextStyle.short,
                                laceholder="Type your answer here...",
                                required=True,
                        ),
                        discord.ui.InputText(
                            label="Why should we choose you over other applicants?",
                            style=discord.InputTextStyle.long,
                            placeholder="Type your answer here...",
                            required=True,
                        ),
                    ],
                )
            )
        await ctx.respond(embed=embed, view=self)
        self.add_item(giveaway_app_button)
        self.add_item(apply_giveaway_button)

    @discord.ui.button(label="Partnership Staff Applications", style=discord.ButtonStyle.secondary)
    async def partnership_app_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            embed = discord.Embed(
                title = "Partnership Staff Application",
                description=(
                    "Hello! Welcome to the Cosmos Partnership Staff Applications, otherwise known as CPSA. \n"
                    "To apply for our partnership staff team, there are some requirements you need to understand and meet:\n\n"
                    "- 1st. You must be active in our server, meaning you need atleast chatter level 20 or higher.\n"
                    "- 2nd. You must have basic knowledge of how partnerships work in our server.\n"
                    "- 3rd. You must have a clean modlog, meaning no warnings, bans, or kicks in the last 30 days.\n"
                    "- 4th. You must have good communication skills, and must be able to work well with others.\n\n"
                    "If you meet these requirements, there is a very high chance you will be accepted into our partnership staff team, good luck!"
                )
                discord.Color=Grey()
                set.footer(text="Good luck!")
            )
        )
        @discord.ui.button(label="Partnership Staff Application Form", style=discord.ButtonStyle.secondary)
        async def apply_partnership_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.response.send_modal(
                discord.ui.Modal(
                    title="Partnership Staff Application Form",
                    components=[
                        discord.ui.InputText(
                            label="Why do you want to join our partnership staff team?",
                            style=discord.InputTextStyle.long,
                            placeholder="Type your answer here...",
                            required=True,
                        ),
                        discord.ui.InputText(
                            label="What is your chatter level?",
                            style=discord.InputTextStyle.short,
                            placeholder="Type your answer here...",
                            required=True,
                        ),
                        discord.ui.InputText(
                            label="Do you have any experience with partnerships? If so, please explain.",
                            style=discord.InputTextStyle.long,
                            placeholder="Type your answer here...",
                            required=True,
                        ),
                        discord.ui.InputText(
                            label="Why should we choose you over other applicants?",
                            style=discord.InputTextStyle.long,
                            placeholder="Type your answer here...",
                            required=True,
                        ),
                    ],
                )
            )
        await ctx.respond(embed=embed, view=self)
        self.add_item(partnership_app_button)
        self.add_item(apply_partnership_button)