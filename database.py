async def add_event_object(client_pg_con, guild_id: int, event_name: str, month: str, day: int, year: int, hour: int, minute: int, channel_id: int, description: str, job_id: str, users_opted_in: list):
  await client_pg_con.execute(f"""INSERT INTO events_{guild_id} (event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in)
                                  VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
                                  event_name, month, day, year, hour, minute, channel_id, description, job_id, users_opted_in)

async def remove_event_object(client_pg_con, guild_id: int, event_name: str):
  await client_pg_con.execute(f"""DELETE FROM events_{guild_id} WHERE event_name='{event_name}';""")

async def add_deadline(client_pg_con, guild_id: int, job_id: str, job_name: str, year: int, month: str, day: int, hour: int, minute: int):
  await client_pg_con.execute(f"""INSERT INTO jobs_{guild_id} (job_id, job_name, year, month, day, hour, minute)
                                  VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                                  job_id, job_name, year, month, day, hour, minute)

async def remove_deadline(client_pg_con, guild_id: int, id: str):
  await client_pg_con.execute(f"""DELETE FROM jobs_{guild_id} WHERE job_id='{id}';""")