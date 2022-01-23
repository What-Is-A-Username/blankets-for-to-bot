import hosting
import os
from discord.ext.commands.context import Context
from discord import message
import requests
from typing import List
from datetime import datetime, timezone
import contentful

from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['DISCORD_GUILD']
TESTING_GUILD = os.environ['TESTING_GUILD']

# Contentful Delivery API
contentful_space_id = os.environ['CONTENTFUL_SPACE_ID']
contentful_access_token = os.environ['CONTENTFUL_ACCESS_TOKEN'] 
client = contentful.Client(contentful_space_id, contentful_access_token)

# Embed Message Design
EMBED_COLOUR = 0xfc5c5c
# EMBED_FOOTER_ICON_URL = os.environ['EMBED_FOOTER_ICON_URL']

# The letter of the column containing totals on the Total page
TOTAL_COLUMN_LETTER = 'B'
# The index of the column containing totals on the Total page 
TOTAL_COLUMN_IDX = ord(TOTAL_COLUMN_LETTER) - ord('A')
# The final vertical column of data on the Total page
FINAL_TOTAL_COLUMN_LETTER = 'M'
# The final vertical column of data on the Monthly page
FINAL_MONTH_COLUMN_LETTER = 'P'
TOTAL_SHEET_NAME = 'Total'

# The acceptable format of months that the bot recognizes
MONTHS = {'january': 'Jan 2022', 
    'february': 'Feb 2022', 
    'march': 'Mar 2022',
    'april': 'Apr 2022',
    'may': 'May 2022',
    'june': 'Jun 2022',
    'july': 'Jul 2022',
    'august': 'Aug 2022',
    'september': 'Sep 2021',
    'october': 'Oct / Nov 2021',
    'november': 'Oct / Nov 2021',
    'december': 'Dec 2021'}

intents = discord.Intents.default()
intents.members = True
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
bot = commands.Bot(command_prefix='!', intents = intents, help_command=help_command)

# Send the bot developer a private message
async def send_bot_admin_message(message: str):
    bot_admin_id = int(os.environ['TROUBLESHOOT_CONTACT_ID'])
    bot_admin = bot.get_user(bot_admin_id)
    if bot_admin == None:
        print("Could not find user with ID", bot_admin_id)
        return
    else:
        await bot_admin.send(message)

# Request data of a given cell range. Access values in data with ['values']
async def request_data(ctx: Context, sheet: str, range: str, majorDimension: str = 'ROWS') -> List[str]: 
    spreadsheet = os.environ['SPREADSHEET_ID']
    api_key = os.environ['GOOGLE_CLOUD_API_KEY']
    sheet = sheet.replace('/', '%2f')
    request_link = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet}/values/{sheet}!{range}?key={api_key}'
    print("Sent a request to", request_link)

    try:
        response = requests.get(request_link, timeout = 10)
        response.raise_for_status()
        requested_data = response.json()
        return requested_data
    except requests.exceptions.HTTPError as http_error:
        await ctx.send("HTTP Error encountered.")
        await send_bot_admin_message("HTTP Error:" + str(http_error))
    except requests.exceptions.ConnectionError as conn_error:
        await ctx.send("Connection Error encountered.")
        await send_bot_admin_message("Error connecting to points tracker:" + str(conn_error))
    except requests.exceptions.Timeout as timeout_error:
        await ctx.send("Request Error encountered.")
        await send_bot_admin_message("Request timeout error:" + str(timeout_error))
    except requests.exceptions.RequestException as other_error:
        await ctx.send("Error encountered during request.")
        await send_bot_admin_message("Error:" + str(other_error))
    
    return None
    
# Return a list of headings from the total page page
async def request_all_total_headings(ctx: Context) -> List[str]:
    req = await request_data(ctx, TOTAL_SHEET_NAME, f'5:5')
    req = req['values']
    if req == None:
        return None; 
    return req[0]

# Return a list of headings from a monthly page
async def request_all_monthly_headings(ctx: Context, sheet: str) -> List[str]:
    req = await request_data(ctx, sheet, f'3:3')
    req = req['values']
    if req == None:
        return None; 
    return req[0]

# Return a list of all the member point data from the Total page
async def request_all_total_member_data(ctx: Context) -> List[List[str]]:
    headings = await request_all_total_headings(ctx)
    final_month_column_letter = chr(ord('A') + len(headings) - 1)
    req = await request_data(ctx, TOTAL_SHEET_NAME, f'A6:{final_month_column_letter}')
    member_data = req['values']

    for i in range(len(member_data)):
        missing_cells = len(headings) - len(member_data[i])
        if missing_cells > 0: 
            member_data[i].extend([''] * missing_cells)
        else: 
            member_data[i] = member_data[i][:len(headings)]
    return member_data

