from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='홍명보')
    async def hong_myung_bo(self, ctx):
        await ctx.send(f'**이게 축구야?**')

async def setup(bot):
    await bot.add_cog(Fun(bot))
