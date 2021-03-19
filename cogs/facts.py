from discord.ext import commands


class Facts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def animal_fact(self, ctx, animal):
        async with self.bot.session.get(f"https://some-random-api.ml/facts/{animal}") as f:
            data = await f.json()
        embed = ctx.embed(title="Did you know...", description=data.get("fact", "The API isn't working right now."))
        await ctx.send(embed=embed)

    @commands.command(aliases=['dogfact'])
    async def dog_fact(self, ctx):
        """Sends a dog fact."""
        await self.animal_fact(ctx, "dog")

    @commands.command(aliases=['catfact'])
    async def cat_fact(self, ctx):
        """Sends a cat fact."""
        await self.animal_fact(ctx, "cat")

    @commands.command(aliases=['pandafact'])
    async def panda_fact(self, ctx):
        """Sends a panda fact."""
        await self.animal_fact(ctx, "panda")

    @commands.command(aliases=['foxfact'])
    async def fox_fact(self, ctx):
        """Sends a fox fact."""
        await self.animal_fact(ctx, "fox")

    @commands.command(aliases=['birbfact'])
    async def birb_fact(self, ctx):
        """Sends a birb fact."""
        await self.animal_fact(ctx, "birb")

    @commands.command(aliases=['koalafact'])
    async def koala_fact(self, ctx):
        """Sends a koala fact."""
        await self.animal_fact(ctx, "koala")

    @commands.command(aliases=['kangaroofact'])
    async def kangaroo_fact(self, ctx):
        """Sends a kangaroo fact."""
        await self.animal_fact(ctx, "kangaroo")

    @commands.command(aliases=['racoonfact'])
    async def racoon_fact(self, ctx):
        """Sends a racoon fact."""
        await self.animal_fact(ctx, "racoon")

    @commands.command(aliases=['elephantfact'])
    async def elephant_fact(self, ctx):
        """Sends a elephant fact."""
        await self.animal_fact(ctx, "elephant")

    @commands.command(aliases=['giraffefact'])
    async def giraffe_fact(self, ctx):
        """Sends a giraffe fact."""
        await self.animal_fact(ctx, "giraffe")

    @commands.command(aliases=['whalefact'])
    async def whale_fact(self, ctx):
        """Sends a whale fact."""
        await self.animal_fact(ctx, "whale")


def setup(bot):
    bot.add_cog(Facts(bot))
