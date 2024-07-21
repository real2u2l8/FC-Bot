from discord.ext import commands
import random

class Dice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='주사위', help='Example: $주사위 100')
    async def roll(self, ctx, number: int):
        if number < 1:
            await ctx.send(f'{ctx.author.mention} 숫자는 1 이상이어야 합니다!')
            return

        result = random.randint(1, number)
        await ctx.send(f'{ctx.author.mention}: **{result}**')

async def setup(bot):
    await bot.add_cog(Dice(bot))


