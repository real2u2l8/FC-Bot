import discord
from discord.ext import commands
import re
import asyncio

class Service(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.registration_channel_id = 1264200662900670464  # 선수-등록 채널 ID

    ### 환영인사 서비스
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 환영 메시지를 보낼 채널 설정
        welcome_channel_id = 1264107685813420060  # 환영 메시지를 보낼 채널의 ID
        welcome_channel = self.bot.get_channel(welcome_channel_id)
        
        if welcome_channel:
            # 멤버의 아바타 URL을 가져오기, 아바타가 없으면 기본 아바타 URL 사용
            avatar_url = member.avatar.url if member.avatar else member.default_avatar.url

            # 임베드 메시지 생성
            embed = discord.Embed(
                title="ESPN에 오신걸 환영합니다.",
                description=(
                    f"{member.mention}\n"
                    "안녕하세요. **EA Sports Proclub Networks**입니다.\n\n"
                    "#서버-규정을 꼭 읽어주시고, 즐거운 시간 되세요! 🎉"
                ),
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=avatar_url)  # 새 멤버의 아바타를 썸네일로 추가
            
            # 임베드 메시지 보내기
            await welcome_channel.send(embed=embed)
            
            # 유저가이드 메시지 서비스
            user_guide_channel_id = 1264213588516671592  # 유저 가이드 채널의 ID
            user_guide_channel = self.bot.get_channel(user_guide_channel_id)

            if user_guide_channel:
                # 유저 가이드 메시지 작성
                guide_message = (
                    f"{member.mention}, #선수-등록 에서 `$선수등록` 을 사용하여, 역할을 부여 받으세요. "
                )

                # 유저 가이드 채널에 메시지 보내기
                await user_guide_channel.send(guide_message)
      
    
    @commands.command(name='선수등록')
    async def start_registration(self, ctx):
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
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

            msg = await self.bot.wait_for('message', check=check, timeout=300)

                   # 한글을 제외한 모든 문자를 허용
            if re.search("[ㄱ-ㅎㅏ-ㅣ가-힣]", msg.content):
                await thread.send("닉네임에 한글은 포함될 수 없습니다.")
                await asyncio.sleep(10)
                await thread.delete()
                return

            nickname = msg.content

            try:
                await ctx.author.edit(nick=nickname)
                await thread.send(f"{ctx.author.mention}의 닉네임이 성공적으로 {nickname}(으)로 변경되었습니다.")
            except discord.Forbidden:
                await thread.send("닉네임을 변경할 권한이 없습니다.")
                await asyncio.sleep(10)
                await thread.delete()
                return

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

            await ctx.send(f"{ctx.author.mention}님이 성공적으로 등록되었습니다!")
            await asyncio.sleep(10)
            await thread.delete()

        except asyncio.TimeoutError:
            await thread.send(f"{ctx.author.mention}, 5분 내에 닉네임을 입력하지 않아 등록이 취소되었습니다.")
            await asyncio.sleep(10)
            await thread.delete()
            
async def setup(bot):
    await bot.add_cog(Service(bot))
