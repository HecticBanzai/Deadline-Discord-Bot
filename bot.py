import discord
from discord import option
from discord.utils import get
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import helpers
import database
from event import *

from dotenv import load_dotenv
import os

# import math

import asyncpg

load_dotenv()

client = discord.Bot(debug_guilds=[os.getenv("TEST_GUILD")])

scheduler = AsyncIOScheduler()
scheduler.start()

event_list = {}

async def schedule_next_reminder(event):
        channel = client.get_channel(event.channel_id)
        now = datetime.now()

        event_deadline = datetime(event.year, helpers.months_table_to_int[event.month], event.day, event.hour, event.minute, now.second, now.microsecond)

        time_difference = event_deadline - now

        # difference_in_minutes = (time_difference.seconds % 3600) / 60
        # difference_in_hours = math.floor(time_difference.seconds / 3600)
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
            await database.add_deadline(
                    channel.guild.id, 
                    event.job_id+"-remind", 
                    event.event_name+"-remind",
                    next_reminder_date.year,
                    helpers.months_table_to_str[next_reminder_date.month],
                    next_reminder_date.day,
                    event.hour,
                    event.minute)

        # If the event is at exactly 1 day away
        elif difference_in_days == 1:
            next_reminder_date = event_deadline - timedelta(hours = 1)

            scheduler.add_job(
                remind, 
                CronTrigger(year=next_reminder_date.year, month=next_reminder_date.month, day=next_reminder_date.day, hour=next_reminder_date.hour, minute=next_reminder_date.minute),
                args=[event], 
                id=event.job_id+"-remind",
                name=event.event_name+"-remind")
            await database.add_deadline(
                    channel.guild.id, 
                    event.job_id+"-remind", 
                    event.event_name+"-remind",
                    next_reminder_date.year,
                    helpers.months_table_to_str[next_reminder_date.month],
                    next_reminder_date.day,
                    next_reminder_date.hour,
                    next_reminder_date.minute)

        # If it is the day of the event
        else:
            next_reminder_date = event_deadline - timedelta(minutes = 15)

            if not next_reminder_date < now:
                scheduler.add_job(
                    remind, 
                    CronTrigger(year=next_reminder_date.year, month=next_reminder_date.month, day=next_reminder_date.day, hour=next_reminder_date.hour, minute=next_reminder_date.minute),
                    args=[event], 
                    id=event.job_id+"-remind",
                    name=event.event_name+"-remind")
                await database.add_deadline(
                        channel.guild.id, 
                        event.job_id+"-remind", 
                        event.event_name+"-remind",
                        next_reminder_date.year,
                        helpers.months_table_to_str[next_reminder_date.month],
                        next_reminder_date.day,
                        next_reminder_date.hour,
                        next_reminder_date.minute)

        scheduler.print_jobs()

async def notify_event_start(event):
    await client.wait_until_ready()
    channel = client.get_channel(event.channel_id)

    role = get(channel.guild.roles, name=event.event_name)

    embed = event.embed_for_create()

    await channel.send(f"{role.mention}", embed=embed)

    event_list.pop(event.event_name)

    await database.remove_deadlines(channel.guild.id, event.job_id)

    delete_role_datetime = datetime(event.year, helpers.months_table_to_int[event.month], event.day, event.hour, event.minute) + timedelta(minutes=5)

    scheduler.add_job(
        delete_role, 
        CronTrigger(year=delete_role_datetime.year, month=delete_role_datetime.month, day=delete_role_datetime.day, hour=delete_role_datetime.hour, minute=delete_role_datetime.minute), 
        args=[event], 
        id=event.event_name+"-delete",
        name=event.event_name+"-delete")
    await database.add_deadline(
            channel.guild.id, 
            event.event_name+"-delete", 
            event.event_name+"-delete",
            delete_role_datetime.year,
            helpers.months_table_to_str[delete_role_datetime.month],
            delete_role_datetime.day,
            delete_role_datetime.hour,
            delete_role_datetime.minute)

    remind_job_exists = scheduler.get_job(event.job_id+"-remind")

    if remind_job_exists:
        scheduler.remove_job(event.job_id+"-remind")
        await database.remove_deadlines(channel.guild.id, event.job_id+"-remind")

