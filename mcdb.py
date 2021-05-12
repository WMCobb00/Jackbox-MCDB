"""
Title: Jackbox-Minecraft-Coordinate-Database
Author: Billy Cobb
Desc: A Minecraft coordinate and player database Discord bot for the Jackbox Discord server
"""

import discord
from discord.ext import commands, tasks
import asyncio
import mcstatus
from mcstatus import MinecraftServer
import json
import random
from datetime import datetime


""" Client Vars """


token = ''  # insert Discord bot token here
cmd_prefix = '%'
listening_to = cmd_prefix
client = commands.Bot(command_prefix=cmd_prefix, help_command=None, case_insensitive=True)
minecraft_server_ip = ''  # insert Minecraft server ip here


""" Global Vars """


json_files = {
	'log': './.resources/CommandLog.jso',
	'locations': './.resources/Locations.json',
	'members': './.resources/Members.json'
}


emojis = {
	'online': '\U0001F7E2',  # green circle
	'offline': '\U000026AA',  # white circle
	'right_arrow': '\U000027A1',
	'left_arrow': '\U00002B05',
	'close': '\U0000274C'
}


""" Helper Functions """


def load_json_data(path: str):
	"""
	Loads a Python dict from a json file
	:param path: String path to the json file
	:return: a Python dict of the json data
	"""
	try:
		file_r = open(path, "r")
	except FileNotFoundError:
		print('load_json_data() ERROR: File was not found')
		return None
	try:
		file_data = json.load(file_r)
	except json.decoder.JSONDecodeError:
		print('load_json_data() ERROR: Improper file type or format')
		return None
	file_r.close()
	return file_data


def dump_json_data(file_data: dict, path: str):
	"""
	Dumps a Python dict to a json file
	:param file_data: The Python dict to be converted and dumped
	:param path: String path to the json file
	:return: None
	"""
	try:
		file_w = open(path, "w")
	except FileNotFoundError:
		print('dump_json_data() ERROR: File was not found')
		return None
	try:
		json.dump(file_data, file_w)
	except json.decoder.JSONDecodeError:
		print('dump_json_data() ERROR: Improper file type or format')
		return None
	file_w.close()


def get_server_status(server_ip: str):
	"""
	Looks up a provided server ip and returns its status
	:param server_ip: A string containing the server IP
	:return: The server status (An mcstatus PingResponse object)
	"""
	server = MinecraftServer.lookup(server_ip)
	status = server.status()
	return status


def get_server_description(status: mcstatus.pinger.PingResponse):
	"""
	Checks to see if and what the server's provided description is
	:param status: An mcstatus PingResponse object
	:return: The servers description if one exists, else None
	"""
	if 'text' in [key for key in status.raw['description']]:
		server_desc = status.raw['description']['text']
	else:
		server_desc = None
	return server_desc


def get_members_online(status: mcstatus.pinger.PingResponse):
	"""
	Gets the number of members currently online
	:param status: An mcstatus PingResponse object
	:return: The list of members online if any, else None
	"""
	if 'sample' in [key for key in status.raw['players']]:
		members_online = [user['name'] for user in status.raw['players']['sample']]
		return members_online
	return None


