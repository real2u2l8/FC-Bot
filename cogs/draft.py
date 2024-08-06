import discord
from discord.ext import commands
import asyncio
import random

class Draft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.positions = {}  # 각 채널의 포지션 정보를 저장하는 딕셔너리
        self.teams = {}  # 각 채널의 팀 정보를 저장하는 딕셔너리
        self.user_positions = {}  # 사용자의 포지션 정보를 저장하는 딕셔너리
        self.registration_channel_id = 1264757976997040240  # 대기 등록 채널 ID
        self.waiting_pool = []  # 대기 목록에 있는 사용자 리스트
        self.allowed_roles = ["매니저", ""]  # 명령어를 사용할 수 있는 허용된 역할들
        self.formations = {}  # 각 채널의 포메이션 정보를 저장하는 딕셔너리
        self.draft_message_ids = {}  # 각 채널의 드래프트 메시지 ID를 저장하는 딕셔너리

    @commands.command(name='대기참가')
    async def join_waiting_list(self, ctx):
        # 대기 목록에 사용자를 추가하는 명령어
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if ctx.author in self.waiting_pool:
            await ctx.send(f"{ctx.author.mention}님은 이미 대기 목록에 있습니다.")
        else:
            self.waiting_pool.append(ctx.author)
            await ctx.send(f"{ctx.author.mention}님이 대기 목록에 추가되었습니다.")
        await self.show_waiting_list(ctx)

    @commands.command(name='대기삭제')
    async def leave_waiting_list(self, ctx):
        # 대기 목록에서 사용자를 제거하는 명령어
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if ctx.author in self.waiting_pool:
            self.waiting_pool.remove(ctx.author)
            await ctx.send(f"{ctx.author.mention}님이 대기 목록에서 제거되었습니다.")
        else:
            await ctx.send(f"{ctx.author.mention}님은 대기 목록에 없습니다.")
        await self.show_waiting_list(ctx)

    @commands.command(name='대기전체삭제')
    async def clear_waiting_list(self, ctx):
        # 대기 목록을 모두 초기화하는 명령어
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if not await self.has_allowed_role(ctx):
            await ctx.send("이 명령어를 사용할 권한이 없습니다.")
            return

        self.waiting_pool.clear()
        await ctx.send("대기 목록이 초기화되었습니다.")
        await self.show_waiting_list(ctx)

    async def show_waiting_list(self, ctx):
        # 현재 대기 목록을 출력하는 함수
        if not self.waiting_pool:
            await ctx.send("현재 대기 목록이 비어 있습니다.")
        else:
            waiting_list = "\n".join(f"{idx + 1}. {member.mention}" for idx, member in enumerate(self.waiting_pool))
            embed = discord.Embed(title="대기 목록 현황", description=waiting_list, color=discord.Color.blue())
            await ctx.send(embed=embed)

    async def has_allowed_role(self, ctx):
        # 사용자가 허용된 역할을 가지고 있는지 확인하는 함수
        return any(role.name in self.allowed_roles for role in ctx.author.roles)

    @commands.command(name="드래프트")
    async def start_draft(self, ctx, team_count: str):
        # 드래프트를 시작하는 명령어
        if team_count not in ["1", "2"]:
            await ctx.send("팀 수는 1 또는 2만 가능합니다. 올바른 명령어 형식은 `$드래프트 1` 또는 `$드래프트 2`입니다.")
            return

        # 4-3-3 포메이션으로 팀 설정
        self.formations[ctx.channel.id] = ["4-3-3"] * int(team_count)
        self.init_draft(ctx.channel.id, int(team_count), self.formations[ctx.channel.id])
        
        # 드래프트 메시지를 생성하고 이모지를 추가
        draft_message = await ctx.send("### 포메이션: 4-3-3\n **원하는 포지션의 이모지를 클릭하세요.**")
        self.draft_message_ids[ctx.channel.id] = draft_message.id

        emojis = self.get_emojis_for_formation(ctx.guild, self.formations[ctx.channel.id][0])
        for emoji in emojis.values():
            await draft_message.add_reaction(emoji)

        # 10초 동안 카운트다운 메시지를 업데이트
        countdown_message = await ctx.send("카운트다운: 10초 남았습니다!")
        for i in range(10, 0, -1):
            await countdown_message.edit(content=f"카운트다운: {i}초 남았습니다!")
            await asyncio.sleep(1)

        # 10초 후 드래프트 자동 완료
        await countdown_message.edit(content="시간이 만료되었습니다. 드래프트를 완료합니다.")
        await self.complete_draft(ctx, int(team_count))

    def init_draft(self, channel_id, team_count, formations):
        # 드래프트 초기화 함수
        self.positions[channel_id] = {f"Team {i+1}": {pos: [] for pos in self.get_positions_for_formation(formations[i])} for i in range(team_count)}
        self.teams[channel_id] = {f"Team {i+1}": {pos: [] for pos in self.get_positions_for_formation(formations[i])} for i in range(team_count)}
        self.user_positions[channel_id] = {}

    def get_positions_for_formation(self, formation):
        # 포메이션에 따른 포지션 리스트 반환
        formations = {
            "4-3-3": ["ST", "LW", "RW", "CM", "CDM", "LB", "CB", "RB", "GK"],
        }
        return formations.get(formation, [])

    def get_emojis_for_formation(self, guild, formation):
        # 서버의 이모지를 사용하여 포지션 매핑 함수
        emojis = {
            "4-3-3": {
                'ST': discord.utils.get(guild.emojis, name="ESPN_ST"),
                'LW': discord.utils.get(guild.emojis, name="ESPN_LW"),
                'RW': discord.utils.get(guild.emojis, name="ESPN_RW"),
                'CM': discord.utils.get(guild.emojis, name="ESPN_CM"),
                'CDM': discord.utils.get(guild.emojis, name="ESPN_DM"),
                'LB': discord.utils.get(guild.emojis, name="ESPN_LB"),
                'CB': discord.utils.get(guild.emojis, name="ESPN_CB"),
                'RB': discord.utils.get(guild.emojis, name="ESPN_RB"),
                'GK': discord.utils.get(guild.emojis, name="ESPN_GK"),
            },
        }
        return emojis.get(formation, {})

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # 이모지 반응 추가 시 호출되는 이벤트 리스너
        if user.bot or reaction.message.id != self.draft_message_ids.get(reaction.message.channel.id):
            return

        channel_id = reaction.message.channel.id
        if user.id in self.user_positions[channel_id]:
            return  # 중복 클릭 방지

        positions = self.get_positions_for_formation(self.formations[channel_id][0])
        position_map = self.get_emojis_for_formation(reaction.message.guild, self.formations[channel_id][0])

        position = next((pos for pos, emoji in position_map.items() if emoji == reaction.emoji), None)
        if position:
            # CM과 CB는 각 2명의 선수를 배정
            max_players = 2 if position in ["CM", "CB"] else 1
            if len(self.positions[channel_id][f"Team 1"][position]) < max_players:
                self.positions[channel_id][f"Team 1"][position].append(user)
                self.user_positions[channel_id][user.id] = position

    @commands.command(name='드래프트완료')
    async def complete_draft_command(self, ctx):
        # 관리자가 드래프트를 수동으로 완료하는 명령어
        if not await self.has_allowed_role(ctx):
            await ctx.send("이 명령어를 사용할 권한이 없습니다.")
            return
        await self.complete_draft(ctx, len(self.formations[ctx.channel.id]))

    async def complete_draft(self, ctx, team_count):
        # 드래프트 완료 후 결과 출력 함수
        channel_id = ctx.channel.id
        unselected_users = []

        for team in range(1, team_count + 1):
            for position, users in self.positions[channel_id][f"Team {team}"].items():
                if users:
                    max_players = 2 if position in ["CM", "CB"] else 1
                    chosen_users = random.sample(users, min(max_players, len(users)))
                    for chosen_user in chosen_users:
                        self.teams[channel_id][f"Team {team}"][position].append(chosen_user)
                    unselected_users.extend([user for user in users if user not in chosen_users])

        # Team 1 결과 임베드 생성
        embed_team1 = discord.Embed(title="A팀 드래프트 결과", color=discord.Color.blue())
        for position in self.get_positions_for_formation(self.formations[channel_id][0]):
            embed_team1.add_field(name=position, value=self.get_user_mention(channel_id, "Team 1", position), inline=False)
        await ctx.send(embed=embed_team1)

        # Team 2 결과 임베드 생성 (필요 시)
        if team_count == 2:
            embed_team2 = discord.Embed(title="B팀 드래프트 결과", color=discord.Color.red())
            for position in self.get_positions_for_formation(self.formations[channel_id][1]):
                embed_team2.add_field(name=position, value=self.get_user_mention(channel_id, "Team 2", position), inline=False)
            await ctx.send(embed=embed_team2)

        if unselected_users:
            unselected_message = "포지션에 선택되지 않은 인원:\n"
            unselected_message += "\n".join(f"{user.mention} - {self.user_positions[channel_id][user.id]}" for user in unselected_users)
            await ctx.send(unselected_message)
            await ctx.send(f'**$뽑기 [포지션]** 명령어를 사용하여 포지션 경쟁을 시작하세요.\n')

        self.reset_draft(channel_id)

    def get_user_mention(self, channel_id, team, position):
        # 유저의 멘션을 반환하는 함수
        users = self.teams[channel_id][team].get(position, [])
        return ", ".join(user.mention for user in users) if users else position

    def reset_draft(self, channel_id):
        # 드래프트 관련 정보를 초기화하는 함수
        self.user_positions.pop(channel_id, None)
        self.positions.pop(channel_id, None)
        self.teams.pop(channel_id, None)
        self.formations.pop(channel_id, None)
        self.draft_message_ids.pop(channel_id, None)

async def setup(bot):
    # 코그를 봇에 추가하는 함수
    await bot.add_cog(Draft(bot))
