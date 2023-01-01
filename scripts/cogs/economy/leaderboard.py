import discord
from discord.ext import commands
from discord import app_commands

import typing
import math
import aiosqlite

from scripts import nubot
from scripts.utils import embeds

_LEADERBOARD_SECTION_SIZE: int = 10


async def get_leaderboard_section(
        bot: nubot.Nubot,
        interaction: discord.Interaction,
        place: int,
        leaderboard_length: int
) -> discord.Embed:
    async with aiosqlite.connect("data/database.db") as db:
        db.row_factory = aiosqlite.Row
        await db.execute(f"CREATE TABLE IF NOT EXISTS economy_{interaction.guild.id} (id, balance, UNIQUE(id))")
        cursor: aiosqlite.Cursor = await db.execute(
            f"""
            SELECT
             *
            FROM
             economy_{interaction.guild.id}
            ORDER BY
             balance DESC
            LIMIT {_LEADERBOARD_SECTION_SIZE}
            OFFSET {place - 1}
            """
        )
        data: typing.Iterable[aiosqlite.Row] = await cursor.fetchall()

    embed: discord.Embed = discord.Embed(
        title=f"**Leaderboard of** ***{interaction.guild.name}***",
        color=embeds.DEFAULT_EMBED_COLOR
    )
    embed.set_thumbnail(url=interaction.guild.icon.url)

    c: int = place
    for row in data:
        user: discord.User = bot.get_user(row["id"])
        embed.add_field(
            name=f"**{c}. {user.name}#{user.discriminator}**",
            value=f":coin: **{row['balance']}**",
            inline=False
        )
        c += 1

    embed.set_footer(
        text=
        f"""
{math.ceil(place / _LEADERBOARD_SECTION_SIZE)} / \
{math.ceil(leaderboard_length / _LEADERBOARD_SECTION_SIZE)}
        """
    )

    return embed


class LeaderboardButtons(discord.ui.View):

    def __init__(
            self,
            bot: nubot.Nubot, interaction: discord.Interaction,
            place: int,
            leaderboard_length: int,
            user_id: int
    ) -> None:
        super().__init__(timeout=180)
        self.place: int = place
        self.leaderboard_length: int = leaderboard_length
        self.last_interaction: discord.Interaction = interaction
        self.bot: nubot.Nubot = bot
        self.user_id: int = user_id

    @discord.ui.button(label="<", style=discord.ButtonStyle.blurple)
    async def backward_button(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
    ) -> None:
        self.last_interaction = interaction

        new_place: int

        if self.place - _LEADERBOARD_SECTION_SIZE <= 0:
            new_place = self.leaderboard_length - (self.leaderboard_length % _LEADERBOARD_SECTION_SIZE - 1)
        else:
            new_place = self.place - _LEADERBOARD_SECTION_SIZE

        self.place = new_place

        embed: discord.Embed = await get_leaderboard_section(
            self.bot,
            interaction,
            new_place,
            self.leaderboard_length
        )

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label=">", style=discord.ButtonStyle.blurple)
    async def forward_button(
            self,
            interaction: discord.Interaction,
            button: discord.ui.Button
    ) -> None:
        self.last_interaction = interaction

        new_place: int

        if self.place + _LEADERBOARD_SECTION_SIZE > self.leaderboard_length:
            new_place = 1
        else:
            new_place = self.place + _LEADERBOARD_SECTION_SIZE

        self.place = new_place

        embed: discord.Embed = await get_leaderboard_section(
            self.bot,
            interaction,
            new_place,
            self.leaderboard_length
        )

        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        await self.last_interaction.edit_original_response(view=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embeds.cant_interact(), ephemeral=True)
            return False
        return True


class Leaderboard(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @app_commands.command(name="leaderboard")
    @app_commands.describe(place="place, from which, to start")
    async def leaderboard(
            self,
            interaction: discord.Interaction,
            place: typing.Optional[str] = "1"
    ) -> None:
        """Displays the leaderboard of the server, the ranking is based on money"""
        if not place.isdigit():
            await interaction.response.send_message(
                embed=embeds.simple_error_embed(f"`place` must be a positive integer!"),
                ephemeral=True
            )
            return

        place = int(place)

        async with aiosqlite.connect("data\\database.db") as db:
            await db.execute(f"CREATE TABLE IF NOT EXISTS economy_{interaction.guild.id} (id, balance, UNIQUE(id))")
            cursor = await db.execute(f"SELECT * FROM economy_{interaction.guild.id}")
            leaderboard_length: int = len(await cursor.fetchall())

        if leaderboard_length == 0:
            await interaction.response.send_message(
                embed=embeds.simple_error_embed("This guild doesn\'t have a leaderboard yet!"),
                ephemeral=True
            )
            return

        if place > leaderboard_length or place < 1:
            await interaction.response.send_message(
                embed=embeds.simple_error_embed(f"There\'s no person in place {place}!"),
                ephemeral=True
            )
            return

        place_offset: int = (place % _LEADERBOARD_SECTION_SIZE - 1)
        if place_offset >= 0:
            place -= place_offset
        else:
            place -= _LEADERBOARD_SECTION_SIZE - 1

        embed: discord.Embed = await get_leaderboard_section(
            self.bot,
            interaction,
            place,
            leaderboard_length
        )

        view = LeaderboardButtons(
            self.bot,
            interaction,
            place,
            leaderboard_length,
            interaction.user.id
         )

        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Leaderboard(bot))
