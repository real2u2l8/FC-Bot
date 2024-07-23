import discord
from discord.ext import commands
import json
import logging
import asyncio
import os

# Load config
with open('config.json') as f:
    config = json.load(f)

# Get the absolute path for the log file
log_file = config.get('log_file', 'bot.log')
log_file_path = os.path.abspath(log_file)

# Ensure the log directory exists
log_dir = os.path.dirname(log_file_path)
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s: %(message)s', handlers=[
    logging.FileHandler(log_file_path),
    logging.StreamHandler()
])

# Initialize bot
intents = discord.Intents.default()
intents.reactions = True
intents.messages = True
intents.members = True
intents.message_content = True  # This is needed to read message content

bot = commands.Bot(command_prefix=config['prefix'], intents=intents)

async def load_extensions():
    initial_extensions = ['cogs.adminCommands', 'cogs.attendance', 'cogs.common', 'cogs.service', 'cogs.draft', 'cogs.register']
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
