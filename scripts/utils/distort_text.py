import random


async def distort_text(text: str) -> str:
    upper_chance: int = 1
    output = ""
    for char in text:
        if random.randint(0, upper_chance):
            output += char.upper()
            upper_chance = 1
        else:
            output += char.lower()
            upper_chance += 1
    return output