async def delete_role(event):
    channel = client.get_channel(event.channel_id)
    role_to_delete = get(channel.guild.roles, name=event.event_name)
    await role_to_delete.delete()
    await database.remove_event_object(channel.guild.id, event.event_name)

async def remind(event):
    await client.wait_until_ready()
    channel = client.get_channel(event.channel_id)

    role = get(channel.guild.roles, name=event.event_name)

    embed = event.embed_for_remind()
    view = event.view_with_buttons()

    await channel.send(f"{role.mention}", embed=embed, view=view)

    await database.remove_deadlines(channel.guild.id, event.job_id+"-remind")
    
    await schedule_next_reminder(event)

@client.event
async def on_ready():
    for guild in client.guilds:
        con = await asyncpg.connect(os.getenv("DATABASE_URL"))

        await con.execute(f"""CREATE TABLE IF NOT EXISTS events_{guild.id} (
                event_name text PRIMARY KEY, 
                month text, 
                day integer, 
                year integer, 
                hour integer,
                minute integer,
                channel_id bigint,
                description text,
                job_id text,
                users_opted_in bigint[])""")

        await con.execute(f"""CREATE TABLE IF NOT EXISTS jobs_{guild.id} (
                job_id text, 
                job_name text, 
                year integer, 
                month text, 
                day integer, 
                hour integer,
                minute integer)""")

        event_rows = await con.fetch(f"""SELECT * FROM events_{guild.id}""")
        for row in event_rows:
            event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in = row

            event_deadline = datetime(year, helpers.months_table_to_int[month], day, hour, minute)
            delete_deadline = event_deadline + timedelta(minutes=5)

            event_date_not_passed = datetime.now() < event_deadline
            delete_time_not_passed = datetime.now() < delete_deadline

            if delete_time_not_passed or event_date_not_passed:
                event_list[event_name] = event(event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in)
            else:
                channel = client.get_channel(event.channel_id)
                guild_id = channel.guild.id

                await database.remove_event_object(guild_id, event_name)

        job_rows = await con.fetch(f"""SELECT * FROM jobs_{guild.id}""")
        for row in job_rows:
            job_id, job_name, year, month, day, hour, minute = row

            job_deadline = datetime(year, helpers.months_table_to_int[month], day, hour, minute)

            date_passed = datetime.now() > job_deadline

            if date_passed:
                await database.remove_deadlines(guild.id, job_id)
            else:
                if job_id.endswith("-remind"):
                    scheduler.add_job(
                            remind, 
                            CronTrigger(year=year, month=helpers.months_table_to_int[month], day=day, hour=hour, minute=minute),
                            args=[event_list[job_name.removesuffix("-remind")]], 
                            id=job_id,
                            name=job_name)
                elif job_id.endswith("-delete"):
                    scheduler.add_job(
                            delete_role, 
                            CronTrigger(year=year, month=helpers.months_table_to_int[month], day=day, hour=hour, minute=minute), 
                            args=[event_list[job_name.removesuffix("-delete")]], 
                            id=job_id,
                            name=job_name)
                else:
                    scheduler.add_job(
                            notify_event_start, 
                            CronTrigger(year=year, month=helpers.months_table_to_int[month], day=day, hour=hour, minute=minute), 
                            args=[event_list[job_name]], 
                            id=job_id, 
                            name=job_name)

        scheduler.print_jobs()

        await con.close()

    print("Deadline Bot is up and running!")
    print("-------------------------------")

@client.event
async def on_guild_join(guild):
    con = await asyncpg.connect(os.getenv("DATABASE_URL"))

    await con.execute(f"""CREATE TABLE IF NOT EXISTS events_{guild.id} (
            event_name text PRIMARY KEY, 
            month text, 
            day integer, 
            year integer, 
            hour integer,
            minute integer,
            channel_id bigint,
            description text,
            job_id text,
            users_opted_in bigint[])""")

    await con.execute(f"""CREATE TABLE IF NOT EXISTS jobs_{guild.id} (
            job_id text, 
            job_name text, 
            year integer, 
            month text, 
            day integer, 
            hour integer,
            minute integer)""")

    await con.close()

