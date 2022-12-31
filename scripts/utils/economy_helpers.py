import aiosqlite
import typing


async def set_balance(
        user_id: int,
        guild_id: int,
        amount: int = 0
) -> None:
    async with aiosqlite.connect("data/database.db") as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS economy_{guild_id} (id, balance, UNIQUE(id))")
        await db.execute(f"INSERT OR REPLACE INTO economy_{guild_id} VALUES ({user_id}, {amount})")
        await db.commit()


async def get_balance(
        user_id: int,
        guild_id: int
) -> int:
    async with aiosqlite.connect("data/database.db") as db:
        await db.execute(f"CREATE TABLE IF NOT EXISTS economy_{guild_id} (id, balance, UNIQUE(id))")
        db.row_factory = aiosqlite.Row

        cursor: aiosqlite.Cursor = await db.execute(f"SELECT * FROM economy_{guild_id} WHERE id = {user_id}")
        data: typing.Optional[aiosqlite.Row] = await cursor.fetchone()

    if not data:
        await set_balance(user_id, guild_id, amount=0)
        return 0

    return data["balance"]
