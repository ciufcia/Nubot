import discord
from discord.ext import commands
from discord import app_commands

import typing
import random

from scripts import nubot
from scripts.utils import embeds, economy_helpers


class MinesweeperGame:

    def __init__(self, width: int, height: int, number_of_mines: int) -> None:

        self.width = width
        self.height = height
        self.mine_amount = number_of_mines
        self.board: typing.List[typing.List[int]] = [[x, y] for x in range(width) for y in range(height)]
        self.values: typing.List[int] = [0] * width * height
        self.states: typing.List[int] = [0] * width * height
        self.mines_coordinates: typing.List[typing.List[int]] = random.sample(self.board, number_of_mines)
        self.revealed_cells: int = 0

        for coordinates in self.mines_coordinates:
            index: int = coordinates[0] + coordinates[1] * width

            self.values[index] = 9  # bombs will be represented as nines

            neighbors: typing.List[typing.List[int]] = self.get_neighbors(coordinates)

            for neighbor_coordinates in neighbors:
                index: int = neighbor_coordinates[0] + neighbor_coordinates[1] * width

                if self.values[index] != 9:
                    self.values[index] += 1

    def get_neighbors(self, coordinates: typing.List[int]) -> typing.List[typing.List[int]]:
        cx: int = coordinates[0]
        cy: int = coordinates[1]
        return [
            [x, y] for [x, y] in self.board
            if [cx, cy] == [x - 1, y - 1] or
               [cx, cy] == [x, y - 1] or
               [cx, cy] == [x + 1, y - 1] or
               [cx, cy] == [x - 1, y] or
               [cx, cy] == [x + 1, y] or
               [cx, cy] == [x - 1, y + 1] or
               [cx, cy] == [x, y + 1] or
               [cx, cy] == [x + 1, y + 1]
        ]

    def update(self, coordinates: typing.List[int]) -> int:
        index: int = coordinates[0] + coordinates[1] * self.width

        if self.states[index] not in (0, 2):
            return 0

        self.states[index] = 1
        self.revealed_cells += 1

        if self.values[index] == 9:
            return 1

        if self.values[index] == 0:
            self.reveal_neighbors(coordinates)

        if self.revealed_cells == self.width * self.height - self.mine_amount:
            return 2

        return 0

    def reveal_neighbors(self, coordinates: typing.List[int]) -> None:
        neighbors: typing.List[typing.List[int]] = self.get_neighbors(coordinates)
        for neighbor in neighbors:
            index: int = neighbor[0] + neighbor[1] * self.width
            if self.states[index] not in (0, 2):
                continue
            self.states[index] = 1
            self.revealed_cells += 1
            if self.values[index] == 0:
                self.reveal_neighbors(neighbor)

    def reveal_all_cells(self) -> None:
        for i in range(len(self.states)):
            self.states[i] = 1


class DifficultySelectView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=180.0)
        self.success = False
        self.select_values = []
        self.user_id = user_id

    @discord.ui.select(
        placeholder="Choose the difficulty",
        options=[
            discord.SelectOption(label="Easy", emoji="💚", description="5x5 with 3 bombs"),
            discord.SelectOption(label="Medium", emoji="💪", description="10x10 with 15 bombs"),
            discord.SelectOption(label="Hard", emoji="😈", description="14x14 with 30 bombs")
        ]
    )
    async def difficulty_select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        select.disabled = True
        await interaction.response.edit_message(view=self)
        self.success = True
        self.select_values = select.values
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embeds.cant_interact_with_private_view(), ephemeral=True)
            return False
        return True

class InGameView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180.0)
        self.pressed_button: str = "nothing"
        self.user_id: int = user_id

    @discord.ui.button(label="⛏", style=discord.ButtonStyle.green, row=0)
    async def mine_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "mine")

    @discord.ui.button(label="↑", style=discord.ButtonStyle.blurple, row=0)
    async def up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "up")

    @discord.ui.button(label="🚩", style=discord.ButtonStyle.red, row=0)
    async def flag_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "flag")

    @discord.ui.button(label="←", style=discord.ButtonStyle.blurple, row=1)
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "left")

    @discord.ui.button(label="↓", style=discord.ButtonStyle.blurple, row=1)
    async def down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "down")

    @discord.ui.button(label="→", style=discord.ButtonStyle.blurple, row=1)
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.button_pressed(interaction, "right")

    async def button_pressed(self, interaction: discord.Interaction, button: str):
        self.pressed_button = button
        await interaction.response.defer()
        self.stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embeds.cant_interact_with_private_view(), ephemeral=True)
            return False
        return True


