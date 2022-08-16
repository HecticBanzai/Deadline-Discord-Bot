import discord
from discord import option
from discord.utils import get
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import helpers
from event import *

from dotenv import load_dotenv
import os

import math

load_dotenv()

bot = discord.Bot(debug_guilds=[os.getenv("TEST_GUILD"), os.getenv("GUILD")])

event_list = {}

scheduler = AsyncIOScheduler()
scheduler.start()

def schedule_next_reminder(event):
    now = datetime.now()

    event_deadline = datetime(event.year, helpers.months_table[event.month], event.day, event.hour, event.minute, now.second, now.microsecond)

    time_difference = event_deadline - now

    difference_in_minutes = (time_difference.seconds % 3600) / 60
    difference_in_hours = math.floor(time_difference.seconds / 3600)
    difference_in_days = time_difference.days

    # print(f"hours {difference_in_hours}")
    # print(f"minutes {difference_in_minutes}")
    # print(event_deadline - now)
  
    # If the event is at least 1 day away
    if difference_in_days > 1:

        # If the event is at least 42 days away
        if difference_in_days > 42:
            padded_difference_in_days = difference_in_days - 42

            # print(f"padded difference {padded_difference_in_days}" )

            # Check if the amount of days away is a multiple of 28
            if padded_difference_in_days % 28 != 0:
                next_reminder_date = now + timedelta(days=padded_difference_in_days % 28)
            else:
                next_reminder_date = now + timedelta(days=28)
        
        # If the event is at least 42 days away
        else:
            # Check if the amount of days away is a multiple of 14
            if difference_in_days % 14 != 0:
                next_reminder_date = now + timedelta(days=difference_in_days % 14)
            else:
                next_reminder_date = now + timedelta(days=14)

            # print(f"next reminder date {next_reminder_date}")

            # Check if the last reminder is on the day of the event
            same_date = next_reminder_date.year == event_deadline.year and next_reminder_date.month == event_deadline.month and next_reminder_date.day == event_deadline.day
            if same_date:
                next_reminder_date -= timedelta(days=1)

        # if (now + timedelta(hours = difference_hours, minutes = difference_minutes)) > now and (now + timedelta(hours = difference_hours, minutes = difference_minutes)) < event_deadline:
        #     print("goes into next day")
        #     next_reminder_date += timedelta(days = 1)

        scheduler.add_job(
            remind, 
            CronTrigger(year=next_reminder_date.year, month=next_reminder_date.month, day=next_reminder_date.day, hour=event.hour, minute=event.minute),
            args=[event], 
            id=event.job_id+"-remind",
            name=event.event_name+"-remind")

    # If the event is at exactly 1 day away
    elif difference_in_days == 1:
        next_reminder_date = event_deadline - timedelta(hours = 1)

        scheduler.add_job(
            remind, 
            CronTrigger(year=next_reminder_date.year, month=next_reminder_date.month, day=next_reminder_date.day, hour=next_reminder_date.hour, minute=next_reminder_date.minute),
            args=[event], 
            id=event.job_id+"-remind",
            name=event.event_name+"-remind")

    # If it is the day of the event
    else:
        next_reminder_date = event_deadline - timedelta(minutes = 15)

        scheduler.add_job(
            remind, 
            CronTrigger(year=next_reminder_date.year, month=next_reminder_date.month, day=next_reminder_date.day, hour=next_reminder_date.hour, minute=next_reminder_date.minute),
            args=[event], 
            id=event.job_id+"-remind",
            name=event.event_name+"-remind")

    # scheduler.print_jobs()

async def notify_event_start(event):
    await bot.wait_until_ready()
    channel = bot.get_channel(event.channel.id)

    role = get(channel.guild.roles, name=event.event_name)

    embed = event.embed_for_create()

    await channel.send(f"{role.mention}", embed=embed)

    scheduler.add_job(
        delete_role, 
        CronTrigger(year=event.year, month=helpers.months_table[event.month], day=event.day, hour=event.hour, minute=event.minute+5), 
        args=[event], 
        name=event.event_name+"-delete")
    scheduler.remove_job(event.job_id+"-remind")

async def delete_role(event):
    role_to_delete = get(event.channel.guild.roles, name=event.event_name)
    await role_to_delete.delete()

async def remind(event):
    await bot.wait_until_ready()
    channel = bot.get_channel(event.channel.id)

    role = get(channel.guild.roles, name=event.event_name)

    embed = event.embed_for_remind()
    view = event.view_with_buttons()

    await channel.send(f"{role.mention}", embed=embed, view=view)
    
    schedule_next_reminder(event)

