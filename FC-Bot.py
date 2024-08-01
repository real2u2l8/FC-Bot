import discord
from discord.ext import commands
import json
import logging
from logging.handlers import TimedRotatingFileHandler
import asyncio
import os
import sys
import traceback
from datetime import datetime

# config.json 파일에서 설정 불러오기
with open('config.json') as f:
    config = json.load(f)

# 로그 디렉토리 설정
log_dirs = {
    'commands': 'logs/commands',        # 명령어 로그
    'errors': 'logs/errors',            # 에러 로그
    'state': 'logs/state',              # 봇 상태 로그
    'user_activity': 'logs/user_activity' # 사용자 활동 로그
}

# 각 로그 디렉토리를 생성
for path in log_dirs.values():
    os.makedirs(path, exist_ok=True)

# 현재 시간을 로그 파일 이름에 추가
timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

# 로그 핸들러 설정
loggers = {}
for key, path in log_dirs.items():
    log_file = os.path.join(path, f'{key}_log_{timestamp}')
    logger = logging.getLogger(key)
    logger.setLevel(logging.INFO)
    handler = TimedRotatingFileHandler(log_file, when='h', interval=4, backupCount=6)  # 4시간마다 로그 회전
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)
    loggers[key] = logger

# 디스코드에서 에러 알림을 받을 채널 및 사용자 설정
ERROR_CHANNEL_ID = 1268592140439781475  # 디스코드 채널 ID
MENTION_USER_ID = 338696340001390593   # 멘션할 사용자 ID

# 예기치 않은 예외를 위한 에러 로깅 설정
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 타임스탬프를 포함한 에러 로그 파일 생성
    error_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    error_log_file = os.path.join(log_dirs['errors'], f'python_error_{error_time}')
    
    # 메인 로그에 에러 발생을 기록
    loggers['errors'].error(f"An unhandled exception occurred. See {error_log_file} for details.")
    
    # 에러 내용을 에러 로그 파일에 기록
    with open(error_log_file, 'w') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    
    # 디스코드 채널에서 에러를 알림
    loop = asyncio.get_event_loop()
    loop.create_task(notify_error(exc_type, exc_value, exc_traceback, error_time, error_log_file))

# 예외 핸들러를 기본 핸들러로 설정
sys.excepthook = handle_exception

# 봇 초기화
intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
intents.members = True
intents.message_content = True  # 메시지 내용을 읽기 위한 권한

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

# 확장 모듈 로드
async def load_extensions():
    initial_extensions = ['cogs.adminCommands', 'cogs.attendance', 'cogs.common', 'cogs.service', 'cogs.draft', 'cogs.register','cogs.autoMessage', 'cogs.logViewer']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            loggers['state'].info(f'Successfully loaded extension {extension}')
        except Exception as e:
            loggers['state'].error(f'Failed to load extension {extension}.', exc_info=True)

# 디스코드 채널에 에러 알림을 보내는 함수
async def notify_error(exc_type, exc_value, exc_traceback, error_time, error_log_file):
    await bot.wait_until_ready()
    channel = bot.get_channel(ERROR_CHANNEL_ID)
    user = bot.get_user(MENTION_USER_ID)
    
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

# 봇이 준비되었을 때 실행되는 이벤트
@bot.event
async def on_ready():
    loggers['state'].info(f'Logged in as {bot.user.name} - {bot.user.id}')
    await load_extensions()

# 명령어가 실행될 때 로그 기록
@bot.event
async def on_command(ctx):
    loggers['commands'].info(f'Command executed: {ctx.command} by {ctx.author} in {ctx.channel}')

# 명령어 실행 중 에러 발생 시 로그 기록
@bot.event
async def on_command_error(ctx, error):
    loggers['commands'].error(f'Error in command {ctx.command}: {error}', exc_info=True)

# 사용자가 서버에 가입했을 때 로그 기록
@bot.event
async def on_member_join(member):
    loggers['user_activity'].info(f'Member joined: {member.name} (ID: {member.id})')

# 사용자가 서버를 떠났을 때 로그 기록
@bot.event
async def on_member_remove(member):
    loggers['user_activity'].info(f'Member left: {member.name} (ID: {member.id})')

# 봇 실행
async def main():
    async with bot:
        await bot.start(config['token'])

asyncio.run(main())
