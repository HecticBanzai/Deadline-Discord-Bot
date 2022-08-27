from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

import databasehelpers

from discord.utils import get

import event

def delete_role_and_event(event):
    channel = event.send_to_channel

    role_to_delete = get(channel.guild.roles, name=event.event_name)

    role_to_delete.delete()
    databasehelpers.remove_event_object(channel.guild.id, event.event_name)

def add_event_jobs(scheduler: AsyncIOScheduler, event_object: event):
    scheduler.add_job(
        event_object.announce_start, 
        trigger=CronTrigger(
            year=event_object.event_deadline.year,
            month=event_object.event_deadline.month,
            day=event_object.event_deadline.day,
            hour=event_object.event_deadline.hour,
            minute=event_object.event_deadline.minute),
        id=event_object.job_id, 
        name=event_object.event_name)

    scheduler.add_job(
        event_object.announce_reminder, 
        trigger=CronTrigger(
            year=event_object.remind_date.year,
            month=event_object.remind_date.month,
            day=event_object.remind_date.day,
            hour=event_object.remind_date.hour,
            minute=event_object.remind_date.minute), 
        id=event_object.job_id+"-remind", 
        name=event_object.event_name+"-remind")

    scheduler.add_job(
        delete_role_and_event, 
        trigger=CronTrigger(
            year=event_object.delete_date.year,
            month=event_object.delete_date.month,
            day=event_object.delete_date.day,
            hour=event_object.delete_date.hour,
            minute=event_object.delete_date.minute), 
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