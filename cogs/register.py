import discord
from discord.ext import commands
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup

class Register(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.registration_channel_id = 1264200662900670464  # 선수-등록 채널 ID
    
    @commands.command(name='선수등록')
    async def start_registration(self, ctx, cafe_link: str = None):
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if cafe_link is None:
            await ctx.send("네이버 카페 링크를 입력해주세요.")
            return

        role_name = "ESPN"
        role = discord.utils.get(ctx.guild.roles, name=role_name)

        if role in ctx.author.roles:
            await ctx.send(f"{ctx.author.mention}님은 이미 등록되어 있습니다.")
            return

        if not ctx.guild.me.guild_permissions.manage_nicknames:
            await ctx.send("봇에 닉네임을 변경할 권한이 없습니다.")
            return

        try:
            thread = await ctx.channel.create_thread(
                name=f"등록-{ctx.author.name}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )
            await thread.add_user(ctx.author)
            await thread.send(f"{ctx.author.mention} 닉네임을 입력해주세요. (한글은 허용되지 않습니다)")

            def check(m):
                return m.channel == thread and m.author == ctx.author

            while True:
                try:
                    msg = await self.bot.wait_for('message', check=check, timeout=300)

                    # 한글을 제외한 모든 문자를 허용
                    if re.search("[ㄱ-ㅎㅏ-ㅣ가-힣]", msg.content):
                        await thread.send("닉네임에 한글은 포함될 수 없습니다. 다시 입력해주세요.")
                    else:
                        nickname = msg.content
                        break
                except asyncio.TimeoutError:
                    await thread.send(f"{ctx.author.mention}, 5분 내에 닉네임을 입력하지 않아 등록이 취소되었습니다.")
                    await asyncio.sleep(10)
                    await thread.delete()
                    return

            try:
                await ctx.author.edit(nick=nickname)
                await thread.send(f"{ctx.author.mention}의 닉네임이 성공적으로 {nickname}(으)로 변경되었습니다.")
            except discord.Forbidden:
                await thread.send("닉네임을 변경할 권한이 없습니다.")
                await asyncio.sleep(10)
                await thread.delete()
                return

            # 게시글이 존재하는지 확인
            post_exists = await self.check_post_exists(cafe_link)
            if post_exists:
                if role:
                    try:
                        await ctx.author.add_roles(role)
                        await thread.send(f"{ctx.author.mention}에게 {role_name} 역할이 성공적으로 부여되었습니다.")
                    except discord.Forbidden:
                        await thread.send("역할을 부여할 권한이 없습니다.")
                        await asyncio.sleep(10)
                        await thread.delete()
                        return
                else:
                    await thread.send(f"{role_name} 역할을 찾을 수 없습니다.")
                    await asyncio.sleep(10)
                    await thread.delete()
                    return

                await ctx.send(f"{ctx.author.mention}님이 성공적으로 등록되었습니다!\n<#1264609466947604550>에서 공방 출석체크 진행중 입니다! 많은 참석 부탁드려요!!")
            else:
                await thread.send("입력하신 링크에 해당 게시글이 존재하지 않습니다. 등록이 취소되었습니다.")
            
            await asyncio.sleep(10)
            await thread.delete()

        except asyncio.TimeoutError:
            await thread.send(f"{ctx.author.mention}, 5분 내에 닉네임을 입력하지 않아 등록이 취소되었습니다.")
            await asyncio.sleep(10)
            await thread.delete()

    async def check_post_exists(self, cafe_link):
        # 네이버 카페 페이지를 요청
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(cafe_link, headers=headers) as response:
                if response.status == 200:
                    print(f"Successfully accessed {cafe_link}.")
                    return True
                else:
                    print(f"Failed to access {cafe_link}. Status code: {response.status}")
                    return False

async def setup(bot):
    await bot.add_cog(Register(bot))
