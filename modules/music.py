from telethon import events
from telegram import client

import yt_dlp
import asyncio

from panel_web import append_log, record_music_archive



NAME = "music"

DESCRIPTION = "جستجو و ارسال موزیک"


HELP = """
🎵 Music


🎧 جستجو و ارسال موزیک


دستور:

پخش [نام آهنگ]


مثال:

پخش Bleed Amotti

"""


DOWNLOADER = "@scload_bot"



# جلوگیری از تداخل درخواست‌ها
music_lock = asyncio.Lock()





def search_soundcloud(query):

    try:

        options = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True
        }


        with yt_dlp.YoutubeDL(options) as ydl:

            result = ydl.extract_info(
                "scsearch1:" + query,
                download=False
            )


            if result.get("entries"):

                return result["entries"][0]["webpage_url"]


    except Exception as e:

        print(
            "SEARCH ERROR:",
            e
        )


    return None







@client.on(events.NewMessage)
async def music_handler(event):


    text = event.raw_text.strip()



    if not text.startswith("پخش "):

        return



    query = text[4:].strip()



    if not query:

        return




    async with music_lock:


        status = await event.reply(
            "🔍 پیدا کردن آهنگ..."
        )



        url = search_soundcloud(query)



        if not url:


            await status.edit(
                "❌ آهنگ پیدا نشد"
            )

            return






        await status.edit(
            "⬇️ درخواست دانلود..."
        )






        downloader = await client.get_entity(
            DOWNLOADER
        )



        received = None






        async def catcher(msg):


            nonlocal received



            if msg.sender_id != downloader.id:

                return




            print(
                "DOWNLOADER:",
                msg.raw_text,
                bool(msg.media)
            )



            if msg.media and received is None:

                received = msg







        client.add_event_handler(
            catcher,
            events.NewMessage()
        )







        await client.send_message(
            DOWNLOADER,
            url
        )







        for _ in range(120):


            if received:

                break



            await asyncio.sleep(1)







        client.remove_event_handler(
            catcher
        )






        if not received:


            await status.edit(
                "❌ موزیک دریافت نشد"
            )

            return






        await status.edit(
            "🎵 ارسال موزیک..."
        )







        try:


            await client.send_file(

                event.chat_id,

                received.media,

                caption=""

            )

            record_music_archive(query, source="telegram")
            append_log("music", "Telegram music sent to chat", {"query": query}, user="telegram")


        except Exception as e:


            print(
                "SEND ERROR:",
                e
            )


            await status.edit(
                "❌ خطا در ارسال"
            )

            return






        await status.delete()







async def start():

    print(
        "Music started"
    )