import discord
from discord.ext import commands
from discord import app_commands

import random
import typing

from scripts import nubot
from scripts.utils import embeds, economy_helpers


class Gambling(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @app_commands.command(name="beg")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    async def beg(self, interaction: discord.Interaction):
        """Lets you earn a bit of money with a relatively low risk of losing it"""
        possibilities: typing.List[int] = [-5, 2, 5, 10, 20, 50]
        chances: typing.List[int] = [10, 15, 25, 25, 20, 5]
        outcome: int = random.choices(possibilities, weights=chances)[0]

        current_balance: int = await economy_helpers.get_balance(interaction.user.id, interaction.guild.id)
        new_balance: int = current_balance + outcome

        coins_lost: int

        if new_balance > 0:
            await economy_helpers.set_balance(interaction.user.id, interaction.guild.id, new_balance)
            coins_lost = abs(outcome)
        else:
            await economy_helpers.set_balance(interaction.user.id, interaction.guild.id, 0)
            coins_lost = current_balance

        embed: discord.Embed
        if outcome > 0:
            embed = discord.Embed(
                title="**You've managed to earn some money!**",
                description=f"**:coin: {outcome}** has been added to your account!",
                color=embeds.DEFAULT_EMBED_COLOR
            )
        else:
            embed = discord.Embed(
                title="**You got robbed!**",
                description=f"You lost **:coin: {coins_lost}**!",
                color=embeds.DEFAULT_EMBED_COLOR
            )

        await interaction.response.send_message(embed=embed)

    @beg.error
    async def beg_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(embed=embeds.command_on_cooldown(error.retry_after), ephemeral=True)
        else:
            raise error


async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Gambling(bot))
