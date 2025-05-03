import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, ContextTypes, filters

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define conversation states
PHONE, DESCRIPTION = range(2)

# Replace with your actual values
TELEGRAM_BOT_TOKEN = "7907696558:AAETzUUyY9fRfSavBWlDQ927wgJiw6BkIIM"
OWNER_USERNAME = "ismoilov1202"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask for phone number."""
    user = update.effective_user
    
    # Create keyboard with contact request button
    contact_keyboard = KeyboardButton(text="Share Contact", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[contact_keyboard]], one_time_keyboard=True)
    
    await update.message.reply_text(
        f"👋 Hello {user.first_name}! I'm your Customer Service Bot.\n\n"
        f"I'll help collect some information about your software needs and forward it to our team.\n\n"
        f"First, please share your phone number by clicking the button below.",
        reply_markup=reply_markup
    )
    
    return PHONE

async def phone_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the phone number and ask for service description."""
    user = update.effective_user
    contact = update.message.contact
    
    # Store phone number in user_data
    if contact and contact.phone_number:
        context.user_data['phone_number'] = contact.phone_number
        logger.info(f"Phone number received from {user.first_name}: {contact.phone_number}")
        
        await update.message.reply_text(
            f"Thanks for sharing your contact!\n\n"
            f"Now, please describe the software or service you need in detail. "
            f"Be as specific as possible to help us understand your requirements better."
        )
        
        return DESCRIPTION
    else:
        await update.message.reply_text("Please share your contact information using the button.")
        return PHONE

async def description_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the description and forward all information to the owner."""
    user = update.effective_user
    description = update.message.text
    
    # Store description in user_data
    context.user_data['description'] = description
    context.user_data['username'] = user.username or "Not provided"
    context.user_data['first_name'] = user.first_name
    context.user_data['last_name'] = user.last_name or ""
    
    # Prepare message for owner
    owner_message = (
        f"🔔 New Customer Request 🔔\n\n"
        f"👤 Name: {user.first_name} {user.last_name or ''}\n"
        f"🆔 Telegram Username: @{user.username or 'Not provided'}\n"
        f"📱 Phone Number: {context.user_data['phone_number']}\n\n"
        f"📝 Service Description:\n{description}"
    )
    
    try:
        # Forward the information to the owner
        await context.bot.send_message(chat_id=f"@{OWNER_USERNAME}", text=owner_message)
        logger.info(f"Information forwarded to owner from user {user.id}")
        
        # Confirm to the user
        await update.message.reply_text(
            "Thank you for providing all the information! Your request has been forwarded to our team.\n\n"
            "We'll review your requirements and get back to you soon.\n\n"
            "If you have any additional questions, feel free to message us again."
        )
        
    except Exception as e:
        logger.error(f"Error forwarding information to owner: {e}")
        await update.message.reply_text(
            "Thank you for providing all the information! Your request has been received.\n\n"
            "We'll review your requirements and get back to you soon.\n\n"
            "If you have any additional questions, feel free to message us again."
        )
    
    # Clear user data
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    await update.message.reply_text(
        "Registration cancelled. You can start again anytime with /start."
    )
    context.user_data.clear()
    return ConversationHandler.END

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "This bot helps collect information about your software needs.\n\n"
        "Use /start to begin the registration process.\n"
        "Use /cancel to cancel the current operation."
    )

def main() -> None:
    """Run the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, phone_callback)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
