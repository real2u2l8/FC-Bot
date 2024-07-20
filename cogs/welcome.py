from discord.ext import commands
import discord

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # 환영 메시지를 보낼 채널 설정
        welcome_channel_id = 1264107685813420060  # 환영 메시지를 보낼 채널의 ID
        welcome_channel = self.bot.get_channel(welcome_channel_id)

        # 환영 메시지
        welcome_message = (
            f"안녕하세요, {member.mention}!\n **{member.guild.name}**에 오신 것을 환영합니다!\n"
            "서버-규정을 꼭 읽어주시고, 즐거운 시간 되세요! 🎉"
        )

        # 환영 메시지 보내기
        if welcome_channel:
            await welcome_channel.send(welcome_message)

        # 개인 메시지 보내기 (옵션)
        # try:
        #     await member.send(
        #         f"안녕하세요, {member.mention}! {member.guild.name} 서버에 오신 것을 환영합니다!\n"
        #         "서버 규칙을 꼭 읽어주시고, 즐거운 시간 되세요! 🎉"
        #     )
        # except discord.Forbidden:
        #     pass

async def setup(bot):
    await bot.add_cog(Welcome(bot))
