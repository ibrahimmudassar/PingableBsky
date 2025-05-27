import json
import os
import sys

import atproto
import gspread
import pandas as pd
from discord_webhook import DiscordEmbed, DiscordWebhook  # Added for Discord webhook
from environs import Env
from google.oauth2.service_account import Credentials

sys.stdout.reconfigure(encoding="utf-8")

# Load environment variables from .env file
env = Env()
env.read_env()


def discord_webhook_send(DISCORD_WEBHOOK_URL, post_text):
    if DISCORD_WEBHOOK_URL:
        webhook = DiscordWebhook(url=DISCORD_WEBHOOK_URL)
        embed = DiscordEmbed(
            description=post_text + " <@407021843246088204>",
            color="58acff",  # Hex color #58acff (light blue)
        )
        embed.set_author(name="Fabrizio Romano")
        embed.set_footer(text="Made by Ibrahim Mudassar")
        webhook.add_embed(embed)
        try:
            response = webhook.execute()
            if (
                response.status_code == 204 or response.status_code == 200
            ):  # Check for successful execution
                print(f"Successfully sent tweet to Discord: {post_text[:50]}...")
            else:
                print(
                    f"Error sending tweet to Discord: {response.status_code} - {response.content.decode()}"
                )
        except Exception as e:
            print(f"Error sending tweet to Discord: {e}")


# Authentication
client = atproto.Client()
USERNAME = os.getenv("BSKY_USERNAME")
PASSWORD = os.getenv("BSKY_PASSWORD")

if not USERNAME or not PASSWORD:
    raise ValueError(
        "BSKY_USERNAME and BSKY_PASSWORD environment variables must be set."
    )

try:
    client.login(USERNAME, PASSWORD)
    print("Login successful!")
except atproto.exceptions.InvalidPasswordError:
    print("Invalid username or password. Please check your credentials.")
    exit()
except Exception as e:
    print(f"An error occurred during login: {e}")
    exit()

# Get user posts
handle = "fabrizioromano.yopro20.com"  # Replace with the desired user handle

response = client.get_author_feed(handle, limit=10)  # Adjust limit as needed
posts = response.feed

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(
    json.loads(env("GS_CREDS")),
    scopes=scopes,
)

gc = gspread.authorize(creds)

sht1 = gc.open_by_key("12tZfqRsyxhAO08e7I-q_kOwmKo-kefbDV9IcUQ8dTHE").sheet1

sheet_data = sht1.get_all_values()
# new = pd.DataFrame(scraped_data)
seen = pd.DataFrame(sheet_data[1:], columns=sheet_data[0])

not_added_posts = []

for post_item in posts:
    post = post_item.post
    if post.record.text not in seen["tweet"].values and post.record.text not in not_added_posts:
        not_added_posts.append(post.record.text)

# Discord Webhook URL
DISCORD_WEBHOOK_URL = env("DISCORD_WEBHOOK_URL")

# Add new posts to the Google Sheet and send to Discord
if not_added_posts:
    # Prepare data for insertion
    new_rows = [[post] for post in not_added_posts]

    # Get the next empty row
    next_row = len(sheet_data) + 1

    # Add new posts to the sheet
    sht1.insert_rows(new_rows, next_row)

    for post_text in not_added_posts:
        # Original "here we go" check (can be kept or modified as needed)
        if "here we go" in post_text.lower():
            print(f"'Here we go' detected: {post_text}")

            discord_webhook_send(DISCORD_WEBHOOK_URL,post_text)
