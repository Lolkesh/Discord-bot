import asyncio
import os
import discord
from discord.ext import commands
from flask import Flask, redirect, request
import threading
import aiohttp
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://{your-repl-url}.repl.co/callback")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)

@bot.event
async def on_ready():
    if bot.user:
        print(f'Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

@app.route("/")
def home():
    return f'<h1>Discord OAuth Bot</h1><p><a href="/login">Click here to login with Discord</a></p>'

@app.route("/login")
def login():
    oauth_url = (
        f"https://discord.com/api/oauth2/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify+guilds"
    )
    return redirect(oauth_url)

@app.route("/callback")
async def callback():
    code = request.args.get('code')
    if not code:
        return "<h1>Error</h1><p>No authorization code provided</p>", 400

    try:
        async with aiohttp.ClientSession() as session:
            token_data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'scope': 'identify guilds'
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            async with session.post('https://discord.com/api/v10/oauth2/token', data=token_data, headers=headers) as token_resp:
                token_json = await token_resp.json()
            
            access_token = token_json.get("access_token")
            if not access_token:
                error_msg = token_json.get("error_description", "Unknown error")
                return f"<h1>Error</h1><p>Failed to get access token: {error_msg}</p>", 400
            
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            async with session.get("https://discord.com/api/v10/users/@me", headers=auth_headers) as user_resp:
                user_data = await user_resp.json()
            
            user_id = int(user_data.get("id"))
            username = user_data.get("username")

            async with session.get("https://discord.com/api/v10/users/@me/guilds", headers=auth_headers) as guilds_resp:
                guilds = await guilds_resp.json()

        guild_list = "\n".join([f"**{g['name']}** (ID: {g['id']})" for g in guilds])
        dm_message = f"Here are the servers you belong to:\n\n{guild_list}" if guild_list else "You don't belong to any servers."

        async def send_dm(user_id, message):
            user = bot.get_user(user_id)
            if not user:
                user = await bot.fetch_user(user_id)
            try:
                await user.send(message)
                print(f"Successfully sent DM to user {user_id}")
            except discord.Forbidden:
                print(f"Cannot send DM to user {user_id} - DMs are disabled")
                raise
            except Exception as e:
                print(f"Failed to send DM to user {user_id}: {e}")
                raise

        loop = bot.loop
        future = asyncio.run_coroutine_threadsafe(send_dm(user_id, dm_message), loop)
        try:
            future.result(timeout=10)
            return f"<h1>Success!</h1><p>Hello {username}! I have sent your server list to your Discord DMs!</p>"
        except discord.Forbidden:
            return f"<h1>Error</h1><p>I cannot send you a DM. Please enable DMs from server members in your Discord privacy settings.</p>", 403
        except Exception as e:
            print(f"Error sending DM: {e}")
            return f"<h1>Error</h1><p>Failed to send DM. Please try again later.</p>", 500

    except Exception as e:
        print(f"Error in callback: {e}")
        return f"<h1>Error</h1><p>An error occurred during authentication. Please try again.</p>", 500

def run_flask():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    if not all([DISCORD_BOT_TOKEN, CLIENT_ID, CLIENT_SECRET]):
        print("ERROR: Missing required environment variables!")
        print("Please set DISCORD_BOT_TOKEN, CLIENT_ID, and CLIENT_SECRET")
        exit(1)
    
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    print("Starting Discord bot...")
    if DISCORD_BOT_TOKEN:
        bot.run(DISCORD_BOT_TOKEN)
