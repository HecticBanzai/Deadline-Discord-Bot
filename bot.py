import discord
from discord import option
from discord.utils import get, utcnow

from datetime import datetime, timedelta

import pytz

import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import helpers
import schedulerhelpers
import databasehelpers
from event import *

from dotenv import load_dotenv
import os

import asyncpg

load_dotenv()

client = discord.Bot(debug_guilds=[os.getenv("TEST_GUILD"), os.getenv("GUILD")])

guild_list = {}

async def delete_role_and_event(event):
    channel = event.send_to_channel

    role_to_delete = get(channel.guild.roles, name=event.event_name)

    await role_to_delete.delete()
    await databasehelpers.remove_event_object(channel.guild.id, event.event_name)

@client.event
async def on_ready():
    for guild in client.guilds:
        event_list = {}

        scheduler = AsyncIOScheduler()
        scheduler.start()

        con = await asyncpg.connect(os.getenv("DATABASE_URL"))

        await con.execute(f"""CREATE TABLE IF NOT EXISTS events_{guild.id} (event_name text PRIMARY KEY, 
                                                                            event_deadline_str text,
                                                                            send_to_channel_id bigint,
                                                                            description text,
                                                                            job_id text,
                                                                            users_opted_in bigint[])""")

        event_rows = await con.fetch(f"""SELECT * FROM events_{guild.id}""")
        
        for row in event_rows:
            event_name, event_deadline_str, send_to_channel_id, description, job_id, users_opted_in = row

            event_deadline = datetime.fromisoformat(event_deadline_str)
            send_to_channel = client.get_channel(send_to_channel_id)

            delete_date = event_deadline + timedelta(days=1)

            event_date_not_passed = utcnow() < event_deadline.astimezone(pytz.utc)
            delete_date_not_passed = utcnow() < delete_date.astimezone(pytz.utc)

            if delete_date_not_passed:
                created_event = event(event_name, event_deadline, send_to_channel, description, job_id, users_opted_in)

                event_list[event_name] = created_event

                scheduler.add_job(
                    delete_role_and_event, 
                    trigger=CronTrigger(
                        year=delete_date.astimezone(pytz.utc).year,
                        month=delete_date.astimezone(pytz.utc).month,
                        day=delete_date.astimezone(pytz.utc).day,
                        hour=delete_date.astimezone(pytz.utc).hour,
                        minute=delete_date.astimezone(pytz.utc).minute), 
                    args=[event_list[event_name]], 
                    id=job_id+"-delete", 
                    name=event_name+"-delete")

                if event_date_not_passed:
                    scheduler.add_job(
                        created_event.announce_start, 
                        trigger=CronTrigger(
                            year=event_deadline.astimezone(pytz.utc).year,
                            month=event_deadline.astimezone(pytz.utc).month,
                            day=event_deadline.astimezone(pytz.utc).day,
                            hour=event_deadline.astimezone(pytz.utc).hour,
                            minute=event_deadline.astimezone(pytz.utc).minute),  
                        id=job_id, 
                        name=event_name)

                    if utcnow() < created_event.remind_date:
                        scheduler.add_job(
                            created_event.announce_reminder, 
                            trigger=CronTrigger(
                                year=created_event.remind_date.astimezone(pytz.utc).year,
                                month=created_event.remind_date.astimezone(pytz.utc).month,
                                day=created_event.remind_date.astimezone(pytz.utc).day,
                                hour=created_event.remind_date.astimezone(pytz.utc).hour,
                                minute=created_event.remind_date.astimezone(pytz.utc).minute), 
                            id=job_id+"-remind",
                            name=event_name+"-remind")

            else:
                await databasehelpers.remove_event_object(guild.id, event_name)

        scheduler.print_jobs()

        guild_list[guild.id] = {
            "event list": event_list,
            "scheduler": scheduler
        }

        await con.close()

    print("Deadline Bot is up and running!")
    print("-------------------------------")

@client.event
async def on_guild_join(guild):
    con = await asyncpg.connect(os.getenv("DATABASE_URL"))

    await con.execute(f"""CREATE TABLE IF NOT EXISTS events_{guild.id} (event_name text PRIMARY KEY, 
                                                                            event_deadline_str text,
                                                                            send_to_channel_id bigint,
                                                                            description text,
                                                                            job_id text,
                                                                            users_opted_in bigint[])""")

    await con.close()

    event_list = {}

    scheduler = AsyncIOScheduler()
    scheduler.start()

    guild_list[guild.id] = {
        "event list": event_list,
        "scheduler": scheduler
    }

