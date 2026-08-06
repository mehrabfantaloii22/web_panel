import asyncio
import importlib
import os
from threading import Thread

from telegram import client

import panel
from app import DashboardApp


MODULE_FOLDER = "modules"


LOADED_MODULES = {}


def start_web_dashboard():
    app = DashboardApp()
    app.run()


async def load_modules():


    tasks = []



    for file in os.listdir(MODULE_FOLDER):


        if not file.endswith(".py"):

            continue



        if file.startswith("__"):

            continue




        module_name = file[:-3]



        try:


            module = importlib.import_module(
                f"{MODULE_FOLDER}.{module_name}"
            )



            LOADED_MODULES[module_name] = module



            panel.add_module(
                module_name
            )




            if hasattr(module, "start"):


                tasks.append(
                    module.start()
                )



            print(
                f"Loaded: {module_name}"
            )



        except Exception as e:


            print(
                f"ERROR LOADING {module_name}: {e}"
            )







    # آپدیت هلپ بعد از لود همه ماژول‌ها

    if "help" in LOADED_MODULES:


        help_module = LOADED_MODULES["help"]



        help_module.HELP_TEXTS.clear()



        for name, module in LOADED_MODULES.items():


            if name == "help":

                continue



            if hasattr(module, "HELP"):


                help_module.HELP_TEXTS[name] = module.HELP



            elif hasattr(module, "DESCRIPTION"):


                help_module.HELP_TEXTS[name] = (
                    module.DESCRIPTION
                )





    if tasks:


        await asyncio.gather(
            *tasks
        )







async def main():


    print(
        "Starting web dashboard..."
    )

    web_thread = Thread(target=start_web_dashboard, daemon=True)
    web_thread.start()

    print(
        "Connecting to Telegram..."
    )

    await client.start()



    print(
        "Telegram Connected ✅"
    )



    await load_modules()



    print(
        "All modules loaded ✅"
    )



    await client.run_until_disconnected()







if __name__ == "__main__":


    asyncio.run(
        main()
    )