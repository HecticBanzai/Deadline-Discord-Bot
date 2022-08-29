from datetime import datetime
import discord
from discord.ui import Button, View
from discord.utils import get, utcnow

import helpers
import databasehelpers

from datetime import datetime, timedelta

def create_reminder_date(event_deadline):
    now = utcnow()

    time_difference = event_deadline - now

    difference_in_days = time_difference.days

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

            # Check if the last reminder is on the day of the event
            same_date = next_reminder_date.year == event_deadline.year and next_reminder_date.month == event_deadline.month and next_reminder_date.day == event_deadline.day
            if same_date:
                next_reminder_date -= timedelta(days=1)

        return next_reminder_date

    # If the event is at exactly 1 day away
    elif difference_in_days == 1:
        next_reminder_date = event_deadline - timedelta(hours = 1)

        return next_reminder_date

  # If it is the day of the event
    else:
        next_reminder_date = event_deadline - timedelta(minutes = 15)

        if not next_reminder_date < now:
            return next_reminder_date
        else:
            return event_deadline + timedelta(days=2)

class event:
  def __init__(self, event_name: str, event_deadline: datetime, send_to_channel: discord.TextChannel, description: str, job_id: str, users_opted_in: list):
    self.event_name = event_name
    self.event_deadline = event_deadline
    self.remind_date = create_reminder_date(event_deadline)
    self.delete_date = event_deadline + timedelta(days=1)
    self.send_to_channel = send_to_channel
    self.description = description
    self.job_id = job_id
    self.users_opted_in = users_opted_in or []
  
  def __str__(self):
    return f"Event: {self.event_name}, {self.event_deadline.strftime('%Y/%m/%d %H:%M:%S %Z')}"

  async def announce_create(self):
      embed = discord.Embed(title="Event Created!", color=0xad6fa)
      embed.add_field(name="Event Name", value=self.event_name, inline=False)
      embed.add_field(name="Date & Time", value=f"{self.event_deadline.strftime('%Y/%m/%d %H:%M:%S %Z')}", inline=True)

      if self.description != None:
          embed.add_field(name="Description", value=self.description, inline=False)

      view = self.view_with_buttons()

      await self.send_to_channel.send(embed=embed, view=view)

  async def announce_reminder(self):
      embed = discord.Embed(title="Event Reminder!", color=0xad6fa)
      embed.add_field(name="Event Name", value=self.event_name, inline=False)
      embed.add_field(name="Date & Time", value=f"{self.event_deadline.strftime('%Y/%m/%d %H:%M:%S %Z')}", inline=True)

      if self.description != None:
          embed.add_field(name="Description", value=self.description, inline=False)

      view = self.view_with_buttons()

      role = get(self.send_to_channel.guild.roles, name=self.event_name)

      await self.send_to_channel.send(f"{role.mention}", embed=embed, view=view)

  async def announce_start(self):
      embed = discord.Embed(title="Event Starting!", color=0xad6fa)
      embed.add_field(name="Event Name", value=self.event_name, inline=False)
      embed.add_field(name="Date & Time", value=f"{self.event_deadline.strftime('%Y/%m/%d %H:%M:%S %Z')}", inline=True)
      
      if self.description != None:
          embed.add_field(name="Description", value=self.description, inline=False)

      role = get(self.send_to_channel.guild.roles, name=self.event_name)

      await self.send_to_channel.send(f"{role.mention}", embed=embed)

  async def announce_update(self):
      embed = discord.Embed(title="Event Updated!", color=0xad6fa)
      embed.add_field(name="Event Name", value=self.event_name, inline=False)
      embed.add_field(name="Date & Time", value=f"{self.event_deadline.strftime('%Y/%m/%d %H:%M:%S %Z')}", inline=True)
      
      if self.description != None:
          embed.add_field(name="Description", value=self.description, inline=False)

      view = self.view_with_buttons()

      role = get(self.send_to_channel.guild.roles, name=self.event_name)

      await self.send_to_channel.send(f"{role.mention}", embed=embed, view=view)

  async def announce_delete(self):
      embed = discord.Embed(title="Event Deleted!", color=0xad6fa)
      embed.add_field(name="Event Name", value=self.event_name, inline=False)

      role = get(self.send_to_channel.guild.roles, name=self.event_name)

      await self.send_to_channel.send(f"{role.mention}", embed=embed)
  
  def update_event(self, new_event_name: str, new_event_deadline: datetime, new_send_to_channel: discord.channel, new_description: str):
    return event(new_event_name, new_event_deadline, new_send_to_channel, new_description, self.job_id, self.users_opted_in)

  def view_with_buttons(self):
    view = View(timeout=None)

    opt_in_button = Button(label="Opt in for reminders", style=discord.ButtonStyle.success)
    opt_out_button = Button(label="Opt out of reminders", style=discord.ButtonStyle.danger)
    get_attendance_button = Button(label="Check attendance", style=discord.ButtonStyle.primary)
    
    view.add_item(opt_in_button)
    view.add_item(opt_out_button)
    view.add_item(get_attendance_button)

    async def opt_in(interaction):
        if self.event_deadline < utcnow():
          await interaction.response.send_message(f"Cannot give you reminders for **{self.event_name}**! The event's deadline has already passed.", ephemeral=True)

        else:
          member = interaction.user
          role = get(interaction.guild.roles, name=self.event_name)

          if role != None:
            if member.id not in self.users_opted_in:
              self.users_opted_in.append(member.id)

              await databasehelpers.update_attendance_list(interaction.guild_id, self.users_opted_in, self.event_name)

              await member.add_roles(role)

              await interaction.response.send_message(f"You will now recieve reminders for **{self.event_name}**!", ephemeral=True)
            else:
              await interaction.response.send_message(f"You are already recieving reminders for **{self.event_name}**!", ephemeral=True)

          else:
            await interaction.response.send_message(f"Cannot send you notifications for **{self.event_name}**! Maybe the event was updated/deleted?", ephemeral=True)

    async def opt_out(interaction):
        if self.event_deadline < utcnow():
            await interaction.response.send_message(f"Cannot opt you out of reminders for **{self.event_name}**! The event's deadline has already passed.", ephemeral=True)

        else:
          member = interaction.user
          role = get(interaction.guild.roles, name=self.event_name)

          if role != None:
            if member.id in self.users_opted_in:
              self.users_opted_in.remove(member.id)

              await databasehelpers.update_attendance_list(interaction.guild_id, self.users_opted_in, self.event_name)

              await member.remove_roles(role)

              await interaction.response.send_message(f"You will no longer recieve reminders for **{self.event_name}**!", ephemeral=True)

            else:
              await interaction.response.send_message(f"You are already not recieving reminders for **{self.event_name}**!", ephemeral=True)

          else:
            await interaction.response.send_message(f"Cannot opt you out of notifications for **{self.event_name}**! Maybe the event was updated/deleted?", ephemeral=True)

    async def get_attendance(interaction):
      if len(self.users_opted_in) == 0:
        embed = discord.Embed(title=f"{self.event_name}", color=0xad6fa)
        embed.add_field(name="Attendance List", value="No one is attending!", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
      else:
        memberlist = []

        for member_id in self.users_opted_in:
          member = interaction.guild.get_member(member_id)

          memberlist.append(f"{member.display_name}#{member.discriminator}")

        embed = discord.Embed(title=f"{self.event_name}", color=0xad6fa)
        embed.add_field(name=f"Attendance List ({len(event.users_opted_in)} total)", value='\n'.join(memberlist), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    opt_in_button.callback = opt_in
    opt_out_button.callback = opt_out
    get_attendance_button.callback = get_attendance

    return view