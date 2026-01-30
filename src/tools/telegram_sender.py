"""Telegram bot for sending daily reports."""

import asyncio
from typing import Optional
from telegram import Bot
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
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                )
                return str(message.message_id)
            else:
                # Split into multiple messages
                return await self._send_long_message(content)

        except Exception as e:
            print(f"Error sending Telegram message: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def _send_long_message(self, content: str) -> Optional[str]:
        """Send long message by splitting into chunks.

        Args:
            content: Message content to split

        Returns:
            Last message ID if successful
        """
        try:
            messages_to_send = []
            current_chunk = ""
            
            # Split by lines to preserve formatting
            lines = content.split('\n')
            
            for line in lines:
                # Check if adding this line would exceed limit
                test_chunk = current_chunk + '\n' + line if current_chunk else line
                
                if len(test_chunk) > self.MAX_MESSAGE_LENGTH - 100:
                    # Current chunk is full, save it and start new one
                    if current_chunk:
                        messages_to_send.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk = test_chunk
            
            # Add remaining content
            if current_chunk:
                messages_to_send.append(current_chunk)
            
            # Send all chunks
            last_message_id = None
            
            for i, chunk in enumerate(messages_to_send, 1):
                message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=chunk,
                    disable_web_page_preview=True,
                    parse_mode='Markdown',
                )
                last_message_id = str(message.message_id)
                
                # Small delay between messages to avoid rate limits
                if i < len(messages_to_send):
                    await asyncio.sleep(0.5)
            
            return last_message_id

        except Exception as e:
            print(f"Error sending split messages: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def send_error(self, error_message: str) -> None:
        """Send error notification to Telegram.

        Args:
            error_message: Error message to send
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"⚠️ Error in AI News Brief\n\n{error_message}",
            )
        except Exception as e:
            print(f"Error sending error notification: {e}")
