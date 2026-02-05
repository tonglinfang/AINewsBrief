"""统一的消息格式化模块 - 为三个简报项目提供一致的格式"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod


class UnifiedMessageFormatter(ABC):
    """统一消息格式化基类"""

    # 统一的emoji配置
    HEADER_EMOJI = {
        "ai": "🤖",
        "tech": "🚀",
        "stock": "📈",
    }

    PRIORITY_EMOJIS = {
        "critical": "🔥",
        "high": "⚡",
        "medium": "📌",
        "low": "📋",
    }

    # 统一的分隔符
    DIVIDER_HEAVY = "━" * 30
    DIVIDER_LIGHT = "─" * 30

    @staticmethod
    def escape_markdown(text: str) -> str:
        """转义markdown特殊字符

        Args:
            text: 要转义的文本

        Returns:
            转义后的文本
        """
        if not text:
            return ""
        chars_to_escape = ["_", "*", "`", "["]
        for char in chars_to_escape:
            text = text.replace(char, f"\\{char}")
        return text

    @staticmethod
    def format_importance_stars(score: int, max_score: int = 10) -> str:
        """转换重要性分数为星级

        Args:
            score: 重要性分数
            max_score: 最高分数

        Returns:
            星级字符串
        """
        normalized = int((score / max_score) * 5)
        return "⭐" * max(1, min(5, normalized))

    @staticmethod
    def format_score_badge(score: int, max_score: int = 10) -> str:
        """格式化分数徽章

        Args:
            score: 分数
            max_score: 最高分

        Returns:
            格式化的分数徽章
        """
        percentage = (score / max_score) * 100
        if percentage >= 80:
            emoji = "🔴"  # 高
        elif percentage >= 60:
            emoji = "🟡"  # 中
        else:
            emoji = "🟢"  # 低/正常
        return f"{emoji} {score}/{max_score}"

    def format_telegram_header(
        self,
        report_type: str,
        date: datetime,
        total_items: int,
        stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """格式化Telegram消息头部

        Args:
            report_type: 报告类型 (ai/tech/stock)
            date: 报告日期
            total_items: 文章总数
            stats: 额外的统计信息

        Returns:
            格式化的头部内容
        """
        emoji = self.HEADER_EMOJI.get(report_type, "📰")
        title_map = {
            "ai": "AI快訊",
            "tech": "科技快訊",
            "stock": "美股快訊",
        }
        title = title_map.get(report_type, "資訊快訊")

        lines = [
            f"{emoji} *{title}*",
            f"📅 {date.strftime('%Y-%m-%d %H:%M')}",
            self.DIVIDER_LIGHT,
            f"📊 *本期摘要* · 共 *{total_items}* 則",
        ]

        # 添加额外统计信息
        if stats:
            stat_parts = []
            for key, value in stats.items():
                stat_parts.append(f"{key}: *{value}*")
            if stat_parts:
                lines.append(" | ".join(stat_parts))

        lines.append("")
        return "\n".join(lines)

    def format_telegram_article(
        self,
        index: int,
        title: str,
        summary: str,
        url: str,
        source: str,
        importance: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        insight: Optional[str] = None,
        key_points: Optional[List[str]] = None,
    ) -> str:
        """格式化Telegram消息的单篇文章

        Args:
            index: 文章编号
            title: 标题
            summary: 摘要
            url: 链接
            source: 来源
            importance: 重要性分数
            metadata: 额外元数据（如分类、标签等）
            insight: 洞察
            key_points: 关键要点

        Returns:
            格式化的文章内容
        """
        # 转义特殊字符
        title = self.escape_markdown(title)
        summary = self.escape_markdown(summary)

        lines = []

        # 标题行：编号 + 标题 + 重要性
        title_parts = [f"*{index}.*"]
        title_parts.append(f"*{title}*")

        if importance:
            stars = self.format_importance_stars(importance)
            title_parts.append(stars)

        lines.append(" ".join(title_parts))

        # 元数据行
        meta_parts = []
        if metadata:
            for key, value in metadata.items():
                if value:
                    meta_parts.append(f"{key}: {self.escape_markdown(str(value))}")
        meta_parts.append(f"來源: {self.escape_markdown(source)}")
        lines.append("_" + " · ".join(meta_parts) + "_")

        lines.append("")

        # 摘要
        lines.append(f"💭 {summary}")

        # 洞察
        if insight:
            lines.append(f"💡 _{self.escape_markdown(insight)}_")

        # 关键要点
        if key_points:
            lines.append("")
            lines.append("*關鍵要點*:")
            for point in key_points[:3]:  # 限制最多3个要点
                lines.append(f"  • {self.escape_markdown(point)}")

        # 链接
        lines.append(f"🔗 [閱讀原文]({url})")
        lines.append("")

        return "\n".join(lines)

    def format_telegram_footer(self, report_type: str) -> str:
        """格式化Telegram消息底部

        Args:
            report_type: 报告类型

        Returns:
            格式化的底部内容
        """
        project_map = {
            "ai": "AI News Brief",
            "tech": "Tech News Brief",
            "stock": "US Stock Brief",
        }
        project = project_map.get(report_type, "News Brief")

        return f"\n{self.DIVIDER_LIGHT}\n_🤖 Auto-generated by {project}_"

    @abstractmethod
    def format_telegram_message(self, data: Any) -> str:
        """格式化完整的Telegram消息

        Args:
            data: 报告数据

        Returns:
            格式化的Telegram消息
        """
        pass

    def format_markdown_header(
        self,
        report_type: str,
        date: datetime,
        total_items: int,
        stats: Optional[Dict[str, Any]] = None,
    ) -> str:
        """格式化Markdown报告头部

        Args:
            report_type: 报告类型
            date: 报告日期
            total_items: 文章总数
            stats: 额外统计信息

        Returns:
            格式化的头部内容
        """
        emoji = self.HEADER_EMOJI.get(report_type, "📰")
        title_map = {
            "ai": "AI資訊簡報",
            "tech": "科技資訊簡報",
            "stock": "美股投資簡報",
        }
        title = title_map.get(report_type, "資訊簡報")

        lines = [
            f"# {emoji} {title}",
            "",
            f"**日期**: {date.strftime('%Y年%m月%d日 %H:%M')}  ",
            f"**文章數量**: {total_items} 篇  ",
        ]

        if stats:
            for key, value in stats.items():
                lines.append(f"**{key}**: {value}  ")

        lines.extend(["", "---", ""])

        return "\n".join(lines)

    def format_markdown_article(
        self,
        index: int,
        title: str,
        summary: str,
        url: str,
        source: str,
        importance: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        key_points: Optional[List[str]] = None,
        additional_sections: Optional[Dict[str, str]] = None,
    ) -> str:
        """格式化Markdown报告的单篇文章

        Args:
            index: 文章编号
            title: 标题
            summary: 摘要
            url: 链接
            source: 来源
            importance: 重要性分数
            metadata: 元数据
            key_points: 关键要点
            additional_sections: 额外章节（如投资影响、风险等）

        Returns:
            格式化的文章内容
        """
        lines = []

        # 标题
        emoji = self.PRIORITY_EMOJIS.get("high", "📌")
        importance_badge = ""
        if importance:
            importance_badge = f" ({self.format_score_badge(importance)})"

        lines.append(f"### {emoji} {index}. {title}{importance_badge}")
        lines.append("")

        # 元数据
        meta_parts = [f"**來源**: {source}"]
        if metadata:
            for key, value in metadata.items():
                if value:
                    meta_parts.append(f"**{key}**: {value}")
        lines.append(" | ".join(meta_parts))
        lines.append("")

        # 摘要
        lines.append(f"**摘要**: {summary}")
        lines.append("")

        # 关键要点
        if key_points:
            lines.append("**關鍵要點**:")
            for point in key_points:
                lines.append(f"- {point}")
            lines.append("")

        # 额外章节
        if additional_sections:
            for section_title, section_content in additional_sections.items():
                lines.append(f"**{section_title}**: {section_content}")
                lines.append("")

        # 链接
        lines.append(f"[閱讀完整文章]({url})")
        lines.append("")
        lines.append("---")
        lines.append("")

        return "\n".join(lines)

    def format_markdown_footer(self, report_type: str, generation_time: datetime) -> str:
        """格式化Markdown报告底部

        Args:
            report_type: 报告类型
            generation_time: 生成时间

        Returns:
            格式化的底部内容
        """
        project_map = {
            "ai": "AI News Brief",
            "tech": "Tech News Brief",
            "stock": "US Stock Brief",
        }
        project = project_map.get(report_type, "News Brief")

        return (
            f"\n---\n\n"
            f"*📡 Generated by {project} at {generation_time.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        )

    @abstractmethod
    def format_markdown_report(self, data: Any) -> str:
        """格式化完整的Markdown报告

        Args:
            data: 报告数据

        Returns:
            格式化的Markdown报告
        """
        pass
