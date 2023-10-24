#(©)CodeXBotz



# Import necessary modules and functions
import os
import asyncio
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from verify import *  # Import your verification-related functions here
from bot import Bot
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, VERIFY, VERIFY_EXPIRATION_HOURS, DB_URI, DB_NAME
from helper_func import subscribed, encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user, verification_collection
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient
import secrets
import hashlib
import requests

SECONDS = int(os.getenv("SECONDS", "10"))

# Define your MongoDB connection details
DB_URI = "mongodb+srv://tamecoy270:3Co7M2Ptibeh7oUQ@cluster0.a4lxwlf.mongodb.net/?retryWrites=true&w=majority"
DB_NAME = "Cluster0"
VERIFY_EXPIRATION_HOURS = 24

# Initialize the MongoClient and database
client = MongoClient(DB_URI)
db = client[DB_NAME]

# Access the 'verification' collection (replace with your collection name)
collection = db.verification

async def get_verification_token(user_id):
    # Connect to the MongoDB database
    client = MongoClient(DB_URI)
    db = client[DB_NAME]

    # Access the 'verification' collection (replace with your collection name)
    collection = db.verification

    # Find the user's verification data in the collection
    user_data = collection.find_one({"user_id": user_id})

    if user_data:
        # Check if the existing token is still valid
        current_time = datetime.now()
        expiration_time = user_data.get("expiration_time")

        if current_time <= expiration_time:
            # Return the existing token and update its expiration time
            new_expiration_time = current_time + timedelta(hours=24)
            collection.update_one(
                {"user_id": user_id},
                {"$set": {"expiration_time": new_expiration_time}},
            )
            return user_data.get("token")
        else:
            # If the token is expired, set its status to "deactivated" and generate a new one
            status_of_token = "deactivated"
    else:
        # If no valid token is found, generate a new one
        verification_token = secrets.token_hex(16)  # Generates a 32-character hexadecimal token

        # Calculate the expiration time (24 hours from now)
        new_expiration_time = datetime.now() + timedelta(hours=24)

        # Define the status of the token as "active"
        status_of_token = "active"

        # Update or insert the verification data in the collection
        collection.update_one(
            {"user_id": user_id},
            {"$set": {"token": verification_token, "expiration_time": new_expiration_time, "status_of_token": status_of_token}},
            upsert=True,  # Insert a new document if not found
        )

        return verification_token

async def get_token(client, user_id, url):
    # Your code to shorten the verification URL
    return shortened_url


# Define your shortening service API and API key
SHORTENER_API = "4e5ad4ad0887416c80a30df41097dd96004b1f19"
API_KEY = "24316517"

# Define an async function to get the shortened URL
async def get_shortened_url(long_url, shortener_api, api_key):
    try:
        # Construct the request URL with the provided API and API key
        request_url = f"{shortener_api}?api={api_key}&url={long_url}"

        # Send a GET request to the shortening service
        response = requests.get(request_url)

        if response.status_code == 200:
            # Parse the response JSON and extract the shortened URL
            data = response.json()
            shortened_url = data.get("shortenedUrl")
            return shortened_url
        else:
            return None  # Shortening failed

    except Exception as e:
        return None  # An error occurred during shortening

# Define an async function to use the get_shortened_url function
async def main():
    long_url = "https://example.com"
    shortened_url = await get_shortened_url(long_url, SHORTENER_API, API_KEY)

    if shortened_url:
        print(f"Shortened URL: {shortened_url}")
    else:
        print("URL shortening failed.")

# Run the main function if the script is executed
if __name__ == "__main__":
    import requests
    import asyncio
    asyncio.run(main())



async def is_verified_user(user_id):
    # Connect to the MongoDB database
    client = MongoClient(DB_URI)
    db = client[DB_NAME]

    # Access the 'verification' collection (replace with your collection name)
    collection = db.verification

    # Query the collection to find the verification data for the user
    verification_data = collection.find_one({"user_id": user_id, "status_of_token": "active"})

    if verification_data:
        # Check if the verification timestamp is within the 24-hour window
        current_time = datetime.now()
        verification_timestamp = verification_data.get('timestamp')

        if verification_timestamp:
            time_difference = current_time - verification_timestamp

            if time_difference < timedelta(hours=24):
                return True  # User is verified

    return False  # User is not verified

