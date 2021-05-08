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


emojis = {
		'online': '\U0001F7E2',  # green circle
		'offline': '\U000026AA',  # white circle
		'right_arrow': '\U000027A1',
		'left_arrow': '\U00002B05',
		'close': '\U0000274C'
	}


""" Helper Functions """


def get_server_description():
	"""
	Checks to see if and what the server's provided description is
	:return:
	"""
	server = MinecraftServer.lookup(minecraft_server_ip)
	status = server.status()

	if 'text' in [key for key in status.raw['description']]:
		server_desc = status.raw['description']['text']
	else:
		server_desc = None
	return server_desc


def get_members_online():
	"""
	Gets the number of members currently online
	:return: The list of members online if any, else None
	"""
	server = MinecraftServer.lookup(minecraft_server_ip)
	status = server.status()

	if 'sample' in [key for key in status.raw['players']]:
		members_online = [user['name'] for user in status.raw['players']['sample']]
		return members_online
	return None


async def update_members(interval: int, members_online: get_members_online()):
	"""
	Checks for members online in set intervals to update their last seen status
	:return:
	"""
	while True:
		if members_online is not None:
			members_file_r = open("./.resources/members.json", "r")
			members = json.load(members_file_r)
			members_file_r.close()
			for i in members_online:
				if i in members:
					members[i]["LastSeen"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
				else:
					#  IsAdmin is set to False by default and is updated manually
					members[i] = {"LastSeen": datetime.now().strftime("%m/%d/%Y %H:%M:%S"), "IsAdmin": False}
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
	await update_members(120, get_members_online())  # checks for status changes in members being online to update json


@client.event
async def on_message(message):
	"""
	Executed when a message is sent in a text channel
	:return: None
	"""
	if message.channel.name == 'general':  # set the name of the channel the bot should listen to here
		await client.process_commands(message)


""" Client Commands """


@client.command(name='add', description='Adds a correctly formatted POI to the database')
async def add(ctx):
	pass


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
	user_tag = ctx.author.mention

	server = MinecraftServer.lookup(minecraft_server_ip)
	status = server.status()

	num_members_online = status.players.online
	server_latency = status.latency  # in ms

	# get_members_online provides a list of player names currently online
	if get_members_online() is None:
		members_online = []
	else:
		members_online = get_members_online()

	# server_desc provides the server description, if one exists
	if get_server_description() is not None:
		server_desc = get_server_description()
	else:
		server_desc = ''

	# gets data from Members.json
	members_file_r = open("./.resources/members.json", "r")
	members = json.load(members_file_r)
	members_file_r.close()

	total_members = 0
	admin_online = 0
	member_list = ''  # Used for member_status embed
	for i in members:
		total_members += 1
		if i in members_online:
			members[i]["LastSeen"] = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
			print(members)
			member_list += f"{i}  {emojis['online']}\n*Last seen:* {members[i]['LastSeen']}\n"
			if i["IsAdmin"] == True:
				admin_online += 1
		else:
			member_list += f"{i}  {emojis['offline']}\n*Last seen:* {members[i]['LastSeen']}\n"
	member_list += '\n\n\n\nPage 2/2'

	# updates data in Members.json
	members_file_w = open("./.resources/members.json", "w")
	json.dump(members, members_file_w)
	members_file_w.close()

	# messages
	messages = []

	server_info = discord.Embed(title=f'**{minecraft_server_ip} SERVER INFO**',
			description=f"*{server_desc}*", color=0xBA74EE)
	server_info.set_author(name=client.user.name, icon_url=client.user.avatar_url)
	server_info.add_field(name=f"**Server Info**",
					value=f'***Latency:*** {server_latency}ms\n***Total Members:*** {total_members}\n\
					\r***Members online:*** {num_members_online}\n***Admin Online***: {admin_online}\n\n\n\nPage 1/2',
						  inline=True)
	messages.append(server_info)

	member_status = discord.Embed(title=f'**{minecraft_server_ip} MEMBER STATUS**',
					description=f"*{server_desc}*", color=0xBA74EE)
	member_status.set_author(name=client.user.name, icon_url=client.user.avatar_url)
	member_status.add_field(name='**Member Status**', value=member_list, inline=True)
	messages.append(member_status)

	# loop to send message and allow for reaction controls
	index = 0
	msg = None
	send_flag = True
	while True:
		if send_flag:
			res = await ctx.send(user_tag, embed=messages[index])
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


if __name__ == '__main__':
	client.run(token)