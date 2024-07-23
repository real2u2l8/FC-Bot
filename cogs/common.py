from discord.ext import commands
import discord
import random
import asyncio

class Common(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lottery_active = {}  # 각 채널에서의 뽑기 상태를 추적

    # 도움말 명령어
    @commands.command(name='도움말')
    async def show_help(self, ctx):
        help_message = (
            "# 사용 가능한 명령어 목록\n\n"
            "## 출석관련:\n"
            "**$출첵 [월일 (4자리 숫자)]**\n"
            "예시: `$출첵 0721` - 7월 21일 출석체크를 시작합니다.\n\n"
            "**$출첵마감**\n"
            "현재 진행 중인 출석체크를 마감하고 결과를 표시합니다.\n\n"
            "## 드래프트 관련:\n"
            "**$드래프트도움말** 를 참조하세요.\n\n"
            "## 기타 기능:\n"
            "**$주사위 `숫자`**\n\n"
            "입력한 숫자 내로 랜덤값을 표시합니다.\n"
            "**$뽑기 [목적어]**\n"
            "간단한 뽑기 기능입니다.\n\n"
            "**$홍명보**\n"
            "팀플레이가 안되서 속상하시다면..\n\n"
            "## 관리 전용:\n"
            "**$반복멘션 @유저**\n"
            "지정된 유저를 5번 반복 멘션합니다.(매니저 전용)\n\n"
        )
        await ctx.send(help_message)
        
    @commands.command(name='드래프트도움말')
    async def show_draft_help(self, ctx):
        draft_help_message = (
            "## 드래프트, 대기 명령어 도움말:\n"
            "**$드래프트 [숫자] (1,2만 가능합니다.)**\n"
            "최대 2팀까지의 드래프트를 진행합니다.\n\n"
        )
        await ctx.send(draft_help_message)

    # 반복멘션 명령어
    @commands.command(name='반복멘션')
    @commands.has_role('매니저')  # 특정 역할을 가진 유저만 사용 가능
    async def repeat_mention(self, ctx, member: commands.MemberConverter):
        for _ in range(6):
            await ctx.send(f'{member.mention}\n')
            
    # 주사위 명령어
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
        img_url = "https://tenor.com/view/%ED%99%8D%EB%AA%85%EB%B3%B4-gif-27244258"
        await ctx.send(f'# **이게 팀이야?**\n')
        await ctx.send(img_url)

    # 뽑기 명령어
    @commands.command(name='뽑기')
    async def lottery(self, ctx, *, purpose: str):
        if self.lottery_active.get(ctx.channel.id, False):
            await ctx.send("이미 진행 중인 뽑기가 있습니다.")
            return

        self.lottery_active[ctx.channel.id] = True
        message = await ctx.send(f"**{purpose}**\n15초 안에 체크 이모지를 눌러주세요! ✅")
        await message.add_reaction("✅")

        countdown_message = await ctx.send("카운트다운: 15초")
        for i in range(14, 0, -1):
            await asyncio.sleep(1)
            await countdown_message.edit(content=f"카운트다운: {i}초")
        await asyncio.sleep(1)
        await countdown_message.delete()

        message = await ctx.channel.fetch_message(message.id)
        users = [user async for user in message.reactions[0].users() if not user.bot]

        if users:
            random.shuffle(users)
            winners = users[:3]  # 상위 3명을 뽑기
            results = [f"{idx+1}등: {winner.mention}" for idx, winner in enumerate(winners)]
            await ctx.send(f"**{purpose}** - 결과:\n" + "\n".join(results))
        else:
            await ctx.send("아무도 체크하지 않았습니다.")

        self.lottery_active[ctx.channel.id] = False

async def setup(bot):
    await bot.add_cog(Common(bot))
