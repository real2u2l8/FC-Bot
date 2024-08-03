import asyncio
import discord
from discord.ext import commands
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import traceback
from datetime import datetime

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_dirs = {
            'commands': 'logs/commands',        # 명령어 로그 디렉토리
            'errors': 'logs/errors',            # 에러 로그 디렉토리
            'state': 'logs/state',              # 봇 상태 로그 디렉토리
            'user_activity': 'logs/user_activity' # 사용자 활동 로그 디렉토리
        }

        # 디스코드에서 에러 알림을 받을 채널 및 사용자 설정
        self.ERROR_CHANNEL_ID = 1268592140439781475  # 디스코드 채널 ID
        self.MENTION_USER_ID = 338696340001390593    # 멘션할 사용자 ID

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
            # 타임스탬프를 파일 이름에 추가
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            log_file = os.path.join(path, f'{key}_log_{timestamp}.log')

            # 타임스탬프가 포함된 파일 생성
            with open(log_file, 'a'):
                pass

            logger = logging.getLogger(key)
            logger.setLevel(logging.INFO)

            # TimedRotatingFileHandler 설정
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

        # 모든 로그 카테고리에 에러 발생을 기록
        for logger_name in self.loggers:
            self.loggers[logger_name].error(f"An unhandled exception occurred in {logger_name}. See {error_log_file} for details.")

        # 에러 내용을 에러 로그 파일에 기록
        with open(error_log_file, 'w') as f:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

        # 디스코드 채널에서 에러를 알림
        loop = asyncio.get_event_loop()
        loop.create_task(self.notify_error(exc_type, exc_value, exc_traceback, error_time, error_log_file))

    async def notify_error(self, exc_type, exc_value, exc_traceback, error_time, error_log_file):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(self.ERROR_CHANNEL_ID)
        user = self.bot.get_user(self.MENTION_USER_ID)
        
        # 에러가 발생한 줄 번호를 추출
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        error_message = ''.join(tb_lines)
        error_line = None
        for line in tb_lines:
            if "File" in line and ", line" in line:
                error_line = line
                break
        
        if channel and user:
            error_message = (
                f"{user.mention} **에러 발생 알림**\n"
                f"**시간:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**로그 파일:** `{error_log_file}`\n"
                f"**에러 줄:** `{error_line}`\n"
                f"에러 메시지: ```{exc_type.__name__}: {exc_value}```"
            )
            await channel.send(error_message)

    # 명령어 실행 중 에러 발생 시 로그 기록
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        for logger_name in self.loggers:
            self.loggers[logger_name].error(f'Error in command {ctx.command}: {error}', exc_info=True)

    # 봇 이벤트 발생 시 로그 기록
    @commands.Cog.listener()
    async def on_command(self, ctx):
        self.loggers['commands'].info(f'Command executed: {ctx.command} by {ctx.author} in {ctx.channel}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        self.loggers['user_activity'].info(f'Member joined: {member.name} (ID: {member.id})')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.loggers['user_activity'].info(f'Member left: {member.name} (ID: {member.id})')

async def setup(bot):
    await bot.add_cog(Logging(bot))
