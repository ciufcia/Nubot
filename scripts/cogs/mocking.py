import discord
from discord.ext import commands
from discord import app_commands

import aiosqlite
import typing

from scripts import nubot
from scripts.utils import embeds


class Mocking(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

        self.mock_context_menu = app_commands.ContextMenu(name='mock', callback=self.mock_ctx_menu)
        self.bot.tree.add_command(self.mock_context_menu)

        self.unmock_context_menu = app_commands.ContextMenu(name='unmock', callback=self.unmock_ctx_menu)
        self.bot.tree.add_command(self.unmock_context_menu)

    @app_commands.command(name="mock")
    @app_commands.describe(member="member to mock")
    async def mock_command(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Mocks a member, whenever they send a message"""
        await self.mock(interaction, member)

    async def mock_ctx_menu(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await self.mock(interaction, member)

    @app_commands.command(name="unmock")
    @app_commands.describe(member="member to stop mocking")
    async def unmock_command(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Stops mocking a member"""
        await self.unmock(interaction, member)

    async def unmock_ctx_menu(self, interaction: discord.Interaction, member: discord.Member) -> None:
        await self.unmock(interaction, member)

    @classmethod
    async def mock(cls, interaction: discord.Interaction, member: discord.Member) -> None:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=embeds.command_usage_denied("*Requires administrator permissions*"),
                ephemeral=True
            )
            return

        is_already_mocked: bool = False

        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row
            await db.execute(f"CREATE TABLE IF NOT EXISTS mocking_{interaction.guild.id} (id)")
            cursor: aiosqlite.Cursor = await db.execute(
                f"SELECT * FROM mocking_{interaction.guild.id} WHERE id = {member.id}"
            )
            data: typing.Iterable[aiosqlite.Row] = await cursor.fetchone()
            if data:
                is_already_mocked = True
            await db.execute(
                f"INSERT INTO mocking_{interaction.guild.id} VALUES ({member.id})")
            await db.commit()

        if not is_already_mocked:
            embed: discord.Embed = discord.Embed(
                title=f"Began mocking **{member.name}**!",
                color=embeds.DEFAULT_EMBED_COLOR
            )
            embed.set_thumbnail(url=member.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=embeds.simple_error_embed(
                    f"Member **{member.name}** is already being mocked!"
                ),
                ephemeral=True
            )

    @classmethod
    async def unmock(cls, interaction: discord.Interaction, member: discord.Member) -> None:
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=embeds.command_usage_denied("*Requires administrator permissions*"),
                ephemeral=True
            )
            return

        is_already_mocked: bool = True

        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row
            await db.execute(f"CREATE TABLE IF NOT EXISTS mocking_{interaction.guild.id} (id)")
            cursor: aiosqlite.Cursor = await db.execute(
                f"SELECT * FROM mocking_{interaction.guild.id} WHERE id = {member.id}"
            )
            data: typing.Optional[typing.Dict[typing.Any, typing.Any]] = await cursor.fetchone()
            if not data:
                is_already_mocked = False
            else:
                await db.execute(f"DELETE FROM mocking_{interaction.guild.id} WHERE id = {member.id}")
            await db.commit()

        if is_already_mocked:
            embed: discord.Embed = discord.Embed(
                title=f"Stopped mocking **{member.name}**!",
                color=embeds.DEFAULT_EMBED_COLOR
            )
            embed.set_thumbnail(url=member.avatar.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(
                embed=embeds.simple_error_embed(
                    f"Member **{member.name}** wasn\'t being mocked in the first place!"
                ),
                ephemeral=True
            )


async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Mocking(bot))
