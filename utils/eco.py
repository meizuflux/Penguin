from discord.ext import commands


class NotRegistered(commands.CommandError):
    pass


async def get_stats(ctx, user_id: int, not_author=False):
    values = (ctx.guild.id, user_id)
    async with ctx.bot.db.acquire() as conn:
        async with conn.transaction():
            registered = await conn.fetchval("SELECT 1 FROM economy WHERE guild_id = $1 AND user_id = $2", *values)
            if not registered:
                if not_author:
                    raise NotRegistered("This user is not registered! Tell them to use the register command.")
                raise NotRegistered(
                    "You are not registered! Use the register command to set up an account at the bank.")

            data = await conn.fetchrow("SELECT cash, bank FROM economy WHERE guild_id = $1 AND user_id = $2", *values)

    return data["cash"], data["bank"]


def get_number(number: str, total: int):
    number = number.replace(",", "")
    if number.endswith("%"):
        number = number.strip("%")
        if not number.isdigit():
            raise commands.BadArgument("That's... not a valid percentage.")
        number = round(float(number))
        if number > 100:
            raise commands.BadArgument("You can't do more than 100%.")
        percentage = lambda percent, total_amount: (percent * total_amount) / 100
        amount = percentage(number, total)

    elif number == 'half':
        amount = total / 2

    elif number in ('max', 'all'):
        amount = total
    elif number.isdigit():
        amount = int(number)
        if amount == 0:
            raise commands.BadArgument("You need to provide an amount that results in over $0")
    else:
        raise commands.BadArgument("Invalid amount provided.")

    amount = round(amount)

    if amount == 0:
        raise commands.BadArgument("The amount you provided resulted in 0..")

    if amount > total:
        raise commands.BadArgument("That's more money than you have...")

    if amount > 100000000000:
        raise commands.BadArgument("Transfers of money over one hundred billion are prohibited.")

    return int(amount)
