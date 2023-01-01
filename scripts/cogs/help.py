import discord
from discord.ext import commands
from discord import app_commands

import typing

from scripts import nubot
from scripts.utils import embeds

class Help(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @app_commands.command(name="help")
    async def help(self, interaction: discord.Interaction):
        """See all of Nubot's commands"""
        embed: discord.Embed = discord.Embed(
            title="🔎 Help 🔍",
            description="All of Nubot\'s commands",
            color=embeds.DEFAULT_EMBED_COLOR
        )

        commands_string: str = "```"

        commands = [
            command for command in self.bot.tree.get_commands()
            if not isinstance(command, discord.app_commands.ContextMenu)
        ]

        c: int = 1
        for command in commands:
            commands_string += command.name
            if c != len(commands):
                commands_string += "\n"
            c += 1

        commands_string += "```"

        embed.add_field(
            name="Commands:",
            value=commands_string
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Help(bot))