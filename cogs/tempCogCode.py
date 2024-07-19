from discord.ext import commands

class Cog1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def hello(self, ctx):
        await ctx.send('Hello, world!')

def setup(bot):
    bot.add_cog(Cog1(bot))