@client.slash_command(description="Create an event deadline")
@option("event_name", description="Enter event name")
@option("month", description="Enter month of event", choices=["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"])
@option("day", description="Enter day of event", min_value=1, max_value=31)
@option("year", description="Enter year of event", min_value=utcnow().year)
@option("hour", description="Enter hour of event", min_value=0, max_value=23)
@option("minute", description="Enter minute of event", min_value=0, max_value=59)
@option("timezone", description="Enter your timezone", choices=["Hawaii", "Aleutian", "Alaska", "Pacific", "Mountain", "Central", "Eastern"])
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
    timezone: str,
    channel: discord.TextChannel,
    description: str
):
    if day > helpers.days_in_month[month]:
        await ctx.respond("Please enter a viable date!", ephemeral=True)
        
    else:
        event_deadline_naive = datetime(year, helpers.months_table_to_int[month], day, hour, minute)
        event_deadline_aware = pytz.timezone(helpers.tzname_to_localize[timezone]).localize(event_deadline_naive)

        event_list = guild_list[ctx.guild.id]["event list"]
        scheduler = guild_list[ctx.guild.id]["scheduler"]

        job_created_before = scheduler.get_job(event_name)

        date_passed = utcnow() > event_deadline_aware.astimezone(pytz.utc)

        if job_created_before:
            await ctx.respond("Could not create deadline! The event name has been taken.", ephemeral=True)
        
        elif date_passed:
            await ctx.respond("Could not create deadline! Maybe the date/time has already passed.", ephemeral=True)
        
        else:
            new_event = event(event_name, event_deadline_aware, channel, description, event_name, [])
            event_list[event_name] = new_event

            await databasehelpers.add_event_object(ctx.guild.id, new_event)
            
            schedulerhelpers.add_event_jobs(scheduler, new_event)

            await ctx.guild.create_role(name=event_name)

            await new_event.announce_create()

            await ctx.respond("Event Successfully Created!")

