import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageOps, ImageFilter

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variable for the bot token
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a screenshot, and I will beautify it for you!")

async def process_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get the highest resolution photo sent
    photo_file = await update.message.photo[-1].get_file()
    
    input_path = "input.png"
    output_path = "beautified.png"
    
    # Download the screenshot locally
    await photo_file.download_to_drive(input_path)
    await update.message.reply_chat_action(action="upload_document")

    try:
        # Open the image
        img = Image.open(input_path).convert("RGBA")
        
        # 1. Settings for beautification
        padding = 80
        bg_color = (30, 41, 59, 255)  # Modern Slate Dark background
        
        # 2. Add rounded corners to the screenshot
        radius = 24
        mask = Image.new("L", img.size, 0)
        from PIL import ImageDraw
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle((0, 0, img.size[0], img.size[1]), radius=radius, fill=255)
        img = ImageOps.fit(img, img.size, keep_aspect=True)
        img.putalpha(mask)

        # 3. Create a larger canvas for the background + padding
        new_width = img.size[0] + (padding * 2)
        new_height = img.size[1] + (padding * 2)
        canvas = Image.new("RGBA", (new_width, new_height), bg_color)
        
        # 4. Paste screenshot onto canvas
        canvas.paste(img, (padding, padding), img)
        
        # Save output
        canvas.convert("RGB").save(output_path, "JPEG", quality=95)
        
        # Send the beautified image back as a high-quality document
        with open(output_path, "rb") as f:
            await update.message.reply_document(document=f, filename="beautified_screenshot.jpg")
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ Sorry, something went wrong while styling your screenshot.")
    finally:
        # Cleanup files
        if os.path.exists(input_path): os.remove(input_path)
        if os.path.exists(output_path): os.remove(output_path)

def main():
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN environment variable found!")
        return

    # Build application
    app = Application.builder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, process_screenshot))
    
    # Start polling (Crucial for Render Background Worker)
    logger.info("Bot started via polling...")
    app.run_polling()

if __name__ == '__main__':
    main()
