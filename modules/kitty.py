from telethon import events
from telegram import client

import sqlite3
import asyncio



NAME = "kitty"


DESCRIPTION = "ارسال پیام خودکار میو در گروه‌ها"



HELP = """
🐱 Kitty


کار:

ارسال خودکار پیام‌های کیتی در گروه‌های فعال.


دستورات:


کیتی اینجا

فعال کردن کیتی در گروه


کیتی حذف

حذف کیتی از گروه


"""



DB = "kitty.db"


DELAY = 310






def init_db():


    con = sqlite3.connect(DB)

    cur = con.cursor()



    cur.execute("""
    CREATE TABLE IF NOT EXISTS kitty_groups(

        chat_id INTEGER PRIMARY KEY

    )
    """)



    con.commit()

    con.close()







def add_group(chat_id):


    con = sqlite3.connect(DB)

    cur = con.cursor()



    cur.execute(

        "INSERT OR IGNORE INTO kitty_groups VALUES (?)",

        (chat_id,)

    )



    con.commit()

    con.close()







def remove_group(chat_id):


    con = sqlite3.connect(DB)

    cur = con.cursor()



    cur.execute(

        "DELETE FROM kitty_groups WHERE chat_id=?",

        (chat_id,)

    )



    con.commit()

    con.close()







def get_groups():


    con = sqlite3.connect(DB)

    cur = con.cursor()



    cur.execute(

        "SELECT chat_id FROM kitty_groups"

    )



    data = cur.fetchall()



    con.close()



    return [

        x[0]

        for x in data

    ]








async def send_kitty(chat_id):


    await client.send_message(

        chat_id,

        "میو"

    )



    await asyncio.sleep(2)



    await client.send_message(

        chat_id,

        "پیشی"

    )









async def kitty_handler(event):


    text = event.raw_text.strip()





    if text == "کیتی اینجا":



        add_group(

            event.chat_id

        )



        await event.reply(

            "🐱 کیتی فعال شد"

        )



        await send_kitty(

            event.chat_id

        )






    elif text == "کیتی حذف":



        remove_group(

            event.chat_id

        )



        await event.reply(

            "🐱 کیتی حذف شد"

        )









async def kitty_loop():


    while True:



        for chat_id in get_groups():


            try:



                await send_kitty(

                    chat_id

                )



            except Exception:


                pass





        await asyncio.sleep(

            DELAY

        )









async def start():


    init_db()



    client.add_event_handler(

        kitty_handler,

        events.NewMessage()

    )



    asyncio.create_task(

        kitty_loop()

    )



    print(

        "Kitty started"

    )