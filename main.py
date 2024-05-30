import os
import discord
from discord.ext import commands, tasks
import datetime
import pymongo
from aiohttp import web

# MongoDB connection
mongo_client = pymongo.MongoClient("mongodb+srv://privxtesav:PvinGNaju5JUCJs6@aya.9cymkwv.mongodb.net/")
db = mongo_client["discord_bot"]
user_collection = db["user_data"]

# Get the bot token from environment variables
TOKEN = os.getenv('tok')

# Create an instance of the bot with a specified command prefix
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True
intents.invites = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command('help')

# Load user data from MongoDB on bot startup
async def load_user_data():
    for user_data in user_collection.find():
        user_invites[user_data['_id']] = user_data['invites']
        user_messages[user_data['_id']] = user_data['messages']

# Tracking invites and messages
user_invites = {}
user_messages = {}
tasks_data = {}

# Reset invites and messages counts daily
@tasks.loop(hours=24)
async def reset_counts():
    user_invites.clear()
    user_messages.clear()

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id})')
    await bot.change_presence(activity=discord.Streaming(name="@ayala", url="https://www.twitch.tv/yourchannel"))
    reset_counts.start()
    await load_user_data()

# Event: On member join
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.channels, name='general')
    if channel:
        await channel.send(f'Welcome to the server, {member.mention}!')

# Event: On message
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = message.author.id
    user_messages[user_id] = user_messages.get(user_id, 0) + 1
    await bot.process_commands(message)

# Event: On invite create
@bot.event
async def on_invite_create(invite):
    inviter_id = invite.inviter.id
    user_invites[inviter_id] = user_invites.get(inviter_id, 0) + 1

