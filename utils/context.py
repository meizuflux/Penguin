import discord
from discord.ext import commands


class CustomContext(commands.Context):
    @property
    def secret(self):
        return 'my secret here'

    # https://github.com/PB4162/PB-Bot/blob/master/utils/classes.py cool    
    async def send(self, content=None, **kwargs):
        if "reply" in kwargs and not kwargs.pop("reply"):
            return await super().send(content, **kwargs)
        try:
            if kwargs.pop("mention", False):
            	mention_author = True
            else:
            	mention_author = False
            content = content.replace("l", "w").replace("L", "W").replace("r", "w").replace("R", "W")
            return await self.reply(content, **kwargs, mention_author=mention_author)
        except discord.HTTPException:
            return await super().send(content, **kwargs)