# Copyright (c) 2026 vanphat111 <phathovan14122006@email.com> | All rights reserved
# discordBot.py

import discord
from discord.ext import commands
from discord import app_commands
import os
import task
import database as db
from utils import log

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        log("INFO", f"Đã đồng bộ {len(synced)} slash commands.")
    except Exception as e:
        log("ERROR", f"Lỗi đồng bộ slash commands: {e}")
    log("INFO", f'Bot Discord đã đăng nhập thành công: {bot.user}')

@bot.tree.command(name="login", description="Đăng nhập tài khoản UTH")
@app_commands.describe(mssv="Mã số sinh viên", password="Mật khẩu portal")
async def login(interaction: discord.Interaction, mssv: str, password: str):
    await interaction.response.send_message("Đang gửi yêu cầu đăng nhập...", ephemeral=True)
    user_id = str(interaction.user.id)
    task.registrationTask.delay(user_id, mssv, password)

@bot.tree.command(name="logout", description="Đăng xuất và xóa toàn bộ dữ liệu tài khoản")
async def logout(interaction: discord.Interaction):
    await interaction.response.send_message("Đang xử lý đăng xuất...", ephemeral=True)
    user_id = str(interaction.user.id)
    task.logoutTask.delay(user_id)

@bot.tree.command(name="lichhoc", description="Xem lịch học theo ngày")
@app_commands.describe(date_str="Ngày cần xem (dd/mm/yyyy), mặc định là hôm nay")
async def lichhoc(interaction: discord.Interaction, date_str: str = None):
    await interaction.response.send_message("Đang tra cứu lịch học...", ephemeral=True)
    user_id = str(interaction.user.id)
    if not date_str:
        import time
        date_str = time.strftime("%d/%m/%Y")
    task.portalTask.delay(user_id, date_str)

@bot.tree.command(name="lichtuan", description="Xem lịch học theo tuần")
@app_commands.describe(start_date="Ngày trong tuần cần xem (dd/mm/yyyy), mặc định là tuần này")
async def lichtuan(interaction: discord.Interaction, start_date: str = None):
    await interaction.response.send_message("Đang tra cứu lịch tuần...", ephemeral=True)
    user_id = str(interaction.user.id)
    if not start_date:
        import time
        start_date = time.strftime("%d/%m/%Y")
    task.portalWeekTask.delay(user_id, start_date)

@bot.tree.command(name="deadline", description="Quét các bài tập chưa hoàn thành")
async def deadline(interaction: discord.Interaction):
    await interaction.response.send_message("Đang quét deadline...", ephemeral=True)
    user_id = str(interaction.user.id)
    task.deadlineTask.delay(user_id)


def run():
    bot.run(os.getenv("DISCORD_TOKEN"))
