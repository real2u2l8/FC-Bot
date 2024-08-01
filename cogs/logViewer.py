import discord
from discord.ext import commands
import os
from discord.ui import View, Button, Select

class LogViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dirs = {
            'commands': 'logs/commands',        # 명령어 로그
            'errors': 'logs/errors',            # 에러 로그
            'state': 'logs/state',              # 봇 상태 로그
            'user_activity': 'logs/user_activity' # 사용자 활동 로그
        }

    @commands.command(name='로그')
    @commands.has_role('매니저')  # '매니저' 역할을 가진 사용자만 이 명령어를 사용할 수 있습니다.
    async def show_logs(self, ctx):
        view = LogCategoryView(self.log_dirs)
        await ctx.send("Choose a log category:", view=view)

    @show_logs.error
    async def show_logs_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("이 명령어를 사용하려면 '매니저' 역할이 필요합니다.")

class LogCategoryView(View):
    def __init__(self, log_dirs):
        super().__init__()
        self.log_dirs = log_dirs
        for category in log_dirs.keys():
            self.add_item(LogCategoryButton(category, log_dirs[category]))

class LogCategoryButton(Button):
    def __init__(self, category, log_dir):
        super().__init__(label=category, style=discord.ButtonStyle.primary)
        self.log_dir = log_dir

    async def callback(self, interaction: discord.Interaction):
        files = os.listdir(self.log_dir)
        if not files:
            await interaction.response.send_message("No logs available in this category.", ephemeral=True)
        else:
            view = LogFileView(self.log_dir, files)
            await interaction.response.send_message(f"Select a log file from {self.label}:", view=view, ephemeral=True)

class LogFileView(View):
    def __init__(self, log_dir, files):
        super().__init__()
        options = [discord.SelectOption(label=file) for file in files]
        self.add_item(LogFileSelect(log_dir, options))

class LogFileSelect(Select):
    def __init__(self, log_dir, options):
        super().__init__(placeholder="Choose a log file...", options=options)
        self.log_dir = log_dir

    async def callback(self, interaction: discord.Interaction):
        file_path = os.path.join(self.log_dir, self.values[0])
        with open(file_path, 'r') as f:
            log_content = f.read()

        # 로그 내용을 읽어서 Discord 메시지로 전송 (내용이 길면 잘라서 표시)
        content = log_content if len(log_content) < 2000 else log_content[-2000:]  # Discord 메시지 길이 제한 대응
        await interaction.response.send_message(f"**{self.values[0]}**\n```{content}```", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LogViewer(bot))
