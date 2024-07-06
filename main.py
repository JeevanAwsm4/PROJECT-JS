import os
import requests
import io

import discord
import google.generativeai as genai
import sqlite3

import keep_alive
from responses import get_response
import google.generativeai as genai
from discord import Message
from keep_alive import keep_alive
from discord.ext import commands


TOKEN = os.environ['TOKEN']
bot = commands.Bot(command_prefix='!',
                   intents=discord.Intents.all(),
                   case_insensitive=True)

#DATABASE SETUP
conn = sqlite3.connect('db.sqlite')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS levels (
                user_id INTEGER PRIMARY KEY,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1
            )''')
conn.commit()

#LEVELING SYSTEM SETUP
XP_PER_LEVEL = 100

#AI SETUP
my_secret = os.environ['API_KEY_GEMINI']
genai.configure(api_key=my_secret)

generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                              generation_config=generation_config,
                              safety_settings=safety_settings)
prompter = ""
prompt_parts = [prompter]

response = model.generate_content(prompt_parts)
print(f"{response.text}")

# LEVELING SYSTEM FUNCTIONS


def calculate_xp(level: int) -> int:
  return sum(range(level + 1)) * 100


def update_user_xp(user_id: int, xp: int):
  cursor.execute('''INSERT OR IGNORE INTO levels (user_id) VALUES (?)''',
                 (user_id, ))
  cursor.execute('''UPDATE levels SET xp = xp + ? WHERE user_id = ?''',
                 (xp, user_id))
  conn.commit()


def get_user_level(user_id: int) -> int:
  cursor.execute('''SELECT level FROM levels WHERE user_id = ?''', (user_id, ))
  result = cursor.fetchone()
  return result[0] if result else 1


def compute_user_level(user_id: int) -> int:
  cursor.execute('''SELECT xp FROM levels WHERE user_id = ?''', (user_id, ))
  xp = cursor.fetchone()[0]
  level = 1
  total_xp = calculate_xp(level)

  while total_xp <= xp:
    total_xp = calculate_xp(level)
    if total_xp <= xp:
      level += 1

  print(f"Level: {level}")
  print(f"Xp:{xp}")
  print(f"Next XP: {total_xp}")

  return level, xp, total_xp


def get_user_xp(user_id: int) -> int:
  cursor.execute('''SELECT xp FROM levels WHERE user_id = ?''', (user_id, ))
  result = cursor.fetchone()
  return result[0] if result else 0


async def fetch_and_send_image(ctx, inpt):
  image_url = f"https://image.pollinations.ai/prompt/{inpt}"
  response = requests.get(image_url)
  if response.status_code == 200:
    image_data = response.content
    file = discord.File(io.BytesIO(image_data), filename="image.jpg")
    await ctx.send(file=file)
  else:
    await ctx.send("Failed to MAKE IMAGE!")


#FUNCTION TO SEND MESSAGES
@bot.event
async def send_message(message: Message, user_message: str) -> None:
  if not user_message:
    print('(Message was empty because intents were not allowed)')
    return
  if is_private := user_message[0] == '?':
    user_message = user_message[1:]

# TO TEST FOR EXCEPTIONS
  try:
    response: str = get_response(user_message)
    if response == None:
      return
    else:
      await message.author.send(
          f"{response} {message.author.mention}"
      ) if is_private else await message.channel.send(
          f"{response} {message.author.mention}")

  except Exception as e:
    print(e)


#TO TEST IF BOT IT READY
@bot.event
async def on_ready() -> None:
  print("Ready to accept commands")


# MAIN FUNCTION TO SEND MESSAGES
@bot.event
async def on_message(message: Message, member: discord.Member = None):
  if message.author == bot.user:
    return
  # TO PRING MESSAGES IN OUR TERMINAL
  username: str = str(message.author)
  user_message: str = message.content
  channel: str = str(message.channel)
  print(f'[{channel}] {username} : "{user_message}")')

  # LEVELING SYSTEM PART -> OLDER CODE
  current_xp = get_user_xp(message.author.id)
  update_user_xp(message.author.id, 10)
  print(current_xp)
  level_before = get_user_level(message.author.id)
  level_after = compute_user_level(message.author.id)
  # AI PART
  if user_message.startswith('/ai'):
    prompter = user_message.replace('/ai', 'In max 1500 characters or letters').strip()
    prompt_parts = [prompter]
    response = model.generate_content(prompt_parts)
    await message.channel.send(response.text)

  # DRAWING PART
  if user_message.startswith('/beta-draw'):
    prompter = user_message.replace('/beta-draw', 'draw a').strip()
    prompt_parts = [prompter]
    response = model.generate_content(prompt_parts)
    await message.channel.send(response.text)

  #EMBED PART
  if user_message.startswith('/embed'):
    if "@" in message.content:
      name = message.mentions[0].display_name
      pfp = message.mentions[0].display_avatar
      embed = discord.Embed(title="This is a user info description",
                            description="Info about the person mentioned",
                            colour=discord.Colour.random())
      embed.set_author(
          name=f"{name}",
          url="https://www.youtube.com/watch?v=urLZoyLUDdE",
          icon_url="https://cdn-icons-png.flaticon.com/128/3135/3135715.png")
      embed.set_thumbnail(url=f"{pfp}")
      embed.add_field(name="Username", value=f"{name}", inline=True)
      embed.add_field(name="User ID",
                      value=f"{message.mentions[0].id}",
                      inline=True)
      embed.add_field(name="User Level",
                      value=f"{compute_user_level(message.mentions[0].id)}",
                      inline=False)
      embed.set_footer(text=f"{name} Made this embed")
      await message.channel.send(embed=embed)
    else:
      name = message.author.display_name
      pfp = message.author.display_avatar
      embed = discord.Embed(title="This is a user info description!",
                            description="Info about the person mentioned.",
                            colour=discord.Colour.random())
      embed.set_author(
          name=f"{name}",
          url="https://www.youtube.com/watch?v=urLZoyLUDdE",
          icon_url="https://cdn-icons-png.flaticon.com/128/3135/3135715.png")
      embed.set_thumbnail(url=f"{pfp}")
      embed.add_field(name="Username", value=f"{name}", inline=True)
      embed.add_field(name="User ID",
                      value=f"{message.author.id}",
                      inline=True)
      embed.add_field(name="User Level",
                      value=f"{compute_user_level(message.author.id)}",
                      inline=False)
      embed.set_footer(text=f"{name} Made this embed")
      await message.channel.send(embed=embed)

  # STATS PART
  if user_message.lower().startswith('/stats') and message.guild:
    await message.channel.send(
        f"Total Number of Members is {message.guild.member_count}")

  # WHISPER SYSTEM PART
  if user_message.lower().startswith('/whisper'):
    await message.delete()
    u_msg = user_message.split()
    u_msg = u_msg[2:]
    u_msg_2 = ' '.join(u_msg)
    await message.mentions[0].send(f"{message.author.mention} said - {u_msg_2}"
                                   )

  # LEVELING SYSTEM PART -> NEW CODE
  if user_message.startswith('/level'):
    member = member or message.author
    level, xp, next_level_xp = compute_user_level(member.id)
    progress = int((xp / next_level_xp) * 10)
    progress_bar = ''.join(
        [':white_large_square:' for _ in range(progress)] +
        [':black_large_square:' for _ in range(10 - progress)])

    embed = discord.Embed(title=f'Level Progress for {member.name}',
                          color=discord.Color.blue())
    embed.add_field(name='Level', value=level, inline=True)
    embed.add_field(name='XP', value=f'{xp}/{next_level_xp}', inline=True)
    embed.add_field(name='Progress', value=f'[{progress_bar}]', inline=False)
    embed.set_thumbnail(url=member.display_avatar)

    await message.channel.send(embed=embed)

  if user_message.startswith('/image'):
    inpt = user_message[len('/image'):].strip()

    await fetch_and_send_image(message.channel, inpt)

    await bot.process_commands(message)

  await send_message(message, user_message)


# THE MAIN FUNCTION
def main() -> None:
  keep_alive()
  bot.run(TOKEN)


#THE BASIC IF FUNCTION
if __name__ == '__main__':
  main()
