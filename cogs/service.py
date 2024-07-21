from discord.ext import commands
import discord

class Service(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
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
                    "서버-규정을 꼭 읽어주시고, 즐거운 시간 되세요! 🎉"
                ),
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=avatar_url)  # 새 멤버의 아바타를 썸네일로 추가

            # 임베드 메시지 보내기
            await welcome_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Service(bot))
