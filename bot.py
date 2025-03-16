import asyncio
import logging
import os
import subprocess
import sys

import yt_dlp
from aiogram import Dispatcher, Bot, F
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import CommandStart
from aiogram.types import BotCommand, Message, FSInputFile
from aiogram.utils.markdown import hlink

from config import conf
from models import User
from models import db

# local_server = TelegramAPIServer.from_base('http://localhost:8081')

bot = Bot(token=conf.bot.BOT_TOKEN)
dp = Dispatcher()
import instaloader

logger = logging.getLogger(__name__)


async def on_start(bot: Bot):
    commands_admin = [
        BotCommand(command='start', description="Bo'tni ishga tushirish")
    ]
    await bot.set_my_commands(commands=commands_admin)
    await db.create_all()


# Instagram credentials
INSTAGRAM_USERNAME = "myfish.sunnat"
INSTAGRAM_PASSWORD = "Sunnat_chef678"

# Initialize Instagram loader
L = instaloader.Instaloader(
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False,
    compress_json=False
)

# Login to Instagram
try:
    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    logger.info("Successfully logged in to Instagram")
except Exception as e:
    logger.error(f"Failed to login to Instagram: {e}")


async def on_shutdown(bot: Bot):
    await bot.delete_my_commands()


@dp.message(CommandStart())
async def language_handler(msg: Message):
    user = await User.get(msg.from_user.id)
    from_user = msg.from_user
    if not user:
        try:
            await User.create(id=from_user.id, first_name=from_user.first_name,
                              last_name=from_user.last_name,
                              username=from_user.username)
        except:
            await bot.send_message(5649321700, f'user: {from_user}')
        if from_user.id in [5649321700, 1353080275]:
            await msg.answer(f"Assalomu aleykum men Instagram Youtubedan video yuklayman")
        else:
            await msg.answer("Assalomu aleykum men Instagram Youtubedan video yuklayman")
    else:
        if from_user.id in [5649321700, 1353080275]:
            await msg.answer("Assalomu aleykum men Instagram Youtubedan video yuklayman")
        else:
            await msg.answer("Assalomu aleykum men Instagram Youtubedan video yuklayman")


@dp.message(F.text.contains("instagram.com"))
async def download_instagram_video(message: Message) -> None:
    """Handler for Instagram links"""
    download_dir = None
    status_msg = None

    try:
        # Send initial status
        status_msg = await message.answer("⏳ Processing your request...")

        # Extract URL and shortcode
        url = message.text.strip()
        # Handle different URL formats
        if "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        elif "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        else:
            await message.answer("❌ Invalid Instagram URL. Please send a valid post or reel link.")
            return

        shortcode = shortcode.split("?")[0]  # Remove URL parameters if any

        # Create directory for downloads
        download_dir = f"downloads_{shortcode}"
        os.makedirs(download_dir, exist_ok=True)

        try:
            # Download the post
            post = instaloader.Post.from_shortcode(L.context, shortcode)

            if post.is_video:
                # Update status
                await status_msg.edit_text("⬇️ Downloading video...")

                # Download the video
                L.download_post(post, target=download_dir)

                # Find the downloaded video file
                video_path = None
                for file in os.listdir(download_dir):
                    if file.endswith(".mp4"):
                        video_path = os.path.join(download_dir, file)
                        break

                if video_path:
                    # Send the video using FSInputFile
                    await status_msg.edit_text("📤 Sending video...")
                    try:
                        video = FSInputFile(video_path)
                        await message.answer_video(
                            video=video,
                            caption="✅ Here's your video!"
                        )
                    except Exception as e:
                        if "File too large" in str(e):
                            await message.answer("❌ Sorry, this video is too large for Telegram. Maximum size is 50MB.")
                        else:
                            logger.error(f"Error sending video: {e}")
                            await message.answer("❌ Error sending video. Please try again.")
                else:
                    await message.answer("❌ Sorry, couldn't find the video file after download.")
            else:
                await message.answer("❌ This post doesn't contain a video.")

        except instaloader.exceptions.InstaloaderException as e:
            error_message = str(e)
            if "login" in error_message.lower():
                await message.answer("❌ Authentication error. Please try again later.")
            else:
                await message.answer(f"❌ Error: {error_message}")
            logger.error(f"Instaloader error: {e}")

    except Exception as e:
        await message.answer("❌ Sorry, something went wrong. Please try again later.")
        logger.error(f"General error: {e}")

    finally:
        # Cleanup downloaded files
        if download_dir and os.path.exists(download_dir):
            try:
                for file in os.listdir(download_dir):
                    file_path = os.path.join(download_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                os.rmdir(download_dir)
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

        # Delete status message
        if status_msg:
            try:
                await status_msg.delete()
            except:
                pass


@dp.message()
async def download_video(message: Message):
    video_url = message.text.strip()

    if "youtube.com" not in video_url and "youtu.be" not in video_url:
        await message.reply("❌ Iltimos, YouTube havolasini yuboring!")
        return

    await message.reply("⏳ Video yuklanmoqda...")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": "video.mp4",
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_path = ydl.prepare_filename(info)
            compressed_path = "compressed.mp4"

        subprocess.run([
            "ffmpeg", "-i", file_path, "-vf", "scale=1280:720",
            "-b:v", "500k", "-b:a", "128k", "-preset", "fast", compressed_path
        ], check=True)
        video = FSInputFile(compressed_path)
        await message.answer_video(video, caption=f"📺 {hlink('YouTube', video_url)} dan yuklandi!")

        # Удаляем файлы после отправки
        os.remove(file_path)
        os.remove(compressed_path)

    except Exception as e:
        await message.reply(f"⚠️ Xatolik yuz berdi: {e}")


async def main():
    dp.startup.register(on_start)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

