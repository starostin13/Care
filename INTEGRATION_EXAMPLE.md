# Example: How to Add Admin Command to Trigger Inactive Player Transfer

This file shows how to integrate the inactive player transfer feature as an admin command in the bot.

## Add this to handlers.py

```python
async def admin_check_inactive_players(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to manually check and transfer inactive players.
    Usage: /check_inactive_players [threshold]
    
    Args:
        threshold (optional): Multiplier for average inactivity (default: 2.0)
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return
    
    # Get threshold from command args, default to 2.0
    threshold = 2.0
    if context.args and len(context.args) > 0:
        try:
            threshold = float(context.args[0])
            if threshold <= 0:
                await update.message.reply_text("❌ Threshold must be a positive number.")
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid threshold value. Using default (2.0).")
            threshold = 2.0
    
    # Send initial message
    await update.message.reply_text(
        f"🔍 Checking for inactive players (threshold: {threshold}x alliance average)...\n"
        "This may take a moment."
    )
    
    try:
        # Run the check
        result = await warmaster_helper.check_and_transfer_inactive_players(
            context, 
            threshold_multiplier=threshold
        )
        
        if result['success']:
            transfers_count = result['transfers_count']
            
            if transfers_count == 0:
                response = "✅ Check complete. No inactive players found."
            else:
                response = f"✅ Check complete. Transferred {transfers_count} player(s):\n\n"
                for transfer in result['transfers']:
                    response += (
                        f"• {transfer['player_name']}\n"
                        f"  From: {transfer['from_alliance']}\n"
                        f"  To: {transfer['to_alliance']}\n"
                        f"  Inactive: {transfer['days_inactive']:.1f} days\n\n"
                    )
            
            await update.message.reply_text(response)
        else:
            await update.message.reply_text(
                f"❌ Error during check: {result.get('error', 'Unknown error')}"
            )
    
    except Exception as e:
        logger.error(f"Error in admin_check_inactive_players: {e}")
        await update.message.reply_text(
            "❌ An error occurred while checking for inactive players. Check logs for details."
        )


async def admin_view_inactivity_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command to view inactivity statistics for all alliances.
    Usage: /inactivity_stats
    """
    user_id = update.effective_user.id
    
    # Check if user is admin
    is_admin = await sqllite_helper.is_user_admin(user_id)
    if not is_admin:
        await update.message.reply_text("⛔ This command is only available to administrators.")
        return
    
    try:
        alliances = await sqllite_helper.get_all_alliances()
        
        if not alliances:
            await update.message.reply_text("No alliances found.")
            return
        
        response = "📊 **Alliance Inactivity Statistics**\n\n"
        
        for alliance_id, alliance_name in alliances:
            avg_inactivity = await sqllite_helper.get_alliance_average_inactivity_days(alliance_id)
            player_count = await sqllite_helper.get_alliance_player_count(alliance_id)
            
            response += f"**{alliance_name}** (ID: {alliance_id})\n"
            response += f"  Members: {player_count}\n"
            
            if avg_inactivity is not None:
                response += f"  Avg Inactivity: {avg_inactivity:.1f} days\n"
            else:
                response += "  Avg Inactivity: No data\n"
            
            response += "\n"
        
        await update.message.reply_text(response)
    
    except Exception as e:
        logger.error(f"Error in admin_view_inactivity_stats: {e}")
        await update.message.reply_text("❌ An error occurred while fetching statistics.")
```

## Register the handlers

Add this to your bot application setup (usually in the main bot file):

```python
# Add admin command handlers
application.add_handler(CommandHandler("check_inactive_players", admin_check_inactive_players))
application.add_handler(CommandHandler("inactivity_stats", admin_view_inactivity_stats))
```

## Set up automatic scheduled checks (optional)

To automatically check for inactive players on a schedule:

```python
from telegram.ext import ApplicationBuilder

async def scheduled_inactive_player_check(context):
    """Scheduled job to check for inactive players weekly."""
    logger.info("Running scheduled inactive player check...")
    result = await warmaster_helper.check_and_transfer_inactive_players(
        context,
        threshold_multiplier=2.0  # Adjust as needed
    )
    
    if result['success'] and result['transfers_count'] > 0:
        logger.info(f"Scheduled check: Transferred {result['transfers_count']} inactive players")
    else:
        logger.info("Scheduled check: No inactive players found")

# In your application setup
application = ApplicationBuilder().token(config.crusade_care_bot_telegram_token).build()

# Run weekly (every 7 days)
application.job_queue.run_repeating(
    scheduled_inactive_player_check,
    interval=timedelta(days=7),  # Check once per week
    first=timedelta(hours=1)  # First run after 1 hour of bot start
)
```

## Usage Examples

### Check for inactive players with default threshold (2.0x):
```
/check_inactive_players
```

### Check with custom threshold (1.5x more strict):
```
/check_inactive_players 1.5
```

### Check with custom threshold (3.0x less strict):
```
/check_inactive_players 3.0
```

### View alliance inactivity statistics:
```
/inactivity_stats
```

## Notes

- Only admins (users with `is_admin = 1`) can use these commands
- The threshold determines how strict the inactivity detection is (lower = more strict)
- All transfers send notifications to relevant parties (admins, transferred player, alliance members)
- The scheduled check runs silently in the background
