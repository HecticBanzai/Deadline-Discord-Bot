# Deadline Discord Bot

## Table of Contents
* [General Info](#general-information)
* [Technologies Used](#technologies-used)
* [Features](#features)
* [Screenshots](#screenshots)
* [Setup](#setup)
* [Usage](#usage)
* [Project Status](#project-status)
* [Room for Improvement](#room-for-improvement)
* [Acknowledgements](#acknowledgements)
* [Contact](#contact)
<!-- * [License](#license) -->


## General Information
- The Deadline Discord Bot is designed to remind people of upcoming events via roles and pings.
- Because of our busy high school lives, sometimes we get sidetracked from the events we plan. With this Discord bot, we will not have to worry about remembering what's coming up.
- After taking learning basic Python in my high school Artificial Intelligence class, I wanted to expand my knowledge and experience programming for real world applications with tools such as Heroku and Github. 

## Technologies Used
- Python - version 3.10.6
- Py-cord - version 2.0.0
- APScheduler - version 3.9.1
- Python-dotenv - version 0.20.0
- Heroku - Version 20

## Features
- Create deadlines for events at any time
- Update deadlines for any change of plans
- Delete deadlines
- Opt in or out of reminders for deadlines


## Screenshots
![Example screenshot](./screenshots/create-deadline.png)
![Example screenshot2](./screenshots/create-deadline2.png)

## Setup
- [Requirements](requirements.txt)

## Usage

- "*" stands for an optional input

### Create Deadline

`/deadline {event_name} {month} {day} {year} {hour} {minute} {channel} {*description}`

- ***event_name***: Name of the event you will make the deadline for. It will also be the name of the role that the command will create.
- ***month***: The month of the deadline date. The command will give you the list of all the months to choose from.
- ***day***: The day of the deadline date. You must enter the correct day for each month. For example, entering 31 for the month of September will not work.
- ***year***: The year of the deadline date. By default the minimum year will be the current year.
- ***hour***: The hour of the deadline date. You must enter value between 0 and 23 where 0 stands for 12:00 AM and 23 stands for 11:00 PM
- ***minute***: The minute of the deadline date. You must enter a value between 0 and 59.
- ***channel***: This will be the channel that the bot will send reminders to. This does not include updates to deadlines/events.
-  ***description***: A description is optional. This is where you can put any extra details such as where to meet up or what is going to happen at the event.

![Example deadline](./screenshots/example%20deadline.png)

### Update Event

`/update {event_name} {*new_event_name} {*month} {*day} {*year} {*hour} {*minute} {*channel} {*description}`

- ***event_name***: Name of the event you will update. Comes in the form of a role, meaning you must select a role that the bot as created or else an error will be raised.
- ***new_event_name***: New name for the of event you want to change. This will also change the role name.

![Example deadline](./screenshots/example%20update.png)

### Delete Event

`/delete {event_name}`

- ***event_name***: Name of the event you will delete. Comes in the form of a role, meaning you must select a role that the bot as created or else an error will be raised.

![Example deadline](./screenshots/example%20delete.png)

## Project Status
Project is: _in progress_ 

## Room for Improvement
Room for improvement:
- Add more flexible reminder scheduling

To do:
- Add command to opt in or out of reminders.
- Save job list whenever the bot is shut down or restarted
- Add get members command to see who will recieve reminders

## Acknowledgements
- Many thanks to [this tutorial](https://www.youtube.com/watch?v=EreE-0hQibM&ab_channel=JonahLawrence%E2%80%A2DevProTips) for helping me set up the bot on Heroku.
- Thanks you to the [Pycord Discord Server](https://discord.gg/ySu2u8Ff) for helping me through many roadblocks

## Contact
Created by [@HecticBanzai](https://github.com/HecticBanzai) - feel free to contact me!


<!-- Optional -->
<!-- ## License -->
<!-- This project is open source and available under the [... License](). -->

<!-- You don't have to include all sections - just the one's relevant to your project -->