async def mark_user_as_ad_seen(user_id):
    # Connect to the MongoDB database
    client = MongoClient(DB_URI)
    db = client[DB_NAME]

    # Access the 'verification' collection (replace with your collection name)
    collection = db.verification

    # Update the user document to mark their "status_of_token" as "not active"
    collection.update_one({"user_id": user_id, "status_of_token": "active"}, {"$set": {"status_of_token": "not active"}})


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client, message):
    user_id = message.from_user.id if message.from_user else None

    # Check if the user is already verified
    if VERIFY:
        is_verified = await is_verified_user(user_id)

        if is_verified:
            # User is verified and active
            await message.reply_text("You are verified for 24 hours.")
        else:
            # Generate a verification token if not verified
            token = await get_verification_token(user_id)

            # Calculate the expiration time
            expiration_time = datetime.now() + timedelta(hours=VERIFY_EXPIRATION_HOURS)

            # Get the current date and time
            current_time = datetime.now()

            # Store the verification data in the MongoDB collection
            verification_data = {
                "user_id": user_id,
                "token": token,
                "expiration_time": expiration_time,
                "timestamp": current_time,
                "status_of_token": "active",  # Set the status as "active" initially
            }

            # Generate a message with the verification token
            text = (
                f"Welcome, {message.from_user.mention}!\n\n"
                "To access our services, please verify your identity.\n\n"
                f"Your verification token: {token}\n\n"
                f"Your verification is valid for {VERIFY_EXPIRATION_HOURS} hours."
            )

            # Create a button for verification
            verification_url = f"https://telegram.me/{client.username}?start=verify-{user_id}-{token}"
            shortened_url = await get_shortened_url(verification_url)

            button = InlineKeyboardButton(
                "Verify",
                url=shortened_url
            )

            # Create a reply markup with the verification button
            reply_markup = InlineKeyboardMarkup([[button]])

            # Send the verification message
            await message.reply_text(text, reply_markup=reply_markup)
    else:
        # Check if the user is verified based on their active status
        is_verified = await is_verified_user(user_id)

        if is_verified:
            # Redirect the user to the bot with a /start command
            await client.send_message(user_id, "/start")
            await message.reply_text("You are verified for 24 hours.")
        else:
            # User is not verified, provide the start message
            await message.reply_text(
                START_MSG,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Verify", url=f"https://telegram.me/{client.username}?start=verify")
                ]])
            )



      
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
        except:
            return
        string = await decode(base64_string)
        argument = string.split("-")

        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except:
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except:
                return

        temp_msg = await message.reply("Please wait Baby...")

        try:
            messages = await get_messages(client, ids)
        except:
            await message.reply_text("Something went wrong..!")
            return

        await temp_msg.delete()

        snt_msgs = []
        

        for msg in messages:
            if bool(CUSTOM_CAPTION) and bool(msg.document):
                caption = CUSTOM_CAPTION.format(
                    previouscaption="" if not msg.caption else msg.caption.html,
                    filename=msg.document.file_name,
                )
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(
                    chat_id=message.from_user.id,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=reply_markup,
                    protect_content=PROTECT_CONTENT,
                )
                snt_msgs.append(snt_msg)
            except:
                pass

        await asyncio.sleep(SECONDS)

        for snt_msg in snt_msgs:
            try:
                await snt_msg.delete()
            except:
                pass

    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data="about"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ]
        )

        await message.reply_text(
            text=START_MSG.format(
                first=message.from_user.first_name,
                last=message.from_user.last_name,
                username=None if not message.from_user.username else '@' + message.from_user.username,
                mention=message.from_user.mention,
                id=message.from_user.id
            ),
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            quote=True
        )
        return

    
#=====================================================================================##

WAIT_MSG = """"<b>Processing ...</b>"""

REPLY_ERROR = """<code>Use this command as a replay to any telegram message with out any spaces.</code>"""

#=====================================================================================##

    
    
@Bot.on_message(filters.command('start') & filters.private)
async def not_joined(client: Client, message: Message):
    buttons = [
        [
            InlineKeyboardButton(
                "Join Channel",
                url = client.invitelink)
        ]
    ]
    try:
        buttons.append(
            [
                InlineKeyboardButton(
                    text = 'Try Again',
                    url = f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ]
        )
    except IndexError:
        pass

    await message.reply(
        text = FORCE_MSG.format(
                first = message.from_user.first_name,
                last = message.from_user.last_name,
                username = None if not message.from_user.username else '@' + message.from_user.username,
                mention = message.from_user.mention,
                id = message.from_user.id
            ),
        reply_markup = InlineKeyboardMarkup(buttons),
        quote = True,
        disable_web_page_preview = True
    )

@Bot.on_message(filters.command('users') & filters.private & filters.user(ADMINS))
async def get_users(client: Bot, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text=WAIT_MSG)
    users = await full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")

@Bot.on_message(filters.private & filters.command('broadcast') & filters.user(ADMINS))
async def send_text(client: Bot, message: Message):
    if message.reply_to_message:
        query = await full_userbase()
        broadcast_msg = message.reply_to_message
        total = 0
        successful = 0
        blocked = 0
        deleted = 0
        unsuccessful = 0
        
        pls_wait = await message.reply("<i>Broadcasting Message.. This will Take Some Time</i>")
        for chat_id in query:
            try:
                await broadcast_msg.copy(chat_id)
                successful += 1
            except FloodWait as e:
                await asyncio.sleep(e.x)
                await broadcast_msg.copy(chat_id)
                successful += 1
            except UserIsBlocked:
                await del_user(chat_id)
                blocked += 1
            except InputUserDeactivated:
                await del_user(chat_id)
                deleted += 1
            except:
                unsuccessful += 1
                pass
            total += 1
        
        status = f"""<b><u>Broadcast Completed</u>

Total Users: <code>{total}</code>
Successful: <code>{successful}</code>
Blocked Users: <code>{blocked}</code>
Deleted Accounts: <code>{deleted}</code>
Unsuccessful: <code>{unsuccessful}</code></b>"""
        
        return await pls_wait.edit(status)

    else:
        msg = await message.reply(REPLY_ERROR)
        await asyncio.sleep(8)
        await msg.delete()