async def update_members(interval: int, members_online: list):
	"""
	Checks for members online in set intervals to update their last seen status
	:param interval: The time interval between auto updates
	:param members_online: The list of current members online
	:return:
	"""
	while True:
		if members_online is not None:
			members = load_json_data(json_files['members'])
			for i in members_online:
				if i in members:
					members[i]["LastSeen"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
				else:
					#  IsAdmin is set to False by default and is updated manually
					members[i] = {"LastSeen": datetime.now().strftime("%m/%d/%Y %H:%M:%S"), "IsAdmin": False}
			dump_json_data(members, json_files['members'])
		await asyncio.sleep(interval)


def predicate(message, l, r):
	"""
	:param message: The Discord message being monitored
	:param l: Checks for a message with a lesser index value in the message list
	:param r: Checks for a message with a greater index value in the message list
	:return: The output value of the check function
	"""
	def check(reaction, user):
		"""
		Checks what reaction to a message the user selected
		:param reaction: The reaction added by the user
		:param user: The users id
		:return: True if the user sent the message and selected a supplied reaction, else False
		"""
		if reaction.message.id != message.id or user == client.user:
			return False
		if reaction.emoji == emojis['close']:
			return True
		if l and reaction.emoji == emojis['left_arrow']:
			return True
		if r and reaction.emoji == emojis['right_arrow']:
			return True
		return False
	return check


def updated_member_info(file: str, members_online: list):
	"""
	Provides an Updated member_list string, total_members int, and admin_online int for the server() command embed
	:param file: The json file containing members
	:param members_online: A list from the server status that has members currently online
	:return: A tuple containing member_list string, total_members int, and admin_online int
	"""
	# gets data from Members.json
	members = load_json_data(file)

	total_members = 0
	admin_online = 0
	member_list = ''  # Used for member_status embed
	for i in members:
		total_members += 1
		if i in members_online:
			members[i]["LastSeen"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
			member_list += f"{i}  {emojis['online']}\n*Last seen:* {members[i]['LastSeen']}\n"
			if members[i]["IsAdmin"]:
				admin_online += 1
		else:
			member_list += f"{i}  {emojis['offline']}\n*Last seen:* {members[i]['LastSeen']}\n"
	member_list += '\n\n\n\nPage 2/2'

	# updates data in Members.json
	dump_json_data(members, json_files['members'])
	return total_members, admin_online, member_list


async def reaction_controlled_embed(ctx: discord.ext.commands.context.Context, messages: list):
	"""
	Passes a list of embedded messages and provides reaction controls for them on Discord for users
	:param ctx: The context of the command called
	:param messages: The list of embeds
	:return: None
	"""
	msg_tag = ctx.author.mention
	index = 0
	msg = None
	send_flag = True
	while True:
		if send_flag:
			res = await ctx.send(msg_tag, embed=messages[index])
			send_flag = False
		else:
			res = await msg.edit(embed=messages[index])
		if res is not None:
			msg = res
		l = index != 0
		r = index != len(messages) - 1
		if l:
			await msg.add_reaction(emojis['left_arrow'])
		if r:
			await msg.add_reaction(emojis['right_arrow'])
		await msg.add_reaction(emojis['close'])
		try:
			react, user = await client.wait_for('reaction_add', check=predicate(msg, l, r), timeout=60.0)
		except asyncio.TimeoutError:  # user has 60.0 secs to react to message else it is deleted and loop exits
			await msg.delete()
			break
		if react.emoji == emojis['close']:  # deletes message if close emoji is selected
			await msg.delete()
			break
		if react.emoji == emojis['left_arrow']:
			index -= 1
			await msg.clear_reaction(emojis['left_arrow'])
		elif react.emoji == emojis['right_arrow']:
			index += 1
			await msg.clear_reaction(emojis['right_arrow'])
		await msg.clear_reaction(emojis['close'])


""" Client Events """


@client.event
async def on_ready():
	"""
	Executed when the client establishes a connection with Discord
	:return: None
	"""
	print('Connection to Discord established successfully', end='\n')
	# Sets activity status
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=listening_to))
	print(f'Client is listening to commands prefixed with {cmd_prefix}', end='\n')
	# checks for status changes in members being online to update Members.json
	await update_members(30, get_members_online(get_server_status(minecraft_server_ip)))


@client.event
async def on_message(message):
	"""
	Executed when a message is sent in a text channel
	:param message: Any message sent in a server the bot is in
	:return: None
	"""
	if message.channel.name == 'general':  # set the name of the channel the bot should listen to here
		await client.process_commands(message)


""" Client Commands """


