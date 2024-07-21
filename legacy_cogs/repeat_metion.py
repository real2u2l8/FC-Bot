from discord.ext import commands

class RepeatMention(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='반복멘션')
    async def repeat_mention(self, ctx, member: commands.MemberConverter):
        for _ in range(6):
            await ctx.send(f'{member.mention}\n')
            
async def setup(bot):
    await bot.add_cog(RepeatMention(bot))
