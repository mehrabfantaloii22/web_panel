import json
import os

from telethon import events

from telegram import client


SETTINGS_FILE = "settings.json"



def load_settings():

    data = {}

    if os.path.exists(SETTINGS_FILE):

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except:

            data = {}



    if "modules" not in data:

        data["modules"] = {}



    save_file(data)

    return data





def save_file(data):

    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )





settings = load_settings()





def save_settings():

    save_file(settings)






# ثبت ماژول‌ها هنگام لود شدن

def add_module(name):


    if name not in settings["modules"]:


        settings["modules"][name] = True

        save_settings()







def module_exists(name):

    return name in settings["modules"]






def get_status(state):

    if state:

        return "🟢 فعال"

    return "🔴 خاموش"







def panel_text():


    modules = settings["modules"]


    total = len(modules)


    active = sum(
        1 for x in modules.values()
        if x
    )


    inactive = total - active



    text = f"""
╔════════════════════╗
        🧃 FANTA
   Module Control Panel
╚════════════════════╝


📦 تعداد ماژول‌ها: {total}

🟢 فعال: {active}
🔴 خاموش: {inactive}


━━━━━━━━━━━━━━━━━━

"""



    if not modules:

        text += "❌ ماژولی وجود ندارد"

    else:


        for name,state in modules.items():

            text += (
                f"{get_status(state)}  "
                f"{name}\n"
            )



    text += """

━━━━━━━━━━━━━━━━━━


⚙️ کنترل:

روشن:

نام ماژول روشن


مثال:

music روشن


خاموش:

نام ماژول خاموش


مثال:

dong خاموش



📖 راهنما:

راهنمای نام ماژول

مثال:

راهنمای music

"""


    return text







async def send_error(event,name):


    await event.reply(
        f"❌ ماژول «{name}» وجود ندارد."
    )







@client.on(events.NewMessage)
async def panel_handler(event):


    me = await client.get_me()



    if event.sender_id != me.id:

        return



    text = event.raw_text.strip()



    if text == "پنل":


        await event.reply(
            panel_text()
        )

        return






    parts = text.split()



    if len(parts) != 2:

        return




    name = parts[0]

    action = parts[1]






    if action not in [
        "روشن",
        "خاموش"
    ]:

        return






    if not module_exists(name):


        await send_error(
            event,
            name
        )

        return






    if action == "روشن":


        settings["modules"][name] = True

        save_settings()


        await event.reply(
            f"🟢 {name} روشن شد"
        )

        return






    if action == "خاموش":


        settings["modules"][name] = False

        save_settings()


        await event.reply(
            f"🔴 {name} خاموش شد"
        )

        return







@client.on(events.NewMessage)
async def list_handler(event):


    me = await client.get_me()



    if event.sender_id != me.id:

        return



    if event.raw_text.strip() != "لیست ماژول":

        return





    text = """
📦 لیست ماژول‌های FANTA


"""



    for name,state in settings["modules"].items():

        text += (
            f"{get_status(state)} "
            f"{name}\n"
        )



    await event.reply(
        text
    )








async def start():

    print(
        "Panel started"
    )