# Return a list of all member point data from a monthly page
async def request_all_monthly_data(ctx: Context, sheet: str) -> List[List[str]]:
    headings = await request_all_monthly_headings(ctx, sheet)
    final_month_column_letter = chr(ord('A') + len(headings) - 1)
    req = await request_data(ctx, sheet, f'A3:{final_month_column_letter}')
    
    member_data = req['values']
    for i in range(len(member_data)):
        missing_cells = len(headings) - len(member_data[i])
        if missing_cells > 0: 
            member_data[i].extend([''] * missing_cells)
        else: 
            member_data[i] = member_data[i][:len(headings)]
    return member_data

# show leaderboard of top points
@bot.command(name='top', brief='Print the member points leaderboard.', description='Print the member points leaderboard.')
@commands.guild_only()
@commands.cooldown(1, 5, commands.BucketType.user)
async def top(ctx: Context):
	if ctx.author.id == bot.user.id:
		return
	all_data = await request_all_total_member_data(ctx)
	if all_data == None:
		return
	
	# make a list of [member_name, member_points]
	points = [ [member[0], member[1] ] for member in all_data]
    # sort by points into descending order
	points = sorted(points, key = lambda x: x[1], reverse=True)
	# only show top x number of people
	x = 10
	points = points[:x]
	# output the leaderboard
	info = f'\n__Top {x} Point Totals__\n'
	embed = discord.Embed(title='Member Points Leaderboard', description=info, colour=EMBED_COLOUR)
	embed.add_field(name='#', value='\n'.join([str(x) for x in range(1, x+1)])+'\n', inline=True)
	embed.add_field(name='Person', value='\n'.join([person[0] for person in points])+'\n', inline=True)
	embed.add_field(name='Points', value='\n'.join([str(person[1]) for person in points])+'\n', inline=True)
	embed.set_footer(text='Data pulled from points tracker. Access it via !points-link.')
	await ctx.send(embed=embed)
    
# show the messenger how many points they have organized by month
@bot.command(name='points', brief='Give a first name to check the points they have.', description='Provide your first name in order to check how many points you have. Example: !points Jim') 
@commands.cooldown(1, 5, commands.BucketType.user)
async def total_points(ctx: Context, first_name: str = None):
	if ctx.author.id == bot.user.id:
		return
	if first_name == None:
		await ctx.send(f'<@{ctx.author.id}>, we could not find a first name to search for in your !points command. Please specify a first name by typing it after !points.\n **Example**: !points jim')
		return
	all_data = await request_all_total_member_data(ctx)
	if all_data == None:
		return
	lowered_arg = first_name.lower()

	# find a match based on the first name
	match = discord.utils.find(lambda m: lowered_arg == m[0].split(' ')[0].lower(), all_data)

	# if no entry was found for the specified name 
	if match == None:
		if ctx.guild != None:
			bot_developer_role = discord.utils.find(lambda role: role.name == 'Bot Developers', ctx.guild.roles)
			await ctx.send(f'Sorry <@{ctx.author.id}>, we could not find a points entry for a member with name **{first_name}**. Please check for any spelling errors. *If the error persists, please contact one of our <@&{bot_developer_role.id}>*.') 
		else:
			await ctx.send(f'Sorry <@{ctx.author.id}>, we could not find a points entry for a member with name **{first_name}**. Please check for any spelling errors. *If the error persists, please send a message to our Bot Developer*.') 
	# output points for the matching entry
	else:
		total_points = int(match[TOTAL_COLUMN_IDX])
		info = f'Hello <@{ctx.author.id}>!\n\n**{match[0]}** currently has **{total_points}** points!'
		if total_points > 0:
			headings = await request_all_total_headings(ctx)
			headings = headings[2:]
			categories = match[2:]
			breakdown = []
			for i in range(0, len(categories)): 
				categories[i] = categories[i].replace('+', '').replace('-', '')
				if categories[i] != '' and int(categories[i]) != 0:
					breakdown.append([headings[i], categories[i]])
			info = info + '\n\n**__Points Breakdown By Month:__**\n'
			
		embed = discord.Embed(title='Member Points', description=info, colour=EMBED_COLOUR)
		if total_points > 0:
			embed.add_field(name='Month', value='\n'.join([entry[0] for entry in breakdown]), inline=True)
			embed.add_field(name='Points', value='\n'.join([entry[1] for entry in breakdown]), inline=True)
		embed.set_footer(text='Data pulled from points tracker. Access it via !points-link.')
		await ctx.send(embed=embed)

