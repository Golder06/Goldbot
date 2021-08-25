import asyncio
import os
import random

import discord
from discord.ext import commands

import prefix
from config import parse_config

config = parse_config("./config.toml")

origin_commands = ("datapacks", "<#843834879736283156>", "")

whitelisted_links = ["https://mediafire.com/", "https://github.com/", "https://planetminecraft.com/", "https://docs.google.com/"]
temp_white = whitelisted_links[:]
for link in temp_white:
	whitelisted_links.append(link.replace("://", "://www."))
temp_white.clear()
whitelisted_links = tuple(whitelisted_links)


def is_bot_owner(ctx):
	return ctx.author.id in config["owners_id"]


def is_origin_mod(ctx):
	return ctx.author.id in config["origins_mods"]


def check_if_self_hosted():
	try:
		with open(r"C:\Users\cient\OneDrive\Escritorio\Don't delete this text file.txt", "r") as f:
			str(f.read())
		return True
	except FileNotFoundError:
		return False


if check_if_self_hosted():
	parser = prefix.PrefixParser(default="g.")
else:
	parser = prefix.PrefixParser(default="g!")

intents = discord.Intents.all()
client = commands.Bot(command_prefix=parser, case_insensitive=True, intents=intents)
client.remove_command("help")

log = client.get_channel(config["log_channel"])
log2 = client.get_channel(838025060983767051)


@client.event
async def on_ready():
	global log
	global log2
	log = client.get_channel(config["log_channel"])
	log2 = client.get_channel(838025060983767051)


async def autodelete(message: discord.Message):
	content = message.content
	log_message = f"Message by {message.author.name}#{message.author.discriminator} ({message.author.id}) deleted in #datapacks.\nMessage: \n> {content}\nAttachment List Length: {len(message.attachments)}"
	if len(message.attachments) != 0:
		log_message += f"\nAttachment type: {message.attachments[0].content_type}"
	if message.reference:
		log_message += f"\nReferenced Message: {message.reference.jump_url}"
	await discord.Message.delete(message, delay=0)
	if message.content.startswith("!"):
		await message.author.send("Your message in <#749571272635187342> was automatically removed because it was a command. Please use commands in <#843834879736283156>.")
	else:
		await message.author.send("Your message in <#749571272635187342> was automatically removed because it did not contain a file or a link. (From the Origins Mod server)\n\nPD: If your message got deleted yet you had a link or a datapack, please contact Golder06#7041\nPD2: Please remember that the file has to be a `.zip` file.")
	if len(log_message) <= 2000:
		await log.send(log_message)
		await log2.send(log_message)
	else:
		with open('temp.txt', 'w') as f:
			f.write(content)
		with open('temp.txt', 'rb') as f:
			temp = discord.File(f)
		log_message = f"Message by {message.author.name}#{message.author.discriminator} ({message.author.id}) deleted in #datapacks.\nThe message would make the log exceed the 2000 character limit. Sending as Text Document:"
		if len(message.attachments) != 0:
			log_message += f"\nAttachment type: {message.attachments[0].content_type}"
		if message.reference:
			log_message += f"\nReferenced Message: {message.reference.jump_url}"
		await log.send(log_message, file=temp)
		with open('temp.txt', 'rb') as f:
			temp = discord.File(f)
		await log2.send(log_message, file=temp)
		await asyncio.sleep(1)
		os.remove('temp.txt')


