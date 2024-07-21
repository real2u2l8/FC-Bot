from discord.ext import commands
import discord
import random

class Common(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # 도움말 명령어
    @commands.command(name='도움말')
    async def show_help(self, ctx):
        help_message = (
            "**사용 가능한 명령어 목록:**\n\n"
            "**$출첵 [월일 (4자리 숫자)]**\n"
            "예시: `$출첵 0721` - 7월 21일 출석체크를 시작합니다.\n"
            "형식에 맞지 않으면 도움말이 표시됩니다.\n\n"
            "**$출첵마감**\n"
            "현재 진행 중인 출석체크를 마감하고 결과를 표시합니다.\n\n"
            "**$반복멘션 @유저**\n"
            "지정된 유저를 10번 반복 멘션합니다.\n\n"
            "**$주사위 `숫자`**\n"
            "입력한 숫자 내로 랜덤값을 표시합니다.\n\n"
            "**$홍명보**\n"
            "재밌는 일이 일어날거에요.\n\n"
            "**$리로드 [Cog 이름]**\n"
            "특정 Cog를 다시 로드합니다. (관리자 전용)\n\n"
        )
        await ctx.send(help_message)
    # 반복멘션 명령어
    @commands.command(name='반복멘션')
    async def repeat_mention(self, ctx, member: commands.MemberConverter):
        for _ in range(6):
            await ctx.send(f'{member.mention}\n')
    #주사위 명령어        
    @commands.command(name='주사위', help='Example: $주사위 100')
    async def roll(self, ctx, number: int):
        if number < 1:
            await ctx.send(f'{ctx.author.mention} 숫자는 1 이상이어야 합니다!')
            return

        result = random.randint(1, number)
        await ctx.send(f'{ctx.author.mention}: **{result}**')
        
    # 웃긴 커맨드
    @commands.command(name='홍명보')
    async def hong_myung_bo(self, ctx):
        await ctx.send(f'**이게 축구야?**')
            

async def setup(bot):
    await bot.add_cog(Common(bot))
