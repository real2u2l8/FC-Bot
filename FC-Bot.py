import discord
from discord.ext import commands
import asyncio
import json

# config.json 파일에서 설정 불러오기
with open('config.json') as f:
    config = json.load(f)

# 디스코드 봇 설정
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

# 확장 모듈 로드
async def load_extensions():
    initial_extensions = ['cogs.logging', 'cogs.adminCommands', 'cogs.attendance', 'cogs.common', 'cogs.service', 'cogs.draft', 'cogs.register', 'cogs.autoMessage', 'cogs.logViewer']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f'Successfully loaded {extension}')
        except Exception as e:
            print(f'Failed to load {extension}: {e}')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    await load_extensions()

# 봇 실행
async def main():
    async with bot:
        await bot.start(config['token'])

asyncio.run(main())
