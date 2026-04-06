import logging
import os
import time
import asyncio
from typing import Union, Optional, AsyncGenerator

# Logging setup
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logging.getLogger('pyrogram').setLevel(logging.ERROR)
logger = logging.getLogger(__name__)

try:
    import uvloop
    ul = True
except ImportError:
    ul = False

from pyrogram import types, Client, StopPropagation
from pyrogram.handlers import MessageHandler
from pyrogram.errors import FloodWait
from aiohttp import web

# App imports
from web import web_app
from info import (
    URL, INDEX_CHANNELS, SUPPORT_GROUP, LOG_CHANNEL, API_ID, 
    DATA_DATABASE_URL, API_HASH, BOT_TOKEN, PORT, BIN_CHANNEL, 
    ADMINS, SECOND_FILES_DATABASE_URL, FILES_DATABASE_URL
)
from utils import temp, get_readable_time, check_premium
from database.users_chats_db import db

if ul:
    uvloop.install()

class Bot(Client):
    def __init__(self):
        super().__init__(
            name='Auto_Filter_Bot',
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"},
            sleep_threshold=60 # Auto-handle short floodwaits (up to 60s)
        )
        self.listeners = {}
        self.add_handler(MessageHandler(self._listener_handler), group=-1)

    async def _listener_handler(self, client: Client, message: types.Message):
        if not message.chat or not message.from_user:
            return

        listener_id = (message.chat.id, message.from_user.id)
        if listener_id in self.listeners:
            future = self.listeners[listener_id]
            if not future.done():
                future.set_result(message)
            raise StopPropagation

    async def listen(self, chat_id: int, user_id: int, timeout: int = 60) -> Optional[types.Message]:
        future = asyncio.get_event_loop().create_future()
        listener_id = (chat_id, user_id)

        if listener_id in self.listeners:
            old_future = self.listeners[listener_id]
            if not old_future.done():
                old_future.cancel()

        self.listeners[listener_id] = future

        try:
            message = await asyncio.wait_for(future, timeout)
            return message
        except asyncio.TimeoutError:
            return None
        finally:
            self.listeners.pop(listener_id, None)

    async def start(self, **kwargs):
        await super().start()
        temp.START_TIME = time.time()
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        if os.path.exists('restart.txt'):
            with open("restart.txt") as file:
                try:
                    line = file.read().strip()
                    if line:
                        chat_id, msg_id = map(int, line.split())
                        await self.edit_message_text(chat_id=chat_id, message_id=msg_id, text='Restarted Successfully!')
                except Exception as e:
                    logger.error(f"Restart file error: {e}")
            os.remove('restart.txt')

        temp.BOT = self
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name

        app = web.AppRunner(web_app)
        await app.setup()
        await web.TCPSite(app, "0.0.0.0", PORT).start()

        asyncio.create_task(check_premium(self))
        try:
            await self.send_message(chat_id=LOG_CHANNEL, text=f"<b>{me.mention} Restarted! 🤖</b>")
        except Exception as e:
            logger.error(f"Error sending to LOG_CHANNEL: {e}. Make sure bot is admin.")
            # exit() # Optional: remove exit if you want bot to run anyway

        logger.info(f"@{me.username} is started now ✓\nWebapp started at [{URL}]")

    async def stop(self, **kwargs):
        await super().stop()
        logger.info("Bot Stopped! Bye...")

    async def iter_messages(self, chat_id: Union[int, str], limit: int, offset: int = 0) -> Optional[AsyncGenerator[types.Message, None]]:
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            
            try:
                messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            except FloodWait as e:
                logger.warning(f"FloodWait: Sleeping for {e.value} seconds...")
                await asyncio.sleep(e.value)
                continue # Sleep ke baad wapas koshish karega
            except Exception as e:
                logger.error(f"Error in iter_messages: {e}")
                return

            for message in messages:
                yield message
                current += 1

app = Bot()
app.run()
