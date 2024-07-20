from discord.ext import commands
import discord

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attendance_message_ids = {}  # 채널별 출석체크 메시지 ID 저장
        self.attendance_records = {}  # 채널별 출석체크 기록 저장

    @commands.command(name="출첵")
    async def start_attendance(self, ctx):
        message = await ctx.send(
            "### 출석체크\n"
            "1. 참여: ✅\n"
            "2. 늦참: 🕒\n"
            "3. 불참: ❌\n"
            "4. 미정: ❓"
        )
        self.attendance_message_ids[ctx.channel.id] = message.id
        self.attendance_records[ctx.channel.id] = {}  # 초기화
        reactions = ["✅", "🕒", "❌", "❓"]
        for reaction in reactions:
            await message.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        channel_id = reaction.message.channel.id
        if channel_id in self.attendance_message_ids and reaction.message.id == self.attendance_message_ids[channel_id]:
            status = None
            if reaction.emoji == "✅":
                status = "참여"
            elif reaction.emoji == "🕒":
                status = "늦참"
            elif reaction.emoji == "❌":
                status = "불참"
            elif reaction.emoji == "❓":
                status = "미정"
            
            if status:
                self.attendance_records[channel_id][user.id] = status

    @commands.command(name="출첵마감")
    async def end_attendance(self, ctx):
        channel_id = ctx.channel.id
        if channel_id not in self.attendance_records or not self.attendance_records[channel_id]:
            await ctx.send("아무도 출석체크를 하지 않았습니다.")
            return

        attendance_summary = {
            "참여": [],
            "늦참": [],
            "불참": [],
            "미정": []
        }

        for user_id, status in self.attendance_records[channel_id].items():
            member = ctx.guild.get_member(user_id)
            if member:
                attendance_summary[status].append(member.display_name)

        embed = discord.Embed(title="출석체크 결과", color=discord.Color.blue())
        for status, users in attendance_summary.items():
            if users:
                embed.add_field(name=status, value="\n".join(users), inline=False)

        await ctx.send(embed=embed)
        # Reset attendance record for this channel
        self.attendance_records[channel_id] = {}
        self.attendance_message_ids.pop(channel_id, None)

async def setup(bot):
    await bot.add_cog(Attendance(bot))