import discord
from discord.ext import commands
import asyncio
import json
import traceback

# config.json 파일에서 설정 불러오기
with open('config.json') as f:
    config = json.load(f)

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

# 로드된 확장 모듈을 추적하기 위한 세트
loaded_extensions = set()

# 확장 모듈 로드
async def load_extensions():
    initial_extensions = [
        'cogs.logging', 
        'cogs.adminCommands',
        'cogs.attendance', 
        'cogs.common', 
        'cogs.service', 
        'cogs.draft', 
        'cogs.register',
        'cogs.autoMessage'
    ]
    
    for extension in initial_extensions:
        if extension in loaded_extensions:
            print(f'Extension {extension} is already loaded, skipping.')
            continue
        
        try:
            await bot.load_extension(extension)
            print(f'Successfully loaded {extension}')
            loaded_extensions.add(extension)  # 성공적으로 로드된 모듈을 세트에 추가
        except Exception as e:
            print(f'Failed to load {extension}: {e}')
            traceback.print_exc()  # 전체 스택 트레이스를 출력

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await load_extensions()

# 봇 실행
async def main():
    async with bot:
        await bot.start(config['token'])

asyncio.run(main())