@bot.event
async def on_ready():
  print("Deadline Bot is up and running!")

@bot.slash_command()
@option("event_name", description="Enter event name")
@option("month", description="Enter month of event", choices=["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
@option("day", description="Enter day of event", min_value=1, max_value=31)
@option("year", description="Enter year of event", min_value=datetime.now().year)
@option("hour", description="Enter hour of event")
@option("minute", description="Enter minute of event", min_value=0, max_value=59)
@option("channel", description="Select which channel to be notified in")
@option("description", description="Add description or extra details", required=False)
async def deadline(
    ctx: discord.ApplicationContext,
    event_name: str,
    month: str,
    day: int,
    year: int,
    hour: int,
    minute: int,
    channel: discord.TextChannel,
    description: str
):
    if not scheduler.get_job(event_name):
        new_event = event(event_name, month, day, year, hour, minute, channel, description, event_name, [])
        event_list[event_name] = new_event

        embed = new_event.embed_for_create()
        view = new_event.view_with_buttons()
        
        scheduler.add_job(
            notify_event_start, 
            CronTrigger(year=year, month=helpers.months_table[month], day=day, hour=hour, minute=minute), 
            args=[new_event], 
            id=new_event.job_id, 
            name=new_event.job_id)

        schedule_next_reminder(new_event)

        await ctx.guild.create_role(name=event_name)
        await ctx.respond(embed=embed, view=view)
    else:
        ctx.respond("Job has been created before! Choose another name!", ephemeral=True)

@bot.slash_command()
@option("event_name", description="Select event to update")
@option("new_event_name", description="Enter new event name", required=False)
@option(
    "month", 
    description="Enter month of event", 
    choices=["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 
    required=False
)
@option("day", description="Enter day of event", min_value=1, max_value=31, required=False)
@option("year", description="Enter year of event", min_value=datetime.now().year, required=False)
@option("hour", description="Enter hour of event", required=False)
@option("minute", description="Enter minute of event", min_value=0, max_value=59, required=False)
@option("channel", description="Select which channel to be notified in", required=False)
@option("description", description="Add description or extra details", required=False)
async def update(
    ctx: discord.ApplicationContext,
    event_name: discord.Role,
    new_event_name: str,
    month: str,
    day: int,
    year: int,
    hour: int,
    minute: int,
    channel: discord.TextChannel,
    description: str
):
    if event_name.name not in event_list:
        await ctx.respond("Please select an event!", ephemeral=True)
    else:
        current_event = event_list[event_name.name]

        updated_event = current_event.update_event(
            new_event_name=new_event_name or current_event.event_name,
            month=month or current_event.month,
            day=day or current_event.day,
            year=year or current_event.year,
            hour=hour or current_event.hour,
            minute=minute or current_event.minute,
            channel=channel or current_event.channel,
            description=description or current_event.description,
            job_id=current_event.job_id
        )

        event_list.pop(event_name.name)

        event_list[updated_event.event_name] = updated_event

        scheduler.remove_job(updated_event.job_id)
        scheduler.remove_job(updated_event.job_id+"-remind")
        scheduler.add_job(
            notify_event_start, 
            CronTrigger(
                year=updated_event.year,  
                month=helpers.months_table[updated_event.month], 
                day=updated_event.day, 
                hour=updated_event.hour, 
                minute=updated_event.minute
            ),
            args=[updated_event],
            id=updated_event.job_id,
            name=updated_event.event_name)
        schedule_next_reminder(updated_event)

        await event_name.edit(name=updated_event.event_name)

        embed = updated_event.embed_for_update()
        view = updated_event.view_with_buttons()

        role = get(ctx.guild.roles, name=updated_event.event_name)

        await ctx.send(f"{role.mention}")
        await ctx.respond(embed=embed, view=view)

@bot.slash_command()
@option("event_name", description="Select which event to delete")
async def delete(ctx: discord.ApplicationContext, event_name: discord.Role):
    if event_name.name not in event_list:
        await ctx.respond("Please select an event!", ephemeral=True)
    else:
        event_to_delete = event_list.pop(event_name.name)

        scheduler.remove_job(event_to_delete.job_id)
        scheduler.remove_job(event_to_delete.job_id+"-remind")

        await event_name.delete()

        embed = event_to_delete.embed_for_delete()

        await ctx.respond(embed=embed)

bot.run(os.getenv("TOKEN"))