import asyncio
from datetime import datetime

def __main__(*args):
    deadlinePlugin = args[0]
    job = deadlinePlugin.GetJob()

    # get datetime
        # schedule date convert to datetime object
    schedule_date = job.JobScheduledStartDateTime
    schedule_str = str(schedule_date)
    schedule_object = datetime.strptime(schedule_str, "%m/%d/%Y %H:%M:%S")

    current_date = datetime.now()

    # compare hours
    delta = (schedule_object - current_date)
    delta_sec = int(delta.total_seconds())

    # wait difference if positive
    if(delta_sec > 0):
        print(f"We will be waiting for {delta_sec} seconds.")
        print("waiting...")
        asyncio.run(wait(delta_sec))

    print("Render can start now.")


async def wait(dl):
    await asyncio.sleep(dl)