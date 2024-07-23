import discord
from discord.ext import commands, tasks

class AutoMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guide_channel_id = 1264757976997040240  # 드래프트 가이드를 올릴 채널 ID
        self.send_guide_message.start()  # 드래프트 가이드 시작 트리거

    def cog_unload(self):
        self.send_guide_message.cancel()

    @tasks.loop(minutes=30)  # 몇 분마다 자동 메시지 전송
    async def send_guide_message(self):
        guide_channel = self.bot.get_channel(self.guide_channel_id)
        if guide_channel:
            embed = discord.Embed(
                title="대기 채널 준수 가이드",
                description=(
                    "- <#1264757976997040240>에서 명령어를 입력하세요.\n"
                    "- <#1264611457065025597>에서 대기 부탁드립니다.\n"
                    "- **$대기참가** 입력하여 대기 목록에 추가됩니다.\n"
                    "- **$대기삭제** 입력하여 대기 목록에서 제거됩니다.\n"
                    "- **관리자 전용**:\n"
                    "- **$대기삭제번호 [번호순서]** : 해당 순번의 인원을 삭제합니다.\n"
                    "- **$대기전체삭제** : 대기 목록을 초기화 합니다.\n"
                    "- 드래프트 참여 혹은 게임 참여 시 대기 삭제 부탁드립니다.\n"
                ),
                color=discord.Color.blue()
            )
            await guide_channel.send(embed=embed)
        else:
            print(f"Cannot find channel with ID {self.guide_channel_id}")

    @send_guide_message.before_loop
    async def before_send_guide_message(self):
        await self.bot.wait_until_ready()

async def setup(bot):
    await bot.add_cog(AutoMessage(bot))
