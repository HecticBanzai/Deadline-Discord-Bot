from datetime import datetime
import asyncpg

import os

from event import *

async def add_event_object(guild_id: int, event_object: event):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))

  await con.execute(f"""INSERT INTO events_{guild_id} (event_name, event_deadline_str, send_to_channel_id, description, job_id, users_opted_in)
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        event_object.event_name, 
                        event_object.event_deadline.isoformat(), 
                        event_object.send_to_channel.id, 
                        event_object.description, 
                        event_object.job_id, 
                        event_object.users_opted_in)
  await con.close()

async def remove_event_object(guild_id: int, event_name: str):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))

  await con.execute(f"""DELETE FROM events_{guild_id} WHERE event_name='{event_name}';""")
  await con.close()

async def update_attendance_list(guild_id: int, user_id_list: list, event_name: str):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))

  await con.execute(f"""UPDATE events_{guild_id}
                        SET users_opted_in = $1
                        WHERE event_name = $2;""",
                        user_id_list,
                        event_name)
  await con.close()