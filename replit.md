# Discord OAuth Bot

## Overview
A Discord bot that uses OAuth2 to authenticate users via a web interface and sends them a DM listing all their Discord servers.

## Features
- Discord bot with OAuth2 integration
- Flask web server for OAuth callback handling
- Automatic DM sending with server list
- Secure credential management using environment variables

## Project Structure
- `main.py` - Main bot file with Discord bot and Flask server
- `.env` - Environment variables (not committed to git)
- `.env.example` - Example environment variables template
- `.gitignore` - Git ignore file for Python projects

## Setup Instructions
1. Create a Discord Application at https://discord.com/developers/applications
2. Create a bot and enable the "Message Content Intent" and "Server Members Intent"
3. Copy the Bot Token
4. Copy the Client ID and Client Secret from OAuth2 section
5. Add the redirect URI in OAuth2 settings: `https://your-repl-url.repl.co/callback`
6. Set environment variables:
   - `DISCORD_BOT_TOKEN` - Your bot token
   - `CLIENT_ID` - Your application client ID
   - `CLIENT_SECRET` - Your OAuth2 client secret
   - `REDIRECT_URI` - Your OAuth2 redirect URI

## Usage
1. Visit the web interface at your Repl URL
2. Click "Login with Discord"
3. Authorize the application
4. Receive a DM with your server list

## Technology Stack
- Python 3.11
- discord.py - Discord bot framework
- Flask - Web server
- aiohttp - Async HTTP requests
- python-dotenv - Environment variable management

## Recent Changes
- Initial project setup (November 7, 2025)
- Created Discord bot with OAuth2 integration
- Added Flask web server for OAuth callback
- Implemented DM sending functionality