@client.event
async def on_message(message: discord.Message):
	if message.guild is None and not message.author.bot:
		modmail = False
		for guild in message.author.mutual_guilds:
			if guild.id == 734127708488859831:
				modmail = True
				break
		if modmail:
			if message.content.startswith("$"):
				channel = client.get_channel(814542424793153556)
				embed = discord.Embed(title=f"{message.author.name}#{message.author.discriminator}")
				embed.set_author(name=message.author.id)
				embed.add_field(name="Description:", value=message.content.lstrip('$'))
				mail_message = await channel.send(embed=embed)
				await message.channel.send("Your message has been sent to the Origins Server's Mods.")

				def reply_check(msg):
					try:
						res = msg.reference.message_id == mail_message.id and msg.channel.id == 814542424793153556
					except AttributeError:
						res = False
					return res

				reply = await client.wait_for('message', check=reply_check)
				await message.channel.send(f"{reply.content}")
				await reply.add_reaction("\U00002705")
			else:
				await message.channel.send("If you want to contact the Origins Server's Modmail, you have to use `$` as a prefix to your message.")
	elif message.channel.id == 749571272635187342:  # If the message is in the #datapacks channel and isn't made by a user with administrator permissions it'll check if it has a .zip file attached to it or if it has a link. If it doesn't, the message gets deleted
		if message.author.bot:
			await discord.Message.delete(message, delay=0)
		if is_origin_mod(message):
			pass
		if len(message.attachments) != 0:
			if any(link in message.content for link in whitelisted_links):
				return
			elif message.attachments[0].content_type != "application/zip":
				await autodelete(message)
		else:
			if not any(link in message.content for link in whitelisted_links):
				await autodelete(message)
	elif message.content.startswith("!<#843834879736283156>"):
		if message.channel.id != 843834879736283156:
			serious = client.get_emoji(821796259333537813)
			try:
				await message.reference.resolved.reply(f"Please use your commands in <#843834879736283156>, so the other channels don't get messy! {serious}")
			except AttributeError:
				await message.channel.send(f"Please use your commands in <#843834879736283156>, so the other channels don't get messy! {serious}")
		else:
			await message.reply("This message is already in <#843834879736283156>...")
	else:
		if message.guild.id == 734127708488859831 and not is_origin_mod(message):  # If the message is in the Origins Server, it won't try to process it as a command. (Don't think it'd be a good idea to let people use Gøldbot's commands there.)
			if message.content.startswith("g!"):
				# if message.content.lstrip("g!").startswith(origin_commands):
				if message.channel.id == 843834879736283156:
					await message.reply(f"Gøldbot commands have been disabled in this server. {random.choices(['~~But you can always add me to your server with this link wink wink <https://discord.com/api/oauth2/authorize?client_id=573680244213678081&permissions=8&scope=bot>~~', ''], [1,10])[0]}")
				else:
					await message.reply("Gøldbot commands have been disabled in this server.")
		else:
			await client.process_commands(message)


def embed_template(ctx, title=None, description=None, footer="", image: str = "", icon: str = ""):
	embed = discord.Embed(description=description, color=random.randint(0, 0xffffff))
	if icon != "":
		embed.set_author(name=title, icon_url=icon)
	else:
		embed.set_author(name=title)
	embed.set_footer(
		text=f"{footer}\nTo see more information about a specific command, type {ctx.prefix}help <command>.\nGøldbot was created by Golder06#7041.",
		icon_url="https://i.imgur.com/ZgG8oJn.png")
	embed.set_thumbnail(url="https://i.imgur.com/8bOl5gU.png")
	if image != "":
		embed.set_image(url=image)
	return embed


@client.command(name="help")
async def _help(ctx, command=None):
	if command is None:
		title = "Commands"
		with open("help_texts/general_help.txt", "r", encoding='utf-8') as file:
			help_text = file.read()
		with open("help_texts/mod_help.txt", "r", encoding='utf-8') as file:
			mod_text = file.read()
		with open("help_texts/owner_help.txt", "r", encoding='utf-8') as file:
			owner_text = file.read()
		if ctx.author.guild_permissions.administrator:
			help_text += mod_text
		if is_bot_owner(ctx):
			help_text += owner_text
	else:
		command = command.lower()
		try:
			title = command.capitalize()
			with open(f"help_texts/specific_help/{command}.txt", encoding='utf-8') as file:
				help_text = file.read()
		except FileNotFoundError:
			title = "Error!"
			help_text = "Command not found."
	embed = embed_template(ctx, title, help_text.format(prefix=ctx.prefix), "\n<>=Necessary, []=optional.")
	await ctx.send(embed=embed)


@client.command()
async def prefix(ctx, new_prefix=None):
	perm = ctx.author.guild_permissions.administrator
	if new_prefix is None:
		await ctx.send(f"Server's prefix currently set to `{ctx.prefix}`.")
	else:
		if perm:
			sv = str(ctx.guild.id)
			parser.update(sv, new_prefix)
			await ctx.send(f"Prefix changed to `{new_prefix}`!")
		else:
			raise commands.CheckFailure

if __name__ == "__main__":
	for filename in os.listdir('./cogs'):
		if filename.endswith('.py'):
			client.load_extension(f'cogs.{filename[:-3]}')

	if check_if_self_hosted():
		TOKEN = "NzkxMDY2MzQ5MjUzODIwNDc4.X-Jv8g.bEiIuTfej1rshqehrR_v1T5rvsk"
	else:
		TOKEN = "NTczNjgwMjQ0MjEzNjc4MDgx.XMuXXA.ywRBVp3AnGQjCiRwjYJsk3Oryk4"

	client.run(TOKEN)
