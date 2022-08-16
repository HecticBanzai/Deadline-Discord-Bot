import discord
from discord.ui import Button, View
from discord.utils import get

import helpers

class event:
  def __init__(self, event_name, month, day, year, hour, minute, channel, description, job_id, users_opted_in):
    self.event_name = event_name
    self.month = month
    self.day = day
    self.year = year
    self.hour = hour
    self.minute = minute
    self.channel = channel
    self.description = description
    self.job_id = job_id
    self.users_opted_in = [] or users_opted_in

  def __str__(self):
    return f"Event: {self.event_name}, {self.month}/{self.day}/{self.year}, {self.hour}:{self.minute}"

  def embed_for_create(self):
    embed = discord.Embed(title="Event Created!", color=0xad6fa)
    embed.add_field(name="Event Name", value=self.event_name, inline=False)
    embed.add_field(name="Date", value=f"{helpers.create_date_string(self.month, self.day, self.year)}", inline=True)
    embed.add_field(name="Time", value=f"{helpers.create_time_string(self.hour, self.minute)}", inline=True)

    if self.description != None:
        embed.add_field(name="Description", value=self.description, inline=False)

    return embed

  def embed_for_remind(self):
    embed = discord.Embed(title="Event Reminder!", color=0xad6fa)
    embed.add_field(name="Event Name", value=self.event_name, inline=False)
    embed.add_field(name="Date", value=f"{helpers.create_date_string(self.month, self.day, self.year)}", inline=True)
    embed.add_field(name="Time", value=f"{helpers.create_time_string(self.hour, self.minute)}", inline=True)

    if self.description != None:
        embed.add_field(name="Description", value=self.description, inline=False)

    return embed

  def embed_for_start(self):
    embed = discord.Embed(title="Event Starting!", color=0xad6fa)
    embed.add_field(name="Event Name", value=self.event_name, inline=False)
    embed.add_field(name="Date", value=f"{helpers.create_date_string(self.month, self.day, self.year)}", inline=True)
    embed.add_field(name="Time", value=f"{helpers.create_time_string(self.hour, self.minute)}", inline=True)

    if self.description != None:
        embed.add_field(name="Description", value=self.description, inline=False)

    return embed

  def embed_for_update(self):
    embed = discord.Embed(title="Event Updated!", color=0xad6fa)
    embed.add_field(name="Event Name", value=self.event_name, inline=False)
    embed.add_field(name="Date", value=f"{helpers.create_date_string(self.month, self.day, self.year)}", inline=True)
    embed.add_field(name="Time", value=f"{helpers.create_time_string(self.hour, self.minute)}", inline=True)

    if self.description != None:
        embed.add_field(name="Description", value=self.description, inline=False)

    return embed

  def embed_for_delete(self):
    embed = discord.Embed(title="Event Deleted!", color=0xad6fa)
    embed.add_field(name="Event Name", value=self.event_name, inline=False)

    return embed

  def view_with_buttons(self):
    view = View(timeout=None)

    opt_in_button = Button(label="Opt in for reminders", style=discord.ButtonStyle.success)
    opt_out_button = Button(label="Opt out of reminders", style=discord.ButtonStyle.danger)
    get_attendance_button = Button(label="Check attendance", style=discord.ButtonStyle.primary)
    
    view.add_item(opt_in_button)
    view.add_item(opt_out_button)
    view.add_item(get_attendance_button)

    async def opt_in(interaction):
        member = interaction.user
        role = get(interaction.guild.roles, name=self.event_name)

        if role != None:
          if member not in self.users_opted_in:
            self.users_opted_in.append(member)
            await member.add_roles(role)
            await interaction.response.send_message(f"You will now recieve reminders for **{self.event_name}**!", ephemeral=True)
        else:
          await interaction.response.send_message(f"Cannot send you notifications for **{self.event_name}**! Maybe the event was updated?", ephemeral=True)

    async def opt_out(interaction):
        member = interaction.user
        role = get(interaction.guild.roles, name=self.event_name)

        if role != None:
          if member in self.users_opted_in:
            self.users_opted_in.remove(member)
            await member.remove_roles(role)
            await interaction.response.send_message(f"You will no longer recieve reminders for **{self.event_name}**!", ephemeral=True)
        else:
          await interaction.response.send_message(f"Cannot opt you out of notifications for **{self.event_name}**! Maybe the event was updated?", ephemeral=True)

    async def get_attendance(interaction):
      if len(self.users_opted_in) == 0:
        embed = discord.Embed(title=f"{self.event_name}", color=0xad6fa)
        embed.add_field(name="Attendance List", value="No one is attending!", inline=False)

        await interaction.response.send_message(embed=embed)
      else:
        memberlist = []

        for member in self.users_opted_in:
          memberlist.append(f"{member.display_name}#{member.discriminator}")

        embed = discord.Embed(title=f"{self.event_name}", color=0xad6fa)
        embed.add_field(name="Attendance List", value='\n'.join(memberlist), inline=False)

        await interaction.response.send_message(embed=embed)
        
    opt_in_button.callback = opt_in
    opt_out_button.callback = opt_out
    get_attendance_button.callback = get_attendance

    return view

  def update_event(self, new_event_name, month, day, year, hour, minute, channel, description, job_id):
    return event(new_event_name, month, day, year, hour, minute, channel, description, job_id, self.users_opted_in)