import discord
from discord.ext import commands
import json

# Load config
with open('config.json') as f:
    config = json.load(f)

# Initialize bot
bot = commands.Bot(command_prefix=config['prefix'])

# Load cogs
# initial_extensions = ['cogs.cog1', 'cogs.cog2']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)

# Run bot
bot.run(config['token'])
