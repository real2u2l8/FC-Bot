import discord
from discord.ext import commands
import random
import asyncio

class Draft(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.draft_message_ids = {}
        self.positions = {}
        self.teams = {}
        self.user_positions = {}
        self.registration_channel_id = 1264757976997040240
        self.waiting_pool = []
        self.allowed_roles = ["매니저", ""]
        self.formations = {}  # 추가된 속성: 채널별 포메이션 저장

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

    @leave_waiting_list.error
    async def leave_waiting_list_error(self, ctx, error):
        if isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("**$대기삭제** 만 사용하세요.")

    @commands.command(name='대기삭제번호')
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

    async def show_waiting_list(self, ctx):
        if not self.waiting_pool:
            await ctx.send("현재 대기 목록이 비어 있습니다.")
        else:
            waiting_list = "\n".join(f"{idx + 1}. {member.mention}" for idx, member in enumerate(self.waiting_pool))
            embed = discord.Embed(title="대기 목록 현황", description=waiting_list, color=discord.Color.blue())
            await ctx.send(embed=embed)

    async def has_allowed_role(self, ctx):
        return any(role.name in self.allowed_roles for role in ctx.author.roles)

    @commands.command(name="드래프트")
    async def start_draft(self, ctx, team_count: str):
        if team_count not in ["1", "2"]:
            await ctx.send("팀 수는 1 또는 2만 가능합니다. 올바른 명령어 형식은 `$드래프트 1` 또는 `$드래프트 2`입니다.")
            return

        self.formations[ctx.channel.id] = ["4-3-3"] * int(team_count)
        await self.start_draft_process(ctx, int(team_count), self.formations[ctx.channel.id])

    @commands.command(name="드래프트선택")
    async def start_draft_with_selection(self, ctx):
        self.formations[ctx.channel.id] = []
        await self.select_formation(ctx, 1)

    async def select_formation(self, ctx, team_count):
        view = FormationSelectView(self, ctx, team_count)
        await ctx.send("포메이션을 선택해주세요:", view=view)

    async def start_draft_process(self, ctx, team_count, formations):
        self.init_draft(ctx.channel.id, team_count, formations)

        for i in range(1, team_count + 1):
            formation = formations[i - 1]
            message = await ctx.send(
                f"## {team_count}개 팀 드래프트 - {formation}\n"
                "### 중복으로 눌러도 처음 누른 포지션으로 진행 되니 유의 바랍니다.\n"
            )
            self.draft_message_ids[ctx.channel.id] = message.id

            for emoji_name in self.get_emojis_for_formation(formation).values():
                emoji = discord.utils.get(ctx.guild.emojis, name=emoji_name)
                await message.add_reaction(emoji)

            countdown_message = await ctx.send(self.get_countdown_message(10))
            for i in range(9, -1, -1):
                await asyncio.sleep(1)
                await countdown_message.edit(content=self.get_countdown_message(i))
            await countdown_message.delete()

        await self.complete_draft(ctx, int(team_count))

    def init_draft(self, channel_id, team_count, formations):
        self.positions[channel_id] = {f"Team {i+1}": {pos: [] for pos in self.get_positions_for_formation(formations[i])} for i in range(team_count)}
        self.teams[channel_id] = {f"Team {i+1}": {pos: None for pos in self.get_positions_for_formation(formations[i])} for i in range(team_count)}
        self.user_positions[channel_id] = {}

    def get_positions_for_formation(self, formation):
        formations = {
            "4-3-3": ["ST", "LW", "RW", "LCM", "RCM", "CDM", "LB", "LCB", "RCB", "RB", "GK"],
            "4-2-3-1": ["ST", "LW", "AM", "RW", "LCM", "RCM", "LB", "LCB", "RCB", "RB", "GK"],
            "3-4-3": ["ST", "LF", "RF", "LCM", "RCM", "LB", "RB", "LCB", "RCB", "CB", "GK"],
            "3-5-2 (CAM)": ["LF", "RF", "AM", "LCM", "RCM", "LB", "RB", "LCB", "RCB", "CB", "GK"],
            "3-5-2 (CDM)": ["LF", "RF", "LCM", "RCM", "CDM", "LB", "RB", "LCB", "RCB", "CB", "GK"],
        }
        return formations.get(formation, [])

    def get_emojis_for_formation(self, formation):
        emojis = {
            "4-3-3": {'ST': 'ESPN_ST', 'LW': 'ESPN_LW', 'RW': 'ESPN_RW', 'LCM': 'ESPN_CM', 'RCM': 'ESPN_CM', 'CDM': 'ESPN_DM', 'LB': 'ESPN_LB', 'LCB': 'ESPN_CB', 'RCB': 'ESPN_CB', 'RB': 'ESPN_RB', 'GK': 'ESPN_GK'},
            "4-2-3-1": {'ST': 'ESPN_ST', 'LW': 'ESPN_LW', 'RW': 'ESPN_RW', 'AM': 'ESPN_AM', 'LCM': 'ESPN_CM', 'RCM': 'ESPN_CM', 'LB': 'ESPN_LB', 'LCB': 'ESPN_CB', 'RCB': 'ESPN_CB', 'RB': 'ESPN_RB', 'GK': 'ESPN_GK'},
            "3-4-3": {'ST': 'ESPN_ST', 'LF': 'ESPN_LF', 'RF': 'ESPN_RF', 'LCM': 'ESPN_CM', 'RCM': 'ESPN_CM', 'LB': 'ESPN_LB', 'RB': 'ESPN_RB', 'LCB': 'ESPN_CB', 'RCB': 'ESPN_CB', 'CB': 'ESPN_CB', 'GK': 'ESPN_GK'},
            "3-5-2 (CAM)": {'LF': 'ESPN_LF', 'RF': 'ESPN_RF', 'AM': 'ESPN_AM', 'LCM': 'ESPN_CM', 'RCM': 'ESPN_CM', 'LB': 'ESPN_LB', 'RB': 'ESPN_RB', 'LCB': 'ESPN_CB', 'RCB': 'ESPN_CB', 'CB': 'ESPN_CB', 'GK': 'ESPN_GK'},
            "3-5-2 (CDM)": {'LF': 'ESPN_LF', 'RF': 'ESPN_RF', 'LCM': 'ESPN_CM', 'RCM': 'ESPN_CM', 'CDM': 'ESPN_DM', 'LB': 'ESPN_LB', 'RB': 'ESPN_RB', 'LCB': 'ESPN_CB', 'RCB': 'ESPN_CB', 'CB': 'ESPN_CB', 'GK': 'ESPN_GK'},
        }
        return emojis.get(formation, {})

    def get_countdown_message(self, seconds):
        number_emoji_map = {
            1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
            6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟",
        }
        return f"**카운트다운 {number_emoji_map.get(seconds, '❓')} 초 남았습니다!**"

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or reaction.message.id not in self.draft_message_ids.values():
            return

        channel_id = reaction.message.channel.id
        if user.id in self.user_positions[channel_id]:
            return

        position_map = {
            "ESPN_ST": "ST", "ESPN_LW": "LW", "ESPN_RW": "RW",
            "ESPN_CM": "LCM", "ESPN_DM": "CDM", "ESPN_LB": "LB", "ESPN_RB": "RB",
            "ESPN_CB": "LCB", "ESPN_GK": "GK", "ESPN_AM": "AM", "ESPN_LF": "LF", "ESPN_RF": "RF",
        }

        formation = self.formations[channel_id][0] if len(self.formations[channel_id]) == 1 else "4-3-3"
        positions = self.get_positions_for_formation(formation)
        position_map = {emoji: pos for pos, emoji in zip(positions, self.get_emojis_for_formation(formation).values())}

        position = position_map.get(reaction.emoji.name)
        if position:
            self.positions[channel_id][f"Team {1 if reaction.message.id == list(self.draft_message_ids.values())[0] else 2}"][position].append(user)
            self.user_positions[channel_id][user.id] = position

    async def complete_draft(self, ctx, team_count):
        channel_id = ctx.channel.id
        unselected_users = []

        for team in range(1, team_count + 1):
            for position, users in self.positions[channel_id][f"Team {team}"].items():
                if users:
                    chosen_users = random.sample(users, 1)
                    for chosen_user in chosen_users:
                        self.teams[channel_id][f"Team {team}"][position] = chosen_user
                    unselected_users.extend([user for user in users if user not in chosen_users])

        # Team 1 임베드 생성
        embed_team1 = discord.Embed(title="A팀 드래프트 결과", color=discord.Color.blue())
        for position in self.get_positions_for_formation(self.formations[channel_id][0]):
            embed_team1.add_field(name=position, value=self.get_user_mention(channel_id, "Team 1", position), inline=False)
        await ctx.send(embed=embed_team1)

        # Team 2 임베드 생성
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
        user = self.teams[channel_id][team].get(position)
        return user.mention if user else position

    def reset_draft(self, channel_id):
        self.draft_message_ids.pop(channel_id, None)
        self.user_positions.pop(channel_id, None)
        self.positions.pop(channel_id, None)
        self.teams.pop(channel_id, None)
        self.formations.pop(channel_id, None)

class FormationSelectView(discord.ui.View):
    def __init__(self, cog, ctx, team_count):
        super().__init__(timeout=180)
        self.cog = cog
        self.ctx = ctx
        self.team_count = team_count
        for i in range(1, team_count + 1):
            self.add_item(FormationSelect(f"Team {i} 포메이션 선택", self))

    async def on_timeout(self):
        await self.cog.reset_draft(self.ctx.channel.id)

class FormationSelect(discord.ui.Select):
    def __init__(self, placeholder, view):
        options = [
            discord.SelectOption(label="4-3-3", description="4-3-3 포메이션"),
            discord.SelectOption(label="4-2-3-1", description="4-2-3-1 포메이션"),
            discord.SelectOption(label="3-4-3", description="3-4-3 포메이션"),
            discord.SelectOption(label="3-5-2 (CAM)", description="3-5-2 (CAM) 포메이션"),
            discord.SelectOption(label="3-5-2 (CDM)", description="3-5-2 (CDM) 포메이션")
        ]
        super().__init__(placeholder=placeholder, min_values=1, max_values=1, options=options)
        self.custom_view = view

    async def callback(self, interaction: discord.Interaction):
        formation = self.values[0]
        await interaction.response.send_message(f"{formation} 포메이션이 선택되었습니다.", ephemeral=True)
        self.custom_view.cog.formations[self.custom_view.ctx.channel.id].append(formation)
        if len(self.custom_view.cog.formations[self.custom_view.ctx.channel.id]) == self.custom_view.team_count:
            await self.custom_view.cog.start_draft_process(self.custom_view.ctx, self.custom_view.team_count, self.custom_view.cog.formations[self.custom_view.ctx.channel.id])

async def setup(bot):
    await bot.add_cog(Draft(bot))