class Minesweeper(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @app_commands.command(name="minesweeper")
    async def minesweeper(self, interaction: discord.Interaction) -> None:
        """Play classic minesweeper"""
        embed: discord.Embed = discord.Embed(
            title=":triangular_flag_on_post: Minesweeper :bomb:",
            description="Uncover all of the mine-free cells, to win!\n:o: is your cursor.",
            color=embeds.DEFAULT_EMBED_COLOR
        )
        view: DifficultySelectView = DifficultySelectView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()

        if not view.success:
            await interaction.edit_original_response(view=None)
            return

        difficulty: str = view.select_values[0]

        difficulties_data: typing.Dict[str, typing.Dict[str, int]] = {
            "Easy": {"size": 5, "mine_amount": 3, "prize": 100},
            "Medium": {"size": 10, "mine_amount": 15, "prize": 250},
            "Hard": {"size": 14, "mine_amount": 30, "prize": 1000}
        }

        game: MinesweeperGame = MinesweeperGame(
            difficulties_data[difficulty]["size"],
            difficulties_data[difficulty]["size"],
            difficulties_data[difficulty]["mine_amount"]
        )

        cursor_position: typing.List[int, int] = [0, 0]

        in_game_view: InGameView = InGameView(interaction.user.id)

        await interaction.edit_original_response(
            embed=await self.display_as_embed(game, cursor_position),
            view=in_game_view
        )

        while True:
            await in_game_view.wait()

            match in_game_view.pressed_button:
                case "nothing":
                    await interaction.edit_original_response(view=None)
                    return
                case "mine":
                    game_state: int = game.update(cursor_position)
                    if game_state == 1:
                        won = False
                        break
                    elif game_state == 2:
                        won = True
                        break
                case "up":
                    if cursor_position[1] > 0:
                        cursor_position[1] -= 1
                case "flag":
                    index: int = cursor_position[0] + cursor_position[1] * game.width
                    if game.states[index] != 1:
                        game.states[index] = 2
                case "left":
                    if cursor_position[0] > 0:
                        cursor_position[0] -= 1
                case "down":
                    if cursor_position[1] < difficulties_data[difficulty]["size"]-1:
                        cursor_position[1] += 1
                case "right":
                    if cursor_position[0] < difficulties_data[difficulty]["size"] - 1:
                        cursor_position[0] += 1

            in_game_view = InGameView(interaction.user.id)

            await interaction.edit_original_response(
                embed=await self.display_as_embed(game, cursor_position),
                view=in_game_view
            )

        game.reveal_all_cells()

        if won:
            embed = discord.Embed(
                title="🏆 You\'ve won! 🏆",
                description=await self.display_as_text(game),
                color=embeds.DEFAULT_EMBED_COLOR
            )
            current_bal: int = await economy_helpers.get_balance(interaction.user.id, interaction.guild.id)
            await economy_helpers.set_balance(
                interaction.user.id,
                interaction.guild.id,
                current_bal + difficulties_data[difficulty]['prize']
            )
            embed.add_field(name="You\'ve been awarded:", value=f"**:coin: {difficulties_data[difficulty]['prize']}**!")
        else:
            embed = discord.Embed(
                title="🤦 You\'ve lost! 🤦‍",
                description=await self.display_as_text(game),
                color=embeds.DEFAULT_EMBED_COLOR
            )

        await interaction.edit_original_response(embed=embed, view=None)

    @classmethod
    async def display_as_text(
            cls,
            game: MinesweeperGame,
            cursor_pos: typing.Optional[typing.List[int]] = None
    ) -> str:
        emoji_mapping: typing.Dict[typing.Union[int, str], str] = {
            0: ":white_small_square:",
            1: ":one:",
            2: ":two:",
            3: ":three:",
            4: ":four:",
            5: ":five:",
            6: ":six:",
            7: ":seven:",
            8: ":eight:",
            9: ":bomb:",
            "covered": ":blue_square:",
            "flag": ":triangular_flag_on_post:",
            "cursor": ":o:"
        }

        emoji_representation: str = ""

        cursor_pos_index: typing.Optional[int] = None
        if cursor_pos is not None:
            cursor_pos_index = cursor_pos[0] + cursor_pos[1] * game.width

        for y in range(game.height):
            for x in range(game.width):
                index: int = x + y * game.width
                if cursor_pos_index is not None:
                    if index == cursor_pos_index:
                        emoji_representation += emoji_mapping["cursor"]
                        continue
                if game.states[index] == 0:
                    emoji_representation += emoji_mapping["covered"]
                elif game.states[index] == 1:
                    emoji_representation += emoji_mapping[game.values[index]]
                elif game.states[index] == 2:
                    emoji_representation += emoji_mapping["flag"]
            emoji_representation += "\n"

        return emoji_representation

    async def display_as_embed(
            self,
            game: MinesweeperGame,
            cursor_pos: typing.Optional[typing.List[int]] = None
    ) -> discord.Embed:
        embed: discord.Embed = discord.Embed(
            title=":triangular_flag_on_post: Minesweeper :bomb:",
            description=await self.display_as_text(game, cursor_pos),
            color=embeds.DEFAULT_EMBED_COLOR
        )

        return embed


async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Minesweeper(bot))
