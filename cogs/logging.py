import discord
from discord.ext import commands, tasks
import os
from discord.ui import View, Button, Select
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import traceback
import asyncio
from datetime import datetime

class Logging(commands.Cog):
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

        # 각 로그 디렉토리를 생성
        for path in self.log_dirs.values():
            os.makedirs(path, exist_ok=True)

        # 로그 설정
        self.loggers = self.setup_loggers()

        # 전역 예외 핸들러 설정
        sys.excepthook = self.handle_exception

    def setup_loggers(self):
        loggers = {}
        for key, path in self.log_dirs.items():
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file = os.path.join(path, f'{key}_log_{timestamp}.log')
            with open(log_file, 'a'):
                pass

            logger = logging.getLogger(key)
            logger.setLevel(logging.INFO)
            handler = TimedRotatingFileHandler(log_file, when='h', interval=4, backupCount=6, encoding='utf-8')
            handler.suffix = "%Y-%m-%d_%H-%M-%S"  # 회전된 로그 파일의 타임스탬프 형식
            handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
            logger.addHandler(handler)
            loggers[key] = logger

        return loggers

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        # 타임스탬프를 포함한 에러 로그 파일 생성
        error_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        error_log_file = os.path.join(self.log_dirs['errors'], f'python_error_{error_time}.log')

        # 메인 로그에 에러 발생을 기록
        self.loggers['errors'].error(f"An unhandled exception occurred. See {error_log_file} for details.")

        # 에러 내용을 에러 로그 파일에 기록
        with open(error_log_file, 'w') as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

        # 디스코드 채널에서 에러를 알림
        loop = asyncio.get_event_loop()
        loop.create_task(self.notify_error(exc_type, exc_value, exc_traceback, error_time, error_log_file))

    async def notify_error(self, exc_type, exc_value, exc_traceback, error_time, error_log_file):
        channel = self.bot.get_channel(self.log_summary_channel_id)
        if channel:
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            error_message = ''.join(tb_lines[-2:])
            await channel.send(
                f"**에러 발생 알림**\n"
                f"**시간:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**로그 파일:** `{error_log_file}`\n"
                f"에러 메시지: ```{exc_type.__name__}: {exc_value}```\n"
                f"자세한 내용은 로그 파일을 참조하세요."
            )

    @commands.Cog.listener()
    async def on_ready(self):
        """봇이 준비되었을 때 상태를 로깅"""
        self.loggers['state'].info(f'Logged in as {self.bot.user.name} - {self.bot.user.id}')
        await self.bot.change_presence(activity=discord.Game(name="Logging!"))

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """모든 명령어 사용 시 로깅"""
        self.loggers['commands'].info(f'Command executed: {ctx.command} by {ctx.author} in {ctx.channel}')
        if ctx.command.name in self.monitor_commands:
            self.loggers['commands'].info(f'Monitored command executed: {ctx.command} by {ctx.author} in {ctx.channel}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """명령어 실행 중 에러 발생 시 로깅"""
        self.loggers['commands'].error(f'Error in command {ctx.command}: {error}', exc_info=True)
        self.loggers['errors'].error(f'Error in command {ctx.command}: {error}', exc_info=True)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """사용자 활동 로그 - 서버에 새로운 멤버 가입 시"""
        self.loggers['user_activity'].info(f'Member joined: {member.name} (ID: {member.id})')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """사용자 활동 로그 - 멤버가 서버를 떠날 시"""
        self.loggers['user_activity'].info(f'Member left: {member.name} (ID: {member.id})')

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
        report_file = os.path.join(result_dir, f'log_summary_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
        with open(report_file, 'w') as f:
            f.write("\n".join(summary_report))

    @log_summary.before_loop
    async def before_log_summary(self):
        await self.bot.wait_until_ready()

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

class LogSearchView(View):
    def __init__(self, log_dirs):
        super().__init__()
        self.log_dirs = log_dirs
        options = [discord.SelectOption(label=key) for key in log_dirs.keys()]
        self.add_item(LogSearchCategorySelect(options))

class LogSearchCategorySelect(Select):
    def __init__(self, options):
        super().__init__(placeholder="검색할 로그 카테고리를 선택하세요...", options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("검색할 키워드를 입력하세요.", ephemeral=True)
        self.selected_category = self.values[0]  # 선택된 카테고리 저장
        self.view.stop()  # 드롭다운 메뉴 비활성화 후 키워드 입력을 받기 위해 뷰 종료

class LogDownloadView(View):
    def __init__(self, log_dirs):
        super().__init__()
        options = [discord.SelectOption(label=key) for key in log_dirs.keys()]
        self.add_item(LogDownloadCategorySelect(options))

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
    await bot.add_cog(Logging(bot))
