import discord
from discord.ext import commands, tasks
from discord import app_commands

import aiosqlite
import asyncio
import typing
import random
import datetime

from scripts import nubot
from scripts.utils import embeds

_BOARD_WIDTH: int = 9
_BOARD_HEIGHT: int = 5
_SNAKE_STARTING_POS_X: int = 4
_SNAKE_STARTING_POS_Y: int = 2
_SNAKE_UPDATE_DELTA: datetime.timedelta = datetime.timedelta(minutes=5.0)


class SnakeGame:

    @classmethod
    async def create(cls) -> None:
        async with aiosqlite.connect("data/database.db") as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS snake (id, board, body, score, direction, is_lost, UNIQUE(id))
                """
            )
            await db.execute("DELETE FROM snake")

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS snake_votes (id, vote, UNIQUE(id))
                """
            )
            await db.execute("DELETE FROM snake_votes")

            # 0 = blank
            # 1 = head
            # 2 = body
            # 3 = apple
            board: typing.List[int] = [0 for _ in range(_BOARD_WIDTH * _BOARD_HEIGHT)]

            body: typing.List[int] = [_SNAKE_STARTING_POS_X + _SNAKE_STARTING_POS_Y * _BOARD_WIDTH]
            board[body[0]] = 1

            apples: typing.List[int] = random.sample([elem for elem in range(len(board)) if elem != body[0]], 3)
            for apple in apples:
                board[apple] = 3

            await db.execute(
                f"""
                INSERT INTO snake
                VALUES (0, '{board}', '{body}', 0, 0, 0)
                """
            )

            await db.commit()

    @classmethod
    async def move(cls) -> None:
        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row

            cursor: aiosqlite.Cursor = await db.execute("SELECT * FROM snake WHERE id = 0")
            game_data: typing.Optional[typing.Dict[str, typing.Any]] = await cursor.fetchone()

            cursor = await db.execute("SELECT * FROM snake_votes")
            vote_data: typing.Iterable[aiosqlite.Row] = await cursor.fetchall()

            votes: typing.List[int] = [0] * 4

            elem: typing.Dict[str, typing.Any]
            for elem in vote_data:
                votes[elem["vote"]] += 1

            direction: int = game_data["direction"]

            max_index: int = 0
            for i in range(len(votes)):
                if votes[i] > votes[max_index]:
                    max_index = i

            for i in range(len(votes)):
                if i == max_index:
                    continue
                if votes[i] == votes[max_index]:
                    break
            else:
                direction = max_index

            board: typing.List[int] = eval(game_data["board"])
            body: typing.List[int] = eval(game_data["body"])
            score: int = game_data["score"]

            last_elem: int = body[len(body)-1]
            board[last_elem] = 0

            for i in range(len(body)-1, 0, -1):
                body[i] = body[i - 1]
                board[body[i]] = 2

            new_head_index: int = body[0]

            match direction:
                case 0:
                    new_head_index += 1
                case 1:
                    new_head_index += _BOARD_WIDTH
                case 2:
                    new_head_index -= 1
                case 3:
                    new_head_index -= _BOARD_WIDTH

            if new_head_index in body\
                or (direction == 0 and new_head_index % _BOARD_WIDTH == 0)\
                or (direction == 1 and new_head_index >= len(board))\
                or (direction == 2 and new_head_index % _BOARD_WIDTH == _BOARD_WIDTH - 1)\
                    or (direction == 3 and new_head_index < 0):
                await SnakeGame.create()
                return

            if board[new_head_index] == 3:
                body.append(last_elem)
                board[last_elem] = 2
                score += 1

                free_indices = [i for i in range(len(board)) if board[i] == 0]

                if len(free_indices) != 0:
                    apple_index = random.sample(free_indices, 1)[0]

                board[apple_index] = 3

            body[0] = new_head_index
            board[body[0]] = 1

            await db.execute(
                f"""
                INSERT OR REPLACE INTO snake
                VALUES (0, '{board}', '{body}', {score}, {direction}, {game_data['is_lost']})
                """
            )

            await db.execute(f"DELETE FROM snake_votes")

            await db.commit()

    @classmethod
    async def embed_representation(cls, last_update_time: datetime.datetime) -> discord.Embed:
        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row

            cursor: aiosqlite.Cursor = await db.execute("SELECT * FROM snake WHERE id = 0")
            game_data: typing.Optional[typing.Dict[str, typing.Any]] = await cursor.fetchone()

            emoji_mapping: typing.Dict[int, str] = {
                0: ":blue_square:",
                1: ":frog:",
                2: ":green_circle:",
                3: ":apple:"
            }

            direction_emojis: typing.Dict[int, str] = {
                0: ":arrow_right:",
                1: ":arrow_down:",
                2: ":arrow_left:",
                3: ":arrow_up:",
            }

            emoji_board: str = ""

            board: typing.List[str] = eval(game_data["board"])

            for i in range(_BOARD_HEIGHT):
                for j in range(_BOARD_WIDTH):
                    emoji_board += emoji_mapping[board[j + i * _BOARD_WIDTH]]
                emoji_board += "\n"

            embed: discord.Embed = discord.Embed(
                title="🐍 Snake 🐍",
                color=embeds.DEFAULT_EMBED_COLOR
            )

            if game_data["is_lost"] == 0:
                embed.add_field(
                    name="Game:",
                    value=emoji_board
                )

                cursor = await db.execute("SELECT * FROM snake_votes")
                vote_data: typing.Iterable[aiosqlite.Row] = await cursor.fetchall()

                votes: typing.List[int] = [0] * 4

                elem: typing.Dict[int, typing.Any]
                for elem in vote_data:
                    votes[elem["vote"]] += 1

                votes_string: str = ""
                for i in range(len(votes)):
                    votes_string += f"{direction_emojis[i]}: {votes[i]}\n"

                embed.add_field(
                    name="votes:",
                    value=votes_string
                )
            else:
                embed.add_field(
                    name="Game: Lost",
                    value=emoji_board
                )

            embed.add_field(
                name="Score:",
                value=f"{game_data['score']}",
                inline=False
            )

            embed.add_field(
                name="Current direction:",
                value=f"{direction_emojis[game_data['direction']]}",
                inline=False
            )

            time_till_next_update: datetime.timedelta = _SNAKE_UPDATE_DELTA - (
                        datetime.datetime.now() - last_update_time)

            hours, r = divmod(time_till_next_update.seconds, 3600)
            minutes, seconds = divmod(r, 60)

            embed.set_footer(text=f"Time till next update: {hours}:{minutes}:{seconds}")

            return embed


