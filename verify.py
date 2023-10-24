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

async def verify_user(bot, userid, token, bot_username):
    user = await bot.get_users(userid)

    # Calculate the expiration time (24 hours from the current time)
    tz = pytz.timezone('Asia/Kolkata')
    expiration_time = datetime.now(tz) + timedelta(hours=24)

    # Store the verification and expiration times in the VERIFIED dictionary
    VERIFIED[user.id] = {
        "verification_time": datetime.now(tz),
        "expiration_time": expiration_time
    }

    # Return the Telegram bot URL
    return await generate_telegram_bot_url(bot_username)


async def check_verification(bot, userid):
    user = await bot.get_users(userid)
    
    # Get the timezone
    tz = pytz.timezone('Asia/Kolkata')  # Adjust the timezone as needed
    
    current_time = datetime.now(tz)  # Make current_time offset-aware

    if user.id in VERIFIED.keys():
        expiration_time = VERIFIED[user.id]

        if current_time < expiration_time:
            return True  # User is verified
        else:
            return False  # Verification has expired
    else:
        return False  # User is not verified


async def generate_telegram_bot_url(username):
    return f'tg://resolve?domain={username}&start=verified'

if __name__ == "__main__":
    # Replace 'bot_username' with your actual bot's username
    bot_username = "@FileXTera_bot"
    print("Bot URL:", generate_telegram_bot_url(bot_username))
