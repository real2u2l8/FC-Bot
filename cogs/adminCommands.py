import discord
from discord.ext import commands
import logging

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.massage_log_channel_id = 1264772087156047944  # 메시지 로그를 기록할 채널의 ID
        self.channeling_log_channel_id = 1264981112695033887  # 채널관련 로그를 기록할 채널의 ID
        self.member_log_channel_id = 1264981524764299284  # 멤버 로그를 기록할 채널의 ID
        self.excluded_roles = ["BOT"]  # 로그에서 제외할 역할들
    # cogs 업데이트 후 reload
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
            
    ### 로그 전용 함수
    # 메시지 삭제 로그
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not any(role.name in self.excluded_roles for role in message.author.roles):
            log_channel = self.bot.get_channel(self.massage_log_channel_id)
            if log_channel:
                embed = discord.Embed(title="사용자 메시지 삭제 로그", color=discord.Color.red())
                embed.add_field(name="사용자", value=message.author.mention, inline=False)
                embed.add_field(name="채널", value=message.channel.mention, inline=False)
                embed.add_field(name="내용", value=message.content, inline=False)
                await log_channel.send(embed=embed)
    # 사용자 가입 로그
    @commands.Cog.listener()
    async def on_member_join(self, member):
        log_channel = self.bot.get_channel(self.member_log_channel_id)
        if log_channel:
            embed = discord.Embed(title="새로운 사용자 가입", color=discord.Color.green())
            embed.add_field(name="사용자", value=member.mention, inline=False)
            embed.add_field(name="가입 시간", value=member.joined_at, inline=False)
            await log_channel.send(embed=embed)
    # 사용자 퇴장 로그
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        log_channel = self.bot.get_channel(self.member_log_channel_id)
        if log_channel:
            embed = discord.Embed(title="사용자 퇴장", color=discord.Color.orange())
            embed.add_field(name="사용자", value=member.mention, inline=False)
            await log_channel.send(embed=embed)
    # 채널생성 로그
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        log_channel = self.bot.get_channel(self.channeling_log_channel_id)
        if log_channel:
            embed = discord.Embed(title="채널 생성", color=discord.Color.blue())
            embed.add_field(name="채널", value=channel.mention, inline=False)
            await log_channel.send(embed=embed)
    # 채널삭제 로그
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        log_channel = self.bot.get_channel(self.channeling_log_channel_id)
        if log_channel:
            embed = discord.Embed(title="채널 삭제", color=discord.Color.dark_blue())
            embed.add_field(name="채널", value=channel.name, inline=False)
            await log_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
