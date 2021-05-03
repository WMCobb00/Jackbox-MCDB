'''
Title: Jackbox-Minecraft-Coordinate-Database
Author: Billy Cobb
Desc: A Minecraft coordinate and player database Discord bot for the Jackbox Discord server
'''

import discord
from discord.ext import commands, tasks
import mcstatus
from mcstatus import MinecraftServer
import json
import random
import datetime


''' Client Vars '''
token = ''
cmd_prefix = '%'
listening_to = cmd_prefix
client = commands.Bot(command_prefix=cmd_prefix, help_command=None, case_insensitive=True)
minecraft_server_ip = ''  # insert minecraft server ip here


''' Client Events '''
@client.event
async def on_ready():
	'''
	Executed when the client establishes a connection with Discord
	'''
	print('Connection to Discord established succesfully', end='\n')
	await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=listening_to))  # Sets activity status
	print(f'Client is listening to commands prefixed with {cmd_prefix}', end='\n')

@client.event
async def on_message(message):
	'''
	Checks that the command is called in the minecrafcoords channel
	'''
	if message.channel.name == 'general':  # set the name of the channel the bot should listen to here
		await client.process_commands(message)


''' Client Commands '''
@client.command(name='add', description='Adds a correctly formatted POI to the database')
async def add(ctx):
	pass

@client.command(name='find', description='Returns POI data of all POI having names which contain the input name')
async def find(ctx):
	pass

@client.command(name='random', description='Returns a random POI, if dimmension is specified a random POI in that dimmension is returned')
async def random(ctx):
	pass

@client.command(name='near', description='Returns the five closest POI in the same dimmension as the input coordinates')
async def near(ctx):
	pass

@client.command(name='stats', description='Returns contribution and query information for a selected user')
async def stats(ctx):
	pass

@client.command(name='server', description='Returns server and player info at the time of request')
async def server(ctx):
	await ctx.message.delete()  # deletes users message to prevent buildup of commands

	server = MinecraftServer.lookup(minecraft_server_ip)
	status = server.status()

	num_players_online = status.players.online
	server_latency = status.latency  # in ms
	# users_connected provides a list of player names currently online
	if 'sample' in [ key for key in status.raw['players'] ]:
		users_connected = [ user['name'] for user in status.raw['players']['sample'] ]
	else:
		users_connected = []
	# server_desc provides the server description, if one exists
	if 'text' in [ key for key in status.raw['description'] ]:
		server_desc = status.raw['description']['text']

	emojis = {
	'server_status_logo': '\U0001F7E3',  # purple circle
	'online': '\U0001F7E2',  # green circle
	'offline': '\U000026AB',  # black circle 
	'next_arrow': '\U000027A1',
	'back_arrow': '\U00002B05',
	'close': '\U0000274C'
	}
	
	# messages
	server_info = discord.Embed(title=f'**{minecraft_server_ip} SERVER INFO**',\
			description=f"*{server_desc}*", color=0xBA74EE)
	server_info.set_author(name=client.user.name, icon_url= client.user.avatar_url)
	server_info.add_field(name=f"**Server Info**",\
            value=f'***Latency:*** {server_latency}ms\n***Total Members:*** n\n***Members online:*** {num_players_online}\n\
            ***Admin Online***: n\n\n\n\nPage 1/2', inline=True)

	member_status = discord.Embed(title=f'**{minecraft_server_ip} MEMBER STATUS**',\
			description=f"*{server_desc}*", color=0xBA74EE)
	member_status.set_author(name=client.user.name, icon_url= client.user.avatar_url)

	# https://stackoverflow.com/questions/51796005/reaction-pagination-button-forward-and-back-python
	message = ctx.author.mention
	embed = await ctx.send(message, embed=server_info)
	await embed.add_reaction(emojis['next_arrow'])
	await embed.add_reaction(emojis['close'])





''' Run Method '''
if __name__ == '__main__':
    client.run(token)