@client.command(name='add', description='Adds a correctly formatted location to the database')
async def add(ctx, *args):
	await ctx.message.delete()
	locs = load_json_data("./.resources/Locations.json")

	messages = []
	# formatting error message
	format_err = discord.Embed(title=f'**FORMATTING ERROR**', color=0xEC1C1C,
							   description='The format of the location data provided was not formatted correctly')
	format_err.set_author(name=client.user.name, icon_url=client.user.avatar_url)
	format_err.add_field(name=f"**Examples**",
						  value='```Format for entering coordinates:\n\n'
								'Symbol of dimension (i.e. Overworld=O, Nether=N, End=E),\
								 Name of location, x-coord, y-coord, z-coord\n\n'
								'Examples:\n\n'
								'Overworld Zombie Spawner:\n'
								'O, Zombie Spawner, 53, 35, 639\n\n'
								'Nether Bastian:\n'
								'N, Bastian, -239, 36, 513```', inline=True)

	# formatting location name already exists
	already_exists_err = discord.Embed(title=f'**NAME ALREADY IN USE**', color=0xFFFF00,
							   description='The name you selected has already been used, maybe try another?')
	already_exists_err.set_author(name=client.user.name, icon_url=client.user.avatar_url)

	# checks to see that message is formatted correctly
	new_loc = []
	if len(args) != 5:
		messages.append(format_err)
		await reaction_controlled_embed(ctx, messages)
		return
	for i in range(len(args)):
		new_loc.append(args[i].lower().replace(",", ""))  # removes commas from all components
		if i != 1:
			new_loc[i].replace(" ", "")  # removes spaces from all components except for name
	if new_loc[1] not in locs:
		if new_loc[0] == "o" or "n" or "e":
			try:
				int(new_loc[2])
				int(new_loc[3])
				int(new_loc[4])
			except ValueError:
				messages.append(format_err)
				await reaction_controlled_embed(ctx, messages)
				return
			locs[new_loc[1]] = {"Dimension": new_loc[0], "X": new_loc[2], "Y": new_loc[3], "Z": new_loc[4]}
			dump_json_data(locs, json_files['locations'])
		else:
			messages.append(format_err)
			await reaction_controlled_embed(ctx, messages)
			return
	else:
		messages.append(already_exists_err)
		await reaction_controlled_embed(ctx, messages)


@client.command(name='find', description='Returns POI data of all POI having names which contain the input name')
async def find(ctx):
	pass


@client.command(name='random', description='Returns a random POI, if dimension is specified a random POI in that\
dimension is returned')
async def random(ctx):
	pass


@client.command(name='near', description='Returns the five closest POI in the same dimension as the input coordinates')
async def near(ctx):
	pass


@client.command(name='stats', description='Returns contribution and query information for a selected user')
async def stats(ctx):
	pass


@client.command(name='server', description='Returns server and player info at the time of request')
async def server(ctx):
	"""
	Responds to a call of the server command by a user and supplies server and member statuses
	:param ctx: Command context passed
	:return: None
	"""
	await ctx.message.delete()  # deletes users message to prevent buildup of commands

	status = get_server_status(minecraft_server_ip)

	num_members_online = status.players.online
	server_latency = status.latency  # in ms

	# get_members_online provides a list of player names currently online
	if get_members_online(status) is None:
		members_online = []
	else:
		members_online = get_members_online(status)

	# server_desc provides the server description, if one exists
	if get_server_description(status) is not None:
		server_desc = get_server_description(status)
	else:
		server_desc = ''

	member_info = updated_member_info(json_files['members'], members_online)

	# list of embedded messages to be sent
	messages = []

	server_info = discord.Embed(title=f'**{minecraft_server_ip} SERVER INFO**',
			description=f"*{server_desc}*", color=0xBA74EE)
	server_info.set_author(name=client.user.name, icon_url=client.user.avatar_url)
	server_info.add_field(name=f"**Server Info**",
					value=f'***Latency:*** {server_latency}ms\n***Total Members:*** {member_info[0]}\n\
					***Members online:*** {num_members_online}\n***Admin Online***: {member_info[1]}\n\n\n\nPage 1/2',
						  inline=True)
	messages.append(server_info)

	member_status = discord.Embed(title=f'**{minecraft_server_ip} MEMBER STATUS**',
					description=f"*{server_desc}*", color=0xBA74EE)
	member_status.set_author(name=client.user.name, icon_url=client.user.avatar_url)
	member_status.add_field(name='**Member Status**', value=member_info[2], inline=True)
	messages.append(member_status)

	# loop to send embedded messages and allow for reaction controls
	await reaction_controlled_embed(ctx, messages)


if __name__ == '__main__':
	client.run(token)