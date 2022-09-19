import os
import re

import discord
import googletrans
import oxford
import wikipedia
from discord.ext import commands
from googletrans.models import Detected  # Pain.
from iso639 import languages

from libs import botutils, urban, googlesearch


class Information(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot
		self.translator = googletrans.Translator()
		self.lang_dict = googletrans.LANGUAGES
		self.oxford = oxford.SyncClient(os.getenv('DICT_ID'), os.getenv('DICT_TOKEN'))
		botutils.log("Information Cog ready!")

	@staticmethod
	def get_dict_key(dictionary, value):
		key_list = list(dictionary.keys())
		value_list = list(dictionary.values())
		for listed_value in value_list:
			if listed_value == value:
				return key_list[value_list.index(value)]
		return value

	def detect_language(self, string):
		detected_lang = self.translator.detect(string)
		if isinstance(detected_lang, list):
			detected_lang = max(detected_lang, key=lambda lang: lang.confidence)

		elif isinstance(detected_lang.lang, list) and isinstance(detected_lang.confidence, list):
			detected_lang_tuple = max(zip(detected_lang.lang, detected_lang.confidence))
			detected_lang = Detected(lang=detected_lang_tuple[0], confidence=detected_lang_tuple[1])

		return detected_lang

	@commands.command(
		aliases=('definition', 'define'),
		description='Get the definition of a word.',
		extras={
			'example': 'auric'
		}
	)
	async def dictionary(self, ctx, *, query):
		error_embed = await botutils.error_template(ctx, f'Definition for "{query.title()}" not found.', send=False)

		message = await ctx.send("Getting definition...")
		try:
			definitions = self.oxford.define(query)
			emb = botutils.embed_template(
				title=f'Definition of "{query.title()}":', description=definitions[0].capitalize(),
				footer='Powered by Oxford Dictionary'
			)
		except oxford.Exceptions.WordNotFoundException:
			emb = error_embed

		await message.edit(content=None, embed=emb)

	@commands.command(
		aliases=("googleit", "googlesearch", "search"),
		description="Make a quick Google Search from Discord because you're too lazy to open your browser.",
		extras={
			"signature": "<Query>",
			"example": 'How to perform a Google Search from Discord'
		}
	)
	async def google(self, ctx, *, search_request):
		message = await ctx.send(f"Searching for `{search_request}`...")
		async with ctx.typing():
			results = []
			search_results = googlesearch.search(search_request, stop=10)
			for i, result in enumerate(search_results, start=1):
				results.append(f"`{i}.`\t**[{discord.utils.escape_markdown(result.title)}](<{result.link}>)**")

			output_str = '\n'.join(results)
			if not output_str:
				output_str = "**No results found.**"
			embed = botutils.embed_template("Google", output_str,
												icon="https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/Google_%22G%22_Logo.svg/1200px-Google_%22G%22_Logo.svg.png")
		await message.edit(content=None, embed=embed)
		try:
			os.remove(".google-cookie")
		except FileNotFoundError:
			pass

	@commands.command(
		aliases=("detect",),
		description='Detects the language of a quoted sentence.',
		extras={
			"example": "Hola, mi nombre es Gøldbot y hablo español"
		}
	)
	async def language(self, ctx: commands.Context, *, sentence):
		detected_lang = self.detect_language(sentence)

		lang_name = languages.get(alpha2=detected_lang.lang[:2]).name
		if detected_lang.confidence:
			await ctx.send(f'"{sentence}" is in **{lang_name}** (Certainty: `{round(detected_lang.confidence * 100)}%`).')
		else:
			await botutils.error_template(ctx, "No correct language detected.")

	@commands.command(
		description='Translates a sentence **surrounded by quotation marks.**',
		extras={
			'signature': '"<Sentence>" [Destination Language] [Source Language]',
			'example': '"Hola, ¿como estás?" japanese spanish'
		}
	)
	async def translate(self, ctx, translate_message, destination_language='en', source_language=None):
		destination_language = destination_language.lower()
		destination_language = self.get_dict_key(self.lang_dict, destination_language)

		if source_language is not None:
			source_language = source_language.lower()
			source_language = self.get_dict_key(self.lang_dict, source_language)
		else:
			source_language = self.detect_language(translate_message).lang
			source_language = source_language.lower()

		try:
			translated_text = discord.utils.escape_markdown(self.translator.translate(translate_message, src=source_language, dest=destination_language).text)
			await ctx.send(
				f'Translated from {self.lang_dict[source_language].capitalize()} to {self.lang_dict[destination_language].capitalize()}\n"{translated_text.capitalize()}".')
		except ValueError:
			await botutils.error_template(ctx, "Invalid language.")

	@commands.command(
		description="Searches a Wikipedia page with your search request.",
		extras={
			'example': 'gold'
		}
	)
	async def wikipedia(self, ctx, *, search_request):
		message = await ctx.send(f"Searching for {search_request}")
		async with ctx.typing():
			title = "Wikipedia"
			description = ""
			image = "https://i.imgur.com/7kT1Ydo.png"
			try:
				result = wikipedia.page(search_request)
				description = f"**[{result.title}]({result.url})**\n{result.summary[:300].strip()}..."
				try:
					image = result.images[0]
				except IndexError:
					pass
			except wikipedia.exceptions.DisambiguationError as e:
				i = 1
				for option in e.options[:9]:
					try:
						disamb_result = wikipedia.page(option, auto_suggest=False)
						if disamb_result.url != "":
							result = f"[{disamb_result.title}]({disamb_result.url})"
						else:
							result = f"~~{disamb_result}~~ **URL Not Found**"
					except wikipedia.exceptions.PageError:
						continue
					i += 1
					description += f"`{i}`: {result}\n"
			except wikipedia.exceptions.PageError:
				description = "Page not found."
			embed = botutils.embed_template(title, description, image=image, icon="https://i.imgur.com/FD1pauH.png")
		await message.edit(content=None, embed=embed)

	@commands.command(
		description="Makes a search on Urban Dictionary.",
		aliases=("urbadictionary",),
		extras={
			"example": "Noob"
		}
	)
	async def urban(self, ctx, *, query):
		pattern = re.compile("\[(.*?)]")
		async with ctx.typing():
			urban_definition = urban.define(query)
			try:
				urban_definition = urban_definition[0]
			except IndexError:
				await botutils.error_template(ctx, f'No definition found for "{query}"')
				return

			definition = urban_definition.definition.split(" ")
			if len(definition) > 70:
				definition = " ".join(definition[:70]) + " (...)"
			else:
				definition = " ".join(definition)

			example = urban_definition.example.split(" ")
			if len(example) > 70:
				example = " ".join(example[:70]) + " (...)"
			else:
				example = " ".join(example)

			hypertexts = re.findall(pattern, definition)
			hypertexts.extend(re.findall(pattern, example))
			hypertexts = {text: urban.define(text)[0].permalink for text in hypertexts}

			# Adds hypertexts to the definition and example strings.
			definition = re.sub(pattern, lambda x: f"{x.group()}({hypertexts[x.group(1)]})", definition)
			example = re.sub(pattern, lambda x: f"{x.group()}({hypertexts[x.group(1)]})", example)

			embed = botutils.embed_template(title=f'Definition for "{urban_definition.word.title()}"',
											description=f"{definition}\n\n**Example:**\n>>> {example}",
											footer="Powered by Urban Dictionary.")
			embed.url = urban_definition.permalink

		await ctx.send(embed=embed)


async def setup(bot):
	await bot.add_cog(Information(bot), override=True)