# shows the messenger how many points they have for a given month
@bot.command(name='monthly-points', brief='Give a first name and a month to check the points they gained that month.', description='Provide a first name and the name of a month in order to check how many points that person gained that month. Examples: "!monthly-points Jim sep" or "!monthly-points september"') 
@commands.cooldown(1, 5, commands.BucketType.user)
async def monthly_points(ctx: Context, first_name: str = None, month: str = None):
	if ctx.author.id == bot.user.id:
		return
	if first_name == None:
		await ctx.send(f'<@{ctx.author.id}>, we could not find a first name to search for in your !monthly-points command. Please specify a first name by typing it after !monthly-points.\n**Example:** !monthly-points jim')
		return
	if month == None:
		await ctx.send(f'<@{ctx.author.id}>, we could not find the month you specified to search for in your !monthly-points command. Please specify a month by typing its name after !monthly-points.\n**Examples:** !monthly-points jim sep *OR* !monthly-points jim september')
		return

	lowered_arg = month.lower()
	identified_month = ''
	for i in list(MONTHS.keys()):
		if lowered_arg in i.lower():
			identified_month = i
			break 
	if identified_month == '':
		await ctx.send(f'Sorry, we tried to search for a month matching with **{month}** but could not find one. Check for misspelling.')
		return 

	all_data = await request_all_monthly_data(ctx, MONTHS[identified_month])
	if all_data == None:
		return

	lowered_arg = first_name.lower()
	match = discord.utils.find(lambda m: lowered_arg == m[0].split(' ')[0].lower(), all_data)

	# if no entry was found for the specified name 
	if match == None:
		if ctx.guild != None:
			bot_developer_role = discord.utils.find(lambda role: role.name == 'Bot Developers', ctx.guild.roles)
			await ctx.send(f'Sorry <@{ctx.author.id}>, we could not find a points entry for a member with name **{first_name}**. Please check for any spelling errors. *If the error persists, please contact one of our <@&{bot_developer_role.id}>*.') 
		else:
			await ctx.send(f'Sorry <@{ctx.author.id}>, we could not find a points entry for a member with name **{first_name}**. Please check for any spelling errors. *If the error persists, please contact the Bot Developer.') 
	# output points for the matching entry
	else:
		total_points = int(match[TOTAL_COLUMN_IDX])
		info = f'Hello <@{ctx.author.id}>!\n\n**{match[0]}** currently has **{total_points}** points!'
		if total_points > 0:
			headings = await request_all_monthly_headings(ctx, MONTHS[identified_month])
			headings = headings[2:]
			categories = match[2:]
			breakdown = []
			for i in range(0, len(categories) - 1): 
				categories[i] = categories[i].replace('+', '').replace('-', '')
				if categories[i] != '' and int(categories[i]) != 0:
					breakdown.append([f'+{int(categories[i])}', headings[i]])
			
			redeemed_points = categories[-1].replace('+', '').replace('-', '')
			if redeemed_points != '' and int(redeemed_points) != 0:
				breakdown.append([f'-{int(redeemed_points)}', 'Points redeemed for prizes'])

			info = info + f'\n\n**__Points Breakdown for {identified_month.title()}:__**\n'
			
		embed = discord.Embed(title='Member Points', description=info, colour=EMBED_COLOUR)
		if total_points > 0:
			embed.add_field(name='Points', value='\n'.join([entry[0] for entry in breakdown]), inline=True)
			embed.add_field(name='Task', value='\n'.join([entry[1] for entry in breakdown]), inline=True)
		embed.set_footer(text='Data pulled from points tracker. Access it via !points-link.')
		await ctx.send(embed=embed)

# message the link to the spreadsheet used to record all points data 
@bot.command(name='points-link', brief='Access the sheet which is used to track member rewards points.', description='Access the sheet which is used to track member rewards points.')
@commands.cooldown(1, 30, commands.BucketType.guild)
async def points_link(ctx: Context):
	if ctx.author.id == bot.user.id:
		return 
	spreadsheet = os.environ['SPREADSHEET_ID']
	sheet_link = f'https://docs.google.com/spreadsheets/d/{spreadsheet}'
	info = f'Hello <@{ctx.author.id}>!\n\nView the current members points tally here:\n{sheet_link}\n\nThis spreadsheet is maintained by the executive team. Message them if you have any questions!'
	embed = discord.Embed(title='Member Points Link', description=info, colour=EMBED_COLOUR)
	await ctx.send(embed=embed) 

