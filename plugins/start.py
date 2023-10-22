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
from config import ADMINS, FORCE_MSG, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT
from helper_func import subscribed, encode, decode, get_messages
from database.database import add_user, del_user, full_userbase, present_user
from datetime import datetime, timedelta

SECONDS = int(os.getenv("SECONDS", "10"))

async def get_verification_token(user_id):
    # Implement your verification token generation logic
    # For example, generate a random token here
    token = "your_verification_token_logic_here"
    return token

def store_verification_data(user_id, token, expiration_time):
    # Implement how you store verification data, e.g., in a database
    # In this example, we'll print the information
    print(f"Storing data for user ID {user_id}: Token - {token}, Expiration - {expiration_time}")

@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id if message.from_user else None

    # Check if the user is already verified
    if VERIFY and not await check_verification(client, user_id):
        # Generate a verification token
        token = await get_verification_token(user_id)

        # Calculate the expiration time
        expiration_time = datetime.now() + timedelta(hours=VERIFY_EXPIRATION_HOURS)

        # Store the verification data (You can use your own storage method)
        store_verification_data(user_id, token, expiration_time)

        # Generate a message with the verification token
        text = (
            f"Welcome, {message.from_user.mention}!\n\n"
            "To access our services, please verify your identity.\n\n"
            f"Your verification token: {token}\n\n"
            f"Your verification is valid for {VERIFY_EXPIRATION_HOURS} hours."
        )

        # Create a button for verification
        button = InlineKeyboardButton(
            "Verify",
            url=await get_token(client, user_id, f"https://telegram.me/{client.username}?start=verify-{user_id}-{token}")
        )

        # Create a reply markup with the verification button
        reply_markup = InlineKeyboardMarkup([[button]])

        # Send the verification message
        await message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode="markdown"
        )
    else:
        # User is already verified or verification is disabled
        await message.reply_text(
            START_MSG,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Verify", url=f"https://telegram.me/{client.username}?start=verify")
            ]])
        )

    # You can add more logic here for handling other cases
        
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

            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html, filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup,
                                          protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
                snt_msgs.append(snt_msg)
            except FloodWait as e:
                await asyncio.sleep(e.x)
                snt_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML, reply_markup=reply_markup,
                                          protect_content=PROTECT_CONTENT)
                snt_msgs.append(snt_msg)
            except:
                pass

        await asyncio.sleep(SECONDS)

        for snt_msg in snt_msgs:
            try:
                await snt_msg.delete()
            except:
                pass

        return
    else:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("😊 About Me", callback_data="about"),
                    InlineKeyboardButton("🔒 Close", callback_data="close")
                ]
            ]
        )

        data = message.command[1]

        if data.split("-", 1)[0] == "verify":
            userid = data.split("-", 2)[1]
            token = data.split("-", 3)[2]
            if str(message.from_user.id) != str(userid):
                return
                arg = await message.reply_text(
                    text="The token you provided is invalid\n\nPlease use new token.",
                )
                await asyncio.sleep(5)
                await arg.delete()
            chck = await check_token(client, userid, token)
            if ckck == True:
                arg = await message.reply_text(
                    text="You are Verified for today,\n\nNow you can use me.",
                    protect_content=False
                )
                await verify_user(client, userid, token)
                await asyncio.sleep(20)
                await arg.delete()
            else:
                return
                arg = await message.reply_text(
                    text="Invalid token\n\nUse new token.",
                )
                await asyncio.sleep(25)
                await arg.delete()
            return

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
