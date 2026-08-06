from telethon import events
import asyncio

from telegram import client
import panel


NAME = "hoy"

DESCRIPTION = "منشن کردن اعضای گروه با دستور هوی"



@client.on(events.NewMessage)
async def hoy_handler(event):


    # خاموش بودن ماژول
    if not panel.settings["modules"].get(NAME, True):
        return



    # فقط گروه‌ها
    if not event.is_group:
        return



    text = event.raw_text.strip()


    if text != "هوی":
        return



    print("Hoy started")



    group = await event.get_chat()



    members = await client.get_participants(
        group
    )



    message = (
        "🔔 **هوی به اعضای گروه**\n\n"
    )


    count = 0



    for user in members:


        # حذف ربات‌ها
        if user.bot:
            continue



        if user.username:

            mention = (
                f"@{user.username}"
            )


        else:

            name = (
                user.first_name
                or "User"
            )


            if user.last_name:

                name += (
                    f" {user.last_name}"
                )


            mention = (
                f"[{name}]"
                f"(tg://user?id={user.id})"
            )



        mention += "\n"



        if len(message) + len(mention) > 3500:


            await event.reply(
                message,
                parse_mode="markdown"
            )


            await asyncio.sleep(2)


            message = ""



        message += mention

        count += 1




    if message:


        message += (
            f"\n✅ تعداد منشن: {count}"
        )


        await event.reply(
            message,
            parse_mode="markdown"
        )



    print(
        "Hoy finished"
    )





async def start():

    print(
        "hoy started"
    )