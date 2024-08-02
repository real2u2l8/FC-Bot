import discord
from discord.ext import commands, tasks
import os
from discord.ui import View, Button, Select
import datetime
import shutil
import json

class LogViewer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dirs = {
            'commands': 'logs/commands',        # 명령어 로그
            'errors': 'logs/errors',            # 에러 로그
            'state': 'logs/state',              # 봇 상태 로그
            'user_activity': 'logs/user_activity' # 사용자 활동 로그
        }
        self.monitor_commands = ['$드래프트', '$드래프트선택', '$대기참가', '$선수등록']  # 모니터링할 명령어 리스트
        self.log_summary_channel_id = 1268592140439781475  # 보고서를 보낼 채널 ID
        self.monitoring_period = 3  # 3일 동안 모니터링
        self.log_retention_days = 14  # 로그 보관 기간: 14일
        self.log_summary.start()  # 자동 로그 요약 작업 시작

    @commands.command(name='로그')
    @commands.has_role('매니저')  # '매니저' 역할을 가진 사용자만 이 명령어를 사용할 수 있습니다.
    async def show_logs(self, ctx):
        """로그 카테고리 선택 버튼 표시"""
        view = LogCategoryView(self.log_dirs)
        await ctx.send("로그 카테고리를 선택하세요:", view=view)

    @commands.command(name='로그검색')
    @commands.has_role('매니저')
    async def search_logs(self, ctx):
        """특정 키워드로 로그 검색 (카테고리 선택을 드롭다운으로 처리)"""
        view = LogSearchView(self.log_dirs)
        await ctx.send("검색할 로그 카테고리를 선택하고, 키워드를 입력하세요:", view=view)

    @commands.command(name='로그다운로드')
    @commands.has_role('매니저')
    async def download_log(self, ctx):
        """선택한 카테고리의 최신 로그 파일 다운로드 (카테고리 선택을 드롭다운으로 처리)"""
        view = LogDownloadView(self.log_dirs)
        await ctx.send("다운로드할 로그 카테고리를 선택하세요:", view=view)

    @tasks.loop(hours=72)  # 3일마다 자동으로 실행
    async def log_summary(self):
        """로그 요약 보고서 생성 및 전송"""
        summary_channel = self.bot.get_channel(self.log_summary_channel_id)
        summary_report = []

        # 명령어 사용 빈도 요약
        command_count = {}
        for command in self.monitor_commands:
            command_count[command] = 0

        # 명령어 로그에서 사용 빈도 집계
        for log_file in os.listdir(self.log_dirs['commands']):
            file_path = os.path.join(self.log_dirs['commands'], log_file)
            with open(file_path, 'r') as f:
                for line in f:
                    for command in self.monitor_commands:
                        if command in line:
                            command_count[command] += 1

        summary_report.append("**명령어 사용 빈도**")
        for command, count in command_count.items():
            summary_report.append(f"{command}: {count}회")

        # 주요 에러 요약
        error_summary = []
        for log_file in os.listdir(self.log_dirs['errors']):
            file_path = os.path.join(self.log_dirs['errors'], log_file)
            with open(file_path, 'r') as f:
                error_summary.extend(f.readlines())

        if error_summary:
            summary_report.append("\n**주요 에러 요약**")
            summary_report.append(''.join(error_summary[-5:]))  # 마지막 5개의 에러 메시지를 포함

        # 사용자 활동 요약
        user_activity_summary = []
        for log_file in os.listdir(self.log_dirs['user_activity']):
            file_path = os.path.join(self.log_dirs['user_activity'], log_file)
            with open(file_path, 'r') as f:
                user_activity_summary.extend(f.readlines())

        if user_activity_summary:
            summary_report.append("\n**사용자 활동 요약**")
            summary_report.append(''.join(user_activity_summary[-5:]))  # 마지막 5개의 사용자 활동 로그 포함

        # 보고서를 채널에 전송
        await summary_channel.send("\n".join(summary_report))

        # 요약 보고서를 파일로 저장
        result_dir = 'logs/result/'
        os.makedirs(result_dir, exist_ok=True)
        report_file = os.path.join(result_dir, f'log_summary_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
        with open(report_file, 'w') as f:
            f.write("\n".join(summary_report))

    @log_summary.before_loop
    async def before_log_summary(self):
        await self.bot.wait_until_ready()

    @show_logs.error
    async def show_logs_error(self, ctx, error):
        if isinstance(error, commands.MissingRole):
            await ctx.send("이 명령어를 사용하려면 '매니저' 역할이 필요합니다.")

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """특정 명령어 사용 시 로깅"""
        if ctx.command.name in self.monitor_commands:
            log_file = os.path.join(self.log_dirs['commands'], f'{ctx.command.name}_log')
            with open(log_file, 'a') as f:
                f.write(f'{datetime.datetime.now()}: {ctx.author} used {ctx.command.name} in {ctx.channel}\n')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """사용자 활동 로그 - 서버에 새로운 멤버 가입 시"""
        log_file = os.path.join(self.log_dirs['user_activity'], 'user_activity_log')
        with open(log_file, 'a') as f:
            f.write(f'{datetime.datetime.now()}: {member.name} joined the server.\n')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """사용자 활동 로그 - 멤버가 서버를 떠날 시"""
        log_file = os.path.join(self.log_dirs['user_activity'], 'user_activity_log')
        with open(log_file, 'a') as f:
            f.write(f'{datetime.datetime.now()}: {member.name} left the server.\n')

# 로그 카테고리 선택 뷰
class LogCategoryView(View):
    def __init__(self, log_dirs):
        super().__init__()
        self.log_dirs = log_dirs
        for category in log_dirs.keys():
            self.add_item(LogCategoryButton(category, log_dirs[category]))

# 로그 카테고리 버튼
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

# 로그 파일 뷰
class LogFileView(View):
    def __init__(self, log_dir, files):
        super().__init__()
        options = [discord.SelectOption(label=file) for file in files]
        self.add_item(LogFileSelect(log_dir, options))

# 로그 파일 선택 셀렉트
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

# 로그 검색을 위한 뷰
class LogSearchView(View):
    def __init__(self, log_dirs):
        super().__init__()
        options = [discord.SelectOption(label=key) for key in log_dirs.keys()]
        self.add_item(LogSearchCategorySelect(options))

# 로그 검색 카테고리 셀렉트
class LogSearchCategorySelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="검색할 로그 카테고리를 선택하세요...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"검색할 키워드를 입력하세요.", ephemeral=True)
        self.view.stop()  # 드롭다운 메뉴 비활성화 후 키워드 입력을 받기 위해 뷰 종료

# 로그 다운로드를 위한 뷰
class LogDownloadView(View):
    def __init__(self, log_dirs):
        super().__init__()
        options = [discord.SelectOption(label=key) for key in log_dirs.keys()]
        self.add_item(LogDownloadCategorySelect(options))

# 로그 다운로드 카테고리 셀렉트
class LogDownloadCategorySelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="다운로드할 로그 카테고리를 선택하세요...", options=options)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]
        log_dir = self.view.log_dirs[category]
        files = sorted(os.listdir(log_dir), reverse=True)
        if not files:
            await interaction.response.send_message("No logs available in this category.", ephemeral=True)
        else:
            file_path = os.path.join(log_dir, files[0])
            await interaction.response.send_message(file=discord.File(file_path), ephemeral=True)

async def setup(bot):
    await bot.add_cog(LogViewer(bot))
