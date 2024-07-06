from random import choice, randint
from nextcord.ext import commands
import requests
import json


def get_quote():
  response = requests.get("https://zenquotes.io/api/random")
  json_data = json.loads(response.text)
  quote = json_data[0]['q']
  author = json_data[0]['a']
  f_quote = (
      (quote) +
      "\n \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t \t -By "
      + (author)
  )
  return f_quote


def get_response(user_input: str) -> str:
  lowered: str = user_input.lower()


  if lowered == 'hello':
    return 'Hello'

  if lowered == 'roll':
    return str(randint(1, 6))
  if lowered == 'help':
    return '`This is a help message that you can modify.`'
  if lowered == '/friends':
    return 'I would love to be your friend'
  if lowered == '/happy':
    return 'Good to hear that'
  if lowered == '/sad':
    return 'I am sorry to hear that'
  if lowered == '/inspire':
    return f"{get_quote()} \n is your quote"

    


# ❤️ 
