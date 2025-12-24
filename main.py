import asyncio
import os
import secrets
import discord
from discord import app_commands
from discord.ext import commands
from flask import Flask, redirect, request, session
import threading
import aiohttp
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
CLIENT_ID = os.getenv("CLIENT_ID", "").strip()
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "").strip()
REDIRECT_URI = os.getenv("REDIRECT_URI", "https://{your-repl-url}.repl.co/callback").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", secrets.token_hex(32))

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
app.secret_key = SESSION_SECRET

@bot.event
async def on_ready():
    if bot.user:
        print(f'Bot is ready! Logged in as {bot.user.name} (ID: {bot.user.id})')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    print('------')

@bot.command(name="scan")
async def scan(ctx, *, username: str = None):
    if username is None:
        await ctx.send("Usage: /scan \"username\"")
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You need admin permissions to use this command.")
        return
    
    username = username.strip('"').strip()
    
    if not ctx.guild:
        await ctx.send("This command can only be used in a server!")
        return
    
    target_member = None
    for member in ctx.guild.members:
        if member.name.lower() == username.lower() or member.display_name.lower() == username.lower():
            target_member = member
            break
    
    if not target_member:
        await ctx.send(f"User '{username}' not found in this server.")
        return
    
    if target_member.bot:
        await ctx.send("Cannot scan bot users.")
        return
    
    mutual_guilds = []
    for guild in bot.guilds:
        if guild.get_member(target_member.id):
            mutual_guilds.append(guild)
    
    if not mutual_guilds:
        chunks = [f"**{target_member.name}** is only in this server (or I'm not in their other servers)."]
    else:
        guild_lines = [f"**{guild.name}** (ID: {guild.id})" for guild in mutual_guilds]
        server_list_message = f"**{target_member.name}**'s mutual servers with the bot:\n\n" + "\n".join(guild_lines)
        
        if len(server_list_message) > 1900:
            chunks = []
            current = f"**{target_member.name}**'s mutual servers with the bot:\n\n"
            for line in guild_lines:
                if len(current) + len(line) + 1 > 1900:
                    chunks.append(current)
                    current = line + "\n"
                else:
                    current += line + "\n"
            if current:
                chunks.append(current)
        else:
            chunks = [server_list_message]
    
    try:
        command_user = ctx.author
        for chunk in chunks:
            await command_user.send(chunk)
            await asyncio.sleep(0.5)
        
        await ctx.send(f"Sent {target_member.name}'s server list to your DMs!")
    except discord.Forbidden:
        await ctx.send("I cannot send you a DM. Please enable DMs from server members in your privacy settings.")
    except Exception as e:
        print(f"Error sending DM: {e}")
        await ctx.send("An error occurred while sending the DM.")

@app.route("/")
def home():
    return f'<h1>Discord OAuth Bot</h1><p><a href="/login">Click here to login with Discord</a></p>'

@app.route("/login")
def login():
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    oauth_url = (
        f"https://discord.com/api/oauth2/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=identify+guilds&"
        f"state={state}"
    )
    return redirect(oauth_url)

@app.route("/callback")
async def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code:
        return "<h1>Error</h1><p>No authorization code provided</p>", 400
    
    stored_state = session.pop('oauth_state', None)
    if not stored_state or state != stored_state:
        return "<h1>Error</h1><p>Invalid state parameter. Please try logging in again.</p>", 400

    try:
        async with aiohttp.ClientSession() as http_session:
            token_data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': REDIRECT_URI,
                'scope': 'identify guilds'
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            async with http_session.post('https://discord.com/api/v10/oauth2/token', data=token_data, headers=headers) as token_resp:
                if token_resp.status != 200:
                    error_data = await token_resp.json()
                    error_msg = error_data.get("error_description", "Failed to exchange authorization code")
                    return f"<h1>Error</h1><p>OAuth error: {error_msg}</p>", 400
                token_json = await token_resp.json()
            
            access_token = token_json.get("access_token")
            if not access_token:
                return f"<h1>Error</h1><p>No access token received from Discord</p>", 400
            
            auth_headers = {"Authorization": f"Bearer {access_token}"}
            async with http_session.get("https://discord.com/api/v10/users/@me", headers=auth_headers) as user_resp:
                if user_resp.status != 200:
                    return f"<h1>Error</h1><p>Failed to fetch user information from Discord</p>", 400
                user_data = await user_resp.json()
            
            user_id = user_data.get("id")
            username = user_data.get("username", "User")
            if not user_id:
                return f"<h1>Error</h1><p>Failed to get user ID from Discord</p>", 400
            user_id = int(user_id)

            async with http_session.get("https://discord.com/api/v10/users/@me/guilds", headers=auth_headers) as guilds_resp:
                if guilds_resp.status != 200:
                    return f"<h1>Error</h1><p>Failed to fetch server list from Discord</p>", 400
                guilds = await guilds_resp.json()

        if not guilds:
            messages_to_send = "You don't belong to any servers."
        else:
            guild_lines = [f"**{g.get('name', 'Unknown')}** (ID: {g.get('id', 'N/A')})" for g in guilds]
            dm_messages = []
            current_message = "Here are the servers you belong to:\n\n"
            
            for line in guild_lines:
                if len(current_message) + len(line) + 1 > 1900:
                    dm_messages.append(current_message)
                    current_message = line + "\n"
                else:
                    current_message += line + "\n"
            
            if current_message:
                dm_messages.append(current_message)
            messages_to_send = dm_messages

        async def send_dms(user_id, messages):
            user = bot.get_user(user_id)
            if not user:
                user = await bot.fetch_user(user_id)
            try:
                if isinstance(messages, list):
                    for msg in messages:
                        await user.send(msg)
                        await asyncio.sleep(0.5)
                else:
                    await user.send(messages)
                print(f"Successfully sent DM to user {user_id}")
            except discord.Forbidden:
                print(f"Cannot send DM to user {user_id} - DMs are disabled")
                raise
            except Exception as e:
                print(f"Failed to send DM to user {user_id}: {e}")
                raise

        loop = bot.loop
        future = asyncio.run_coroutine_threadsafe(send_dms(user_id, messages_to_send), loop)
        try:
            future.result(timeout=30)
            server_count = len(guilds) if guilds else 0
            return f"<h1>Success!</h1><p>Hello {username}! I have sent a list of your {server_count} server(s) to your Discord DMs!</p>"
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
