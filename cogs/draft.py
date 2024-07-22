import discord
from discord.ext import commands, tasks
from discord.utils import get
import random
import asyncio

class Draft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.draft_message_ids = {}  # 채널별 드래프트 메시지 ID 저장
        self.positions = {}  # 채널별 포지션 저장
        self.teams = {}  # 채널별 팀 저장
        self.user_positions = {}  # 채널별 사용자 포지션 저장
        self.registration_channel_id = 1264757976997040240  # 대기 참가/삭제 명령어를 사용할 수 있는 채널 ID
        self.guide_channel_id = 1264757976997040240  # 드래프트 가이드를 올릴 채널 ID
        self.waiting_pool = []  # 대기 참가자를 저장하는 리스트
        self.allowed_roles = ["매니저", ""]  # 명령어를 사용할 수 있는 역할 이름들

    def cog_unload(self):
        pass

    @commands.command(name='대기참가')
    async def join_waiting_list(self, ctx):
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
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if ctx.author in self.waiting_pool:
            self.waiting_pool.remove(ctx.author)
            await ctx.send(f"{ctx.author.mention}님이 대기 목록에서 제거되었습니다.")
        else:
            await ctx.send(f"{ctx.author.mention}님은 대기 목록에 없습니다.")

        await self.show_waiting_list(ctx)

    @commands.command(name='대기삭제_번호')
    async def leave_waiting_list_by_number(self, ctx, index: int):
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if not await self.has_allowed_role(ctx):
            await ctx.send("이 명령어를 사용할 권한이 없습니다.")
            return

        if 1 <= index <= len(self.waiting_pool):
            removed_user = self.waiting_pool.pop(index - 1)
            await ctx.send(f"{removed_user.mention}님이 대기 목록에서 제거되었습니다.")
        else:
            await ctx.send("잘못된 인덱스입니다. 올바른 인덱스를 입력해주세요.")

        await self.show_waiting_list(ctx)

    @commands.command(name='대기전체삭제')
    async def clear_waiting_list(self, ctx):
        if ctx.channel.id != self.registration_channel_id:
            await ctx.send("이 명령어는 특정 채널에서만 사용할 수 있습니다.")
            return

        if not await self.has_allowed_role(ctx):
            await ctx.send("이 명령어를 사용할 권한이 없습니다.")
            return

        self.waiting_pool.clear()
        await ctx.send("대기 목록이 초기화되었습니다.")
        await self.show_waiting_list(ctx)

    # 대기현황 함수
    async def show_waiting_list(self, ctx):
        if not self.waiting_pool:
            await ctx.send("현재 대기 목록이 비어 있습니다.")
        else:
            waiting_list = "\n".join(f"{idx + 1}. {member.mention}" for idx, member in enumerate(self.waiting_pool))
            embed = discord.Embed(title="대기 목록 현황", description=waiting_list, color=discord.Color.blue())
            await ctx.send(embed=embed)

    # 특정 역할 확인 함수
    async def has_allowed_role(self, ctx):
        member_roles = [role.name for role in ctx.author.roles]
        for role in self.allowed_roles:
            if role in member_roles:
                return True
        return False

    @commands.command(name="드래프트")
    async def start_draft(self, ctx, team_count: str):
        if team_count not in ["1", "2"]:
            await ctx.send("팀 수는 1 또는 2만 가능합니다. 올바른 명령어 형식은 `$드래프트 1` 또는 `$드래프트 2`입니다.")
            return

        self.init_draft(ctx.channel.id, int(team_count))

        # 서버 이모지 가져오기
        st_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_ST')
        lw_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_LW')
        rw_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_RW')
        lcm_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_CM')
        rcm_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_CM')
        cdm_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_DM')
        lb_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_LB')
        lcb_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_CB')
        rcb_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_CB')
        rb_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_RB')
        gk_emoji = discord.utils.get(ctx.guild.emojis, name='ESPN_GK')

        message = await ctx.send(
            f"## {team_count}개 팀 드래프트\n"
            "### 중복으로 눌러도 처음 누른 포지션으로 진행 되니 유의 바랍니다.\n"
            "### 4-3-3 포메이션\n"
        )
        self.draft_message_ids[ctx.channel.id] = message.id
        reactions = [
            st_emoji, lw_emoji, rw_emoji, lcm_emoji, rcm_emoji, cdm_emoji, lb_emoji, lcb_emoji, rcb_emoji, rb_emoji, gk_emoji
        ]

        # 포지션 선택 이모지 추가 및 10초 카운트다운 표시
        countdown_message = await ctx.send(self.get_countdown_message(10, ctx))
        for reaction in reactions:
            await message.add_reaction(reaction)
        
        for i in range(10, 0, -1):
            await asyncio.sleep(1)
            await countdown_message.edit(content=self.get_countdown_message(i, ctx))
        await asyncio.sleep(1)
        await countdown_message.delete()

        await self.complete_draft(ctx, int(team_count))

    def init_draft(self, channel_id, team_count):
        self.positions[channel_id] = {
            "ST": [],
            "LW": [],
            "RW": [],
            "LCM": [],
            "RCM": [],
            "CDM": [],
            "LB": [],
            "RB": [],
            "LCB": [],
            "RCB": [],
            "GK": []
        }
        self.teams[channel_id] = {
            "Team 1": {
                "ST": None,
                "LW": None,
                "RW": None,
                "LCM": None,
                "RCM": None,
                "CDM": None,
                "LB": None,
                "RB": None,
                "LCB": None,
                "RCB": None,
                "GK": None
            },
            "Team 2": {
                "ST": None,
                "LW": None,
                "RW": None,
                "LCM": None,
                "RCM": None,
                "CDM": None,
                "LB": None,
                "RB": None,
                "LCB": None,
                "RCB": None,
                "GK": None
            } if team_count == 2 else {}
        }
        self.user_positions[channel_id] = {}

    def get_countdown_message(self, seconds, ctx):
        question_emoji = get(ctx.guild.emojis, name='question_mark')
        if question_emoji is None:
            question_emoji = '❓'  # Default to ❓ if custom emoji is not found

        number_emoji_map = {
            1: "1️⃣",
            2: "2️⃣",
            3: "3️⃣",
            4: "4️⃣",
            5: "5️⃣",
            6: "6️⃣",
            7: "7️⃣",
            8: "8️⃣",
            9: "9️⃣",
            10: "🔟",
        }
        return f"**카운트다운 {number_emoji_map.get(seconds, str(question_emoji))} 초 남았습니다!**"

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or reaction.message.id not in self.draft_message_ids.values():
            return

        channel_id = reaction.message.channel.id
        if user.id in self.user_positions[channel_id]:  # 사용자가 이미 포지션을 선택했는지 확인
            return

        position_map = {
            "ESPN_ST": "ST",
            "ESPN_LW": "LW",
            "ESPN_RW": "RW",
            "ESPN_CM": "LCM" if len(self.positions[channel_id]["LCM"]) <= len(self.positions[channel_id]["RCM"]) else "RCM",
            "ESPN_DM": "CDM",
            "ESPN_LB": "LB",
            "ESPN_RB": "RB",
            "ESPN_CB": "LCB" if len(self.positions[channel_id]["LCB"]) <= len(self.positions[channel_id]["RCB"]) else "RCB",
            "ESPN_GK": "GK"
        }

        position = position_map.get(reaction.emoji.name)
        if position:
            self.positions[channel_id][position].append(user)
            self.user_positions[channel_id][user.id] = position  # 사용자 포지션 저장

    async def complete_draft(self, ctx, team_count):
        channel_id = ctx.channel.id
        unselected_users = []

        for position, users in self.positions[channel_id].items():
            if position in ["LCB", "RCB"]:
                chosen_users = random.sample(users, min(2 if team_count == 2 else 1, len(users)))
                for i, chosen_user in enumerate(chosen_users):
                    team = "Team 1" if i < 1 else "Team 2"
                    self.teams[channel_id][team][position] = chosen_user
                unselected_users.extend([user for user in users if user not in chosen_users])
            else:
                if users:
                    chosen_users = random.sample(users, min(team_count, len(users)))
                    for i, chosen_user in enumerate(chosen_users):
                        team = "Team 1" if i == 0 else "Team 2"
                        self.teams[channel_id][team][position] = chosen_user
                    unselected_users.extend([user for user in users if user not in chosen_users])

        # Team 1 임베드 생성
        embed_team1 = discord.Embed(title="A팀 드래프트 결과", color=discord.Color.blue())
        embed_team1.add_field(name="포워드", value=self.get_team_field(channel_id, "Team 1", "ST", "LW", "RW"), inline=False)
        embed_team1.add_field(name="미드필더", value=self.get_team_field(channel_id, "Team 1", "LCM", "RCM", "CDM"), inline=False)
        embed_team1.add_field(name="수비수", value=self.get_team_field(channel_id, "Team 1", "LB", "LCB", "RCB", "RB"), inline=False)
        embed_team1.add_field(name="골키퍼", value=self.get_user_mention(channel_id, "Team 1", "GK"), inline=False)
        await ctx.send(embed=embed_team1)

        # Team 2 임베드 생성
        if team_count == 2:
            embed_team2 = discord.Embed(title="B팀 드래프트 결과", color=discord.Color.red())
            embed_team2.add_field(name="포워드", value=self.get_team_field(channel_id, "Team 2", "ST", "LW", "RW"), inline=False)
            embed_team2.add_field(name="미드필더", value=self.get_team_field(channel_id, "Team 2", "LCM", "RCM", "CDM"), inline=False)
            embed_team2.add_field(name="수비수", value=self.get_team_field(channel_id, "Team 2", "LB", "LCB", "RCB", "RB"), inline=False)
            embed_team2.add_field(name="골키퍼", value=self.get_user_mention(channel_id, "Team 2", "GK"), inline=False)
            await ctx.send(embed=embed_team2)

        if unselected_users:
            unselected_message = "포지션에 선택되지 않은 인원:\n"
            for user in unselected_users:
                for position, users in self.positions[channel_id].items():
                    if user in users:
                        unselected_message += f"{user.mention} - {position}\n"
            await ctx.send(unselected_message)
            await ctx.send(f'**$뽑기 [포지션]** 명령어를 사용하여 포지션 경쟁을 시작하세요.\n')

        # Reset draft state for the channel
        self.reset_draft(channel_id)

    def get_team_field(self, channel_id, team, *positions):
        return "\n".join([f"{pos} - {self.get_user_mention(channel_id, team, pos)}" for pos in positions])

    def get_user_mention(self, channel_id, team, position):
        user = self.teams[channel_id][team].get(position)
        return user.mention if user else position

    def reset_draft(self, channel_id):
        self.draft_message_ids.pop(channel_id, None)
        self.user_positions.pop(channel_id, None)
        self.positions.pop(channel_id, None)
        self.teams.pop(channel_id, None)

async def setup(bot):
    await bot.add_cog(Draft(bot))
