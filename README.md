# Blankets for T.O. Bot
A Discord bot written in Python for the Blankets for T.O. Discord server.

## About 
The bot was written with `discord.py` and it responds to text commands sent via a Discord message. A primary function of the bot is to help keep Blankets for T.O. members updated on their personal points totals under the Member Rewards system. The bot accesses this data by sending requests to Google Sheets API v4, since all Member Rewards points are stored on a public view-only spreadsheet.

Made with Python, Flask, [Discord.py](https://discordpy.readthedocs.io/en/stable/#) and [Google Sheets API](https://developers.google.com/sheets/api/)

## Implemented Commands
All commands begin with `!`, but can differ in their availability for call in private messages and in servers.

### Check total rewards points

The `!points` command shows a member's total accumulated points under the Blankets for T.O. Member Rewards system.

![Example of calling points command](/screenshots/points.png)

### Show a breakdown of each month

The `!monthly-points` command shows a member's points for a single month and a breakdown of points gained by each separate task that month.

![Example of calling monthly-points command](/screenshots/monthly-points.png)

### Check rewards points leaderboard

The `!top` command displays a Top 10 Leaderboard of the members with the greatest number of points.

![Example of calling top command](/screenshots/top.png)

### Provide a site link to the tracker spreadsheet

The `!points-link` command gives a link to the master tracker of points which users can manually check. 

![Example of calling points-link command](/screenshots/points-link.png) 

### Direct users to rules and tips

The `!rules` command prompts users to visit the **#server-rules** channel on our server, which contains server-wide guidelines, as well as tips on how to use Discord and the server.

![Example of calling rules command](/screenshots/rules.png) 

### Retrieve a list of servers the bot has joined

The `!get-guilds` command is a bot-owner only command that allows the owner to check which servers the bot has been added to. 

### Retrieve your user id

The `!get-id` command is a quick command which returns the user their unique Discord ID which is used for @ mentions in bot messages.

## Functionalities 

### Automated private welcome message
Upon joining the Blankets for T.O. server, the member receives a friendly welcome message encouraging them to introduce themselves. It also suggests where they would find help for how to use Discord and how to navigate the server.

![Example of private welcome message](/screenshots/private-welcome.png) 

### Prompts if no command is recognized
The bot identifies messages received via private message and messages starting with `!` in a server which failed to call a valid command, and gives a simple help message to the user.

![Example of not receiving a command](/screenshots/no-command-error.png) 

### Informative error messages
When a user uses a command incorrectly, the bot gives informative messages supplemented with examples to help the user correct any errors.

![Example of a command error message](/screenshots/missing-argument-error.png) 

### Critical request error logging
Upon encountering a problem running the request to the Google Sheets API, the bot sends a private message to the bot owner specifying the error encountered. This allows bad requests to be identified quickly and fixed.

![Example of a request error](/screenshots/request-error.png) 

