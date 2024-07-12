import discord
from discord.ext import commands
import json

# Load token from a separate file or replace 'YOUR_BOT_TOKEN' with your bot's token directly
with open("config.json", "r") as config_file:
    config = json.load(config_file)
TOKEN = config['TOKEN']

intents = discord.Intents.default()
intents.members = True
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Dictionary to store user data (in memory for simplicity)
user_data = {}

# XP and leveling settings
XP_PER_MESSAGE = 10
LEVELS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
    11: "XI", 12: "XII", 13: "XIII", 14: "XIV", 15: "XV",
    16: "XVI", 17: "XVII", 18: "XVIII", 19: "XIX", 20: "XX"
}

def get_next_level_xp(level):
    return level * 100

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id not in user_data:
        user_data[user_id] = {'xp': 0, 'level': 1}

    user_data[user_id]['xp'] += XP_PER_MESSAGE
    current_level = user_data[user_id]['level']
    next_level_xp = get_next_level_xp(current_level)

    if user_data[user_id]['xp'] >= next_level_xp:
        user_data[user_id]['level'] += 1
        new_level = user_data[user_id]['level']
        await message.channel.send(f'Congratulations {message.author.mention}, you have reached level {LEVELS[new_level]}!')
        await assign_role(message.author, LEVELS[new_level])

    await bot.process_commands(message)

async def assign_role(member, level_name):
    guild = member.guild
    role = discord.utils.get(guild.roles, name=f"Level {level_name}")
    if role:
        await remove_level_roles(member)
        await member.add_roles(role)

async def remove_level_roles(member):
    for role in member.roles:
        if role.name.startswith("Level "):
            await member.remove_roles(role)

@bot.command(name='level')
async def check_level(ctx):
    user_id = str(ctx.author.id)
    if user_id in user_data:
        xp = user_data[user_id]['xp']
        level = user_data[user_id]['level']
        await ctx.send(f'{ctx.author.mention}, you are currently level {LEVELS[level]} with {xp} XP.')
    else:
        await ctx.send(f'{ctx.author.mention}, you have no XP yet.')

bot.run(TOKEN)
