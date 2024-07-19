from discord.ext import commands
import datetime

class Attendance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.attendance_message_id = None
        self.attendance_record = {}

    @commands.command(name="출첵")
    async def start_attendance(self, ctx):
        message = await ctx.send(
            "20시까지 정해주세요.:\n"
            "1. 참여: ✅\n"
            "2. 늦참: 🕒\n"
            "3. 불참: ❌\n"
            "4. 미정: ❓"
        )
        self.attendance_message_id = message.id
        reactions = ["✅", "🕒", "❌", "❓"]
        for reaction in reactions:
            await message.add_reaction(reaction)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        if reaction.message.id == self.attendance_message_id:
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
                self.attendance_record[user.id] = status

    @commands.command(name="출첵마감")
    async def end_attendance(self, ctx):
        if not self.attendance_record:
            await ctx.send("출석체크한 인원이 없습니다.")
            return

        attendance_summary = {
            "참여": [],
            "늦참": [],
            "불참": [],
            "미정": []
        }

        for user_id, status in self.attendance_record.items():
            member = ctx.guild.get_member(user_id)
            if member:
                attendance_summary[status].append(member.display_name)

        summary_message = "출석체크 결과:\n"
        for status, users in attendance_summary.items():
            summary_message += f"{status}:\n" + "\n".join(f" - {user}" for user in users) + "\n\n"

        await ctx.send(summary_message)
        # Reset attendance record for next use
        self.attendance_record = {}

async def setup(bot):
    await bot.add_cog(Attendance(bot))
