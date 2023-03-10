import asyncio

import discord
from discord.ext import commands, tasks

import os
import typing


async def _get_cog_file_dirs(base_dir: str, return_list: typing.Optional[typing.List[str]] = []) -> typing.List[str]:
    for filename in os.listdir(base_dir):
        if os.path.isdir(f"{base_dir}/{filename}"):
            await _get_cog_file_dirs(f"{base_dir}/{filename}", return_list=return_list)
        elif filename.endswith(".py"):
            return_list.append(f"{base_dir}/{filename}")
    return return_list


async def _change_filepath_to_python_path(path: str) -> str:
    return ".".join(os.path.normpath(path).split(os.sep))[:-3]


class Nubot(commands.Bot):

    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all(), command_prefix="0", help_command=None)
        self.__COG_DIR_NAME: str = "scripts/cogs"
        self.__COG_DIR: str = "scripts.cogs"

    async def add_cogs(self) -> None:
        cog_paths: typing.List[str] = await _get_cog_file_dirs("scripts/cogs")

        for i in range(len(cog_paths)):
            cog_paths[i] = await _change_filepath_to_python_path(cog_paths[i])

        for cog in cog_paths:
            print(f"-> Loading cog: `{cog}`", end=" ")
            await self.load_extension(cog)
            print("Finished")

    async def setup_hook(self) -> None:
        print("Starting setup_hook...")
        await self.add_cogs()
        print("-> Starting snake...", end=" ")
        self.get_cog("Snake").move.start()
        print("Finished")
        self.sync_commands.start()
        print("Finished setup_hook")

    @tasks.loop(minutes=1.0, count=1)
    async def sync_commands(self) -> None:
        print("Starting syncing task...")
        print("-> Waiting for the bot to log in...")
        await self.wait_until_ready()
        guild: discord.Guild
        for guild in self.guilds:
            print(f"-> Syncing application commands for guild with ID: {guild.id}", end=" ")
            self.tree.copy_global_to(guild=guild)
            print("Finished")
        await self.tree.sync()
        print("Finished syncing task")
