# Python script with OpenAI API
# Make sure you have your own API Key find here --> https://platform.openai.com/api-keys
# And your discord bot TOKEN find here --> https://discord.com/developers/applications/

# pip install openai
# pip install discord

import openai
import discord
from discord import Intents
import os

openai.api_key = "NO!!!!"

TOKEN = "NO NO NO NO!!!"

# Create a Discord client
intents = discord.Intents.default()
intents.message_content = True  # Ensure this intent is enabled
client = discord.Client(intents=intents)

# Event: Bot is ready and connected
@client.event
async def on_ready():
    print(f'Ms. Helpful has arrived {client.user.name}')

# Event: Bot receives a message
@client.event
async def on_message(message):
    if message.author == client.user:
        return  # Ignore messages from the bot itself

    if message.content.startswith('!ai'):
        prompt = message.content[len('!ai'):].strip()
        if not prompt:
            await message.channel.send("Please provide a prompt for MagbungkalAI.")
            return
        
        try:
            # Call OpenAI's chat completion endpoint to generate a response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150  # Adjust max tokens based on your needs
            )
            await message.channel.send(response['choices'][0]['message']['content'].strip())
        
        except Exception as e:
            await message.channel.send(f"Error occurred: {str(e)}")

# Run the bot
client.run(TOKEN)