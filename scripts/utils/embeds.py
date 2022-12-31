import discord

import math

DEFAULT_EMBED_COLOR = int("3e00ff", 16)
ERROR_EMBED_COLOR = int("ff0000", 16)


def simple_error_embed(value: str) -> discord.Embed:
    return discord.Embed(title=value, color=int("ff0000", 16))


def command_usage_denied(reason: str = "Not specified") -> discord.Embed:
    return discord.Embed(
        title="You can't use this command",
        description=f"**Reason:** {reason}",
        color=ERROR_EMBED_COLOR
    )


def command_on_cooldown(time_till_cooldown_end: float) -> discord.Embed:
    display_time: int = math.ceil(time_till_cooldown_end)
    if display_time == 1:
        return discord.Embed(
            title="You\'re on a cooldown",
            description="You can use this command again in **a second**",
            color=ERROR_EMBED_COLOR
        )
    else:
        return discord.Embed(
            title="You\'re on a cooldown",
            description=f"You can use this command again in **{display_time} seconds**",
            color=ERROR_EMBED_COLOR
        )


def cant_interact_with_private_view() -> discord.Embed:
    return discord.Embed(title="You can\'t interact with a private view", color=ERROR_EMBED_COLOR)
