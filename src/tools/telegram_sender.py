"""Telegram bot for sending daily reports."""

import asyncio
from typing import Optional
from telegram import Bot
from telegram.constants import ParseMode
from src.models.report import DailyReport
from src.config import settings


class TelegramSender:
    """Sends daily reports to Telegram."""

    # Telegram message size limit
    MAX_MESSAGE_LENGTH = 4096

    def __init__(self):
        """Initialize Telegram sender."""
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id

    async def send_report(self, report: DailyReport) -> Optional[str]:
        """Send daily report to Telegram.

        Args:
            report: Daily report to send

        Returns:
            Message ID if successful, None otherwise
        """
        try:
            content = report.markdown_content

            # Check if message is too long
            if len(content) <= self.MAX_MESSAGE_LENGTH:
                message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=content,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                return str(message.message_id)
            else:
                # Split into multiple messages
                return await self._send_long_message(content)

        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return None

    async def _send_long_message(self, content: str) -> Optional[str]:
        """Send long message by splitting into multiple parts.

        Args:
            content: Message content to split

        Returns:
            Last message ID if successful
        """
        try:
            # Split by sections (marked by ##)
            sections = content.split("\n## ")
            current_message = sections[0]
            last_message_id = None

            for i, section in enumerate(sections[1:], 1):
                section_text = f"\n## {section}"

                # Check if adding this section would exceed limit
                if len(current_message) + len(section_text) > self.MAX_MESSAGE_LENGTH - 100:
                    # Send current message
                    message = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=current_message,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                    last_message_id = str(message.message_id)

                    # Start new message
                    current_message = section_text
                else:
                    current_message += section_text

            # Send remaining content
            if current_message:
                message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=current_message,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_web_page_preview=True,
                )
                last_message_id = str(message.message_id)

            return last_message_id

        except Exception as e:
            print(f"Error sending split messages: {e}")
            return None

    async def send_error(self, error_message: str) -> None:
        """Send error notification to Telegram.

        Args:
            error_message: Error message to send
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"⚠️ *Error in AI News Brief*\n\n```\n{error_message}\n```",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            print(f"Error sending error notification: {e}")
