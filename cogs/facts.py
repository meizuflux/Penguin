"""
Copyright (C) 2021 ppotatoo

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from discord.ext import commands
import requests


class Facts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.command()
    async def fact(self, ctx, animal):
        """Tells you a fact of the given animal parameter"""
        r = requests.get(f"https://some-random-api.ml/facts/{animal}")
        res = r.json()
        fact = res["fact"]
        factfun = ["Here's a fact", "Here's one", "I bet you dint know"]
        m = discord.Embed(title=f"{random.choice(factfun)}", description=f"{fact}", color=discord.Color.random())
        await ctx.send(embed = m)
        #The help command for this can be available animal's are :-
        #Dog
        #Cat
        #Panda
        #Fox
        #Bird
        #Koala
        #Whale

def setup(bot):
    bot.add_cog(Facts(bot))
