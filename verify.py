import os
import string
import random
import pytz
from datetime import date, datetime, timedelta
import requests as re

SHORTNER = os.environ.get("SHORTENER_SITE")
API = os.environ.get("SHORTENER_API")

async def get_shortlink(link):
    res = re.get(f'https://{SHORTNER}/api?api={API}&url={link}')
    res.raise_for_status()
    data = res.json()
    return data.get('shortenedUrl')

async def generate_random_string(num: int):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(num))
    return random_string

TOKENS = {}
VERIFIED = {}

async def check_token(bot, userid, token):
    user = await bot.get_users(userid)
    if user.id in TOKENS.keys():
        TKN = TOKENS[user.id]
        if token in TKN.keys():
            is_used = TKN[token]
            if is_used:
                return False
            else:
                return True
    else:
        return False

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = await generate_random_string(7)
    TOKENS[user.id] = {token: False}
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_shortlink(link)
    return str(shortened_verify_url)

async def verify_user(bot, userid, token):
    user = await bot.get_users(userid)
    TOKENS[user.id] = {token: True}
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    VERIFIED[user.id] = str(today)

    # Update the verification timestamp to mark the user as verified for 24 hours
    expiration_time = datetime.now() + timedelta(hours=24)
    VERIFIED[user.id] = expiration_time

    return await generate_telegram_bot_url(bot_username)

async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    current_time = datetime.now()
    if user.id in VERIFIED.keys():
        expiration_time = VERIFIED[user.id]
        if current_time < expiration_time:
            return True
        else:
            return False
    else:
        return False

async def generate_telegram_bot_url(username):
    return f'tg://resolve?domain={username}&start=verified'
