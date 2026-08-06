from telethon import events
import asyncio
import time

from telegram import client
import panel


NAME = "dong"

DESCRIPTION = "تقسیم پول بین اعضای گروه به صورت مساوی"



# ذخیره مراحل کاربران
sessions = {}



TIMEOUT = 120



@client.on(events.NewMessage)
async def dong_handler(event):


    # خاموش بودن ماژول
    if not panel.settings["modules"].get(NAME, True):
        return



    if not event.is_group:
        return



    user_id = event.sender_id

    chat_id = event.chat_id

    text = event.raw_text.strip()



    # شروع دونگ

    if text == "دونگ":


        sessions[chat_id] = {

            "owner": user_id,

            "step": "money",

            "time": time.time()

        }



        await event.reply(
            "💰 مبلغ کل را وارد کنید:"
        )


        return





    # اگر سشن وجود ندارد
    if chat_id not in sessions:
        return



    session = sessions[chat_id]



    # فقط شروع کننده

    if session["owner"] != user_id:
        return



    # حذف سشن قدیمی

    if time.time() - session["time"] > TIMEOUT:


        del sessions[chat_id]


        await event.reply(
            "❌ زمان دونگ تمام شد."
        )


        return





    session["time"] = time.time()





    # مرحله مبلغ

    if session["step"] == "money":


        if not text.isdigit():

            await event.reply(
                "❌ فقط عدد وارد کنید."
            )

            return



        session["money"] = int(text)

        session["step"] = "method"



        await event.reply(
            """
روش تقسیم را انتخاب کنید:

👥 اعضا
یا
✍️ دستی
"""
        )


        return





    # انتخاب روش

    if session["step"] == "method":



        if text == "دستی":


            session["step"] = "count"


            await event.reply(
                "👥 تعداد نفرات را وارد کنید:"
            )


            return




        elif text == "اعضا":


            members = await client.get_participants(
                chat_id
            )


            count = 0


            for user in members:

                if not user.bot:

                    count += 1



            await finish(
                event,
                session["money"],
                count
            )


            del sessions[chat_id]


            return




        else:


            await event.reply(
                "❌ فقط بنویسید: اعضا یا دستی"
            )


            return





    # تعداد دستی

    if session["step"] == "count":


        if not text.isdigit():


            await event.reply(
                "❌ تعداد باید عدد باشد."
            )

            return



        count = int(text)



        await finish(
            event,
            session["money"],
            count
        )


        del sessions[chat_id]





async def finish(event, money, count):


    if count <= 0:

        await event.reply(
            "❌ تعداد نامعتبر است."
        )

        return



    share = money // count



    await event.reply(
        f"""
💰 مبلغ کل:
{money:,}

👥 تعداد:
{count}

💵 سهم هر نفر:
{share:,} تومان
"""
    )






async def start():

    print(
        "dong started"
    )