@bot.command(name='events', brief='Print a list of upcoming and recent events.', description='Print a list of upcoming and recent events run by Blankets for T.O.')
@commands.cooldown(1, 10, commands.BucketType.user)
async def events(ctx: Context):
	event_content_type_id = os.environ['EVENT_CONTENT_TYPE_ID']
	events_by_date = client.entries({'content_type': event_content_type_id, 'order': 'fields.eventDate'})
	visible_events = [e for e in events_by_date if e.start_date <= datetime.now(timezone.utc) and e.end_date >= datetime.now(timezone.utc)]
	past_events = [e for e in visible_events if e.event_date < datetime.now(timezone.utc)]
	upcoming_events = [e for e in visible_events if e.event_date >= datetime.now(timezone.utc)]
	embed = discord.Embed(title='Upcoming and Recent Events', description='Browse this list of upcoming and recent events organized by Blankets for T.O.\n\u200b', colour=EMBED_COLOUR)
	if len(upcoming_events) > 0:
		embed.add_field(name='__UPCOMING EVENTS__', value='\u200b', inline=False)
		for event in upcoming_events:
			embed.add_field(name=event.event_name + ' (' + event.event_date.strftime('%b %d, %Y') + ')', value=event.description+'\n\u200b', inline=False)
	if len(past_events) > 0:
		embed.add_field(name='__RECENT AND ONGOING EVENTS__', value='\u200b', inline=False)
		for event in past_events:
			embed.add_field(name=event.event_name + ' (' + event.event_date.strftime('%b %d, %Y') + ')', value=event.description+'\n\u200b', inline=False)

	embed.set_footer(text='Have any questions? Message our Executive Team!')
	await ctx.send(embed=embed)

# give a link to the rules section 
@bot.command(name='rules', brief='Access Discord help tips and server rules.', description='Access Discord help tips and server rules for this server.')
@commands.guild_only()
@commands.cooldown(1, 30, commands.BucketType.user)
async def rules(ctx: Context):
	if ctx.author.id == bot.user.id:
		return
	# find the rules channel in the server
	rules_channel = discord.utils.find(lambda g: g.name == 'server-rules', ctx.guild.text_channels)
	if rules_channel == None:
		await ctx.send(f'Error: Could not find the rules channel in this server.')
		return 
	# link the messager to the rules channel
	await ctx.send(f'Please see server rules in <#{rules_channel.id}>!')

# print the user id
@bot.command(name='get-id', brief='Print your unique Discord user ID number.', description='Print your unique Discord user ID number.')
@commands.dm_only()
@commands.is_owner()
async def get_id(ctx: Context):
	if ctx.author.id == bot.user.id:
		return
	await ctx.send(f'Your unique Discord user id is {ctx.author.id}.')

# print all the guilds that this bot is currently in
@bot.command(name='get-guilds', brief='Print the list of guilds/servers that have added this bot.', description='Print the list of guilds/servers that have added this bot.')
@commands.dm_only()
@commands.is_owner()
async def guilds(ctx: Context):
	if ctx.author.id == bot.user.id:
		return
	bot_admin_id = int(os.environ['TROUBLESHOOT_CONTACT_ID'])
	bot_admin = bot.get_user(bot_admin_id)
	if ctx.author.id != bot_admin_id:
		return
	else:
		await bot_admin.send("This bot is currently in guilds: " + (', '.join([g.name for g in bot.guilds])))

# send a private dm every time a new member joins the server
@bot.event
async def on_member_join(member: discord.Member):
	message_string = 'Thanks for joining us! On our server, you can get a chance to connect with other members and the executive team!\n\n:wave: Introduce yourself in the **#introductions** channel and say hi! In your intro, feel free to include anything you like. Here are some suggestions:\n- Your name, year and program\n- An interesting fact, interest, hobby or story of yours\n- What other groups you are involved in on campus\n- Any of your social media handles we can follow\n\n:grey_question:**Need help using Discord or our server?** We have included helpful tips in our **#server-rules** channel on the server.\n\n:speech_left:*For any questions, feel free to send your messages on the server or privately. Note: This message is an automated private welcome message.*\n\n**We hope you enjoy your stay!**' 
	await member.send(f':tada: **Welcome to the Blankets for T.O. Discord server, <@{member.id}>!** :tada:\n\n{message_string}')
        
# add a message if it appears that someone is incorrectly using a command
@bot.event
async def on_message(message: message.Message):
	if message.author != bot.user:
		if isinstance(message.channel, discord.channel.DMChannel) or message.content.startswith('!') and message.channel.name == 'bot-commands':
			if message.content.split(' ')[0] not in ['!events', '!help', '!points', '!monthly-points', '!get-guilds', '!get-id', '!rules', '!points-link', '!top']:
				await message.channel.send(f'Hi <@{message.author.id}>. A command could not be recognized in the last message you sent. Check for any misspelling and type "!help" for a list of supported commands.')
	await bot.process_commands(message)
	return

# hosting.keep_alive()
bot.run(TOKEN)
