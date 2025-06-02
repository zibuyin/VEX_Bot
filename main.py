from typing import Set, Any

import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import requests
from discord import app_commands
from numpy.f2py.capi_maps import lcb_map

load_dotenv()
token = os.getenv("DISCORD_TOKEN")
api_key = os.getenv("RE_API_KEY")  # 你的 Robot Events API Key

# token = input("DISCORD_TOKEN")
# api_key = input("RE_API_KEY")  # 你的 Robot Events API Key

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
logging.basicConfig(level=logging.DEBUG, handlers=[handler])

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Successfully synced {len(synced)} commands globally.")
    except Exception as e:
        print(f"Failed to sync commands: {e}")


#DEBUG
@bot.tree.command(name="hello", description="embed test")
@app_commands.describe(information="Enter the team number to search for")
async def hello(interaction: discord.Interaction, information: str):
    embed = discord.Embed(title="Hello World!", description=information)
    await interaction.response.send_message(embed=embed)



#Release
@bot.tree.command(name="fetch", description="Search for information about a VEX team")
@app_commands.describe(team_level="Enter the team level (V5 or IQ or U)", team_number="Enter the team number to search for")
async def fetch(interaction: discord.Interaction, team_level: str, team_number: str):
    team_number = team_number.upper()
    team_level = team_level.upper()  # 统一大写方便判断

    try:
        rec_name, level_int = {"V5": ("V5RC", 1),
                               "IQ": ("VIQRC", 41),
                               "U": ("VURC", 4)}[team_level]
    except KeyError:
        await interaction.response.send_message(
            "Invalid team level! Please enter one of: V5, IQ, U.",
            ephemeral=True
        )
        return
    rec_url = f"https://www.robotevents.com/teams/{rec_name}/{team_number}"


    await interaction.response.defer(thinking=True)

    fetch_url = f"https://www.robotevents.com/api/v2/teams?number={team_number}&program={level_int}&myTeams=false"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        fetch_data = requests.get(fetch_url, headers=headers, timeout=10)

        if fetch_data.status_code != 200:
            await interaction.followup.send(
                f"Failed to fetch data for team {team_number}. Status code: {fetch_data.status_code}",
                ephemeral=True
            )
            return

        data = fetch_data.json()
        if not data.get("data"):
            await interaction.followup.send(
                f"No information found for team {team_number}.",
                ephemeral=True
            )
            return

        team_info: dict = data["data"][0]
        team_name = team_info.get("team_name", "N/A")
        organization = team_info.get("organization", "N/A")

        location = team_info.get("location", {})
        city = location.get("city", "N/A")
        region = location.get("region", "N/A")
        country = location.get("country", "N/A")

        program = team_info.get("program", {}).get("name", "N/A")
        grade = team_info.get("grade", "N/A")
        registered = "Yes" if team_info["registered"] else "No"

        response_message = (
            f"**Team Information**\n"
            f"Team Number: {team_number}\n"
            f"Team Name: {team_name}\n"
            f"Organization: {organization}\n"
            f"Location: {city}, {region}, {country}\n"
            f"Program: {program}\n"
            f"Grade: {grade}\n"
            f"Registered: {registered}\n"
        )
        location: str = f"{city}, {region}, {country}" # String for all the locations

        embed = discord.Embed(title=f"VEX {team_level} Team {team_number}", url=rec_url ,color=discord.Color.red())
        embed.add_field(name="Team Name", value=team_name, inline=False)
        embed.add_field(name="Organization", value=organization, inline=False)
        embed.add_field(name="Location", value=location, inline=False)
        embed.add_field(name="Program", value=program, inline=False)
        embed.add_field(name="Grade", value=grade, inline=False)
        embed.add_field(name="Registered", value=registered, inline=False)

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send(
            f"An error occurred while fetching data: {e}",
            ephemeral=True
        )

bot.run(token, log_handler=handler, log_level=logging.DEBUG)