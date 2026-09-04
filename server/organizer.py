"""Private structured work memory for the MERRICK personal assistant.

Conversation memory answers "what did we discuss?".  This module deliberately
owns a different question: "what still needs to happen, and when?"  It keeps
projects, tasks, reminders, meeting artefacts, and scheduled briefings in one
local SQLite database without placing raw private content in model prompts
unless the owner explicitly asks for a meeting summary.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from functools import cache
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


BRIEFING_KINDS = ("morning", "evening", "weekly")
DEFAULT_BRIEFING_SETTINGS = {
    "morning": (False, "08:00", 0),
    "evening": (False, "18:00", 0),
    "weekly": (False, "09:00", 0),
}
SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._:-]{0,95}", re.IGNORECASE)
SPACE_RE = re.compile(r"\s+")
OPTIONAL_MERRICK_RE = re.compile(
    r"^\s*(?:(?:hey|hello|okay|ok|please)\s+)?(?:jarvis|MERRICK)"
    r"(?=$|[\s,，.!?。！？:：-])\s*[,，.!?。！？:：-]*\s*",
    re.IGNORECASE,
)
SHOW_DASHBOARD_EN_TARGET_RE = re.compile(
    r"\b(?:(?:personal\s+)?assistant(?:\s+(?:dashboard|panel|workspace|workbench))?|"
    r"(?:work|tasks?|projects?|reminders?)\s+(?:dashboard|panel|workspace|workbench|list))\b",
    re.IGNORECASE,
)
SHOW_DASHBOARD_EN_ACTION_RE = re.compile(
    r"\b(?:open|show|view|display|access|bring\s+up|go\s+to|take\s+me\s+to|let\s+me\s+see)\b",
    re.IGNORECASE,
)
SHOW_DASHBOARD_EN_DISCUSSION_RE = re.compile(
    r"^\s*(?:how|why|what|where|when|is|are|do|does|did|should)\b|"
    r"\b(?:do\s+not|don't|never)\s+(?:open|show|view|display|access|bring)\b",
    re.IGNORECASE,
)
SHOW_DASHBOARD_ZH_TARGET_RE = re.compile(
    r"(?:个人助理(?:面板|仪表盘|工作台)?|"
    r"(?:工作|任务|待办|项目|提醒)(?:面板|仪表盘|工作台|列表))",
)
SHOW_DASHBOARD_ZH_ACTION_RE = re.compile(
    r"(?:打开|显示|查看|看看|调出|进入|切换到|带我去)",
)
SHOW_DASHBOARD_ZH_DISCUSSION_RE = re.compile(
    r"^\s*(?:如何|怎么|为什么|什么是)|(?:不要|别)\s*(?:打开|显示|查看|调出|进入)",
)
SHOW_DASHBOARD_CONTENT_REQUEST_RE = re.compile(
    r"\b(?:write|draft|compose|create|generate|produce)\b.{0,100}"
    r"\b(?:report|brief|assessment|review)\b|"
    r"(?:写|撰写|起草|生成|输出|制作).{0,50}(?:报告|简报|评估)",
    re.IGNORECASE,
)
INTELLIGENCE_NEWSPAPER_RE = re.compile(
    r"(?:\b(?:newspaper|news\s+brief|intelligence\s+(?:newspaper|brief))\b|"
    r"(?:情报)?(?:报纸|简报))",
    re.IGNORECASE,
)
INTELLIGENCE_NEWSPAPER_REQUEST_RE = re.compile(
    r"(?:\b(?:give|create|make|prepare|generate|write|build|show|want|need|schedule|subscribe)\b|"
    r"(?:给我|做(?:一份|个)?|生成|写(?:一份|个)?|准备|创建|订阅|每天|定时))",
    re.IGNORECASE,
)
INTELLIGENCE_RECURRING_RE = re.compile(
    r"(?:\b(?:daily|every\s+day|each\s+morning|every\s+morning|subscribe)\b|每天|每日|每天早上|订阅|定时)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class OrganizerCommand:
    kind: str
    payload: dict[str, Any]


def _show_dashboard_intent(source: str) -> bool:
    """Recognise natural requests for MERRICK's internal assistant surface.

    This must run before the desktop-action planner.  The dashboard is a local
    HUD panel, not an installed macOS application named "Assistant Dashboard".
    """
    # A report can legitimately mention the Personal Assistant and request a
    # visually clear Display. Those words describe report content and format;
    # they are not an instruction to open the organizer dashboard.
    if SHOW_DASHBOARD_CONTENT_REQUEST_RE.search(source):
        return False
    target = SHOW_DASHBOARD_EN_TARGET_RE.search(source) or SHOW_DASHBOARD_ZH_TARGET_RE.search(source)
    action = SHOW_DASHBOARD_EN_ACTION_RE.search(source) or SHOW_DASHBOARD_ZH_ACTION_RE.search(source)
    discussion = SHOW_DASHBOARD_EN_DISCUSSION_RE.search(source) or SHOW_DASHBOARD_ZH_DISCUSSION_RE.search(source)
    return bool(target and action and not discussion)


@cache
def _system_timezone():
    """Return the named local zone so future wall-clock times survive DST."""
    candidates: list[str] = []
    configured = os.getenv("TZ", "").lstrip(":")
    if configured:
        candidates.append(configured)
    try:
        resolved = str(Path("/etc/localtime").resolve())
        marker = "/zoneinfo/"
        if marker in resolved:
            candidates.append(resolved.split(marker, 1)[1])
    except OSError:
        pass
    for name in candidates:
        try:
            return ZoneInfo(name)
        except (ValueError, ZoneInfoNotFoundError):
            continue
    return datetime.now().astimezone().tzinfo


def _now_local(now: datetime | None = None) -> datetime:
    value = now or datetime.now().astimezone()
    if value.tzinfo is None:
        value = value.astimezone()
    zone = _system_timezone()
    return value.astimezone(zone) if zone is not None else value


def _iso(value: datetime) -> str:
    return value.astimezone().isoformat(timespec="seconds")


def _clean(value: object, limit: int = 600) -> str:
    if not isinstance(value, str):
        return ""
    return SPACE_RE.sub(" ", value).strip()[:limit]


TASK_MATCH_TOKEN_RE = re.compile(r"[a-z0-9]+|[\u3400-\u9fff]+", re.IGNORECASE)
TASK_MATCH_FILLER_TOKENS = frozenset({
    "a", "an", "the", "my", "please", "task", "tasks", "todo", "to-do",
    "item", "called", "named", "now",
})


def _task_match_text(value: object) -> str:
    """Normalize harmless ASR/politeness variation without changing meaning."""
    text = unicodedata.normalize("NFKC", _clean(value, 300)).casefold()
    text = re.sub(r"(?:这个)?(?:任务|待办)(?:事项)?$", "", text).strip()
    tokens = [
        token for token in TASK_MATCH_TOKEN_RE.findall(text)
        if token not in TASK_MATCH_FILLER_TOKENS
    ]
    return " ".join(tokens)


def _task_match_score(query: str, candidate: str) -> float:
    """Blend phrase and token similarity for conservative local matching."""
    if not query or not candidate:
        return 0.0
    if query == candidate:
        return 1.0
    phrase_score = SequenceMatcher(None, query, candidate).ratio()
    query_tokens = set(query.split())
    candidate_tokens = set(candidate.split())
    overlap = len(query_tokens & candidate_tokens)
    if not overlap:
        return phrase_score
    candidate_coverage = overlap / len(candidate_tokens)
    query_coverage = overlap / len(query_tokens)
    token_score = 0.68 * candidate_coverage + 0.32 * query_coverage
    return max(phrase_score, token_score)


TASK_MATCH_CONFIDENCE = 0.76
TASK_MATCH_AMBIGUITY_MARGIN = 0.10


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex}"


def _parse_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.astimezone()


CHINESE_DIGITS = {
    "零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
    "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
}


def _chinese_number(value: str) -> int | None:
    if value.isascii() and value.isdigit():
        return int(value)
    if value == "十":
        return 10
    if "十" in value:
        left, _, right = value.partition("十")
        tens = CHINESE_DIGITS.get(left, 1) if left else 1
        ones = CHINESE_DIGITS.get(right, 0) if right else 0
        return tens * 10 + ones
    if len(value) == 1:
        return CHINESE_DIGITS.get(value)
    return None


def parse_local_datetime(text: str, *, now: datetime | None = None) -> datetime | None:
    """Parse bounded reminder language in English and Mandarin.

    This intentionally handles explicit, common personal-assistant phrases and
    declines ambiguous dates.  The conversational model never gets authority
    to invent a firing time.
    """
    source = _clean(text, 500)
    if not source:
        return None
    local_now = _now_local(now)

    relative_zh = re.search(
        r"(?P<count>\d{1,4}|[一二两三四五六七八九十]{1,3})\s*"
        r"(?P<unit>分钟|小时|天)\s*(?:以后|之后|后)", source
    )
    relative_en = re.search(
        r"\bin\s+(?P<count>\d{1,4})\s*(?P<unit>minutes?|mins?|hours?|days?)\b",
        source, re.IGNORECASE,
    )
    relative = relative_zh or relative_en
    if relative:
        count_text = relative.group("count")
        count = _chinese_number(count_text) if relative_zh else int(count_text)
        if not count or count < 1:
            return None
        unit = relative.group("unit").casefold()
        if "分钟" in unit or unit.startswith(("minute", "min")):
            return local_now + timedelta(minutes=count)
        if "小时" in unit or unit.startswith("hour"):
            return local_now + timedelta(hours=count)
        return local_now + timedelta(days=count)

    explicit_zh = re.search(
        r"(?P<year>20\d{2})[年/-](?P<month>\d{1,2})[月/-](?P<day>\d{1,2})日?",
        source,
    )
    explicit_en = re.search(
        r"\b(?P<year>20\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})\b",
        source,
    )
    explicit = explicit_zh or explicit_en
    day_offset: int | None = None
    if re.search(r"后天", source):
        day_offset = 2
    elif re.search(r"明天|明早|明晚", source) or re.search(r"\btomorrow\b", source, re.IGNORECASE):
        day_offset = 1
    elif re.search(r"今天|今早|今晚", source) or re.search(r"\btoday\b|\btonight\b", source, re.IGNORECASE):
        day_offset = 0

    period = ""
    period_match = re.search(r"明早|今早|早上|上午|中午|下午|傍晚|今晚|明晚|晚上", source)
    if period_match:
        period = period_match.group(0)
    else:
        english_period = re.search(r"\b(morning|noon|afternoon|evening|tonight)\b", source, re.IGNORECASE)
        if english_period:
            period = english_period.group(1).casefold()

    zh_time = re.search(
        r"(?:(?:早上|上午|中午|下午|傍晚|晚上|今晚|明早|明晚)\s*)?"
        r"(?P<hour>\d{1,2}|[零〇一二两三四五六七八九十]{1,3})\s*点"
        r"(?:(?P<half>半)|(?P<minute>\d{1,2})\s*分?)?",
        source,
    )
    # Do not let the month or day inside an ISO date masquerade as the hour.
    # The time parser only inspects the remaining instruction text.
    en_time_source = source
    if explicit:
        en_time_source = source[:explicit.start()] + " " + source[explicit.end():]
    en_time = re.search(
        r"\b(?:at\s+)?(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>a\.?m\.?|p\.?m\.?)?\b",
        en_time_source,
        re.IGNORECASE,
    )

    hour: int | None = None
    minute = 0
    if zh_time:
        hour = _chinese_number(zh_time.group("hour"))
        minute = 30 if zh_time.group("half") else int(zh_time.group("minute") or 0)
    elif en_time and (
        en_time.group("ampm") or en_time.group("minute") is not None
        or day_offset is not None or explicit is not None
    ):
        hour = int(en_time.group("hour"))
        minute = int(en_time.group("minute") or 0)
        ampm = (en_time.group("ampm") or "").casefold().replace(".", "")
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0

    if hour is None and (day_offset is not None or explicit is not None):
        if period in {"明早", "今早", "早上", "上午", "morning"}:
            hour = 9
        elif period in {"中午", "noon"}:
            hour = 12
        elif period in {"下午", "afternoon"}:
            hour = 15
        elif period in {"傍晚", "今晚", "明晚", "晚上", "evening", "tonight"}:
            hour = 20
        else:
            hour = 9
    if hour is None:
        return None
    if period in {"下午", "傍晚", "今晚", "明晚", "晚上"} and hour < 12:
        hour += 12
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        return None

    try:
        if explicit:
            candidate = local_now.replace(
                year=int(explicit.group("year")), month=int(explicit.group("month")),
                day=int(explicit.group("day")), hour=hour, minute=minute,
                second=0, microsecond=0,
            )
        else:
            target_day = local_now + timedelta(days=day_offset or 0)
            candidate = target_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except ValueError:
        return None
    if explicit is None and day_offset is None and candidate <= local_now:
        candidate += timedelta(days=1)
    if candidate <= local_now - timedelta(seconds=1):
        return None
    return candidate


def _strip_temporal_language(text: str) -> str:
    value = text
    patterns = (
        r"(?:今天|明天|后天|今早|明早|今晚|明晚)",
        r"(?:早上|上午|中午|下午|傍晚|晚上)?\s*(?:\d{1,2}|[零〇一二两三四五六七八九十]{1,3})\s*点(?:半|\d{1,2}\s*分?)?",
        r"\d{1,4}\s*(?:分钟|小时|天)\s*(?:以后|之后|后)",
        r"\b(?:today|tomorrow|tonight)(?:\s+(?:morning|afternoon|evening))?\b",
        r"\b(?:at\s+)?\d{1,2}(?::\d{2})?\s*(?:a\.?m\.?|p\.?m\.?)\b",
        r"\bin\s+\d{1,4}\s*(?:minutes?|mins?|hours?|days?)\b",
        r"20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}日?",
    )
    for pattern in patterns:
        value = re.sub(pattern, " ", value, flags=re.IGNORECASE)
    return _clean(value.strip(" ,，。.!！?？:：-"), 300)


def parse_organizer_command(text: str, *, now: datetime | None = None) -> OrganizerCommand | None:
    source = OPTIONAL_MERRICK_RE.sub("", _clean(text, 800), count=1)
    if not source:
        return None
    lower = source.casefold()

    if re.search(r"(?:确认|批准)(?:刚才|最近|这次)?(?:的)?会议(?:的)?(?:行动项|待办|任务)", source) or re.search(
        r"\b(?:confirm|approve)\s+(?:the\s+)?(?:latest\s+|last\s+)?meeting\s+(?:actions?|tasks?)\b",
        source, re.IGNORECASE,
    ):
        return OrganizerCommand("confirm_meeting_actions", {})

    reminder_requested = "提醒我" in source or re.search(r"\bremind\s+me\b", source, re.IGNORECASE)
    if reminder_requested:
        fire_at = parse_local_datetime(source, now=now)
        if fire_at is None:
            return OrganizerCommand("reminder_missing_time", {})
        title = re.sub(r"提醒我", " ", source, count=1)
        title = re.sub(r"\bremind\s+me(?:\s+to)?\b", " ", title, count=1, flags=re.IGNORECASE)
        title = _strip_temporal_language(title)
        title = re.sub(r"^to\s+", "", title, flags=re.IGNORECASE)
        if not title:
            return OrganizerCommand("reminder_missing_title", {"fire_at": _iso(fire_at)})
        return OrganizerCommand("create_reminder", {"title": title, "fire_at": _iso(fire_at)})

    if INTELLIGENCE_NEWSPAPER_RE.search(source) and INTELLIGENCE_NEWSPAPER_REQUEST_RE.search(source):
        recurring = bool(INTELLIGENCE_RECURRING_RE.search(source))
        parsed_time = parse_local_datetime(source, now=now)
        local_time = parsed_time.strftime("%H:%M") if parsed_time else "08:00"
        title = (
            "每日情报报纸" if recurring and re.search(r"[\u4e00-\u9fff]", source)
            else "Daily intelligence newspaper" if recurring
            else "MERRICK intelligence newspaper"
        )
        return OrganizerCommand("create_intelligence", {
            "title": title,
            "prompt": source,
            "enabled": recurring,
            "local_time": local_time,
            "generate_now": True,
        })

    briefing_terms = {
        "morning": r"晨间简报|早间简报|morning\s+briefing",
        "evening": r"晚间复盘|晚间简报|evening\s+(?:review|briefing)",
        "weekly": r"周报|每周简报|weekly\s+(?:report|briefing)",
    }
    for kind, term in briefing_terms.items():
        if not re.search(term, source, re.IGNORECASE):
            continue
        disable = bool(re.search(r"关闭|停用|不要|取消|\b(?:disable|turn\s+off|stop)\b", source, re.IGNORECASE))
        enable = bool(re.search(r"开启|启用|打开|\b(?:enable|turn\s+on|start)\b", source, re.IGNORECASE))
        parsed_time = parse_local_datetime(source, now=now)
        time_value = parsed_time.strftime("%H:%M") if parsed_time else None
        weekday = None
        weekday_map = {
            "周一": 0, "星期一": 0, "monday": 0,
            "周二": 1, "星期二": 1, "tuesday": 1,
            "周三": 2, "星期三": 2, "wednesday": 2,
            "周四": 3, "星期四": 3, "thursday": 3,
            "周五": 4, "星期五": 4, "friday": 4,
            "周六": 5, "星期六": 5, "saturday": 5,
            "周日": 6, "星期日": 6, "星期天": 6, "sunday": 6,
        }
        for label, value in weekday_map.items():
            if label in lower:
                weekday = value
                break
        if disable or enable or time_value or weekday is not None:
            return OrganizerCommand("configure_briefing", {
                "kind": kind,
                "enabled": False if disable else True if enable else None,
                "time": time_value,
                "weekday": weekday,
            })

    completion_question = bool(re.search(
        r"什么时候|何时|多久|是否|有没有|[?？]\s*$|^\s*(?:when|whether|is|are|did|has|have|was|were)\b",
        source,
        re.IGNORECASE,
    ))
    complete_patterns = (
        r"^(?P<title>.+?)(?:这项|这件|这个)?(?:工作|任务|待办)\s*(?:已经|已)?\s*(?:做好|完成|做完|搞定)(?:了)?$",
        r"^把\s*(?P<title>.+?)\s*(?:标记为|设为)\s*(?:已完成|完成)$",
        r"^(?:请|麻烦)?\s*(?:把\s*)?(?P<title>.+?)\s*(?:这个)?(?:任务|待办)?\s*(?:做完|搞定)(?:了)?$",
        r"^(?:请|麻烦)?\s*(?:完成|标记完成|做完|搞定)\s*(?:一下)?\s*(?:任务|待办)?\s*[：:]?\s*(?P<title>.+)$",
        r"^(?:please\s+)?(?:complete|finish|close)\s+(?:the\s+)?(?:(?:task|to-do)\s+)?(?P<title>.+?)(?:\s+(?:as\s+)?(?:done|complete|completed))?$",
        r"^(?:please\s+)?(?:mark|set)\s+(?:the\s+)?(?:(?:task|to-do)\s+)?(?P<title>.+?)\s+(?:as\s+)?(?:done|complete|completed)$",
        r"^(?:i(?:'ve| have)\s+)?(?:finished|completed|done\s+with)\s+(?:the\s+)?(?:(?:task|to-do)\s+)?(?P<title>.+)$",
        r"^(?P<title>.+?)\s+(?:is|has\s+been)\s+(?:done|complete|completed)$",
    )
    if not completion_question:
        for pattern in complete_patterns:
            match = re.match(pattern, source, re.IGNORECASE)
            if match:
                title = _clean(match.group("title").strip(" .。!！"), 300)
                if title:
                    return OrganizerCommand("complete_task", {"title": title})

    rename_project_patterns = (
        r"^把\s*(?:项目)?\s*(?P<old>.+?)\s*(?:改名为|重命名为|更名为)\s*(?P<new>.+)$",
        r"^(?:重命名|更名)\s*(?:项目)?\s*(?P<old>.+?)\s*(?:为|成)\s*(?P<new>.+)$",
        r"^(?:please\s+)?(?:rename|change\s+the\s+name\s+of)\s+(?:the\s+)?project\s+"
        r"(?P<old>.+?)\s+(?:to|as)\s+(?P<new>.+)$",
    )
    for pattern in rename_project_patterns:
        match = re.match(pattern, source, re.IGNORECASE)
        if match:
            old_title = _clean(match.group("old").strip(" .。!！"), 200)
            new_title = _clean(match.group("new").strip(" .。!！"), 200)
            if old_title and new_title:
                return OrganizerCommand(
                    "rename_project", {"title": old_title, "new_title": new_title}
                )

    archive_project_patterns = (
        r"^(?:请|帮我|麻烦)?\s*(?:删除|移除|归档)\s*(?:项目)?\s*[：:]?\s*(?P<title>.+)$",
        r"^(?:please\s+)?(?:delete|remove|archive)\s+(?:the\s+)?project\s+(?P<title>.+)$",
    )
    for pattern in archive_project_patterns:
        match = re.match(pattern, source, re.IGNORECASE)
        if match:
            title = _clean(match.group("title").strip(" .。!！"), 200)
            if title:
                return OrganizerCommand("archive_project", {"title": title})

    project_patterns = (
        r"^(?:新建|创建|建立|添加)(?:一个)?项目(?:叫|名为)?\s*[：:]?\s*(?P<title>.+)$",
        r"^(?:create|start|add)\s+(?:a\s+)?project(?:\s+(?:called|named))?\s*[:]?\s*(?P<title>.+)$",
    )
    for pattern in project_patterns:
        match = re.match(pattern, source, re.IGNORECASE)
        if match:
            title = _clean(match.group("title").strip(" .。!！"), 200)
            if title:
                return OrganizerCommand("create_project", {"title": title})

    task_list_zh = re.match(
        r"^把\s*(?P<title>.+?)\s*(?:加入|添加到|放到)\s*(?:我的)?(?:任务|待办)(?:列表)?$",
        source,
    )
    if task_list_zh:
        return OrganizerCommand("create_task", {
            "title": _clean(task_list_zh.group("title"), 300),
            "project": "",
        })
    task_project_zh = re.match(
        r"^把\s*(?P<title>.+?)\s*(?:加入|添加到|放到)\s*(?:项目)?\s*(?P<project>.+)$",
        source,
    )
    if task_project_zh:
        return OrganizerCommand("create_task", {
            "title": _clean(task_project_zh.group("title"), 300),
            "project": _clean(task_project_zh.group("project").strip(" .。!！"), 200),
        })
    task_patterns = (
        r"^(?:新建|创建|添加|加入)(?:一个)?(?:任务|待办)(?:事项)?\s*[：:]?\s*(?P<title>.+?)(?:\s*(?:到|至)\s*项目\s*(?P<project>.+))?$",
        r"^(?:add|create)\s+(?:a\s+)?(?:task|to-do)(?:\s+(?:called|named))?\s*[:]?\s*(?P<title>.+?)(?:\s+to\s+(?:the\s+)?project\s+(?P<project>.+))?$",
        r"^(?:please\s+)?(?:add|put)\s+(?P<title>.+?)\s+(?:to|on)\s+(?:my\s+)?(?:task|to-do)\s+list$",
        r"^(?:please\s+)?(?:make|create)\s+(?P<title>.+?)\s+(?:a\s+)?(?:task|to-do)$",
    )
    for pattern in task_patterns:
        match = re.match(pattern, source, re.IGNORECASE)
        if match:
            title = _clean(match.group("title").strip(" .。!！"), 300)
            project = _clean(match.groupdict().get("project", "").strip(" .。!！"), 200)
            if title:
                return OrganizerCommand("create_task", {"title": title, "project": project})

    if _show_dashboard_intent(source) or re.fullmatch(
        r"(?:今天|本周)(?:有|还有)?(?:什么|哪些)?(?:任务|待办|安排)",
        source,
        re.IGNORECASE,
    ):
        return OrganizerCommand("show_dashboard", {})
    return None


class OrganizerStore:
    """Local structured state with one connection per bounded operation."""

    def __init__(self, directory: Path):
        self.directory = directory
        self.path = directory / "jarvis-organizer.db"

    def _connect(self) -> sqlite3.Connection:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5.0)
        self.path.chmod(0o600)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=NORMAL")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL COLLATE NOCASE UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                priority TEXT NOT NULL DEFAULT 'normal',
                due_at TEXT,
                source TEXT NOT NULL DEFAULT 'user',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            );
            CREATE INDEX IF NOT EXISTS tasks_status_due_idx ON tasks(status, due_at);
            CREATE INDEX IF NOT EXISTS tasks_project_idx ON tasks(project_id, status);
            CREATE TABLE IF NOT EXISTS reminders (
                id TEXT PRIMARY KEY,
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL,
                title TEXT NOT NULL,
                fire_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                notification_state TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                delivered_at TEXT
            );
            CREATE INDEX IF NOT EXISTS reminders_fire_idx ON reminders(status, fire_at);
            CREATE TABLE IF NOT EXISTS meeting_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                started_at TEXT NOT NULL,
                ended_at TEXT,
                status TEXT NOT NULL DEFAULT 'recording',
                summary TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meeting_transcript_entries (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES meeting_sessions(id) ON DELETE CASCADE,
                recorded_at TEXT NOT NULL,
                text TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS meeting_transcript_session_idx
                ON meeting_transcript_entries(session_id, id);
            CREATE TABLE IF NOT EXISTS meeting_decisions (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES meeting_sessions(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                text TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS meeting_action_items (
                id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL REFERENCES meeting_sessions(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                title TEXT NOT NULL,
                owner TEXT NOT NULL DEFAULT '',
                due_text TEXT NOT NULL DEFAULT '',
                due_at TEXT,
                status TEXT NOT NULL DEFAULT 'proposed',
                task_id TEXT REFERENCES tasks(id) ON DELETE SET NULL
            );
            CREATE TABLE IF NOT EXISTS briefing_settings (
                kind TEXT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 0,
                local_time TEXT NOT NULL,
                weekday INTEGER NOT NULL DEFAULT 0,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS briefings (
                id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                period_key TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                title TEXT NOT NULL,
                content_json TEXT NOT NULL,
                UNIQUE(kind, period_key)
            );
            CREATE TABLE IF NOT EXISTS intelligence_subscriptions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                prompt TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 0,
                local_time TEXT NOT NULL DEFAULT '08:00',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS intelligence_editions (
                id TEXT PRIMARY KEY,
                subscription_id TEXT NOT NULL
                    REFERENCES intelligence_subscriptions(id) ON DELETE CASCADE,
                period_key TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                title TEXT NOT NULL,
                content_json TEXT NOT NULL,
                sources_json TEXT NOT NULL DEFAULT '[]',
                UNIQUE(subscription_id, period_key)
            );
            CREATE INDEX IF NOT EXISTS intelligence_editions_generated_idx
                ON intelligence_editions(generated_at DESC);
            """
        )
        now = _iso(_now_local())
        with connection:
            for kind, (enabled, local_time, weekday) in DEFAULT_BRIEFING_SETTINGS.items():
                connection.execute(
                    """
                    INSERT OR IGNORE INTO briefing_settings
                        (kind, enabled, local_time, weekday, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (kind, int(enabled), local_time, weekday, now),
                )
        return connection

    def initialise(self) -> None:
        connection = self._connect()
        connection.close()

    @staticmethod
    def _validate_local_time(value: str) -> str:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError("Delivery time is invalid.")
        return value

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def create_project(self, title: str) -> dict[str, Any]:
        name = _clean(title, 200)
        if not name:
            raise ValueError("Project title is required.")
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                existing = connection.execute(
                    "SELECT * FROM projects WHERE title = ? COLLATE NOCASE", (name,)
                ).fetchone()
                if existing:
                    if existing["status"] != "active":
                        connection.execute(
                            "UPDATE projects SET status='active', updated_at=? WHERE id=?",
                            (now, existing["id"]),
                        )
                    row = connection.execute("SELECT * FROM projects WHERE id=?", (existing["id"],)).fetchone()
                    return dict(row)
                project_id = _new_id("project")
                connection.execute(
                    "INSERT INTO projects (id, title, status, created_at, updated_at) VALUES (?, ?, 'active', ?, ?)",
                    (project_id, name, now, now),
                )
                return dict(connection.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone())
        finally:
            connection.close()

    def rename_project(self, project_id_or_title: str, new_title: str) -> dict[str, Any] | None:
        reference = _clean(project_id_or_title, 200)
        name = _clean(new_title, 200)
        if not reference or not name:
            raise ValueError("Both the project and its new name are required.")
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                project = connection.execute(
                    """
                    SELECT * FROM projects
                    WHERE status='active' AND (id=? OR title=? COLLATE NOCASE)
                    LIMIT 1
                    """,
                    (reference, reference),
                ).fetchone()
                if project is None:
                    return None
                try:
                    connection.execute(
                        "UPDATE projects SET title=?, updated_at=? WHERE id=?",
                        (name, now, project["id"]),
                    )
                except sqlite3.IntegrityError as exc:
                    raise ValueError("A project with that name already exists.") from exc
                row = connection.execute(
                    "SELECT * FROM projects WHERE id=?", (project["id"],)
                ).fetchone()
                return dict(row)
        finally:
            connection.close()

    def archive_project(self, project_id_or_title: str) -> dict[str, Any] | None:
        """Soft-delete one project while preserving every task and reminder."""
        reference = _clean(project_id_or_title, 200)
        if not reference:
            raise ValueError("Project is required.")
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                project = connection.execute(
                    """
                    SELECT * FROM projects
                    WHERE status='active' AND (id=? OR title=? COLLATE NOCASE)
                    LIMIT 1
                    """,
                    (reference, reference),
                ).fetchone()
                if project is None:
                    return None
                task_count = int(connection.execute(
                    "SELECT COUNT(*) FROM tasks WHERE project_id=?", (project["id"],)
                ).fetchone()[0])
                # Deleting an organizational container must never cascade into
                # commitments. Tasks (and their reminders) remain intact and
                # simply return to the unassigned task list.
                connection.execute(
                    "UPDATE tasks SET project_id=NULL, updated_at=? WHERE project_id=?",
                    (now, project["id"]),
                )
                connection.execute(
                    "UPDATE projects SET status='archived', updated_at=? WHERE id=?",
                    (now, project["id"]),
                )
                result = dict(project)
                result["status"] = "archived"
                result["detached_tasks"] = task_count
                result["updated_at"] = now
                return result
        finally:
            connection.close()

    def create_task(
        self,
        title: str,
        *,
        project_title: str = "",
        due_at: str | None = None,
        source: str = "user",
    ) -> dict[str, Any]:
        name = _clean(title, 300)
        if not name:
            raise ValueError("Task title is required.")
        project_id = None
        if _clean(project_title, 200):
            project_id = self.create_project(project_title)["id"]
        if due_at and _parse_iso(due_at) is None:
            raise ValueError("Task due time is invalid.")
        now = _iso(_now_local())
        task_id = _new_id("task")
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO tasks
                        (id, project_id, title, status, priority, due_at, source, created_at, updated_at)
                    VALUES (?, ?, ?, 'open', 'normal', ?, ?, ?, ?)
                    """,
                    (task_id, project_id, name, due_at, _clean(source, 80) or "user", now, now),
                )
                row = connection.execute(
                    """
                    SELECT tasks.*, projects.title AS project_title
                    FROM tasks LEFT JOIN projects ON projects.id=tasks.project_id
                    WHERE tasks.id=?
                    """,
                    (task_id,),
                ).fetchone()
                return dict(row)
        finally:
            connection.close()

    def update_task(
        self,
        task_id: str,
        *,
        title: str | None = None,
        due_at: str | None = None,
        due_at_provided: bool = False,
    ) -> dict[str, Any] | None:
        """Edit one open task without changing its linked reminder intent."""
        if not SAFE_ID_RE.fullmatch(task_id):
            raise ValueError("Task is invalid.")
        if title is not None and not _clean(title, 300):
            raise ValueError("Task title is required.")
        normalized_due_at: str | None = None
        if due_at_provided and due_at is not None:
            parsed_due_at = _parse_iso(due_at)
            if parsed_due_at is None:
                raise ValueError("Task due time is invalid.")
            normalized_due_at = _iso(parsed_due_at)
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                current = connection.execute(
                    "SELECT * FROM tasks WHERE id=? AND status='open'", (task_id,)
                ).fetchone()
                if current is None:
                    return None
                next_title = _clean(title, 300) if title is not None else str(current["title"])
                next_due_at = normalized_due_at if due_at_provided else current["due_at"]
                connection.execute(
                    "UPDATE tasks SET title=?, due_at=?, updated_at=? WHERE id=?",
                    (next_title, next_due_at, now, task_id),
                )
                row = connection.execute(
                    """
                    SELECT tasks.*, projects.title AS project_title
                    FROM tasks LEFT JOIN projects ON projects.id=tasks.project_id
                    WHERE tasks.id=?
                    """,
                    (task_id,),
                ).fetchone()
                return dict(row)
        finally:
            connection.close()

    def complete_task(self, title_or_id: str) -> dict[str, Any] | None:
        target = _clean(title_or_id, 300)
        if not target:
            return None
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                row = connection.execute(
                    """
                    SELECT * FROM tasks WHERE status='open' AND (id=? OR title=? COLLATE NOCASE)
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (target, target),
                ).fetchone()
                if row is None:
                    row = connection.execute(
                        """
                        SELECT * FROM tasks WHERE status='open' AND title LIKE ? COLLATE NOCASE
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (f"%{target}%",),
                    ).fetchone()
                if row is None:
                    return None
                connection.execute(
                    "UPDATE tasks SET status='completed', completed_at=?, updated_at=? WHERE id=?",
                    (now, now, row["id"]),
                )
                connection.execute(
                    "UPDATE reminders SET status='cancelled' WHERE task_id=? AND status='pending'",
                    (row["id"],),
                )
                return dict(connection.execute("SELECT * FROM tasks WHERE id=?", (row["id"],)).fetchone())
        finally:
            connection.close()

    def has_exact_open_task(self, title: str) -> bool:
        """Return whether an open task matches after harmless normalization."""
        target = _task_match_text(title)
        if not target:
            return False
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT title FROM tasks WHERE status='open' ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
            return any(_task_match_text(row["title"]) == target for row in rows)
        finally:
            connection.close()

    def resolve_open_task(self, title: str) -> dict[str, Any]:
        """Resolve one spoken title with confidence and ambiguity safeguards."""
        target = _task_match_text(title)
        if not target:
            return {"status": "not_found", "task": None, "candidates": []}
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT * FROM tasks WHERE status='open' ORDER BY created_at DESC LIMIT 500"
            ).fetchall()
            ranked = sorted(
                (
                    (_task_match_score(target, _task_match_text(row["title"])), dict(row))
                    for row in rows
                ),
                key=lambda item: item[0],
                reverse=True,
            )
        finally:
            connection.close()
        if not ranked or ranked[0][0] < TASK_MATCH_CONFIDENCE:
            return {"status": "not_found", "task": None, "candidates": []}
        best_score, best_task = ranked[0]
        close = [
            task for score, task in ranked[:4]
            if score >= TASK_MATCH_CONFIDENCE
            and best_score - score < TASK_MATCH_AMBIGUITY_MARGIN
        ]
        if len(close) > 1:
            return {
                "status": "ambiguous",
                "task": None,
                "candidates": close[:3],
                "score": best_score,
            }
        return {
            "status": "matched",
            "task": best_task,
            "candidates": [best_task],
            "score": best_score,
        }

    def create_reminder(self, title: str, fire_at: str, *, task_id: str | None = None) -> dict[str, Any]:
        name = _clean(title, 300)
        parsed = _parse_iso(fire_at)
        if not name or parsed is None:
            raise ValueError("Reminder title and time are required.")
        reminder_id = _new_id("reminder")
        now = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO reminders
                        (id, task_id, title, fire_at, status, notification_state, created_at)
                    VALUES (?, ?, ?, ?, 'pending', 'pending', ?)
                    """,
                    (reminder_id, task_id, name, _iso(parsed), now),
                )
                return dict(connection.execute("SELECT * FROM reminders WHERE id=?", (reminder_id,)).fetchone())
        finally:
            connection.close()

    def update_reminder(self, reminder_id: str, *, fire_at: str) -> dict[str, Any] | None:
        """Move one pending reminder and make native delivery schedule it again."""
        if not SAFE_ID_RE.fullmatch(reminder_id):
            raise ValueError("Reminder is invalid.")
        parsed_fire_at = _parse_iso(fire_at)
        if parsed_fire_at is None:
            raise ValueError("Reminder time is invalid.")
        connection = self._connect()
        try:
            with connection:
                current = connection.execute(
                    "SELECT * FROM reminders WHERE id=? AND status='pending'", (reminder_id,)
                ).fetchone()
                if current is None:
                    return None
                connection.execute(
                    """
                    UPDATE reminders
                    SET fire_at=?, notification_state='pending', delivered_at=NULL
                    WHERE id=?
                    """,
                    (_iso(parsed_fire_at), reminder_id),
                )
                row = connection.execute(
                    "SELECT * FROM reminders WHERE id=?", (reminder_id,)
                ).fetchone()
                return dict(row)
        finally:
            connection.close()

    def update_notification_state(self, reminder_id: str, *, ok: bool) -> None:
        if not SAFE_ID_RE.fullmatch(reminder_id):
            return
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    "UPDATE reminders SET notification_state=? WHERE id=?",
                    ("scheduled" if ok else "failed", reminder_id),
                )
        finally:
            connection.close()

    def pending_reminders(self, *, now: datetime | None = None) -> list[dict[str, Any]]:
        local_now = _now_local(now)
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    UPDATE reminders SET status='delivered', delivered_at=?
                    WHERE status='pending' AND (
                        (notification_state='scheduled' AND fire_at <= ?)
                        OR fire_at < ?
                    )
                    """,
                    (
                        _iso(local_now), _iso(local_now),
                        _iso(local_now - timedelta(minutes=2)),
                    ),
                )
                rows = connection.execute(
                    "SELECT * FROM reminders WHERE status='pending' ORDER BY fire_at LIMIT 100"
                ).fetchall()
                return [dict(row) for row in rows]
        finally:
            connection.close()

    def cancelled_notification_ids_for_task(self, task_id: str) -> list[str]:
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT id FROM reminders WHERE task_id=? AND status='cancelled'", (task_id,)
            ).fetchall()
            return [str(row["id"]) for row in rows]
        finally:
            connection.close()

    def start_meeting(self, *, title: str = "", now: datetime | None = None) -> dict[str, Any]:
        local_now = _now_local(now)
        meeting_id = _new_id("meeting")
        meeting_title = _clean(title, 200) or f"Meeting · {local_now.strftime('%Y-%m-%d %H:%M')}"
        timestamp = _iso(local_now)
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO meeting_sessions
                        (id, title, started_at, status, summary, created_at, updated_at)
                    VALUES (?, ?, ?, 'recording', '', ?, ?)
                    """,
                    (meeting_id, meeting_title, timestamp, timestamp, timestamp),
                )
                return dict(connection.execute("SELECT * FROM meeting_sessions WHERE id=?", (meeting_id,)).fetchone())
        finally:
            connection.close()

    def append_meeting_transcript(
        self, session_id: str, text: str, *, recorded_at: datetime | None = None
    ) -> None:
        line = _clean(text, 3_000)
        if not SAFE_ID_RE.fullmatch(session_id) or not line:
            return
        connection = self._connect()
        try:
            with connection:
                active = connection.execute(
                    "SELECT 1 FROM meeting_sessions WHERE id=?", (session_id,)
                ).fetchone()
                if active is None:
                    return
                connection.execute(
                    "INSERT INTO meeting_transcript_entries (session_id, recorded_at, text) VALUES (?, ?, ?)",
                    (session_id, _iso(_now_local(recorded_at)), line),
                )
        finally:
            connection.close()

    def meeting_transcript(self, session_id: str, *, limit_chars: int = 30_000) -> str:
        if not SAFE_ID_RE.fullmatch(session_id):
            return ""
        connection = self._connect()
        try:
            rows = connection.execute(
                "SELECT recorded_at, text FROM meeting_transcript_entries WHERE session_id=? ORDER BY id",
                (session_id,),
            ).fetchall()
        finally:
            connection.close()
        lines = [f"[{str(row['recorded_at'])[11:19]}] {row['text']}" for row in rows]
        return "\n".join(lines)[-limit_chars:]

    def finish_meeting(
        self,
        session_id: str,
        *,
        summary: str,
        decisions: Iterable[str],
        action_items: Iterable[dict[str, Any]],
        now: datetime | None = None,
    ) -> dict[str, Any] | None:
        if not SAFE_ID_RE.fullmatch(session_id):
            return None
        timestamp = _iso(_now_local(now))
        clean_summary = _clean(summary, 4_000)
        connection = self._connect()
        try:
            with connection:
                if connection.execute("SELECT 1 FROM meeting_sessions WHERE id=?", (session_id,)).fetchone() is None:
                    return None
                connection.execute(
                    """
                    UPDATE meeting_sessions SET ended_at=?, status='review', summary=?, updated_at=?
                    WHERE id=?
                    """,
                    (timestamp, clean_summary, timestamp, session_id),
                )
                connection.execute("DELETE FROM meeting_decisions WHERE session_id=?", (session_id,))
                connection.execute("DELETE FROM meeting_action_items WHERE session_id=?", (session_id,))
                for position, decision in enumerate(decisions):
                    value = _clean(decision, 700)
                    if value:
                        connection.execute(
                            "INSERT INTO meeting_decisions (session_id, position, text) VALUES (?, ?, ?)",
                            (session_id, position, value),
                        )
                for position, raw in enumerate(action_items):
                    if not isinstance(raw, dict):
                        continue
                    title = _clean(raw.get("title"), 500)
                    if not title:
                        continue
                    due_text = _clean(raw.get("due_text"), 160)
                    due_at = raw.get("due_at") if _parse_iso(raw.get("due_at")) else None
                    if due_at is None and due_text:
                        parsed_due = parse_local_datetime(due_text, now=_now_local(now))
                        due_at = _iso(parsed_due) if parsed_due else None
                    connection.execute(
                        """
                        INSERT INTO meeting_action_items
                            (session_id, position, title, owner, due_text, due_at, status)
                        VALUES (?, ?, ?, ?, ?, ?, 'proposed')
                        """,
                        (session_id, position, title, _clean(raw.get("owner"), 120), due_text, due_at),
                    )
                return dict(connection.execute("SELECT * FROM meeting_sessions WHERE id=?", (session_id,)).fetchone())
        finally:
            connection.close()

    def latest_review_meeting_id(self) -> str | None:
        connection = self._connect()
        try:
            row = connection.execute(
                """
                SELECT id FROM meeting_sessions
                WHERE status='review' AND EXISTS (
                    SELECT 1 FROM meeting_action_items
                    WHERE session_id=meeting_sessions.id AND status='proposed'
                )
                ORDER BY started_at DESC LIMIT 1
                """
            ).fetchone()
            return str(row["id"]) if row else None
        finally:
            connection.close()

    def confirm_meeting_actions(
        self, session_id: str, positions: Iterable[int] | None = None
    ) -> list[dict[str, Any]]:
        if not SAFE_ID_RE.fullmatch(session_id):
            return []
        confirm_all = positions is None
        selected = {
            int(value) for value in (positions or [])
            if isinstance(value, int) or str(value).isdigit()
        }
        connection = self._connect()
        created: list[dict[str, Any]] = []
        try:
            rows = connection.execute(
                """
                SELECT * FROM meeting_action_items
                WHERE session_id=? AND status='proposed' ORDER BY position
                """,
                (session_id,),
            ).fetchall()
            for row in rows:
                if not confirm_all and int(row["position"]) not in selected:
                    continue
                task = self.create_task(
                    str(row["title"]), due_at=row["due_at"], source=f"meeting:{session_id}"
                )
                created.append(task)
                with connection:
                    connection.execute(
                        "UPDATE meeting_action_items SET status='confirmed', task_id=? WHERE id=?",
                        (task["id"], row["id"]),
                    )
            with connection:
                pending = connection.execute(
                    "SELECT 1 FROM meeting_action_items WHERE session_id=? AND status='proposed' LIMIT 1",
                    (session_id,),
                ).fetchone()
                if pending is None:
                    connection.execute(
                        "UPDATE meeting_sessions SET status='completed', updated_at=? WHERE id=?",
                        (_iso(_now_local()), session_id),
                    )
            return created
        finally:
            connection.close()

    def create_intelligence_subscription(
        self,
        *,
        title: str,
        prompt: str,
        enabled: bool = False,
        local_time: str = "08:00",
    ) -> dict[str, Any]:
        """Save the owner's open-ended editorial goal without classifying it.

        The prompt is deliberately the source of truth.  There are no domain,
        ticker, keyword, or questionnaire columns: a food-science paper and a
        semiconductor risk paper follow the same generation path.
        """
        clean_prompt = _clean(prompt, 3_000)
        clean_title = _clean(title, 140)
        if not clean_prompt:
            raise ValueError("Describe the newspaper you want MERRICK to prepare.")
        if not clean_title:
            clean_title = clean_prompt[:72].rstrip(" ,.;，。；")
        delivery_time = self._validate_local_time(local_time)
        subscription_id = _new_id("intelligence")
        timestamp = _iso(_now_local())
        connection = self._connect()
        try:
            with connection:
                connection.execute(
                    """
                    INSERT INTO intelligence_subscriptions
                        (id, title, prompt, enabled, local_time, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subscription_id,
                        clean_title,
                        clean_prompt,
                        int(enabled),
                        delivery_time,
                        timestamp,
                        timestamp,
                    ),
                )
                return dict(connection.execute(
                    "SELECT * FROM intelligence_subscriptions WHERE id=?",
                    (subscription_id,),
                ).fetchone())
        finally:
            connection.close()

    def update_intelligence_subscription(
        self,
        subscription_id: str,
        *,
        title: str | None = None,
        prompt: str | None = None,
        enabled: bool | None = None,
        local_time: str | None = None,
    ) -> dict[str, Any] | None:
        if not SAFE_ID_RE.fullmatch(subscription_id):
            return None
        connection = self._connect()
        try:
            current = connection.execute(
                "SELECT * FROM intelligence_subscriptions WHERE id=?",
                (subscription_id,),
            ).fetchone()
            if current is None:
                return None
            clean_title = _clean(title, 140) if title is not None else str(current["title"])
            clean_prompt = _clean(prompt, 3_000) if prompt is not None else str(current["prompt"])
            if not clean_title or not clean_prompt:
                raise ValueError("A title and an editorial goal are required.")
            delivery_time = (
                self._validate_local_time(local_time)
                if local_time is not None else str(current["local_time"])
            )
            with connection:
                connection.execute(
                    """
                    UPDATE intelligence_subscriptions
                    SET title=?, prompt=?, enabled=?, local_time=?, updated_at=?
                    WHERE id=?
                    """,
                    (
                        clean_title,
                        clean_prompt,
                        int(enabled if enabled is not None else bool(current["enabled"])),
                        delivery_time,
                        _iso(_now_local()),
                        subscription_id,
                    ),
                )
            return dict(connection.execute(
                "SELECT * FROM intelligence_subscriptions WHERE id=?",
                (subscription_id,),
            ).fetchone())
        finally:
            connection.close()

    def delete_intelligence_subscription(self, subscription_id: str) -> bool:
        if not SAFE_ID_RE.fullmatch(subscription_id):
            return False
        connection = self._connect()
        try:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM intelligence_subscriptions WHERE id=?",
                    (subscription_id,),
                )
            return cursor.rowcount > 0
        finally:
            connection.close()

    def intelligence_subscription(self, subscription_id: str) -> dict[str, Any] | None:
        if not SAFE_ID_RE.fullmatch(subscription_id):
            return None
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT * FROM intelligence_subscriptions WHERE id=?",
                (subscription_id,),
            ).fetchone()
            return dict(row) if row else None
        finally:
            connection.close()

    def due_intelligence_subscriptions(
        self, *, now: datetime | None = None
    ) -> list[dict[str, Any]]:
        local_now = _now_local(now)
        period_key = local_now.strftime("%Y-%m-%d")
        connection = self._connect()
        try:
            rows = connection.execute(
                """
                SELECT subscriptions.* FROM intelligence_subscriptions AS subscriptions
                WHERE subscriptions.enabled=1
                  AND subscriptions.local_time <= ?
                  AND NOT EXISTS (
                    SELECT 1 FROM intelligence_editions AS editions
                    WHERE editions.subscription_id=subscriptions.id
                      AND editions.period_key=?
                  )
                ORDER BY subscriptions.local_time, subscriptions.created_at
                """,
                (local_now.strftime("%H:%M"), period_key),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def save_intelligence_edition(
        self,
        subscription_id: str,
        *,
        title: str,
        content: dict[str, Any],
        sources: list[dict[str, Any]],
        now: datetime | None = None,
        force: bool = True,
    ) -> dict[str, Any]:
        if not SAFE_ID_RE.fullmatch(subscription_id):
            raise ValueError("Unknown intelligence subscription.")
        local_now = _now_local(now)
        period_key = local_now.strftime("%Y-%m-%d")
        generated_at = _iso(local_now)
        edition_id = _new_id("edition")
        connection = self._connect()
        try:
            with connection:
                if connection.execute(
                    "SELECT 1 FROM intelligence_subscriptions WHERE id=?",
                    (subscription_id,),
                ).fetchone() is None:
                    raise ValueError("Unknown intelligence subscription.")
                verb = "DO UPDATE SET" if force else "DO NOTHING"
                update = (
                    "generated_at=excluded.generated_at, title=excluded.title, "
                    "content_json=excluded.content_json, sources_json=excluded.sources_json"
                )
                connection.execute(
                    f"""
                    INSERT INTO intelligence_editions
                        (id, subscription_id, period_key, generated_at, title, content_json, sources_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(subscription_id, period_key) {verb} {update if force else ''}
                    """,
                    (
                        edition_id,
                        subscription_id,
                        period_key,
                        generated_at,
                        _clean(title, 240) or "MERRICK Intelligence",
                        json.dumps(content, ensure_ascii=False),
                        json.dumps(sources[:12], ensure_ascii=False),
                    ),
                )
                row = connection.execute(
                    """
                    SELECT * FROM intelligence_editions
                    WHERE subscription_id=? AND period_key=?
                    """,
                    (subscription_id, period_key),
                ).fetchone()
            item = dict(row)
            item["content"] = json.loads(item.pop("content_json"))
            item["sources"] = json.loads(item.pop("sources_json"))
            return item
        finally:
            connection.close()

    def work_journal_days(
        self, *, now: datetime | None = None, history_days: int = 370
    ) -> list[dict[str, Any]]:
        """Build a bounded calendar ledger from structured local work events."""
        local_now = _now_local(now)
        cutoff = local_now - timedelta(days=max(31, min(history_days, 730)))
        days: dict[str, dict[str, Any]] = {}

        def add(value: object, bucket: str, item: dict[str, Any]) -> None:
            parsed = _parse_iso(value)
            if parsed is None or parsed < cutoff:
                return
            date_key = _now_local(parsed).strftime("%Y-%m-%d")
            day = days.setdefault(date_key, {
                "date": date_key,
                "created_tasks": [],
                "completed_tasks": [],
                "scheduled_tasks": [],
                "reminders": [],
                "meetings": [],
                "projects": [],
            })
            if len(day[bucket]) < 40:
                day[bucket].append(item)

        connection = self._connect()
        try:
            for row in connection.execute(
                """
                SELECT tasks.*, projects.title AS project_title
                FROM tasks LEFT JOIN projects ON projects.id=tasks.project_id
                WHERE tasks.created_at>=? OR tasks.completed_at>=? OR tasks.due_at>=?
                ORDER BY tasks.created_at DESC LIMIT 1500
                """,
                (_iso(cutoff), _iso(cutoff), _iso(cutoff)),
            ).fetchall():
                item = dict(row)
                add(row["created_at"], "created_tasks", item)
                add(row["completed_at"], "completed_tasks", item)
                add(row["due_at"], "scheduled_tasks", item)
            for row in connection.execute(
                """SELECT * FROM reminders WHERE created_at>=? OR fire_at>=?
                   ORDER BY fire_at DESC LIMIT 1000""",
                (_iso(cutoff), _iso(cutoff)),
            ).fetchall():
                add(row["fire_at"], "reminders", dict(row))
            for row in connection.execute(
                """SELECT * FROM meeting_sessions WHERE started_at>=?
                   ORDER BY started_at DESC LIMIT 500""",
                (_iso(cutoff),),
            ).fetchall():
                add(row["started_at"], "meetings", dict(row))
            for row in connection.execute(
                """SELECT * FROM projects WHERE created_at>=?
                   ORDER BY created_at DESC LIMIT 500""",
                (_iso(cutoff),),
            ).fetchall():
                add(row["created_at"], "projects", dict(row))
        finally:
            connection.close()

        for day in days.values():
            day["metrics"] = {
                "created": len(day["created_tasks"]),
                "completed": len(day["completed_tasks"]),
                "scheduled": len(day["scheduled_tasks"]),
                "meetings": len(day["meetings"]),
                "reminders": len(day["reminders"]),
                "activity": sum(len(day[key]) for key in (
                    "created_tasks", "completed_tasks", "scheduled_tasks", "reminders", "meetings", "projects"
                )),
            }
        return sorted(days.values(), key=lambda item: item["date"], reverse=True)

    def update_briefing_setting(
        self,
        kind: str,
        *,
        enabled: bool | None = None,
        local_time: str | None = None,
        weekday: int | None = None,
    ) -> dict[str, Any]:
        if kind not in BRIEFING_KINDS:
            raise ValueError("Unknown briefing kind.")
        if local_time is not None and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", local_time):
            raise ValueError("Briefing time is invalid.")
        if weekday is not None and not 0 <= int(weekday) <= 6:
            raise ValueError("Briefing weekday is invalid.")
        connection = self._connect()
        try:
            with connection:
                current = connection.execute(
                    "SELECT * FROM briefing_settings WHERE kind=?", (kind,)
                ).fetchone()
                connection.execute(
                    """
                    UPDATE briefing_settings SET enabled=?, local_time=?, weekday=?, updated_at=?
                    WHERE kind=?
                    """,
                    (
                        int(enabled if enabled is not None else bool(current["enabled"])),
                        local_time or str(current["local_time"]),
                        int(weekday if weekday is not None else current["weekday"]),
                        _iso(_now_local()), kind,
                    ),
                )
                return dict(connection.execute("SELECT * FROM briefing_settings WHERE kind=?", (kind,)).fetchone())
        finally:
            connection.close()

    @staticmethod
    def _period_key(kind: str, now: datetime) -> str:
        if kind == "weekly":
            iso_year, iso_week, _ = now.isocalendar()
            return f"{iso_year}-W{iso_week:02d}"
        return now.strftime("%Y-%m-%d")

    def due_briefing_kinds(self, *, now: datetime | None = None) -> list[str]:
        local_now = _now_local(now)
        connection = self._connect()
        try:
            settings = connection.execute(
                "SELECT * FROM briefing_settings WHERE enabled=1 ORDER BY kind"
            ).fetchall()
            due: list[str] = []
            for setting in settings:
                kind = str(setting["kind"])
                hour, minute = (int(part) for part in str(setting["local_time"]).split(":"))
                if kind == "weekly":
                    scheduled_day = local_now - timedelta(days=(local_now.weekday() - int(setting["weekday"])) % 7)
                    scheduled = scheduled_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    scheduled = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if local_now < scheduled:
                    continue
                period_key = self._period_key(kind, local_now)
                exists = connection.execute(
                    "SELECT 1 FROM briefings WHERE kind=? AND period_key=?",
                    (kind, period_key),
                ).fetchone()
                if exists is None:
                    due.append(kind)
            return due
        finally:
            connection.close()

    def _task_rows(self, where: str, args: tuple[Any, ...]) -> list[dict[str, Any]]:
        connection = self._connect()
        try:
            rows = connection.execute(
                f"""
                SELECT tasks.*, projects.title AS project_title
                FROM tasks LEFT JOIN projects ON projects.id=tasks.project_id
                WHERE {where} ORDER BY COALESCE(tasks.due_at, '9999'), tasks.created_at DESC LIMIT 30
                """,
                args,
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            connection.close()

    def _briefing_operational_context(
        self,
        *,
        now: datetime,
        week_start: datetime,
        next_week: datetime,
    ) -> dict[str, int]:
        """Return bounded local facts used by the editorial briefing layer."""
        connection = self._connect()
        try:
            task_counts = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_tasks,
                    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_tasks,
                    SUM(CASE WHEN status='completed' AND completed_at>=? AND completed_at<? THEN 1 ELSE 0 END) AS completed_week
                FROM tasks
                """,
                (_iso(week_start), _iso(next_week)),
            ).fetchone()
            project_count = connection.execute(
                "SELECT COUNT(*) AS count FROM projects WHERE status='active'"
            ).fetchone()
            reminder_count = connection.execute(
                "SELECT COUNT(*) AS count FROM reminders WHERE status='pending' AND fire_at>=?",
                (_iso(now),),
            ).fetchone()
            return {
                "open_tasks": int(task_counts["open_tasks"] or 0),
                "completed_tasks": int(task_counts["completed_tasks"] or 0),
                "completed_week": int(task_counts["completed_week"] or 0),
                "active_projects": int(project_count["count"] or 0),
                "pending_reminders": int(reminder_count["count"] or 0),
            }
        finally:
            connection.close()

    def generate_briefing(
        self, kind: str, *, now: datetime | None = None, force: bool = False
    ) -> dict[str, Any]:
        if kind not in BRIEFING_KINDS:
            raise ValueError("Unknown briefing kind.")
        local_now = _now_local(now)
        today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today_start + timedelta(days=1)
        next_day = tomorrow + timedelta(days=1)
        week_start = today_start - timedelta(days=today_start.weekday())
        next_week = week_start + timedelta(days=7)
        if kind == "morning":
            title = f"Morning briefing · {local_now.strftime('%A, %d %B')}"
            due = self._task_rows("tasks.status='open' AND tasks.due_at>=? AND tasks.due_at<?", (_iso(today_start), _iso(tomorrow)))
            overdue = self._task_rows("tasks.status='open' AND tasks.due_at<?", (_iso(today_start),))
            upcoming = self._task_rows("tasks.status='open' AND tasks.due_at>=? AND tasks.due_at<?", (_iso(tomorrow), _iso(next_day)))
            headline = "A clear view of today, before the day acquires opinions of its own."
            sections = [
                {"key": "dueToday", "title": "Due today", "items": due},
                {"key": "overdueSection", "title": "Overdue", "items": overdue},
                {"key": "tomorrowSection", "title": "Tomorrow", "items": upcoming},
            ]
            headline_zh = "在一天形成自己的节奏之前，先看清今天。"
        elif kind == "evening":
            title = f"Evening review · {local_now.strftime('%A, %d %B')}"
            completed = self._task_rows("tasks.status='completed' AND tasks.completed_at>=? AND tasks.completed_at<?", (_iso(today_start), _iso(tomorrow)))
            remaining = self._task_rows("tasks.status='open' AND (tasks.due_at IS NULL OR tasks.due_at<?)", (_iso(tomorrow),))
            tomorrow_tasks = self._task_rows("tasks.status='open' AND tasks.due_at>=? AND tasks.due_at<?", (_iso(tomorrow), _iso(next_day)))
            headline = "The day is accounted for; unfinished business remains visible, not forgotten."
            sections = [
                {"key": "completedToday", "title": "Completed today", "items": completed},
                {"key": "stillOpen", "title": "Still open", "items": remaining},
                {"key": "tomorrowSection", "title": "Tomorrow", "items": tomorrow_tasks},
            ]
            headline_zh = "今天已经有了交代；未完成的事情仍然清晰可见，不会被遗忘。"
        else:
            title = f"Weekly report · Week {local_now.isocalendar().week:02d}"
            completed = self._task_rows("tasks.status='completed' AND tasks.completed_at>=? AND tasks.completed_at<?", (_iso(week_start), _iso(next_week)))
            overdue = self._task_rows("tasks.status='open' AND tasks.due_at<?", (_iso(local_now),))
            upcoming = self._task_rows("tasks.status='open' AND tasks.due_at>=? AND tasks.due_at<?", (_iso(local_now), _iso(local_now + timedelta(days=7))))
            headline = "The week in one operational view: progress, exposure, and what comes next."
            sections = [
                {"key": "completedWeek", "title": "Completed this week", "items": completed},
                {"key": "needsAttention", "title": "Needs attention", "items": overdue},
                {"key": "nextSevenDays", "title": "Next seven days", "items": upcoming},
            ]
            headline_zh = "用一个工作视图看清本周：进展、风险和下一步。"
        primary_count = len(sections[0]["items"])
        attention_count = len(sections[1]["items"])
        upcoming_count = len(sections[2]["items"])
        context = self._briefing_operational_context(
            now=local_now,
            week_start=week_start,
            next_week=next_week,
        )
        if kind == "morning":
            clarity_score = max(8, 100 - attention_count * 18 - primary_count * 7)
            edition = "Morning Edition"
            edition_zh = "晨间版"
            if attention_count:
                analysis_title = f"Begin with {attention_count} exposed commitment{'s' if attention_count != 1 else ''}."
                analysis_title_zh = f"先处理 {attention_count} 项已暴露的承诺。"
                risk = "high" if attention_count >= 3 else "guarded"
            elif primary_count:
                analysis_title = f"Today is defined by {primary_count} dated priorit{'ies' if primary_count != 1 else 'y'}."
                analysis_title_zh = f"今天由 {primary_count} 项明确时限任务决定节奏。"
                risk = "guarded" if primary_count >= 4 else "clear"
            else:
                analysis_title = "The dated runway is clear; choose the highest-value move deliberately."
                analysis_title_zh = "今天没有明确到期压力，应主动选择价值最高的一步。"
                risk = "clear"
            analysis_items = [
                {
                    "tone": "priority",
                    "label": "First move",
                    "label_zh": "第一步",
                    "text": (
                        f"Resolve the overdue queue before adding new work; {attention_count} item(s) are already exposed."
                        if attention_count
                        else (
                            f"Protect the first focus block for the {primary_count} item(s) due today."
                            if primary_count
                            else "Use the first focus block to define the next concrete action for the active portfolio."
                        )
                    ),
                    "text_zh": (
                        f"先清理逾期队列，再增加新工作；当前已有 {attention_count} 项暴露。"
                        if attention_count
                        else (
                            f"把第一个专注时段留给今天到期的 {primary_count} 项任务。"
                            if primary_count
                            else "用第一个专注时段，为当前项目组合确定下一项具体行动。"
                        )
                    ),
                },
                {
                    "tone": "horizon",
                    "label": "Horizon",
                    "label_zh": "前瞻",
                    "text": f"{upcoming_count} dated item(s) sit on tomorrow's horizon.",
                    "text_zh": f"明天有 {upcoming_count} 项明确时限任务。",
                },
                {
                    "tone": "system",
                    "label": "System coverage",
                    "label_zh": "系统覆盖",
                    "text": f"{context['pending_reminders']} future reminder(s) protect {context['open_tasks']} open task(s) across {context['active_projects']} active project(s).",
                    "text_zh": f"当前 {context['pending_reminders']} 个未来提醒，覆盖 {context['active_projects']} 个活跃项目中的 {context['open_tasks']} 项未完成任务。",
                },
            ]
        elif kind == "evening":
            total_accounted = primary_count + attention_count
            clarity_score = round(primary_count / total_accounted * 100) if total_accounted else 100
            edition = "Evening Edition"
            edition_zh = "晚间版"
            risk = "high" if attention_count >= 5 else "guarded" if attention_count else "clear"
            analysis_title = (
                f"{primary_count} closed; {attention_count} remain visible."
                if total_accounted
                else "The day closes without an exposed task queue."
            )
            analysis_title_zh = (
                f"今天完成 {primary_count} 项，仍有 {attention_count} 项保持可见。"
                if total_accounted
                else "今天结束时没有暴露的任务队列。"
            )
            analysis_items = [
                {"tone": "priority", "label": "Close", "label_zh": "收尾", "text": f"{attention_count} open item(s) need an explicit defer, delegate, or finish decision.", "text_zh": f"仍有 {attention_count} 项需要明确决定：延期、委派或完成。"},
                {"tone": "horizon", "label": "Tomorrow", "label_zh": "明天", "text": f"{upcoming_count} dated item(s) are already visible for tomorrow.", "text_zh": f"明天已有 {upcoming_count} 项明确时限任务。"},
                {"tone": "system", "label": "Momentum", "label_zh": "进展", "text": f"{context['completed_week']} task(s) have been completed this week.", "text_zh": f"本周已完成 {context['completed_week']} 项任务。"},
            ]
        else:
            total_accounted = primary_count + attention_count
            clarity_score = round(primary_count / total_accounted * 100) if total_accounted else 100
            edition = f"Week {local_now.isocalendar().week:02d} Edition"
            edition_zh = f"第 {local_now.isocalendar().week:02d} 周版"
            risk = "high" if attention_count >= 5 else "guarded" if attention_count else "clear"
            analysis_title = f"The week closes with {primary_count} completions and {attention_count} exposed commitment(s)."
            analysis_title_zh = f"本周完成 {primary_count} 项，仍有 {attention_count} 项承诺暴露。"
            analysis_items = [
                {"tone": "priority", "label": "Exposure", "label_zh": "风险敞口", "text": f"{attention_count} overdue item(s) require an owner and a reset date.", "text_zh": f"{attention_count} 项逾期任务需要明确负责人和新的日期。"},
                {"tone": "horizon", "label": "Next seven days", "label_zh": "未来七天", "text": f"{upcoming_count} dated item(s) define the forward workload.", "text_zh": f"未来七天的工作量由 {upcoming_count} 项明确时限任务构成。"},
                {"tone": "system", "label": "Portfolio", "label_zh": "项目组合", "text": f"{context['open_tasks']} open task(s) remain across {context['active_projects']} active project(s).", "text_zh": f"{context['active_projects']} 个活跃项目中仍有 {context['open_tasks']} 项未完成任务。"},
            ]
        content = {
            "schema_version": 2,
            "publication": {
                "masthead": "The Daily MERRICK",
                "masthead_zh": "MERRICK 每日简报",
                "edition": edition,
                "edition_zh": edition_zh,
                "dateline": local_now.strftime("%A, %d %B %Y · %H:%M"),
            },
            "headline": headline,
            "headline_zh": headline_zh,
            "metrics": {
                "primary": primary_count,
                "attention": attention_count,
                "upcoming": upcoming_count,
                "clarity": clarity_score,
            },
            "context": context,
            "analysis": {
                "title": analysis_title,
                "title_zh": analysis_title_zh,
                "risk": risk,
                "items": analysis_items,
            },
            "visual": {
                "label": "Operational clarity · derived",
                "label_zh": "工作清晰度 · 派生指标",
                "score": clarity_score,
                "risk": risk,
                "series": [
                    {"key": "primary", "label": sections[0]["title"], "value": primary_count},
                    {"key": "attention", "label": sections[1]["title"], "value": attention_count},
                    {"key": "upcoming", "label": sections[2]["title"], "value": upcoming_count},
                ],
            },
            "sections": sections,
            "data_note": "Local MERRICK projects, tasks and reminders. Clarity is a derived workload signal, not an external benchmark.",
            "data_note_zh": "数据来自本机 MERRICK 项目、任务与提醒；清晰度为工作量派生信号，不是外部基准。",
        }
        briefing_id = _new_id("briefing")
        generated_at = _iso(local_now)
        period_key = self._period_key(kind, local_now)
        connection = self._connect()
        try:
            with connection:
                if force:
                    connection.execute(
                        """
                        INSERT INTO briefings
                            (id, kind, period_key, generated_at, title, content_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(kind, period_key) DO UPDATE SET
                            generated_at=excluded.generated_at,
                            title=excluded.title,
                            content_json=excluded.content_json
                        """,
                        (briefing_id, kind, period_key, generated_at, title, json.dumps(content, ensure_ascii=False)),
                    )
                else:
                    connection.execute(
                        """
                        INSERT OR IGNORE INTO briefings
                            (id, kind, period_key, generated_at, title, content_json)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (briefing_id, kind, period_key, generated_at, title, json.dumps(content, ensure_ascii=False)),
                    )
                row = connection.execute(
                    "SELECT * FROM briefings WHERE kind=? AND period_key=?",
                    (kind, period_key),
                ).fetchone()
                result = dict(row)
                result["content"] = json.loads(result.pop("content_json"))
                return result
        finally:
            connection.close()

    def snapshot(self, *, now: datetime | None = None) -> dict[str, Any]:
        local_now = _now_local(now)
        connection = self._connect()
        try:
            projects = [dict(row) for row in connection.execute(
                """
                SELECT projects.*,
                       SUM(CASE WHEN tasks.status='open' THEN 1 ELSE 0 END) AS open_tasks,
                       COUNT(tasks.id) AS total_tasks
                FROM projects LEFT JOIN tasks ON tasks.project_id=projects.id
                GROUP BY projects.id ORDER BY projects.updated_at DESC LIMIT 50
                """
            ).fetchall()]
            tasks = [dict(row) for row in connection.execute(
                """
                SELECT tasks.*, projects.title AS project_title
                FROM tasks LEFT JOIN projects ON projects.id=tasks.project_id
                ORDER BY CASE tasks.status WHEN 'open' THEN 0 ELSE 1 END,
                         COALESCE(tasks.due_at, '9999'), tasks.updated_at DESC LIMIT 120
                """
            ).fetchall()]
            reminders = [dict(row) for row in connection.execute(
                """
                SELECT * FROM reminders
                ORDER BY CASE status WHEN 'pending' THEN 0 ELSE 1 END,
                         CASE WHEN status='pending' THEN fire_at END ASC,
                         fire_at DESC LIMIT 80
                """
            ).fetchall()]
            settings = [dict(row) for row in connection.execute(
                "SELECT * FROM briefing_settings ORDER BY CASE kind WHEN 'morning' THEN 0 WHEN 'evening' THEN 1 ELSE 2 END"
            ).fetchall()]
            briefings: list[dict[str, Any]] = []
            for row in connection.execute("SELECT * FROM briefings ORDER BY generated_at DESC LIMIT 18").fetchall():
                item = dict(row)
                try:
                    item["content"] = json.loads(item.pop("content_json"))
                except (TypeError, ValueError):
                    item["content"] = {}
                briefings.append(item)
            subscriptions = [dict(row) for row in connection.execute(
                """
                SELECT subscriptions.*,
                       COUNT(editions.id) AS edition_count,
                       MAX(editions.generated_at) AS last_generated_at
                FROM intelligence_subscriptions AS subscriptions
                LEFT JOIN intelligence_editions AS editions
                  ON editions.subscription_id=subscriptions.id
                GROUP BY subscriptions.id
                ORDER BY subscriptions.updated_at DESC LIMIT 50
                """
            ).fetchall()]
            intelligence_editions: list[dict[str, Any]] = []
            for row in connection.execute(
                "SELECT * FROM intelligence_editions ORDER BY generated_at DESC LIMIT 50"
            ).fetchall():
                item = dict(row)
                try:
                    item["content"] = json.loads(item.pop("content_json"))
                except (TypeError, ValueError):
                    item["content"] = {}
                try:
                    item["sources"] = json.loads(item.pop("sources_json"))
                except (TypeError, ValueError):
                    item["sources"] = []
                intelligence_editions.append(item)
            meetings: list[dict[str, Any]] = []
            for row in connection.execute(
                "SELECT * FROM meeting_sessions ORDER BY started_at DESC LIMIT 20"
            ).fetchall():
                meeting = dict(row)
                meeting["decisions"] = [dict(value) for value in connection.execute(
                    "SELECT position, text FROM meeting_decisions WHERE session_id=? ORDER BY position",
                    (row["id"],),
                ).fetchall()]
                meeting["action_items"] = [dict(value) for value in connection.execute(
                    """
                    SELECT position, title, owner, due_text, due_at, status, task_id
                    FROM meeting_action_items WHERE session_id=? ORDER BY position
                    """,
                    (row["id"],),
                ).fetchall()]
                meeting["transcript_count"] = int(connection.execute(
                    "SELECT COUNT(*) AS count FROM meeting_transcript_entries WHERE session_id=?",
                    (row["id"],),
                ).fetchone()["count"])
                meetings.append(meeting)
            stats = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN status='open' THEN 1 ELSE 0 END) AS open_tasks,
                    SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed_tasks,
                    SUM(CASE WHEN status='open' AND due_at IS NOT NULL AND due_at < ? THEN 1 ELSE 0 END) AS overdue_tasks
                FROM tasks
                """,
                (_iso(local_now),),
            ).fetchone()
            return {
                "generated_at": _iso(local_now),
                "stats": {key: int(stats[key] or 0) for key in stats.keys()},
                "projects": projects,
                "tasks": tasks,
                "reminders": reminders,
                "meetings": meetings,
                "briefings": briefings,
                "briefing_settings": settings,
                "intelligence_subscriptions": subscriptions,
                "intelligence_editions": intelligence_editions,
                "work_journal_days": self.work_journal_days(now=local_now),
            }
        finally:
            connection.close()
