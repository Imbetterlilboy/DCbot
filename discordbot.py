import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'=== {bot.user} is online ===')
    
    # 1. Clear ALL existing commands
    bot.tree.clear_commands(guild=None)
    print("Cleared all existing commands")
    
    # 2. Re-register commands
    from bot_commands import register_commands  # Changed from setup to register_commands
    register_commands(bot)  # Now calling it directly without await
    
    # 3. Force fresh sync
    try:
        # For testing server (instant)
        TEST_GUILD = discord.Object(id=1320949220114432030)  # REPLACE THIS
        bot.tree.copy_global_to(guild=TEST_GUILD)
        await bot.tree.sync(guild=TEST_GUILD)
        
        # For all servers (may take 1 hour)
        synced = await bot.tree.sync()
        
        print(f"=== SYNCED {len(synced)} COMMANDS ===")
        for cmd in synced:
            print(f"/{cmd.name}")
    except Exception as e:
        print(f"!!! SYNC FAILED: {e}")

@bot.command()
@commands.is_owner()
async def nuclear_sync(ctx):
    """FORCE RECREATE ALL COMMANDS"""
    bot.tree.clear_commands(guild=None)
    from bot_commands import register_commands  # Changed from setup
    register_commands(bot)  # Now calling it directly
    synced = await bot.tree.sync()
    await ctx.send(f"🔥 NUCLEAR SYNC COMPLETE ({len(synced)} commands)")

bot.run(TOKEN)