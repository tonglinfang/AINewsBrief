"""Telegram bot for sending daily reports."""

import asyncio
from typing import List, Optional
from telegram import Bot
from src.models.report import DailyReport
from src.config import settings
from src.utils.logger import get_logger

logger = get_logger("telegram_sender")


class TelegramSender:
    """Sends daily reports to Telegram as individual channel posts."""

    # Telegram message size limit
    MAX_MESSAGE_LENGTH = 4096

    # Delay between posts to avoid Telegram rate limits (seconds)
    POST_DELAY = 1.0

    def __init__(self):
        """Initialize Telegram sender."""
        self.bot = Bot(token=settings.telegram_bot_token)
        self.chat_id = settings.telegram_chat_id

    async def send_report(self, report: DailyReport) -> Optional[str]:
        """Send daily report to Telegram as individual channel posts.

        Each article is posted as a separate message for channel operations.
        Sends a header first, then one post per article.

        Args:
            report: Daily report to send

        Returns:
            Last message ID if successful, None otherwise
        """
        try:
            if report.individual_messages:
                return await self._send_individual_posts(report.individual_messages)
            else:
                # Fallback to legacy single-message mode
                return await self._send_single_report(report.markdown_content)

        except Exception as e:
            logger.error(
                "telegram_send_error",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return None

    async def _send_individual_posts(self, messages: List[str]) -> Optional[str]:
        """Send each message as a separate Telegram post.

        Args:
            messages: List of formatted message strings

        Returns:
            Last message ID if successful, None otherwise
        """
        last_message_id = None

        for i, message in enumerate(messages):
            try:
                # Truncate if a single post somehow exceeds the limit
                if len(message) > self.MAX_MESSAGE_LENGTH:
                    message = message[: self.MAX_MESSAGE_LENGTH - 3] + "..."

                sent = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                )
                last_message_id = str(sent.message_id)

                # Delay between posts (skip after last message)
                if i < len(messages) - 1:
                    await asyncio.sleep(self.POST_DELAY)

            except Exception as e:
                logger.error(
                    "telegram_post_error",
                    post_index=i,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                # Continue sending remaining posts even if one fails

        return last_message_id

    async def _send_single_report(self, content: str) -> Optional[str]:
        """Legacy: send entire report as one (or split) message.

        Args:
            content: Full markdown content

        Returns:
            Message ID if successful, None otherwise
        """
        if len(content) <= self.MAX_MESSAGE_LENGTH:
            message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=content,
                disable_web_page_preview=True,
                parse_mode="Markdown",
            )
            return str(message.message_id)
        else:
            return await self._split_and_send(content)

    async def _split_and_send(self, content: str) -> Optional[str]:
        """Split oversized content and send as multiple messages.

        Args:
            content: Message content to split

        Returns:
            Last message ID if successful, None otherwise
        """
        chunks = []
        current_chunk = ""

        for line in content.split("\n"):
            test_chunk = current_chunk + "\n" + line if current_chunk else line
            if len(test_chunk) > self.MAX_MESSAGE_LENGTH - 100:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = line
            else:
                current_chunk = test_chunk

        if current_chunk:
            chunks.append(current_chunk)

        last_message_id = None
        for i, chunk in enumerate(chunks, 1):
            message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=chunk,
                disable_web_page_preview=True,
                parse_mode="Markdown",
            )
            last_message_id = str(message.message_id)
            if i < len(chunks):
                await asyncio.sleep(0.5)

        return last_message_id

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
            logger.warning("telegram_error_notification_failed", error=str(e))