@client.slash_command(description="Update selected event deadline")
@option("event_name", description="Select event to update")
@option("timezone", description="Enter your timezone", choices=["Hawaii", "Aleutian", "Alaska", "Pacific", "Mountain", "Central", "Eastern"])
@option("new_event_name", description="Enter new event name", required=False)
@option(
    "month", 
    description="Enter month of event", 
    choices=["January", "Feburary", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 
    required=False
)
@option("day", description="Enter day of event", min_value=1, max_value=31, required=False)
@option("year", description="Enter year of event", min_value=utcnow().year, required=False)
@option("hour", description="Enter hour of event", min_value=0, max_value=23, required=False)
@option("minute", description="Enter minute of event", min_value=0, max_value=59, required=False)
@option("channel", description="Select which channel to be notified in", required=False)
@option("description", description="Add description or extra details", required=False)
async def update(
    ctx: discord.ApplicationContext,
    event_name: discord.Role,
    timezone: str,
    new_event_name: str,
    month: str,
    day: int,
    year: int,
    hour: int,
    minute: int,
    channel: discord.TextChannel,
    description: str,
):
    event_list = guild_list[ctx.guild.id]["event list"]
    scheduler = guild_list[ctx.guild.id]["scheduler"]

    event_doesnt_exist = event_name.name not in event_list

    if event_doesnt_exist:
        await ctx.respond("Please select an event!", ephemeral=True)

    elif event_list[event_name.name].event_deadline.astimezone(pytz.utc) < utcnow():
        await ctx.respond("Cannot update this event! The event's deadline has already passed.", ephemeral=True)

    else:
        selected_event_deadline = event_list[event_name.name].event_deadline

        if day != None:
            if day > helpers.days_in_month[month]:
                await ctx.respond("Please enter a viable date!", ephemeral=True)

                return

        event_deadline_naive = datetime(
            year or selected_event_deadline.year, 
            helpers.months_table_to_int[month] or selected_event_deadline.month, 
            day or selected_event_deadline.day, 
            hour or selected_event_deadline.hour, 
            minute or selected_event_deadline.minute)
        event_deadline_aware = pytz.timezone(helpers.tzname_to_localize[timezone]).localize(event_deadline_naive)

        date_already_passed = event_deadline_aware.astimezone(pytz.utc) < utcnow()

        if date_already_passed:
            await ctx.respond("This date/time has already passed!", ephemeral=True)

            return

        event_to_update_delete = event_list.pop(event_name.name)

        new_event_deadline = event_deadline_aware

        new_send_to_channel = channel or event_to_update_delete.send_to_channel

        new_description = description or event_to_update_delete.description

        updated_event = event_to_update_delete.update_event(
            new_event_name=new_event_name or event_to_update_delete.event_name,
            new_event_deadline=new_event_deadline,
            new_send_to_channel=new_send_to_channel,
            new_description=new_description
        )

        await databasehelpers.remove_event_object(ctx.guild.id, event_to_update_delete.event_name)

        event_list[updated_event.event_name] = updated_event

        await databasehelpers.add_event_object(ctx.guild.id, updated_event)

        schedulerhelpers.delete_event_jobs(scheduler, event_to_update_delete)

        schedulerhelpers.add_event_jobs(scheduler, updated_event)

        await event_name.edit(name=updated_event.event_name)

        await updated_event.announce_update()

        await ctx.respond("Event Successfully Updated!")

@client.slash_command(description="Delete selected event deadline")
@option("event_name", description="Select which event to delete")
async def delete(ctx: discord.ApplicationContext, event_name: discord.Role):
    event_list = guild_list[ctx.guild.id]["event list"]
    scheduler = guild_list[ctx.guild.id]["scheduler"]

    event_doesnt_exist = event_name.name not in event_list.keys()

    if event_doesnt_exist:
        await ctx.respond("Please select an event!", ephemeral=True)

    else:
        event_to_delete = event_list.pop(event_name.name)
        await databasehelpers.remove_event_object(ctx.guild.id, event_to_delete.event_name)

        schedulerhelpers.delete_event_jobs(scheduler, event_to_delete)

        await event_to_delete.announce_delete()

        await event_name.delete()

        await ctx.respond("Event Successfully Deleted!")

@client.slash_command(name="opt-in", description="Opt out of reminders for an event deadline")
@option("event_name", description="Select event to get reminders for")
async def opt_in(ctx: discord.ApplicationContext, event_name: discord.Role):
    event_list = guild_list[ctx.guild.id]["event list"]

    event_exists = event_name.name in event_list

    if event_exists:
        if event_list[event_name.name].event_deadline.astimezone(pytz.utc) < utcnow():
            await ctx.respond(f"Cannot give you reminders for **{event_list[event_name.name].event_name}**! The event's deadline has already passed.", ephemeral=True)
        
        else:
            event = event_list[event_name.name]
            member = ctx.user

            member_hasnt_opted_in = member.id not in event.users_opted_in
            
            if member_hasnt_opted_in:
                event.users_opted_in.append(member.id)
                await databasehelpers.update_attendance_list(ctx.guild.id, event.users_opted_in, event.event_name)

                await member.add_roles(event_name)
                await ctx.respond(f"You will now recieve reminders for **{event.event_name}**!", ephemeral=True)
            else:
                await ctx.respond(f"You are already recieving reminders for **{event.event_name}**!", ephemeral=True)

    else:
        await ctx.respond("Please select an event!", ephemeral=True)

@client.slash_command(name="opt-out", description="Opt out of reminders for an event deadline")
@option("event_name", description="Select event to get reminders for")
async def opt_out(ctx: discord.ApplicationContext, event_name: discord.Role):
    event_list = guild_list[ctx.guild.id]["event list"]

    event_exists = event_name.name in event_list

    if event_exists:
        if event_list[event_name.name].event_deadline.astimezone(pytz.utc) < utcnow():
            await ctx.respond(f"Cannot opt you out of reminders for **{event_list[event_name.name].event_name}**! The event's deadline has already passed.", ephemeral=True)
        
        else:
            member = ctx.user

            event = event_list[event_name.name]

            member_has_opted_in = member.id in event.users_opted_in
            
            if member_has_opted_in:
                event.users_opted_in.remove(member.id)
                await databasehelpers.update_attendance_list(ctx.guild.id, event.users_opted_in, event.event_name)

                await member.remove_roles(event_name)
                await ctx.respond(f"You will no longer recieve reminders for **{event.event_name}**!", ephemeral=True)
            else:
                await ctx.respond(f"You are already not recieving reminders for **{event.event_name}**!", ephemeral=True)

    else:
        await ctx.respond("Please select an event!", ephemeral=True)

@client.slash_command(name="get-attendance", description="See who is recieving reminders for this deadline")
@option("event_name", description="Select event to see attendance of")
async def get_attendance(ctx: discord.ApplicationCommand, event_name: discord.Role):
    event_list = guild_list[ctx.guild.id]["event list"]

    event_doesnt_exist = event_name.name not in event_list

    if event_doesnt_exist:
        await ctx.respond("Please select an event!", ephemeral=True)
    else:
        event = event_list[event_name.name]

        embed = discord.Embed(title=f"{event.event_name}", color=0xad6fa)
        
        if len(event.users_opted_in) == 0:
            embed.add_field(name="Attendance List", value="No one is attending!", inline=False)

            await ctx.respond(embed=embed, ephemeral=True)
        else:
            memberlist = []

            for member_id in event.users_opted_in:
                member = ctx.guild.get_member(member_id)

                memberlist.append(f"{member.display_name}#{member.discriminator}")

            embed.add_field(name=f"Attendance List ({len(event.users_opted_in)} total)", value='\n'.join(memberlist), inline=False)

            await ctx.respond(embed=embed, ephemeral=True)

@client.slash_command(name="get-events", description="See a list of all created events in the guild")
async def get_events(ctx: discord.ApplicationCommand):
    current_guild = ctx.guild

    event_list = guild_list[current_guild.id]["event list"]

    embed = discord.Embed(title=f"All events in {current_guild.name}", color=0xad6fa)

    for event_name in event_list:
        event = event_list[event_name]

        deadline = event.event_deadline

        if deadline.astimezone(pytz.utc) > utcnow():

            embed.add_field(
                name=f"{event.event_name}", 
                value=f"{deadline.strftime('%Y/%m/%d %H:%M %Z')}  |  Number of people: {len(event.users_opted_in)}", 
            inline=False)

    if len(embed.fields) == 0:
        embed.add_field(name="No events for this server!", value="¯\_(ツ)_/¯", inline=False)

    await ctx.respond(embed=embed, ephemeral=True)

client.run(os.getenv("TOKEN"))