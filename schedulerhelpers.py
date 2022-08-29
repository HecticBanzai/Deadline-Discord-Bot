from datetime import timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import databasehelpers

import pytz

from discord.utils import get

import event

def delete_role_and_event(event: event):
    channel = event.send_to_channel

    role_to_delete = get(channel.guild.roles, name=event.event_name)

    role_to_delete.delete()
    databasehelpers.remove_event_object(channel.guild.id, event.event_name)

def add_event_jobs(scheduler: AsyncIOScheduler, event_object: event):
    print(event_object.event_deadline)
    event_deadline_utc = event_object.event_deadline.astimezone(pytz.utc)
    remind_date_utc = event_object.remind_date.astimezone(pytz.utc)
    delete_date_utc = event_object.delete_date.astimezone(pytz.utc)

    scheduler.add_job(
        event_object.announce_start, 
        trigger=CronTrigger(
            year=event_deadline_utc.year,
            month=event_deadline_utc.month,
            day=event_deadline_utc.day,
            hour=event_deadline_utc.hour,
            minute=event_deadline_utc.minute),
        id=event_object.job_id, 
        name=event_object.event_name)

    scheduler.add_job(
        event_object.announce_reminder, 
        trigger=CronTrigger(
            year=remind_date_utc.year,
            month=remind_date_utc.month,
            day=remind_date_utc.day,
            hour=remind_date_utc.hour,
            minute=remind_date_utc.minute), 
        id=event_object.job_id+"-remind", 
        name=event_object.event_name+"-remind")

    scheduler.add_job(
        delete_role_and_event, 
        trigger=CronTrigger(
            year=delete_date_utc.year,
            month=delete_date_utc.month,
            day=delete_date_utc.day,
            hour=delete_date_utc.hour,
            minute=delete_date_utc.minute), 
        args=[event_object], 
        id=event_object.job_id+"-delete", 
        name=event_object.event_name+"-delete")
        
    scheduler.print_jobs()

def delete_event_jobs(scheduler, event_object):
    if scheduler.get_job(event_object.job_id):
        scheduler.remove_job(event_object.job_id)

    if scheduler.get_job(event_object.job_id+"-remind"):
        scheduler.remove_job(event_object.job_id+"-remind")

    if scheduler.get_job(event_object.job_id+"-delete"):
        scheduler.remove_job(event_object.job_id+"-delete")

    scheduler.print_jobs()