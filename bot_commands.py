import discord
from discord import app_commands, Embed
from discord.ext import commands
from typing import Optional
import random
import os
import aiohttp
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Configuration
ALLOWED_ROLE_IDS = {1320949785515003935, 1333154842595561542, 1354241093193044128}
ERLC_SERVER_KEY = os.getenv('ERLC_SERVER_KEY')
ERLC_API_URL = "https://api.policeroleplay.community/v1/server/command"
AUTO_ROLE_ID = 1332922436387078234  # Replace with your role ID
MOD_LOG_CHANNEL = 1354947504822812862  # Replace with your channel ID

def is_allowed():
    async def predicate(interaction: discord.Interaction):
        user_roles = {role.id for role in interaction.user.roles}
        if not user_roles.intersection(ALLOWED_ROLE_IDS):
            await interaction.response.send_message(
                "❌ You don't have permission to use this bot!",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

def register_commands(bot: commands.Bot):
    """Register all commands with the bot instance"""
    
    # Auto-role on member join
    @bot.event
    async def on_member_join(member):
        role = member.guild.get_role(AUTO_ROLE_ID)
        if role:
            try:
                await member.add_roles(role)
                print(f"Assigned auto-role to {member.display_name}")
            except Exception as e:
                print(f"Failed to assign auto-role: {e}")

    # ======================
    # MODERATION COMMANDS
    # ======================
    
    @bot.tree.command(name="kick", description="Kick a member from the server")
    @app_commands.describe(
        member="Member to kick",
        reason="Reason for kick"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    @is_allowed()
    async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        try:
            if member.top_role.position >= interaction.user.top_role.position:
                return await interaction.response.send_message("❌ You can't kick members with equal/higher roles!", ephemeral=True)
            
            await member.kick(reason=reason)
            
            embed = Embed(
                title="Member Kicked",
                description=f"{member.mention} was kicked by {interaction.user.mention}",
                color=0xFFA500
            )
            embed.add_field(name="Reason", value=reason)
            
            log_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                await log_channel.send(embed=embed)
            
            await interaction.response.send_message(f"✅ {member.display_name} has been kicked.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick member: {str(e)}", ephemeral=True)

    @bot.tree.command(name="ban", description="Ban a member from the server")
    @app_commands.describe(
        member="Member to ban",
        reason="Reason for ban",
        delete_days="Days of messages to delete (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    @is_allowed()
    async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided", delete_days: int = 0):
        try:
            if member.top_role.position >= interaction.user.top_role.position:
                return await interaction.response.send_message("❌ You can't ban members with equal/higher roles!", ephemeral=True)
            
            await member.ban(reason=reason, delete_message_days=delete_days)
            
            embed = Embed(
                title="Member Banned",
                description=f"{member.mention} was banned by {interaction.user.mention}",
                color=0xFF0000
            )
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Messages Deleted", value=f"{delete_days} days")
            
            log_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                await log_channel.send(embed=embed)
            
            await interaction.response.send_message(f"✅ {member.display_name} has been banned.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban member: {str(e)}", ephemeral=True)

    # ======================
    # YOUR ORIGINAL COMMANDS
    # ======================
    
    @bot.tree.command(name="addrole", description="Assign role to user")
    @app_commands.describe(user="User to receive role", role="Role to assign")
    @app_commands.checks.has_permissions(manage_roles=True)
    @is_allowed()
    async def addrole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        try:
            if not interaction.guild.me.guild_permissions.manage_roles:
                return await interaction.response.send_message("❌ I don't have permission to manage roles!", ephemeral=True)
            if role.position >= interaction.guild.me.top_role.position:
                return await interaction.response.send_message("❌ That role is higher than my highest role!", ephemeral=True)
            await user.add_roles(role)
            await interaction.response.send_message(f"✅ Added {role.mention} to {user.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to add role: {str(e)}", ephemeral=True)

    @bot.tree.command(name="removerole", description="Remove role from user")
    @app_commands.describe(user="User to remove role from", role="Role to remove")
    @app_commands.checks.has_permissions(manage_roles=True)
    @is_allowed()
    async def removerole(interaction: discord.Interaction, user: discord.Member, role: discord.Role):
        try:
            if role not in user.roles:
                return await interaction.response.send_message(f"❌ {user.display_name} doesn't have {role.name} role!", ephemeral=True)
            await user.remove_roles(role)
            await interaction.response.send_message(f"✅ Removed {role.mention} from {user.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to remove role: {str(e)}", ephemeral=True)

    @bot.tree.command(name="nick", description="Change a user's nickname")
    @app_commands.describe(user="User to rename", nickname="New nickname (leave empty to reset)")
    @app_commands.checks.has_permissions(manage_nicknames=True)
    @is_allowed()
    async def nick(interaction: discord.Interaction, user: discord.Member, nickname: Optional[str] = None):
        try:
            if not interaction.guild.me.guild_permissions.manage_nicknames:
                return await interaction.response.send_message("❌ I don't have nickname management permissions!", ephemeral=True)
            if user.top_role.position >= interaction.guild.me.top_role.position:
                return await interaction.response.send_message("❌ Cannot modify users with higher/equal roles!", ephemeral=True)
            await user.edit(nick=nickname)
            action = "reset" if nickname is None else f"changed to '{nickname}'"
            await interaction.response.send_message(f"✅ Successfully {action} nickname for {user.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to change nickname: {str(e)}", ephemeral=True)

    @bot.tree.command(name="echo", description="Make the bot repeat a message")
    @app_commands.describe(
        message="The message to repeat",
        channel="Channel to send to (default: current channel)",
        silent="If true, only you see the confirmation"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    @is_allowed()
    async def echo(interaction: discord.Interaction, message: str, channel: Optional[discord.TextChannel] = None, silent: bool = False):
        try:
            target = channel or interaction.channel
            if not target.permissions_for(interaction.guild.me).send_messages:
                return await interaction.response.send_message("❌ I don't have permissions to send messages there!", ephemeral=True)
            await target.send(message)
            await interaction.response.send_message(
                f"✅ Message sent to {target.mention}" + (" (silently)" if silent else ""),
                ephemeral=silent
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to send message: {str(e)}", ephemeral=True)

    @bot.tree.command(name="ship", description="Calculate love compatibility")
    @app_commands.describe(user1="First person", user2="Second person")
    async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
        score = random.randint(0, 100)
        if score >= 50:
            message = f"💖 Maybe?** {user1.mention} and {user2.mention} are {score}% Mayvbe compatible! 💘"
        if score <= 50:
            message = f"💔 **NO MATCH...** {user1.mention} and {user2.mention} are only {score}% compatible. 😢"
        if score >=75:
            message = f"💖 **MATCH!** {user1.mention} and {user2.mention} are {score}% compatible! 💘"
            await interaction.response.send_message(message)

    @bot.tree.command(name="erlc", description="Execute ER:LC in-game command")
    @app_commands.describe(command="The command to execute (include ':')")
    @is_allowed()
    async def erlc(interaction: discord.Interaction, command: str):
        try:
            if not command.startswith(':'):
                command = f":{command}"

            headers = {
                "Server-Key": ERLC_SERVER_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "command": command
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ERLC_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=5
                ) as response:
                    if response.status == 200:
                        await interaction.response.send_message(
                            f"✅ Executed `{command}`",
                            ephemeral=True
                        )
                    else:
                        error = await response.text()
                        await interaction.response.send_message(
                            f"❌ API Error {response.status}: {error[:200]}",
                            ephemeral=True
                        )
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {str(e)}", ephemeral=True)

        # ======================
    # INFRACTION COMMAND
    # ======================
    @bot.tree.command(name="infraction", description="Issue a staff infraction")
    @app_commands.describe(
        user="User receiving the infraction",
        punishment="Type of punishment",
        reason="Reason for infraction",
        approved_by="Staff member approving this"
    )
    @app_commands.choices(punishment=[
        app_commands.Choice(name="Demotion", value="Demotion"),
        app_commands.Choice(name="Warning", value="Warning"),
        app_commands.Choice(name="Strike", value="Strike"),
        app_commands.Choice(name="Staff Blacklist + Demotion", value="Staff Blacklist + Demotion")
    ])
    @app_commands.checks.has_permissions(manage_roles=True)
    @is_allowed()
    async def infraction(
        interaction: discord.Interaction,
        user: discord.Member,
        punishment: app_commands.Choice[str],
        reason: str,
        approved_by: str
    ):
        """Create an infraction notice"""
        try:
            embed = discord.Embed(
                title="New Horizons Border Roleplay",
                color=0xFF0000  # Red color for infractions
            )
            embed.description = (
                f"**Punishment:** {punishment.value}\n\n"
                f"{user.mention}\n"
                f"**Reason:** {reason}\n\n"
                f"**How to appeal:** To appeal this infraction you can create a IA ticket.\n\n"
                f"**Infraction Approved by:** {approved_by}"
            )
            
            # Send to mod logs if channel exists
            log_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL)
            if log_channel:
                await log_channel.send(embed=embed)
            
            await interaction.response.send_message(
                f"✅ Infraction issued for {user.mention}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to issue infraction: {str(e)}",
                ephemeral=True
            )

        # ======================
    # SERVER STARTUP COMMAND
    # ======================
    @bot.tree.command(name="ssu", description="Announce server startup")
    @is_allowed()
    async def ssu(interaction: discord.Interaction):
        """Send server startup announcement"""
        try:
            # Replace with your actual announcement channel ID
            ANNOUNCEMENT_CHANNEL_ID = 1333147511489298595  
            NOTIFICATION_ROLE_ID = 1332922436387078234  
            channel = interaction.guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)
            role = interaction.guild.get_role(NOTIFICATION_ROLE_ID)

            if not channel:
                return await interaction.response.send_message(
                    "❌ Announcement channel not found!",
                    ephemeral=True
                )
            
            embed = discord.Embed(
                title="🚀 Server Startup Initiated",
                description="@members The server is now starting up!",
                color=0x00FF00  # Green color
            )
            embed.add_field(
                name="Status Updates",
                value="[Click to join server](https://policeroleplay.community/join/NHB)",
                inline=False
            )
            embed.set_footer(text=f"Initiated by {interaction.user.display_name}")
            
            message_content = role.mention if role else ""
            await channel.send(content=message_content, embed=embed)

            await channel.send(embed=embed)
            await interaction.response.send_message(
                "✅ Server startup announced!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to send announcement: {str(e)}",
                ephemeral=True
            )

    # ======================
    # RIDE ALONG COMMAND
    # ======================
    TRAINER_ROLE_ID = 1355369535016013965  # Replace with your actual trainer role ID
    TRAINEE_ROLE_ID = 1355370308453924944  # Replace with your trainee role ID
    RIDEALONG_CHANNEL_ID = 1355378809502826606  # Replace with your announcement channel ID

    @bot.tree.command(name="ridealong", description="Start a new ride along session")
    @app_commands.checks.has_role(TRAINER_ROLE_ID)  # Only trainer role can use this
    async def ridealong(interaction: discord.Interaction):
        """Create a ride along announcement with trainee ping"""
        try:
            # Check if user has trainer role (additional check beyond the decorator)
            if not any(role.id == TRAINER_ROLE_ID for role in interaction.user.roles):
                return await interaction.response.send_message(
                    "❌ You must be a trainer to use this command!",
                    ephemeral=True
                )
            
            import pytz
            from datetime import datetime

            # Get current time in CST
            cst = pytz.timezone('America/Chicago')
            current_time = datetime.now(cst).strftime('%I:%M %p CST')
            
            # Create embed with exact formatting
            embed = discord.Embed(color=0x5865F2)  # Using your server's blue color
            embed.description = (
                "**# New Horizons Border Roleplay Ride Along**\n\n"
                "You must be accepted in the group. If you are go on the sheriff team then "
                "unequip all weapons, go to the briefing room, wait for your trainer.\n\n"
                f"**## Hosted by {interaction.user.display_name}**\n"
                f"**## Started at {current_time}**"
            )
            
            # Get channel and role objects
            channel = interaction.guild.get_channel(RIDEALONG_CHANNEL_ID)
            trainee_role = interaction.guild.get_role(TRAINEE_ROLE_ID)
            
            if not channel:
                return await interaction.response.send_message(
                    "❌ Ride along channel not found!",
                    ephemeral=True
                )
            
            if not trainee_role:
                return await interaction.response.send_message(
                    "❌ Trainee role not found!",
                    ephemeral=True
                )
            
            # Send message with trainee ping and embed
            message = await channel.send(
                content=trainee_role.mention,
                embed=embed
            )
            await message.add_reaction("✅")  # Auto-add checkmark reaction
            
            await interaction.response.send_message(
                f"✅ Ride along session announced in {channel.mention}!",
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to create ride along: {str(e)}",
                ephemeral=True
            )

    bot.tree.command(name="rizzcalculator", description="The rizz calculator is to see if you have no rizz")
    app_commands.describe (user1="First person")
    async def rizzcalculator(interaction: discord.Interaction, user1: discord.Member):
        score = random.randint(0, 100)
        if score <= 75:
            message= "YOU GOT MAJOR SKIBIDI RIZZ😍. ALL THEM GIRLS WANT YOU."
        if score <= 50:
            message= "You have mediocre rizz. Some girls want you."
        if score >= 50:
            message= "No Rizz, No girls.:("
        if score >= 25:
            message= "ITS CRAZY HOW YOU HAVE NO RIZZ AT ALL..."
    
    print(f"Registered {len(bot.tree.get_commands())} commands")
