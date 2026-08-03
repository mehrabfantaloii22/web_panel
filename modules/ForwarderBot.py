from telethon import events
import re
import emoji

from telegram import client
import panel


NAME = "ForwarderBot"

DESCRIPTION = "فوروارد خودکار سیگنال‌ها از کانال مبدا به مقصد"



sources = [
    "Goldtradingmasterg",
]


destination = "Goldiran916"



keywords = [
    "XAUUSD",
    "TP",
    "READY",
    "BUY",
    "SELL",
    "STOP",
]


hit_keywords = [
    "HIT",
    "TP HIT",
    "TP1 HIT",
    "TP2 HIT",
    "TP3 HIT",
    "TP4 HIT",
    "TP5 HIT",
    "SL HIT",
    "STOP HIT",
    "BREAKEVEN",
    "BREAK EVEN",
    "BE",
]


ignore_words = [
    "@Zaman_fx01",
]



last_signals = []





@client.on(events.NewMessage(chats=sources))
async def forward_handler(event):


    # خاموش بودن ماژول
    if not panel.settings["modules"].get(NAME, True):
        return



    text = event.message.message or ""



    text = re.sub(
        r"Money management",
        "",
        text,
        flags=re.IGNORECASE
    )



    text = emoji.replace_emoji(
        text,
        replace=""
    )



    text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )



    if not text:
        return



    if any(
        word.lower() in text.lower()
        for word in ignore_words
    ):
        return



    is_hit = any(
        word.lower() in text.lower()
        for word in hit_keywords
    )



    if is_hit:


        if last_signals:

            await client.send_message(
                destination,
                text,
                reply_to=last_signals[-1]
            )

        else:

            await client.send_message(
                destination,
                text
            )


        return




    if not any(
        key.lower() in text.lower()
        for key in keywords
    ):
        return




    if event.message.media:


        sent = await client.send_file(
            destination,
            event.message.media,
            caption=text
        )


    else:


        sent = await client.send_message(
            destination,
            text
        )



    last_signals.append(
        sent.id
    )



    if len(last_signals) > 20:

        last_signals.pop(0)



    print(
        "Forwarded:",
        text[:40]
    )





async def start():

    print(
        "ForwarderBot started"
    )