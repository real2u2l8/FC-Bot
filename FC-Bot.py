import discord
from discord.ext import commands
import json
import logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)

# Load config
with open('config.json') as f:
    config = json.load(f)

# Initialize bot
intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
intents.members = True
intents.message_content = True  # This is needed to read message content

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

async def load_extensions():
    initial_extensions = ['cogs.adminCommands', 'cogs.attendance', 'cogs.common', 'cogs.service', 'cogs.draft']
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)  # Call by Asyn
            logging.info(f'Successfully loaded extension {extension}')
        except Exception as e:
            logging.error(f'Failed to load extension {extension}.', exc_info=True)

@bot.event
async def on_ready():
    logging.info(f'Logged in as {bot.user.name} - {bot.user.id}')
    await load_extensions()  # Call by Asyn

# Run bot
async def main():
    async with bot:
        await bot.start(config['token'])

asyncio.run(main())