@client.slash_command(description="Create an event deadline")
@option("event_name", description="Enter event name")
@option("month", description="Enter month of event", choices=["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
@option("day", description="Enter day of event", min_value=1, max_value=31)
@option("year", description="Enter year of event", min_value=datetime.now().year)
@option("hour", description="Enter hour of event", min_value=0, max_value=23)
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
    if day > helpers.days_in_month[month]:
        await ctx.respond("Please enter a viable date!", ephemeral=True)
    else:
        event_deadline = datetime(year, helpers.months_table_to_int[month], day, hour, minute)

        job_not_created = not scheduler.get_job(event_name)
        date_not_passed = datetime.now() < event_deadline

        if job_not_created and date_not_passed:
            new_event = event(event_name, month, day, year, hour, minute, channel.id, description, event_name, [])
            event_list[event_name] = new_event
            await database.add_event_object(ctx.guild.id, event_name, month, day, year, hour, minute, channel.id, description, event_name, [])

            embed = new_event.embed_for_create()
            view = new_event.view_with_buttons()
            
            scheduler.add_job(
                notify_event_start, 
                CronTrigger(year=year, month=helpers.months_table_to_int[month], day=day, hour=hour, minute=minute), 
                args=[new_event], 
                id=new_event.job_id, 
                name=new_event.job_id)
            await database.add_deadline(
                    channel.guild.id, 
                    new_event.job_id, 
                    new_event.job_id,
                    year,
                    month,
                    day,
                    hour,
                    minute)

            await schedule_next_reminder(new_event)

            await ctx.guild.create_role(name=event_name)
            await ctx.respond(embed=embed, view=view)
        else:
            await ctx.respond("Could not create deadline! Maybe the event name has been taken or the date/time has already passed.", ephemeral=True)

@client.slash_command(description="Update selected event deadline")
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
@option("hour", description="Enter hour of event", min_value=0, max_value=23, required=False)
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
    if day > helpers.days_in_month[month]:
        await ctx.respond("Please enter a viable date!", ephemeral=True)
    else:
        event_deadline = datetime(year, helpers.months_table_to_int[month], day, hour, minute)

        event_doesnt_exist = event_name.name not in event_list
        date_already_passed = event_deadline < datetime.now()

        if event_doesnt_exist:
            await ctx.respond("Please select an event!", ephemeral=True)
        elif date_already_passed:
            await ctx.respond("This date/time has already passed!", ephemeral=True)
        else:
            current_event = event_list[event_name.name]

            updated_event = current_event.update_event(
                new_event_name=new_event_name or current_event.event_name,
                month=month or current_event.month,
                day=day or current_event.day,
                year=year or current_event.year,
                hour=hour or current_event.hour,
                minute=minute or current_event.minute,
                channel_id=channel.id or current_event.channel_id,
                description=description or current_event.description,
                job_id=current_event.job_id
            )

            event_to_remove = event_list.pop(event_name.name)
            await database.remove_event_object(ctx.guild.id, event_to_remove.event_name)

            event_list[updated_event.event_name] = updated_event
            await database.add_event_object(
                    ctx.guild.id, 
                    updated_event.event_name, 
                    updated_event.month, 
                    updated_event.day, 
                    updated_event.year, 
                    updated_event.hour, 
                    updated_event.minute, 
                    updated_event.channel_id, 
                    updated_event.description, 
                    updated_event.job_id, 
                    updated_event.users_opted_in)

            scheduler.remove_job(updated_event.job_id)
            await database.remove_deadlines(ctx.guild.id, updated_event.job_id)

            scheduler.remove_job(updated_event.job_id+"-remind")
            scheduler.add_job(
                notify_event_start, 
                CronTrigger(
                    year=updated_event.year,  
                    month=helpers.months_table_to_int[updated_event.month], 
                    day=updated_event.day, 
                    hour=updated_event.hour, 
                    minute=updated_event.minute
                ),
                args=[updated_event],
                id=updated_event.job_id,
                name=updated_event.event_name)
            await database.remove_deadlines(ctx.guild.id, updated_event.job_id+"-remind")

            await schedule_next_reminder(updated_event)

            await event_name.edit(name=updated_event.event_name)

            embed = updated_event.embed_for_update()
            view = updated_event.view_with_buttons()

            role = get(ctx.guild.roles, name=updated_event.event_name)

            await ctx.send(f"{role.mention}")
            await ctx.respond(embed=embed, view=view)

@client.slash_command(description="Delete selected event deadline")
@option("event_name", description="Select which event to delete")
async def delete(ctx: discord.ApplicationContext, event_name: discord.Role):
    event_doesnt_exist = event_name.name not in event_list

    if event_doesnt_exist:
        await ctx.respond("Please select an event!", ephemeral=True)
    else:
        event_to_delete = event_list.pop(event_name.name)
        await database.remove_event_object(ctx.guild.id, event_name.name)

        scheduler.remove_job(event_to_delete.job_id)
        await database.remove_deadlines(ctx.guild.id, event_to_delete.job_id)

        scheduler.remove_job(event_to_delete.job_id+"-remind")
        await database.remove_deadlines(ctx.guild.id, event_to_delete.job_id+"-remind")

        await event_name.delete()

        embed = event_to_delete.embed_for_delete()

        await ctx.respond(embed=embed)

@client.slash_command(name="opt-in", description="Opt out of reminders for an event deadline")
@option("event_name", description="Select event to get reminders for")
async def opt_in(ctx: discord.ApplicationContext, event_name: discord.Role):
    member = ctx.user

    event = event_list[event_name.name]

    member_hasnt_opted_in = member.id not in event.users_opted_in
    
    if member_hasnt_opted_in:
        event.users_opted_in.append(member.id)
        await database.update_attendance_list(ctx.guild.id, event.users_opted_in, event.event_name)

        await member.add_roles(event_name)
        await ctx.respond(f"You will now recieve reminders for **{event.event_name}**!", ephemeral=True)
    else:
        await ctx.respond(f"Cannot send you notifications for **{event.event_name}**! Maybe the event was updated?", ephemeral=True)

@client.slash_command(name="opt-out", description="Opt out of reminders for an event deadline")
@option("event_name", description="Select event to get reminders for")
async def opt_out(ctx: discord.ApplicationContext, event_name: discord.Role):
    member = ctx.user

    event = event_list[event_name.name]

    member_has_opted_in = member.id in event.users_opted_in
    
    if member_has_opted_in:
        event.users_opted_in.remove(member.id)
        await database.update_attendance_list(ctx.guild.id, event.users_opted_in, event.event_name)

        await member.remove_roles(event_name)
        await ctx.respond(f"You will no longer recieve reminders for **{event.event_name}**!", ephemeral=True)
    else:
        await ctx.respond(f"Cannot opt you out of notifications for **{event.event_name}**! Maybe the event was updated?", ephemeral=True)

@client.slash_command(name="get-attendance", description="See who is recieving reminders for this deadline")
@option("event_name", description="Select event to see attendance of")
async def get_attendance(ctx: discord.ApplicationCommand, event_name: discord.Role):
    event_doesnt_exist = event_name.name not in event_list

    if event_doesnt_exist:
        await ctx.respond("Please select an event!", ephemeral=True)
    else:
        event = event_list[event_name.name]
        
        if len(event.users_opted_in) == 0:
            embed = discord.Embed(title=f"{event.event_name}", color=0xad6fa)
            embed.add_field(name="Attendance List", value="No one is attending!", inline=False)

            await ctx.respond(embed=embed)
        else:
            memberlist = []

            for member_id in event.users_opted_in:
                member = ctx.guild.get_member(member_id)

                memberlist.append(f"{member.display_name}#{member.discriminator}")

            embed = discord.Embed(title=f"{event.event_name}", color=0xad6fa)
            embed.add_field(name="Attendance List", value='\n'.join(memberlist), inline=False)

            await ctx.respond(embed=embed)

@client.slash_command(name="get-events", description="See a list of all created events")
async def get_events(ctx: discord.ApplicationCommand):
    pass

client.run(os.getenv("TOKEN"))