class InGameView(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=180.0)
        self.pressed_button: int = -1
        self.current_direction: int = 0
        self.user_id: int = user_id

    @discord.ui.button(label="←", style=discord.ButtonStyle.blurple)
    async def left_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if await self.check_if_already_voted(interaction):
            await self.already_voted(interaction)
            return

        if self.current_direction == 0:
            await self.wrong_direction(interaction)
            return

        await self.button_pressed(interaction, 2)

    @discord.ui.button(label="↑", style=discord.ButtonStyle.blurple)
    async def up_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_if_already_voted(interaction):
            await self.already_voted(interaction)
            return

        if self.current_direction == 1:
            await self.wrong_direction(interaction)
            return

        await self.button_pressed(interaction, 3)

    @discord.ui.button(label="↓", style=discord.ButtonStyle.blurple)
    async def down_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_if_already_voted(interaction):
            await self.already_voted(interaction)
            return

        if self.current_direction == 3:
            await self.wrong_direction(interaction)
            return

        await self.button_pressed(interaction, 1)

    @discord.ui.button(label="→", style=discord.ButtonStyle.blurple)
    async def right_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.check_if_already_voted(interaction):
            await self.already_voted(interaction)
            return

        if self.current_direction == 2:
            await self.wrong_direction(interaction)
            return

        await self.button_pressed(interaction, 0)

    async def stop_without_input(self):
        self.pressed_button = -1
        self.stop()

    async def button_pressed(self, interaction: discord.Interaction, button: int) -> None:
        await interaction.response.defer()
        self.pressed_button = button
        self.stop()

    async def wrong_direction(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=embeds.simple_error_embed("The snake can\'t move this way"),
            ephemeral=True
        )
        await self.stop_without_input()

    @classmethod
    async def check_if_already_voted(cls, interaction: discord.Interaction) -> bool:
        async with aiosqlite.connect("data/database.db") as db:
            cursor: aiosqlite.Cursor = await db.execute(f"SELECT * FROM snake_votes WHERE id = {interaction.user.id}")
            data = await cursor.fetchone()
            if data is None:
                return False
            return True

    async def already_voted(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            embed=embeds.simple_error_embed("You have already voted this round"),
            ephemeral=True
        )
        await self.stop_without_input()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(embed=embeds.cant_interact_with_private_view(), ephemeral=True)
            return False
        return True


class Snake(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot
        self.last_update_time: datetime.datetime = datetime.datetime.now()

    @app_commands.command(name="snake")
    async def snake(self, interaction: discord.Interaction) -> None:
        """Play snake with other people globally"""
        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row

            cursor: aiosqlite.Cursor = await db.execute("SELECT * FROM snake WHERE id = 0")
            game_data: typing.Optional[typing.Dict[str, typing.Any]] = await cursor.fetchone()

            if game_data["is_lost"] == 0:
                view: InGameView = InGameView(interaction.user.id)

                await interaction.response.send_message(
                    embed=await SnakeGame.embed_representation(self.last_update_time),
                    view=view
                )

                await view.wait()

                if view.pressed_button == -1:
                    await interaction.edit_original_response(view=None)
                    return

                await db.execute(
                    f"""
                    INSERT OR REPLACE INTO snake_votes VALUES ({interaction.user.id}, {view.pressed_button})
                    """
                )

                await db.commit()

                await interaction.edit_original_response(
                    embed=await SnakeGame.embed_representation(self.last_update_time),
                    view=None
                )
            else:
                await interaction.response.send_message(
                    embed=await SnakeGame.embed_representation(self.last_update_time)
                )

    @tasks.loop(seconds=_SNAKE_UPDATE_DELTA.seconds)
    async def move(self):
        await SnakeGame.move()
        self.last_update_time: datetime.datetime = datetime.datetime.now()

    @move.before_loop
    async def before_move_task(self):
        await asyncio.sleep(_SNAKE_UPDATE_DELTA.seconds)


async def setup(bot: nubot.Nubot) -> None:
    async with aiosqlite.connect("data/database.db") as db:
        try:
            await db.execute("SELECT * FROM snake")
            await db.execute("SELECT * FROM snake_votes")
        except aiosqlite.OperationalError:
            await SnakeGame.create()

    await bot.add_cog(Snake(bot))
