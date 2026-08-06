from telethon import events

from telegram import client



NAME = "help"

DESCRIPTION = "نمایش راهنمای ماژول‌ها"



HELP_TEXTS = {}





@client.on(events.NewMessage)
async def help_handler(event):


    me = await client.get_me()


    if event.sender_id != me.id:

        return



    text = event.raw_text.strip()



    if not text.startswith("راهنمای"):

        return




    name = text.replace(
        "راهنمای",
        ""
    ).strip()





    if name in HELP_TEXTS:


        await event.reply(
            HELP_TEXTS[name]
        )


    else:


        modules = "\n".join(
            HELP_TEXTS.keys()
        )


        await event.reply(
            f"""
❌ راهنما پیدا نشد.

📚 ماژول‌های موجود:

{modules}
"""
        )





async def start():

    print(
        "Help started"
    )