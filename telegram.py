from telethon import TelegramClient

from config import (
    api_id,
    api_hash,
    SESSION_NAME
)


client = TelegramClient(
    SESSION_NAME,
    api_id,
    api_hash
)