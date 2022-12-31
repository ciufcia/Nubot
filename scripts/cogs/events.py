import discord
from discord.ext import commands

from scripts import nubot
from scripts.utils import distort_text

import requests
import aiosqlite
import typing

class Events(commands.Cog):

    def __init__(self, bot: nubot.Nubot) -> None:
        self.bot: nubot.Nubot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.type == discord.ChannelType.private:
            return

        async with aiosqlite.connect("data/database.db") as db:
            db.row_factory = aiosqlite.Row

            await db.execute(f"CREATE TABLE IF NOT EXISTS mocking_{message.guild.id} (id)")
            cursor: aiosqlite.Cursor = await db.execute(
                f"SELECT * FROM mocking_{message.guild.id} WHERE id = {message.author.id}"
            )
            data: typing.Dict[typing.Any, typing.Any] = await cursor.fetchone()

            if data:

                try:
                    request = requests.get(message.content)

                    if request.status_code == 200:
                        distorted_message = message.content
                    else:
                        distorted_message = await distort_text.distort_text(message.content)

                except requests.exceptions.RequestException:
                    distorted_message = await distort_text.distort_text(message.content)

                await message.channel.send(distorted_message)

            await db.commit()

async def setup(bot: nubot.Nubot) -> None:
    await bot.add_cog(Events(bot))