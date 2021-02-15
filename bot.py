import discord
from discord.ext import commands
import os
import aiohttp
import re
import json
import asyncpg
import datetime

class SYSTEM32(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.presences = True
        super().__init__(
            command_prefix=self.get_prefix,
            case_insensitive=True,
            intents=intents,
            owner_ids={809587169520910346},
            description=
            'system 32 will be deleted'
        )
        self._BotBase__cogs = commands.core._CaseInsensitiveDict()
        self.author_id = 809587169520910346
        self.session = aiohttp.ClientSession()
        self.embed_color = 0x9c5cb4  #0x1E90FF
        self.prefixes = {}
        self.default_prefix = 'c//'

    def get_config(self, item: str):
        with open('config.json', 'r') as f:
            f = json.load(f)
        return f[item]

    async def get_prefix(bot, message):
        if message.guild == None:
            return commands.when_mentioned_or(bot.default_prefix)(bot, message)
        try:
            return commands.when_mentioned_or(bot.prefixes[message.guild.id])(bot, message)
        except KeyError:
            prefix = await bot.db.fetchval("SELECT prefix FROM prefixes WHERE serverid = $1", message.guild.id)
            if prefix:
                bot.prefixes[message.guild.id] = prefix
                return commands.when_mentioned_or(bot.prefixes[message.guild.id])(bot, message)
            else:
                await bot.db.execute("INSERT INTO prefixes(serverid,prefix) VALUES($1,$2) ON CONFLICT (serverid) DO UPDATE SET prefix = $2",message.guild.id, bot.default_prefix)
                bot.prefixes[message.guild.id] = bot.default_prefix
                return commands.when_mentioned_or(bot.prefixes[message.guild.id])(bot, message)

    def starter(self):
        try:
            print("Connecting to database ...")
            pool_pg = self.loop.run_until_complete(asyncpg.create_pool(user=self.get_config('USER'), port=5432, host='localhost', password=self.get_config('PASSWORD')))
            print("Connected to PostgreSQL server!")
        except Exception as e:
            print("Could not connect to database:", e)
        else:
            print("Connecting to Discord ...")
            self.uptime = datetime.datetime.utcnow()
            self.db = pool_pg
            extensions = ['jishaku', 'cogs.useful', 'cogs.owner', 'cogs.prefixes']
            for extension in extensions:
                self.load_extension(extension)
            
            self.run(self.get_config('token'))

    async def create_tables(self):
        await self.wait_until_ready()
        await self.db.execute("CREATE TABLE IF NOT EXISTS prefixes (serverid BIGINT PRIMARY KEY,prefix VARCHAR(50))")
        await self.db.execute("CREATE TABLE IF NOT EXISTS scoresaber (userid BIGINT PRIMARY KEY,ssid BIGINT)")

    async def get_context(self, message: discord.Message, *, cls=None):
            return await super().get_context(message, cls=cls or commands.Context)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if re.fullmatch(f"^(<@!?{self.user.id}>)\s*", message.content):
            try:
                sprefix = bot.prefixes[message.guild.id]
            except KeyError:
                prefix = await bot.db.fetchval("SELECT prefix FROM prefixes WHERE serverid = $1", message.guild.id)
                if prefix:
                    sprefix = prefix
                else:
                    sprefix = bot.default_prefix
            await message.channel.send("My prefix on `{}` is `{}`".format(message.guild.name, sprefix))
        await self.process_commands(message)

bot = SYSTEM32()
bot.loop.create_task(bot.create_tables())

os.environ["JISHAKU_NO_UNDERSCORE"] = "True"
os.environ["JISHAKU_NO_DM_TRACEBACK"] = "True"
os.environ["JISHAKU_HIDE"] = "True"

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!\nGuilds: {len(bot.guilds)}\nMembers: {str(sum([guild.member_count for guild in bot.guilds]))}')

if __name__ == "__main__":
    bot.starter()