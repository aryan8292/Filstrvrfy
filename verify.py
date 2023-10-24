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
VERIFIED = {}  # Initialize an empty dictionary to store user verification data

async def get_token(bot, userid, link):
    user = await bot.get_users(userid)
    token = await generate_random_string(7)
    TOKENS[user.id] = {token: False}
    link = f"{link}verify-{user.id}-{token}"
    shortened_verify_url = await get_shortlink(link)
    return str(shortened_verify_url)
    
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


async def verify_user(bot, userid, token, bot_username):
    user = await bot.get_users(userid)

    # Get the current time
    current_time = datetime.now()

    # Calculate the expiration time (24 hours from the current time)
    tz = pytz.timezone('Asia/Kolkata')
    verification_time = current_time.astimezone(tz)  # Make it timezone-aware
    expiration_time = verification_time + timedelta(hours=24)

    # Store the verification and expiration times in the VERIFIED dictionary along with user_id
    user_data = {
        "user_id": user.id,
        "verification_time": verification_time,
        "expiration_time": expiration_time,
        "verification_status": "ACTIVE",  # Set verification status as ACTIVE
    }
    VERIFIED[user.id] = user_data

    # Return the Telegram bot URL
    return await generate_telegram_bot_url(bot_username)

async def check_verification(bot, userid):
    user = await bot.get_users(userid)

    if user.id in VERIFIED.keys():
        user_data = VERIFIED[user.id]
        expiration_time = user_data.get("expiration_time")

        # Get the current time and make it timezone-aware
        tz = pytz.timezone('Asia/Kolkata')  # Adjust the timezone as needed
        current_time = datetime.now(tz)

        if current_time < expiration_time:
            # Update verification status as ACTIVE
            user_data["verification_status"] = "ACTIVE"
            return user_data  # Return the verification data
        else:
            # Update verification status as DEACTIVATED
            user_data["verification_status"] = "DEACTIVATED"
            return False  # Verification has expired
    else:
        return False  # User is not verified

async def generate_telegram_bot_url(bot_username):
    return f'tg://resolve?domain={bot_username}&start=verified'

if __name__ == "__main__":
    # Replace 'bot_username' with your actual bot's username
    bot_username = "@FileXTera_bot"
    print("Bot URL:", generate_telegram_bot_url(bot_username))

