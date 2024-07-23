import discord
from discord.ext import commands
import logging

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.message_log_channel_id = 1264772087156047944  # 메시지 로그를 기록할 채널의 ID
        self.channeling_log_channel_id = 1264981112695033887  # 채널관련 로그를 기록할 채널의 ID
        self.member_log_channel_id = 1264981524764299284  # 멤버 로그를 기록할 채널의 ID
        self.excluded_roles = ["BOT"]  # 로그에서 제외할 역할들

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
        print(f"Message deleted: {message.content} by {message.author}")
        if not any(role.name in self.excluded_roles for role in message.author.roles):
            log_channel = self.bot.get_channel(self.message_log_channel_id)
            if log_channel:
                embed = discord.Embed(title="사용자 메시지 삭제 로그", color=discord.Color.red())
                embed.add_field(name="사용자", value=message.author.mention, inline=False)
                embed.add_field(name="채널", value=message.channel.mention, inline=False)
                embed.add_field(name="내용", value=message.content, inline=False)

                # 감사 로그에서 삭제한 사람 찾기
                async for entry in message.guild.audit_logs(action=discord.AuditLogAction.message_delete, limit=5):
                    if entry.target.id == message.author.id and entry.extra.channel.id == message.channel.id:
                        embed.add_field(name="삭제한 사람", value=entry.user.mention, inline=False)
                        break

                await log_channel.send(embed=embed)
            else:
                print("Logging channel not found for message deletion.")

    # 메시지 수정 로그
    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        print(f"Message edited: {before.content} -> {after.content} by {before.author}")
        if not any(role.name in self.excluded_roles for role in before.author.roles):
            log_channel = self.bot.get_channel(self.message_log_channel_id)
            if log_channel:
                embed = discord.Embed(title="사용자 메시지 수정 로그", color=discord.Color.orange())
                embed.add_field(name="사용자", value=before.author.mention, inline=False)
                embed.add_field(name="채널", value=before.channel.mention, inline=False)
                embed.add_field(name="수정 전 내용", value=before.content, inline=False)
                embed.add_field(name="수정 후 내용", value=after.content, inline=False)
                await log_channel.send(embed=embed)
            else:
                print("Logging channel not found for message edit.")

    # 사용자 가입 로그
    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"Member joined: {member}")
        log_channel = self.bot.get_channel(self.member_log_channel_id)
        if log_channel:
            embed = discord.Embed(title="새로운 사용자 가입", color=discord.Color.green())
            embed.add_field(name="사용자", value=member.mention, inline=False)
            embed.add_field(name="가입 시간", value=member.joined_at, inline=False)
            await log_channel.send(embed=embed)
        else:
            print("Logging channel not found for member join.")

    # 사용자 퇴장 로그
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f"Member left or was kicked: {member}")
        log_channel = self.bot.get_channel(self.member_log_channel_id)
        if log_channel:
            async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
                print(f"Audit log entry for kick: {entry}")
                if entry.target.id == member.id:
                    print(f"Member kicked by {entry.user}")
                    embed = discord.Embed(title="사용자 추방", color=discord.Color.red())
                    embed.add_field(name="사용자", value=member.mention, inline=False)
                    embed.add_field(name="실행자", value=entry.user.mention, inline=False)
                    await log_channel.send(embed=embed)
                    break
            else:
                print("Member left voluntarily")
                embed = discord.Embed(title="사용자 퇴장", color=discord.Color.orange())
                embed.add_field(name="사용자", value=member.mention, inline=False)
                await log_channel.send(embed=embed)
        else:
            print("Logging channel not found for member remove.")

    # 채널 생성 로그
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        print(f"Channel created: {channel.name}")
        log_channel = self.bot.get_channel(self.channeling_log_channel_id)
        if log_channel:
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_create, limit=1):
                print(f"Audit log entry for channel create: {entry}")
                if entry.target.id == channel.id:
                    print(f"Channel created by {entry.user}")
                    embed = discord.Embed(title="채널 생성", color=discord.Color.blue())
                    embed.add_field(name="채널", value=channel.mention, inline=False)
                    embed.add_field(name="생성자", value=entry.user.mention, inline=False)
                    await log_channel.send(embed=embed)
                    break
        else:
            print("Logging channel not found for channel create.")

    # 채널 삭제 로그
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        print(f"Channel deleted: {channel.name}")
        log_channel = self.bot.get_channel(self.channeling_log_channel_id)
        if log_channel:
            async for entry in channel.guild.audit_logs(action=discord.AuditLogAction.channel_delete, limit=1):
                print(f"Audit log entry for channel delete: {entry}")
                if entry.target.id == channel.id:
                    print(f"Channel deleted by {entry.user}")
                    embed = discord.Embed(title="채널 삭제", color=discord.Color.dark_blue())
                    embed.add_field(name="채널", value=channel.name, inline=False)
                    embed.add_field(name="삭제자", value=entry.user.mention, inline=False)
                    await log_channel.send(embed=embed)
                    break
        else:
            print("Logging channel not found for channel delete.")

async def setup(bot):
    await bot.add_cog(Admin(bot))
