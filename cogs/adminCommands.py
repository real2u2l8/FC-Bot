from discord.ext import commands
import logging

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='리로드')
    @commands.is_owner()
    async def reload_cog(self, ctx, cog: str):
        try:
            await self.bot.unload_extension(f'cogs.{cog}')
            await self.bot.load_extension(f'cogs.{cog}')
            await ctx.send(f'Cog {cog} reloaded successfully.')
            logging.info(f'Cog {cog} reloaded successfully.')
        except Exception as e:
            await ctx.send(f'Failed to reload Cog {cog}.')
            logging.error(f'Failed to reload Cog {cog}.', exc_info=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))
