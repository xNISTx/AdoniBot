from discord.ext import commands
from discord import app_commands

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio

import discord
from dotenv import load_dotenv
import os
import sqlite3

from elo_manager import update_elo, get_user, reset_all_elos

# Load token from .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Enable all intents (you need this for DMing and roles)
intents = discord.Intents.all()

# Define bot with command prefix
bot = commands.Bot(command_prefix='!', intents=intents)
tree = bot.tree

# Initialize the scheduler
scheduler = AsyncIOScheduler()

# Track unanswered users
unanswered_users = {}

# Bot active state
bot_active = True

# DAILY HABIT CHECK-IN
async def daily_habit_prompt():
    if not bot_active:
        return
    for member in bot.get_all_members():
        if not member.bot:
            try:
                await member.send(
                    "💡 **Daily Check-in:**\n"
                    "- Did you meditate today? For how long?\n"
                    "- Did you read 1 chapter? From which book?\n"
                    "- Did you do journaling (daily or gratitude)?\n"
                    "- Did you do your Adkar?\n\n"
                    "Please reply in any format before 1AM."
                )
                unanswered_users[member.id] = datetime.now()
            except discord.Forbidden:
                print(f"Couldn't DM {member.name}")

# WEEKLY WORKOUT CHECK-IN (Sundays)
async def weekly_workout_prompt():
    if not bot_active:
        return
    for member in bot.get_all_members():
        if not member.bot:
            try:
                await member.send(
                    "🏋️ **Weekly Workout Check-in:**\n"
                    "How many workouts did you do this week?\n"
                    "If none, please include your reason (sick, travel, fasting, etc)."
                )
            except discord.Forbidden:
                print(f"Couldn't DM {member.name}")

# MONTHLY GOAL CHECK-IN (Last day of month)
async def monthly_goal_prompt():
    if not bot_active:
        return
    for member in bot.get_all_members():
        if not member.bot:
            try:
                await member.send(
                    "🗓 **Monthly Goal Check-in:**\n"
                    "1. How many goals did you complete?\n"
                    "2. How many did you skip?"
                )
            except discord.Forbidden:
                print(f"Couldn't DM {member.name}")

# Check for missed responses
async def check_missed_responses():
    if not bot_active:
        return
    now = datetime.now()
    for user_id, timestamp in list(unanswered_users.items()):
        if now.hour == 1:
            update_elo(user_id, -50)
            user = await bot.fetch_user(user_id)
            try:
                await user.send("⏰ You didn’t respond in time. -50 ELO points applied.")
            except:
                pass
            del unanswered_users[user_id]

# Handle DMs for response
@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = message.author.id

    # If user responded to check-in, remove from unanswered list
    if user_id in unanswered_users:
        del unanswered_users[user_id]

    points = 0
    content = message.content.lower()

    if "meditat" in content:
        for word in content.split():
            if word.isdigit():
                mins = int(word)
                points += (mins // 10) * 3
                break
        if points == 0:
            points -= 6

    if "read" in content or "book" in content:
        user = get_user(user_id)
        today = datetime.now().date()
        last_read = user[5]
        streak = user[3]
        if last_read != str(today):
            streak += 1 if last_read == str(today - timedelta(days=1)) else 1
            base = 5 + (streak - 1)
            points += base
            conn = sqlite3.connect('adoni.db')
            c = conn.cursor()
            c.execute("UPDATE members SET streak = ?, last_read_date = ? WHERE user_id = ?", (streak, today, user_id))
            conn.commit()
            conn.close()
        else:
            points += 5

    if "gratitude" in content:
        points += 2
    if "journal" in content:
        points += 5
    if "journal" not in content and "gratitude" not in content:
        points -= 6

    adkar_count = sum(["morning" in content, "evening" in content, "sleep" in content])
    if adkar_count == 3:
        points += 10
    elif adkar_count > 0:
        points += adkar_count * 2
    else:
        points -= 3

    if points == 0:
        points = -50

    update_elo(user_id, points)
    await message.channel.send(f"✅ Noted! You earned **{points}** ELO today.")

# Slash Commands
@tree.command(name="activate", description="Activate AdoniBot (admins only)")
@app_commands.checks.has_permissions(administrator=True)
async def activate_bot(interaction: discord.Interaction):
    global bot_active
    bot_active = True
    await interaction.response.send_message("✅ AdoniBot has been activated!", ephemeral=True)

@tree.command(name="deactivate", description="Deactivate AdoniBot (admins only)")
@app_commands.checks.has_permissions(administrator=True)
async def deactivate_bot(interaction: discord.Interaction):
    global bot_active
    bot_active = False
    await interaction.response.send_message("⛔ AdoniBot has been deactivated!", ephemeral=True)

@tree.command(name="reset_stats", description="Reset all ELO stats (admins only)")
@app_commands.checks.has_permissions(administrator=True)
async def reset_stats(interaction: discord.Interaction):
    reset_all_elos()
    await interaction.response.send_message("🔄 All ELO stats have been reset!", ephemeral=True)

# When bot is ready
@bot.event
async def on_ready():
    await tree.sync()
    print(f'{bot.user.name} has logged in and is ready to flex.')

    if bot_active:
        scheduler.add_job(daily_habit_prompt, 'cron', hour=22, minute=30)
        scheduler.add_job(weekly_workout_prompt, 'cron', day_of_week='sun', hour=22, minute=30)
        scheduler.add_job(monthly_goal_prompt, 'cron', day='last', hour=22, minute=30)
        scheduler.add_job(check_missed_responses, 'cron', hour=1, minute=0)
        scheduler.start()

# Run the bot
bot.run(TOKEN)
