import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'=== {bot.user} is online ===')
    
    # Clear existing commands
    bot.tree.clear_commands(guild=None)
    print("Cleared all existing commands")
    
    # Register commands
    try:
        from bot_commands import register_commands
        register_commands(bot)
        
        # Sync commands
        TEST_GUILD = discord.Object(id=1320949220114432030)  # Replace with your server ID
        bot.tree.copy_global_to(guild=TEST_GUILD)
        await bot.tree.sync(guild=TEST_GUILD)
        
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands:")
        for cmd in synced:
            print(f"- /{cmd.name}")
    except Exception as e:
        print(f"Error during startup: {e}")

@bot.command()
@commands.is_owner()
async def nuclear_sync(ctx):
    """Force recreate all commands"""
    try:
        bot.tree.clear_commands(guild=None)
        from bot_commands import register_commands
        register_commands(bot)
        synced = await bot.tree.sync()
        await ctx.send(f"🔥 Nuclear sync complete! ({len(synced)} commands)")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# Start the bot
keep_alive()
try:
    bot.run(TOKEN)
except discord.errors.LoginFailure:
    print("Invalid token! Please check your DISCORD_TOKEN in .env")
except Exception as e:
    print(f"Bot crashed: {e}")
