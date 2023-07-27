import discord
from discord.ext import commands
from discord import app_commands

import typing

from scripts import nubot
from scripts.utils import economy_helpers, embeds


class Bal(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @app_commands.command(name="bal")
    @app_commands.describe(member="member, who\'s balance will be checked")
    async def bal(
            self,
            interaction: discord.Interaction,
            member: typing.Optional[discord.Member] = None
    ) -> None:
        """Displays yours or someone else's balance"""
        if member is None:
            member = interaction.user

        money: int = await economy_helpers.get_balance(member.id, interaction.guild.id)

        embed: discord.Embed = discord.Embed(
            title=f"**{member.name}\'s** balance:",
            description=f":coin: **{money}**",
            color=embeds.DEFAULT_EMBED_COLOR
        )
        embed.set_thumbnail(url=member.avatar.url)

        await interaction.response.send_message(embed=embed)


async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Bal(bot))
