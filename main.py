import asyncio
import os

import discord
from discord.ext import commands

from libs import prefix, botutils
from libs.config import parse_config

config = parse_config("./config.toml")

parser = prefix.PrefixParser(default=config['default_prefix'])

bot = commands.Bot(command_prefix=parser, case_insensitive=True, intents=discord.Intents.all(),
				   allowed_mentions=discord.AllowedMentions(everyone=False), owner_id=config['owner_id'])


@bot.event
async def on_ready():
	log = bot.get_channel(botutils.config["log_channel"])
	appinfo = await bot.application_info()
	botutils.log(f'"{bot.user.display_name}" is ready.')
	botutils.log(f"Created by {appinfo.owner}.")
	await log.send("Bot Started.")


async def main():
	async with bot:
		for filename in os.listdir('./cogs'):
			if filename.endswith('.py'):
				try:
					await bot.load_extension(f'cogs.{filename[:-3]}')
				except commands.errors.NoEntryPointError:
					botutils.log(f"{filename[:-3]} Failed to load...")
		# bot.loop.create_task(change_status_task())  # I've chosen to ignore this.
		await bot.start(TOKEN)


if __name__ == "__main__":
	if botutils.check_if_self_hosted():
		selfhost = input("Self Host? (y/n)\n> ")
		match selfhost.lower():
			case 'y':
				TOKEN = os.getenv("SELF_TOKEN")
			case _:
				TOKEN = os.getenv("GOLD_TOKEN")
	else:
		TOKEN = os.getenv("GOLD_TOKEN")
	if not TOKEN:
		TOKEN = input("Gøldbot's Token: ")
	asyncio.run(main())