# Command: Set tasks (Admin only)
@bot.command(name='settask', aliases=['st'], help='Set tasks for all members in the server. Usage: !settask [invites_required] [messages_required]')
@commands.has_permissions(administrator=True)
async def set_task(ctx, invites_required: int = 0, messages_required: int = 0):
    guild_id = ctx.guild.id
    tasks_data[guild_id] = {
        'invites_required': invites_required,
        'messages_required': messages_required
    }
    embed = discord.Embed(title="Task Set", description=f'Tasks set for all members in the server:\nInvites Required: {invites_required}\nMessages Required: {messages_required}', color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Command: Task info
@bot.command(name='task', help='Show tasks set for all members in the server.')
async def task(ctx):
    guild_id = ctx.guild.id
    tasks = tasks_data.get(guild_id, {})
    invites_required = tasks.get('invites_required', 0)
    messages_required = tasks.get('messages_required', 0)
    embed = discord.Embed(title="Task Info", description=f'Tasks set for all members in the server:\nInvites Required: {invites_required}\nMessages Required: {messages_required}', color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Command: Check invites per day
@bot.command(name='checkinvites', aliases=['ci'], help='Check total invites made by a user. Usage: !checkinvites [@user]')
async def check_invites(ctx, user: discord.User = None):
    user_id = user.id if user else ctx.author.id
    total_invites = user_invites.get(user_id, 0)
    embed = discord.Embed(title="Check Invites", description=f'Total invites made by {user.name if user else ctx.author.name}: {total_invites}', color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Command: Check messages per day
@bot.command(name='checkmessages', aliases=['cm'], help='Check total messages sent by a user. Usage: !checkmessages [@user]')
async def check_messages(ctx, user: discord.User = None):
    user_id = user.id if user else ctx.author.id
    total_messages = user_messages.get(user_id, 0)
    embed = discord.Embed(title="Check Messages", description=f'Total messages sent by {user.name if user else ctx.author.name}: {total_messages}', color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Command: Check user activity
@bot.command(name='check', help='Check user activity. Shows total messages sent and invites made by the user.')
async def check(ctx):
    user_id = ctx.author.id
    total_invites = user_invites.get(user_id, 0)
    total_messages = user_messages.get(user_id, 0)
    embed = discord.Embed(title="User Activity", description=f'Activity summary for {ctx.author.name}:\nMessages sent: {total_messages}\nInvites made: {total_invites}', color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Command: Help
@bot.command(name='help', help='Show list of available commands and their descriptions.')
async def help_command(ctx):
    embed = discord.Embed(title="Command List", description="List of available commands:")
    for command in bot.commands:
        embed.add_field(name=f"!{command.name}", value=command.help, inline=False)
    await ctx.send(embed=embed)

# Boost bot's ping
@bot.command()
async def ping(ctx):
    embed = discord.Embed(title="Pong!", description=f"Latency: {round(bot.latency * 1000)}ms", color=discord.Color.dark_theme())
    await ctx.send(embed=embed)

# Remove default help command
bot.remove_command('help')

# Command: Bot Information
@bot.command(name='botinfo', aliases=['info'], help='Display detailed information about the bot and its features.')
async def bot_info(ctx):
    embed = discord.Embed(title="Bot Information", description="Here's some detailed information about the bot and its features:", color=discord.Color.dark_theme())

    # Add sections for each feature with detailed explanations
    embed.add_field(name="1. Tracking Invites", value="This bot automatically tracks the invites made by each user in the server. It keeps a record of who invites whom, aiding in community management and moderation.", inline=False)
    embed.add_field(name="2. Tracking Messages", value="In addition to invites, the bot also tracks the number of messages sent by each user in the server. This feature can help recognize active members and encourage participation.", inline=False)
    embed.add_field(name="3. Setting Tasks", value="Administrators can set tasks for all members in the server, specifying the required number of invites and messages. This gamifies community engagement and incentivizes members to contribute actively.", inline=False)
    embed.add_field(name="4. Checking Invites and Messages", value="Users can easily check their own or others' total invites and messages using commands. This transparency promotes accountability and fosters healthy competition among members.", inline=False)
    embed.add_field(name="5. Checking User Activity", value="For self-awareness and comparison, users can check their activity summary, including total messages sent and invites made. This helps users track their progress and contributions to the community.", inline=False)
    embed.add_field(name="6. Bot's Ping", value="To ensure optimal performance, users can check the bot's latency with the `!ping` command. This feature helps users gauge the responsiveness of the bot and the Discord server.", inline=False)
    embed.add_field(name="7. Help Command", value="To facilitate ease of use, the bot provides a list of available commands and their descriptions with the `!help` command. Users can quickly access command details and functionalities.", inline=False)
    embed.add_field(name="8. Streaming Status", value="The bot's status is set to streaming with a link to Twitch. This adds personality to the bot and allows users to follow the provided link to engage further with the community or content.", inline=False)
    embed.add_field(name="9. Keeping Bot Alive", value="To ensure uninterrupted service, the bot is kept alive 24/7 using an HTTP server. This ensures that the bot remains online and responsive to user interactions at all times.", inline=False)
    embed.add_field(name="10. Additional Features", value="The bot may have additional features and functionalities not listed here. For updates and announcements, please refer to the server's announcements channel or contact the bot administrator.", inline=False)

    # Add additional information and usage tips
    embed.set_footer(text="Feel free to explore and use the bot's features! For more assistance, contact the bot administrator or refer to the documentation.")

    await ctx.send(embed=embed)

# Create HTTP server endpoint
async def keep_alive(request):
    return web.Response(text="I'm alive!")

# Setup and run HTTP server
app = web.Application()
app.router.add_get('/', keep_alive)

# Run the bot and the HTTP server concurrently
async def run_bot():
    await bot.start(TOKEN)

async def run_server():
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)  # Listen on port 8080
    await site.start()

async def main():
    await asyncio.gather(run_bot(), run_server())

# Run the bot and the HTTP server concurrently
import asyncio
if __name__ == "__main__":
    asyncio.run(main())
