import asyncpg

import os

async def add_event_object(guild_id: int, event_name: str, month: str, day: int, year: int, hour: int, minute: int, channel_id: int, description: str, job_id: str, users_opted_in: list):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))
  await con.execute(f"""INSERT INTO events_{guild_id} (event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                        event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in)
  await con.close()

async def remove_event_object(guild_id: int, event_name: str):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))
  await con.execute(f"""DELETE FROM events_{guild_id} WHERE event_name='{event_name}';""")
  await con.close()

async def add_deadline(guild_id: int, job_id: str, job_name: str, year: int, month: str, day: int, hour: int, minute: int):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))
  await con.execute(f"""INSERT INTO jobs_{guild_id} (job_id, job_name, year, month, day, hour, minute)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                        job_id, job_name, year, month, day, hour, minute)
  await con.close()

async def remove_deadlines(guild_id: int, id: str):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))
  await con.execute(f"""DELETE FROM jobs_{guild_id} WHERE job_id='{id}';""")
  await con.close()

async def update_attendance_list(guild_id: int, user_id_list: list, event_name: str):
  con = await asyncpg.connect(os.getenv("DATABASE_URL"))
  await con.execute(f"""UPDATE events_{guild_id}
                        SET users_opted_in = $1
                        WHERE event_name = $2;""",
                        user_id_list,
                        event_name)
  await con.close()