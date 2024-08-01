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

# config.json 파일에서 설정을 로드합니다.
with open('config.json') as f:
    config = json.load(f)

# 로그를 저장할 디렉터리를 설정합니다.
log_dir = 'logs'  # 기본 로그를 저장할 디렉터리
error_log_dir = os.path.join(log_dir, 'errors')  # 에러 로그를 저장할 디렉터리
os.makedirs(log_dir, exist_ok=True)
os.makedirs(error_log_dir, exist_ok=True)

# 로그 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# 타임스탬프가 포함된 파일 핸들러를 생성하는 함수
def create_timed_rotating_log(path):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = os.path.join(path, f'bot_{timestamp}.log')
    handler = TimedRotatingFileHandler(log_filename, when='h', interval=4, backupCount=6)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
    return handler

# 정기적인 로그 파일 핸들러를 추가합니다.
logger.addHandler(create_timed_rotating_log(log_dir))

# 콘솔에 로그를 출력하는 핸들러를 추가합니다.
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(console_handler)

# 예기치 않은 예외에 대한 에러 로그를 설정합니다.
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # 타임스탬프가 포함된 에러 로그 파일을 생성합니다.
    error_time = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    error_log_file = os.path.join(error_log_dir, f'python_error_{error_time}.log')
    
    # 메인 로그에 에러가 발생했음을 기록합니다.
    logger.error(f"Unhandled exception occurred. See {error_log_file} for details.")
    
    # 에러 로그 파일에 에러 세부 정보를 기록합니다.
    with open(error_log_file, 'w') as f:
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)

# 기본 예외 처리기로 위에서 정의한 핸들러를 설정합니다.
sys.excepthook = handle_exception

# 봇 초기화
intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
intents.members = True
intents.message_content = True  # 메시지 내용을 읽기 위해 필요합니다.

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

# 익스텐션 로드
async def load_extensions():
    initial_extensions = ['cogs.adminCommands', 'cogs.attendance', 'cogs.common', 'cogs.service', 'cogs.draft', 'cogs.register', 'cogs.autoMessage']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)  # 비동기 방식으로 익스텐션 로드
            logger.info(f'Successfully loaded extension {extension}')
        except Exception as e:
            logger.error(f'Failed to load extension {extension}.', exc_info=True)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name} - {bot.user.id}')
    await load_extensions()  # 비동기 방식으로 익스텐션 로드

# 봇 실행
async def main():
    async with bot:
        await bot.start(config['token'])

asyncio.run(main())
