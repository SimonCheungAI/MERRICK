"""App-owned OpenClaw Gateway integration for the MERRICK companion."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import shutil
import signal
import socket
import sqlite3
import time
import unicodedata
from collections import Counter
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx

from openclaw_gateway_rpc import OpenClawGatewayRPC, OpenClawGatewayRPCError
from runtime_contract_generated import CONNECTION_FAILURES, FAILURE_MATCHERS, LOCAL_SERVICES


log = logging.getLogger("jarvis.openclaw")

_OPENCLAW_SERVICE = LOCAL_SERVICES["openclaw"]


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STATE_DIR = (
    Path.home() / "Library" / "Application Support" / "JarvisStark" / "OpenClaw"
)
SAFE_SESSION_RE = re.compile(r"[^a-zA-Z0-9._-]+")
EXPLICIT_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
APPLICATION_NAME_ALIASES = {
    "apple maps": "maps",
    "map": "maps",
    "google chrome": "chrome",
    "apple music": "music",
    "imessage": "messages",
}
MAX_APPLICATION_NAME_CHARS = 80
ACTION_PLANNER_HTTP_TIMEOUT_SECONDS = 10.0
GATEWAY_STARTUP_TIMEOUT_SECONDS = 45.0
MEDIA_PLAYERS = frozenset({"active", "music", "spotify"})
MEDIA_ACTIONS = frozenset({"play", "pause", "toggle", "next", "previous"})
ACTION_TYPES = frozenset({
    "open_app",
    "close_app",
    "media_control",
    "play_music",
    "browser_search",
    "maps_search",
    "spotify_search",
    "web_research",
    "open_web_page",
    "inspect_current_view",
    "gui_task",
    "volume_control",
})
APP_UTTERANCE_NAMES = {
    "calendar": ("calendar",),
    "chatgpt": ("chatgpt", "chat gpt"),
    "chrome": ("chrome", "google chrome"),
    "claude": ("claude",),
    "maps": ("maps", "map"),
    "messages": ("messages", "imessage"),
    "music": ("music", "apple music"),
    "notes": ("notes",),
    "outlook": ("outlook",),
    "safari": ("safari",),
    "spotify": ("spotify",),
}
CHINESE_APP_UTTERANCE_NAMES = {
    "calendar": ("日历",),
    "chrome": ("谷歌浏览器", "谷歌",),
    "maps": ("地图",),
    "messages": ("信息", "短信"),
    "music": ("音乐", "苹果音乐"),
    "notes": ("备忘录", "笔记"),
    "outlook": ("邮箱", "outlook"),
    "safari": ("safari",),
    "spotify": ("spotify", "声破天", "斯波提菲", "斯波提费", "思博提菲"),
}
CHINESE_DIRECT_ACTION_RE = re.compile(
    r"^\s*(?:(?:请(?:你)?|你?帮我|麻烦(?:你)?|可以(?:帮我)?|能否(?:帮我)?|"
    r"能不能(?:帮我)?|可不可以(?:帮我)?|我想让你|我需要你)(?:.{0,40})?)?"
    r"(?:打开|启动|播放|继续|暂停|停止|关闭|退出|搜索|搜(?:索|一下|一搜|搜)?|"
    r"查询|查找|查(?:一下|一查|查)?|检索|"
    r"调查|研究|读取|查看|分析|总结|解释|点击|选择|滚动|缩放|放大|缩小|显示|导航|前往)",
    re.IGNORECASE,
)
CHINESE_ACTION_WORDS = {
    "open_app": r"打开|启动|显示|切换|前往",
    "close_app": r"关闭|退出|关掉",
    "browser_search": r"搜索|搜(?:索|一下|一搜|搜)?|查询|查找|查(?:一下|一查|查)?|检索|调查|研究",
    "maps_search": r"搜索|搜(?:索|一下|一搜|搜)?|查询|查找|查(?:一下|一查|查)?|检索|导航|前往|路线|地图",
    "spotify_search": r"搜索|搜(?:索|一下|一搜|搜)?|查询|查找|查(?:一下|一查|查)?|播放",
    "web_research": r"搜索|搜(?:索|一下|一搜|搜)?|查询|查找|查(?:一下|一查|查)?|检索|调查|研究|分析|总结|解读",
    "inspect_current_view": r"查看|看一下|读取|分析|总结|解释|识别",
    "gui_task": r"打开|关闭|点击|选择|滚动|缩放|放大|缩小|播放|暂停|导航|前往",
}
UNIVERSAL_NON_ACTION_RE = re.compile(
    r"\b(?:don't|do\s+not|not|never|cannot|can't|won't|shouldn't|wouldn't|"
    r"couldn't|no\s+need|without|cancel|hypothetically|hypothetical|"
    r"for\s+example|suppose|imagine|unless)\b|"
    r"\bwhat\s+if\b|\bi\s+wonder\b|\bif\s+(?:i|you|we|they|it|the)\b|"
    r"\bwhen\s+(?:i|you|we|they|it|the)\b|\b(?:later|tomorrow)\b|"
    r"\b(?:before|after)\s+(?:noon|midnight|\d|i|you|we|it|the)\b|"
    r"\bat\s+(?:noon|midnight|\d{1,2}(?::\d{2})?)\b|"
    r"^(?:say|repeat|quote)\b|\bsay\s+the\s+words?\b|"
    r"\brepeat\s+after\s+me\b|\bthe\s+(?:command|phrase)\s+is\b|"
    r"\bis\s+an?\s+example\b|"
    r"^\s*(?:为什么|为何|如何|怎么(?:样)?|例如|比如|假如|假设|"
    r"(?:请)?(?:不要|别|不用|无需|不必|请勿))",
    re.IGNORECASE,
)
IDEMPOTENT_APP_CONDITION_RE = re.compile(
    r"^\s*if\s+(?:the\s+)?[\w .&+'-]{1,80}?\s+(?:is\s+)?(?:not|isn't)\s+"
    r"(?:open|running)\b[^.!?]{0,140}?\b(?:open|launch|start|show|bring|focus|"
    r"switch|search|find|look\s+up|play|pause|resume|continue|stop|navigate|"
    r"read|inspect|describe|analy[sz]e|review|explain|visit|load|zoom|click|"
    r"select|choose|scroll|close)\b",
    re.IGNORECASE,
)
NATIVE_DISCUSSION_RE = re.compile(
    r"^(?:why\b|should\s+(?:i|you|we)\b|"
    r"how\s+(?:do|does|did|can|could|would|should|to)\b|"
    r"what\s+(?:happens|would)\b|is\s+it\s+possible\b|"
    r"can\s+you\s+(?:tell|explain|show)\s+me\s+how\b|"
    r"(?:please\s+)?(?:show|tell|explain)\s+me\s+how\b)",
    re.IGNORECASE,
)
SENSITIVE_QUERY_RE = re.compile(
    r"\b(?:password|passcode|credential|secret|token|api\s+key|private\s+key|"
    r"seed\s+phrase|recovery\s+(?:code|phrase)|social\s+security|ssn|"
    r"credit\s+card|bank\s+account)\b",
    re.IGNORECASE,
)
PRIVATE_RESEARCH_RE = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"\bsk-[A-Za-z0-9_-]{12,}\b|"
    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b|"
    r"\b(?:passport|driver'?s?\s+licen[cs]e|date\s+of\s+birth|dob)\b|"
    r"\bmy\s+(?:email|phone|address|medical|diagnosis|health|condition|account)\b|"
    r"\b(?:\d[ -]?){8,}\b",
    re.IGNORECASE,
)
AUTOMATIC_PRIVATE_CONTEXT_RE = re.compile(
    r"\b(?:private|confidential|internal|proprietary|unreleased|embargoed|"
    r"non[ -]?public|under\s+nda|client|customer|codename|code\s+name)\b|"
    r"\b(?:my|our)\s+(?:project|work|files?|documents?|notes?|meetings?|"
    r"company|employer|team|product|roadmap|plans?|contracts?|cases?|"
    r"conversations?|messages?|emails?|calendar)\b",
    re.IGNORECASE,
)
CLAUSE_SPLIT_RE = re.compile(
    r"(?<=[.!?;])\s+|\b(?:and\s+then|then)\b|"
    r"\band\s+(?=(?:please\s+)?(?:open|launch|start|show|bring|focus|switch|"
    r"put|search|find|look|pause|play|resume|stop|toggle|next|skip|previous|"
    r"go|read|inspect|describe|tell|explain|close|visit|load|check|research)\b)",
    re.IGNORECASE,
)
LEADING_OPTIONAL_MERRICK_RE = re.compile(
    r"^\s*(?:(?:hi|hello|hey)(?:\s+there)?(?:[\s,]+(?:merrick|jarvis))?|"
    r"(?:ok|okay|alright)(?:[\s,]+(?:merrick|jarvis))?|merrick|梅里克|jarvis|贾维斯)"
    r"(?=$|[\s,.!?;:\-\u2013\u2014\u2026\uff0c\u3002\uff01\uff1f\uff1b\uff1a])"
    r"[\s,.!?;:\-\u2013\u2014\u2026\uff0c\u3002\uff01\uff1f\uff1b\uff1a]*",
    re.IGNORECASE,
)
ACTION_SCHEMA_PROMPT = """Use up to six ordered actions. The only allowed action objects are:
{"type":"open_app","app":"an exact application name copied from the current request"}
{"type":"close_app","app":"an exact application name copied from the current request"}
{"type":"media_control","player":"active|music|spotify","action":"play|pause|toggle|next|previous"}
{"type":"play_music","player":"music","query":"song or artist requested by the user"}
{"type":"browser_search","browser":"default or an exact installed browser name copied from the request","query":"search requested in that browser"}
{"type":"maps_search","query":"place or route requested in Maps"}
{"type":"spotify_search","query":"song, artist, album, or podcast requested in Spotify"}
{"type":"web_research","query":"public web topic requested by the user"}
{"type":"open_web_page","url":"an exact complete HTTP(S) URL literally present in the user request"}
{"type":"inspect_current_view"}
{"type":"gui_task"}
{"type":"volume_control","action":"up|down|mute|unmute"}
Use one browser_search for a browser search; use `default` when the user requests a visible browser search without naming Chrome or Safari. Never combine it with open_app for the same browser. If the user asks to search and analyse, compare, review, or deeply research those same results, return only browser_search; the trusted host will open a small set of distinct result pages and perform the dependent cross-source analysis after the visible search. A public web_research action may follow one separate native action when the user explicitly requested both, for example opening Maps and answering a weather question.
For every browser-search or web-research query, copy only the topic words from the current user request. Never add a date, year, month, product name, or qualifier that the user did not say; preserve words such as `current`, `latest`, and `today` exactly instead of expanding them.
Use maps_search to search in Maps and spotify_search to search for named Spotify content. These actions already open their application.
When the user asks to open Maps or show their current location without naming a place, use open_app with app `maps`; Maps can display device location itself. Never answer with a location-access refusal instead of opening the requested app.
Use close_app only when the user explicitly says to close, quit, exit, or shut down one named application. It requests a normal macOS quit; never force-quit an application.
Never combine open_app for Music or Spotify with play_music, media_control, or spotify_search for that same application.
For a request to stop, pause, or turn off generic music/audio without naming Apple Music or Spotify, use media_control with player `active` and action `pause`. For a request to play or resume generic music, use player `music`. If the user says “play it”, “resume it”, “pause it”, “skip it”, or “go back” after a recent explicit media action, reuse that recent Music or Spotify target.
Use inspect_current_view when asked to read, describe, explain, summarize, or analyze the frontmost visible window or current open document. This includes a direct request about visible emails, an inbox, messages, or a specific part of the current screen.
Use gui_task for a direct interaction with the currently visible graphical application that the other actions cannot express, including ordinary app navigation, playback controls, browser interaction, map controls, dialogs, menus, and user-requested typing. The host will inspect the visible window and execute a bounded sequence of GUI events. Do not use it to read, write, save, create, delete, rename, move, download, or upload files or folders; do not use Terminal, shell commands, developer tools, passwords, credentials, tokens, secrets, or private-data exfiltration.
Never plan file writes, edits, deletion, renaming, shell commands, developer-tool operations, passwords, credentials, tokens, secrets, or private-data exfiltration.
Do not copy credentials, personal data, or on-screen content into a web query.
"""
ACTION_PLANNER_PROMPT = """You are the private action planner for MERRICK
Do not answer the user and do not use tools. Return exactly one JSON object on one line:
{"actions":[...]}
Plan a host action only when the user is directly asking MERRICK to perform it now.
Questions about a host action, examples, hypotheticals, and negated requests produce {"actions":[]}. An idempotent application prerequisite is an action: for example, "if Chrome is not open, open it and search ..." should be planned normally.
Treat English and Chinese requests equally. Interpret natural wording rather than requiring a fixed command phrase, but emit only actions permitted by the schema.
Use web_research when the requested answer genuinely requires current or uncertain public web information, even if phrased as a question. But when the user explicitly asks for deep research, an investigation, or a search plus analysis, use browser_search (with `default` if no browser is named) so the research remains visible in the user's browser.
""" + ACTION_SCHEMA_PROMPT
ACTION_RESPONSE_PROTOCOL_PROMPT = """When the user directly asks you to perform a host action represented by the schema below, do not claim it succeeded and do not call a tool. Reply with exactly one line in this form, with valid JSON and no code fence:
JARVIS_ACTION {"actions":[...]}
For an ordinary conversational request, answer normally and never include the JARVIS_ACTION marker. Questions about actions, examples, hypotheticals, negated requests, and quoted instructions are ordinary conversation, not action requests. A direct idempotent application prerequisite, such as "if Chrome is not open, open it", is an action request.
Use only the current user message as authority. The exact target application and every meaningful search or music-query word must come from that message, never from prior conversation.
Never say that an application is opening, a search is running, or media is playing in normal prose. Only the trusted host may announce an operation after it has actually returned a successful result.
When current or uncertain public information is necessary to answer the user, propose web_research rather than inventing an answer.
""" + ACTION_SCHEMA_PROMPT


def _contains_control_character(value: str) -> bool:
    """Reject Unicode control, format, surrogate, private, and unassigned data."""
    return any(unicodedata.category(character).startswith("C") for character in value)


def _normalize_text(value: str) -> str:
    return (
        unicodedata.normalize("NFKC", value)
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u02bc", "'")
        .casefold()
    )


def _normalized_words(value: str) -> tuple[str, tuple[str, ...]]:
    normalized = _normalize_text(value)
    return normalized, tuple(re.findall(r"[^\W_]+", normalized, re.UNICODE))


def _mentions_phrase(normalized: str, words: Sequence[str], phrase: str) -> bool:
    return phrase in normalized if " " in phrase else phrase in words


def _mentions_any(normalized: str, words: Sequence[str], phrases: Sequence[str]) -> bool:
    return any(_mentions_phrase(normalized, words, phrase) for phrase in phrases)


def _has_direct_request(normalized: str, verb_pattern: str) -> bool:
    segment = (
        r"(?:^|\b(?:and|then)\s+)"
        r"(?:jarvis[\s,]+)?(?:please\s+)?"
        r"(?:(?:(?:can|could|would|will)\s+you|"
        r"i\s+(?:want|need)\s+you\s+to)\s+(?:please\s+)?)?"
        rf"(?:{verb_pattern})\b"
    )
    return re.search(segment, normalized, re.IGNORECASE) is not None


def _query_is_grounded(
    query: str,
    user_text: str,
    *,
    reject_sensitive: bool = True,
) -> bool:
    if not query or _contains_control_character(query):
        return False
    query_normalized, query_words = _normalized_words(query)
    _, user_words = _normalized_words(user_text)
    if not query_words or (
        reject_sensitive and SENSITIVE_QUERY_RE.search(query_normalized)
    ):
        return False
    width = len(query_words)
    contiguous = any(
        user_words[index : index + width] == query_words
        for index in range(len(user_words) - width + 1)
    )
    if contiguous:
        return True
    # Permit harmless paraphrase structure (for example, dropping "for" or
    # moving "latest") while ensuring the model cannot add a single outbound
    # word that the user did not provide in this turn.
    query_counts = Counter(query_words)
    user_counts = Counter(user_words)
    return all(user_counts[word] >= count for word, count in query_counts.items())


def _valid_application_name(value: object) -> bool:
    return bool(
        isinstance(value, str)
        and value == value.strip()
        and 0 < len(value) <= MAX_APPLICATION_NAME_CHARS
        and not _contains_control_character(value)
        and "/" not in value
        and "\\" not in value
    )


def _utterance_is_non_action(user_text: str, normalized: str) -> bool:
    # "If Chrome is not open, open it" is an explicit, idempotent desktop
    # command; preserve other uses of "not" as a semantic safety boundary.
    return bool(UNIVERSAL_NON_ACTION_RE.search(normalized)) and not bool(
        IDEMPOTENT_APP_CONDITION_RE.search(normalized)
    )


def _action_clauses(normalized: str) -> tuple[str, ...]:
    return tuple(
        clause.strip(" ,")
        for clause in CLAUSE_SPLIT_RE.split(normalized)
        if clause.strip(" ,")
    )


def _mentioned_apps(clause: str) -> set[str]:
    """Return app aliases mentioned inside one candidate action clause."""
    _, words = _normalized_words(clause)
    return {
        app
        for app, names in APP_UTTERANCE_NAMES.items()
        if _mentions_any(clause, words, names)
    }


def _clause_targets_only(
    clause: str,
    allowed_apps: set[str],
    *,
    competing_apps: set[str] | None = None,
) -> bool:
    """Fail closed when a candidate span names a competing application."""
    mentioned = _mentioned_apps(clause)
    if competing_apps is not None:
        mentioned &= competing_apps
    return not (mentioned - allowed_apps)


def _clause_targets_media_player(clause: str, player: str) -> bool:
    """Distinguish generic audio 'music' from the Apple Music application."""
    mentioned = _mentioned_apps(clause)
    if player == "spotify" and "spotify" in mentioned and "music" in mentioned:
        explicit_music_app = re.search(
            r"\bapple\s+music\b|"
            r"\b(?:open|launch|start|show|bring|focus|switch)\s+"
            r"(?:the\s+)?music(?:\s+app)?\b|"
            r"\b(?:in|on|using)\s+(?:the\s+)?music\s+app\b",
            clause,
        )
        if explicit_music_app is None:
            mentioned.discard("music")
    return not (mentioned - {player})


def _has_browser_search_request(clause: str) -> bool:
    """Accept common direct browser-search wording without inferring a query."""
    if _has_direct_request(clause, r"search|find|look\s+up|check|research|investigate"):
        return True
    return bool(
        _has_direct_request(clause, r"open|launch|start|show")
        and re.search(
            r"\b(?:and\s+)?(?:have\s+)?(?:a\s+)?"
            r"(?:check|look|search)\b",
            clause,
        )
    )


def _research_query_is_public(user_text: str, query: str) -> bool:
    combined = f"{user_text}\n{query}"
    return (
        not PRIVATE_RESEARCH_RE.search(combined)
        and not SENSITIVE_QUERY_RE.search(_normalize_text(user_text))
    )


def automatic_research_is_public(user_text: str, query: str) -> bool:
    """Apply the stricter privacy boundary used for implicit web routing."""
    combined = f"{user_text}\n{query}"
    return (
        _research_query_is_public(user_text, query)
        and not AUTOMATIC_PRIVATE_CONTEXT_RE.search(combined)
    )


def _screen_request_is_direct(normalized: str) -> bool:
    normalized = re.sub(
        r"^((?:can|could|would|will)\s+you\s+)"
        r"(?:(?:can|could|would|will)\s+you\s+)+",
        r"\1",
        normalized,
    )
    # Keep the direct-request prefix, verb, and visible target in one bounded
    # match. In particular, never combine "Read this text" with a later
    # explanatory phrase such as "how to inspect the current window".
    direct_target = re.search(
        r"(?:^|\b(?:and|then)\s+)"
        r"(?:jarvis[\s,]+)?(?:please\s+)?"
        r"(?:(?:(?:can|could|would|will)\s+you|"
        r"i\s+(?:want|need)\s+you\s+to)\s+(?:please\s+)?)?"
        r"(?:read|inspect|describe|analy[sz]e|review|explain|look\s+at)\b"
        r"\s+(?:for\s+me\s+)?(?:(?:my|this|the)\s+)?"
        r"(?:(?:current|frontmost|visible|open)\s+){0,3}"
        r"(?:screen|window|document|view)\b"
        r"(?:\s+(?:currently\s+)?(?:visible|open))?"
        r"(?:\s+(?:on|in)\s+(?:my|this|the|current)\s+"
        r"(?:screen|window|view))?",
        normalized,
    )
    deictic_question = re.search(
        r"^what(?:'s|\s+is)\s+on\s+(?:my|this|the|current)\s+"
        r"(?:screen|window)\b|"
        r"^what\s+do\s+you\s+see\s+(?:on|in)\s+"
        r"(?:my|this|the|current)\s+(?:screen|window)\b",
        normalized,
    )
    webpage_question = re.search(
        r"^(?:so\s+)?what\s+(?:(?:can|do)\s+you\s+see|is\s+visible|is\s+on)\s+"
        r"(?:(?:(?:on|in)\s+)?(?:this|the|current)\s+){1,2}"
        r"(?:web\s*page|website|page|tab|screen|window)\b|"
        r"^(?:so\s+)?(?:can|could|would)\s+you\s+"
        r"(?:read|inspect|describe|analy[sz]e|review|explain|look\s+at)\s+(?:this|the|current)\s+"
        r"(?:web\s*page|website|page|tab)\b",
        normalized,
    )
    natural_screen_request = re.search(
        r"^(?:can|could|would|will)\s+you\s+"
        r"(?:take\s+a\s+look\s+at|look\s+at|check|see|read|inspect|describe|analy[sz]e|review|explain)\b"
        r".*\b(?:screen|window|web\s*page|website|page|tab)\b|"
        r"^(?:do\s+you\s+know\s+)?what(?:'s|\s+is)\s+"
        r"(?:happening|going\s+on|visible)\s+(?:in|on)\s+"
        r"(?:(?:this|the|current)\s+)?(?:screen|window|web\s*page|page|tab)\b",
        normalized,
    )
    # Screen collaboration is commonly phrased as "can we analyse this on my
    # screen?" rather than as an imperative to look. It is still an explicit,
    # bounded request to inspect the one frontmost view; require both an
    # analysis verb and a visible-view reference so ordinary math questions do
    # not trigger capture.
    collaborative_screen_request = re.search(
        r"(?:^|\b(?:and|then)\s+)"
        r"(?:(?:can|could|would|will)\s+(?:we|you)|"
        r"(?:please\s+)?(?:help\s+(?:me\s+)?(?:with|to)|let(?:'s|\s+us)))?\s*"
        r"(?:please\s+)?"
        r"(?:analy[sz]e|review|explain|summari[sz]e|solve|work\s+through|"
        r"look\s+at|check|see)\b"
        r".*\b(?:on|in|from)\s+(?:my|this|the(?:\s+current)?|current)\s+"
        r"(?:screen|window|view|document|web\s*page|page|tab)\b|"
        r"(?:^|\b(?:and|then)\s+)(?:can|could|would|will)\s+we\s+"
        r"(?:analy[sz]e|review|explain|solve|work\s+through)\b.*\b"
        r"(?:screen|window|view|document|web\s*page|page|tab)\b",
        normalized,
    )
    # Speech recognition often preserves the key words but not the grammar in
    # a longer spoken request. For this read-only operation, accept an
    # unambiguous visible target plus an analysis/read intent as a final
    # fallback. The action model must still explicitly propose screen
    # inspection, and non-action phrasing is rejected before this helper runs.
    visible_analysis_request = re.search(
        r"\b(?:analy[sz]e|review|explain|summari[sz]e|solve|work\s+through|"
        r"math(?:s|ematics)?|equation|formula)\b"
        # Do not treat questions such as "how do I inspect a window?" as an
        # authorization to capture it. The visible target must be downstream
        # of the requested analysis and not part of a hypothetical explanation.
        r"(?:(?!\b(?:how|why)\b).){0,120}"
        r"\b(?:screen|window|view|document|web\s*page|page|tab)\b",
        normalized,
    )
    # People naturally refer to what is visible rather than repeating "screen".
    # A request such as "tell me what these emails are about" is still a
    # bounded, read-only inspection: the host captures only the frontmost
    # window.  Keep the visual target and the requested explanation together
    # so a general question about email is not mistaken for a desktop action.
    visible_content_request = re.search(
        r"(?:^|\b(?:and|then)\s+)"
        r"(?:jarvis[\s,]+)?(?:please\s+)?"
        r"(?:(?:(?:can|could|would|will)\s+you|"
        r"i\s+(?:want|need)\s+you\s+to)\s+(?:please\s+)?)?"
        r"(?:tell\s+me\s+(?:what|which|about)|"
        r"summari[sz]e|read|inspect|describe|analy[sz]e|review|explain|"
        r"look\s+at|check|see)\b"
        r".*\b(?:these|this|the\s+(?:visible|current|open|selected|unread))?\s*"
        r"(?:emails?|e-?mails?|inbox|mail|messages?|subject\s+lines?|"
        r"threads?|items?|section|part|area)\b",
        normalized,
    )
    return bool(
        direct_target
        or deictic_question
        or webpage_question
        or natural_screen_request
        or collaborative_screen_request
        or visible_analysis_request
        or visible_content_request
    )


def _action_is_bound_to_utterance(
    action: dict,
    user_text: str,
    *,
    allow_deictic_media_context: bool = False,
) -> bool:
    """Bind immediate execution to an unambiguous current utterance."""
    normalized = _normalize_text(user_text)
    # Saying the assistant name is optional. Remove it before clause-local
    # intent parsing so "Merrick: open Safari" and "open Safari" bind equally.
    binding_text = LEADING_OPTIONAL_MERRICK_RE.sub("", normalized, count=1)
    if _utterance_is_non_action(user_text, binding_text):
        return False
    kind = action.get("type")
    clauses = _action_clauses(binding_text)

    # The generic planner can understand Chinese natural language, but the
    # original proof-of-utterance code only recognized English word boundaries.
    # Bind Chinese plans to their explicit local command and named target here,
    # before the English-specific clause parser below.
    if re.search(r"[\u3400-\u9fff]", user_text) and CHINESE_DIRECT_ACTION_RE.search(user_text):
        action_pattern = CHINESE_ACTION_WORDS.get(str(kind), "")
        app = str(action.get("app") or action.get("player") or "")
        aliases = CHINESE_APP_UTTERANCE_NAMES.get(app, ())
        has_target = bool(
            app and (
                app.casefold() in normalized
                or any(alias.casefold() in normalized for alias in aliases)
            )
        )
        query = str(action.get("query") or "").strip().casefold()
        query_grounded = bool(query and query in normalized)
        if kind in {"open_app", "close_app"} and action_pattern:
            if has_target and re.search(action_pattern, user_text):
                return True
        elif kind == "media_control":
            media_words = {
                "play": r"播放|继续|打开|启动",
                "pause": r"暂停|停止|关闭|关掉",
                "toggle": r"切换",
                "next": r"下一首|下一曲|跳过",
                "previous": r"上一首|上一曲|返回上一",
            }
            if has_target and re.search(media_words.get(str(action.get("action")), r"(?!)"), user_text):
                return True
        elif kind in {"browser_search", "maps_search", "spotify_search", "web_research"}:
            if action_pattern and query_grounded and re.search(action_pattern, user_text):
                return True
        elif kind == "inspect_current_view":
            if re.search(action_pattern, user_text) and re.search(r"屏幕|窗口|页面|邮件|地图|当前", user_text):
                return True
        elif kind == "gui_task":
            if re.search(action_pattern, user_text):
                return True

    # Chinese voice commands reach this validator in their original script.
    # Keep the same current-utterance binding as English rather than letting a
    # planner guess whether “播放 Spotify” was an executable request.
    if kind == "media_control" and action.get("player") == "spotify":
        chinese_actions = {
            "play": r"播放|继续|打开|启动",
            "pause": r"暂停|停止|关掉|关闭",
            "next": r"下一首|下一曲|跳过",
            "previous": r"上一首|上一曲|返回上一",
        }
        pattern = chinese_actions.get(action.get("action"))
        if pattern and re.search(r"[\u3400-\u9fff]", user_text) and re.search(
            r"spotify|spot\s*if(?:y|i)?|斯[波博]提[菲费非]|思博提[菲费非]|声破天",
            user_text,
            re.IGNORECASE,
        ):
            return re.search(pattern, user_text) is not None

    if kind in {"open_app", "close_app"}:
        app = action.get("app")
        if not _valid_application_name(app):
            return False
        action_pattern = (
            r"open|launch|start|show|bring|focus|switch|put"
            if kind == "open_app"
            else r"close|quit|exit|turn\s+off|shut\s+(?:down|off)"
        )
        if app not in APP_UTTERANCE_NAMES:
            return any(
                not NATIVE_DISCUSSION_RE.search(clause)
                and _has_direct_request(
                    clause, action_pattern
                )
                and _query_is_grounded(str(app), clause, reject_sensitive=False)
                for clause in clauses
            )
        return any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and _clause_targets_only(clause, {app})
            and _mentions_any(clause, _normalized_words(clause)[1], APP_UTTERANCE_NAMES[app])
            and _has_direct_request(
                clause, action_pattern
            )
            for clause in clauses
        )
    if kind == "media_control":
        player = action.get("player")
        action_pattern = {
            "play": r"play|resume",
            "pause": r"pause|stop|turn\s+off|shut\s+off",
            "toggle": r"toggle|play\s+pause",
            "next": r"next|skip",
            "previous": r"previous",
        }.get(action.get("action"), r"(?!)")
        if player == "active":
            if action.get("action") != "pause":
                return False
            if _mentioned_apps(binding_text) & {"music", "spotify"}:
                # Generic "the music" is not an Apple Music target. Explicit
                # Spotify/Apple Music requests remain bound to that player.
                explicit_player = re.search(
                    r"\bspotify\b|\bapple\s+music\b|"
                    r"\b(?:in|on|using)\s+(?:the\s+)?music\s+app\b",
                    binding_text,
                )
                if explicit_player:
                    return False
            return bool(
                re.search(
                    r"\b(?:pause|stop|turn\s+off|shut\s+off)\b"
                    r"(?:\s+(?:the\s+)?(?:music|audio|sound|playback))?",
                    binding_text,
                )
            )
        if player not in APP_UTTERANCE_NAMES:
            return False
        if allow_deictic_media_context:
            return bool(
                re.search(
                    r"\b(?:play|resume|continue|pause|stop|skip|next|previous|go\s+back)\b"
                    r"\s+(?:it|that|this)\b",
                    binding_text,
                )
            )
        clause_bound = any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and _clause_targets_media_player(clause, player)
            and _mentions_any(
                clause,
                _normalized_words(clause)[1],
                APP_UTTERANCE_NAMES[player],
            )
            and _has_direct_request(clause, action_pattern)
            for clause in clauses
        )
        if clause_bound:
            return True
        # Natural compound speech can name the player in one clause and the
        # playback command in the next: "Open Spotify and play music."
        _, binding_words = _normalized_words(binding_text)
        return bool(
            not NATIVE_DISCUSSION_RE.search(binding_text)
            and _clause_targets_media_player(binding_text, player)
            and _mentions_any(
                binding_text,
                binding_words,
                APP_UTTERANCE_NAMES[player],
            )
            and _has_direct_request(binding_text, action_pattern)
        )
    if kind == "play_music":
        query = str(action.get("query", ""))
        _, query_words = _normalized_words(query)
        generic_audio_words = {
            "apple", "music", "song", "songs", "track", "tracks", "album",
            "artist", "spotify",
        }
        if not bool(set(query_words) - generic_audio_words):
            return False
        for clause in clauses:
            if (
                not NATIVE_DISCUSSION_RE.search(clause)
                and _clause_targets_only(clause, {"music"})
                and _has_direct_request(clause, r"play")
                and _query_is_grounded(
                    query,
                    clause,
                    reject_sensitive=False,
                )
            ):
                return True
        return False
    if kind == "browser_search":
        browser = action.get("browser")
        query = str(action.get("query", ""))
        if browser == "default":
            return any(
                not NATIVE_DISCUSSION_RE.search(clause)
                and not (
                    _mentioned_apps(clause) & {"chrome", "safari"}
                )
                and _has_browser_search_request(clause)
                and _query_is_grounded(query, clause)
                for clause in clauses
            )
        if not _valid_application_name(browser):
            return False
        normalized_browser = _normalize_text(str(browser))
        if normalized_browser in APP_UTTERANCE_NAMES:
            clause_bound = any(
                not NATIVE_DISCUSSION_RE.search(clause)
                and _clause_targets_only(
                    clause,
                    {normalized_browser},
                    competing_apps={"chrome", "safari"},
                )
                and _mentions_any(
                    clause,
                    _normalized_words(clause)[1],
                    APP_UTTERANCE_NAMES[normalized_browser],
                )
                and _has_browser_search_request(clause)
                and _query_is_grounded(query, clause)
                for clause in clauses
            )
            if clause_bound:
                return True
            _, binding_words = _normalized_words(binding_text)
            return bool(
                not NATIVE_DISCUSSION_RE.search(binding_text)
                and _clause_targets_only(
                    binding_text,
                    {normalized_browser},
                    competing_apps={"chrome", "safari"},
                )
                and _mentions_any(
                    binding_text,
                    binding_words,
                    APP_UTTERANCE_NAMES[normalized_browser],
                )
                and _has_browser_search_request(binding_text)
                and _query_is_grounded(query, binding_text)
            )
        clause_bound = any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and normalized_browser in _normalize_text(clause)
            and _has_browser_search_request(clause)
            and _query_is_grounded(query, clause)
            for clause in clauses
        )
        return bool(
            clause_bound
            or (
                not NATIVE_DISCUSSION_RE.search(binding_text)
                and normalized_browser in _normalize_text(binding_text)
                and _has_browser_search_request(binding_text)
                and _query_is_grounded(query, binding_text)
            )
        )
    if kind == "maps_search":
        query = str(action.get("query", ""))
        for clause in clauses:
            _, clause_words = _normalized_words(clause)
            explicit_maps = _mentions_any(clause, clause_words, ("map", "maps"))
            route_request = re.search(
                r"\b(?:directions?|route|navigate)\s+(?:to|from)\b|"
                r"\b(?:take|bring|go)\s+(?:me\s+)?to\b",
                clause,
            )
            direct_maps_query = _has_direct_request(
                clause, r"search|find|show|navigate|directions?|route|take|bring|go"
            )
            open_and_explore = bool(
                _has_direct_request(clause, r"open|launch|start|show")
                and re.search(
                    r"\b(?:see|check|look\s+at|what(?:'s|\s+is))\b.*"
                    r"\b(?:nearby|location)\b",
                    clause,
                )
            )
            if (
                not NATIVE_DISCUSSION_RE.search(clause)
                and _clause_targets_only(clause, {"maps"})
                and bool(explicit_maps or route_request)
                and bool(direct_maps_query or open_and_explore)
                and _query_is_grounded(query, clause)
            ):
                return True
        return False
    if kind == "spotify_search":
        query = str(action.get("query", ""))
        return any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and _clause_targets_only(clause, {"spotify"})
            and _mentions_any(
                clause,
                _normalized_words(clause)[1],
                APP_UTTERANCE_NAMES["spotify"],
            )
            and _has_direct_request(clause, r"search|find|look\s+up|show")
            and _query_is_grounded(query, clause)
            for clause in clauses
        )
    if kind == "web_research":
        query = str(action.get("query", ""))
        if not _research_query_is_public(user_text, query):
            return False
        for clause in clauses:
            targeted_app_search = re.search(
                r"\b(?:search|find|look\s+up)\s+(?:in\s+)?"
                r"(?:chrome|safari|maps|spotify)\b|"
                r"\b(?:in|using|on)\s+(?:chrome|safari|maps|spotify)\b",
                clause,
            )
            has_research_intent = (
                _has_direct_request(
                    clause,
                    r"search|research|find|look\s+up|check|tell",
                )
                or re.search(
                    r"^(?:who|what|when|where|why|how|is|are|do|does|did|can)\b|"
                    r"^(?:latest|current|news|weather|price)\b",
                    clause,
                )
                is not None
            )
            if (
                not targeted_app_search
                and has_research_intent
                and _query_is_grounded(query, clause)
            ):
                return True
        return False
    if kind == "open_web_page":
        normalized_url = _normalize_text(str(action.get("url", "")))
        return any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and normalized_url in clause
            and _has_direct_request(clause, r"open|show|view|visit|load|read")
            for clause in clauses
        )
    if kind == "inspect_current_view":
        return any(
            not NATIVE_DISCUSSION_RE.search(clause)
            and _screen_request_is_direct(clause)
            for clause in clauses
        )
    if kind == "gui_task":
        # The generic visual path is deliberately limited to a direct request
        # about the currently visible app. It never becomes a back door for
        # files, credentials, account changes, or message sending.
        forbidden = re.compile(
            r"\b(?:delete|remove|rename|move|terminal|shell|developer\s+tools|"
            r"password|passcode|credential|token|secret)\b|"
            r"\b(?:write|edit|save|create|download|upload)\s+(?:a\s+)?"
            r"(?:file|document|folder)\b|"
            r"\b(?:file|document|folder)\s+(?:write|edit|save|create|download|upload)\b",
            re.IGNORECASE,
        )
        return bool(
            not forbidden.search(binding_text)
            and any(
                _has_direct_request(
                    clause,
                    r"zoom|click|select|choose|navigate|scroll|go|open|close|"
                    r"switch|show|play|pause|stop|next|previous|search|find|load|visit",
                )
                for clause in clauses
            )
        )
    if kind == "volume_control":
        patterns = {
            "up": r"\b(?:volume\s+up|turn\s+(?:the\s+)?volume\s+up|"
                  r"(?:raise|increase)\s+(?:the\s+)?volume|louder)\b",
            "down": r"\b(?:volume\s+down|turn\s+(?:the\s+)?volume\s+down|"
                    r"(?:lower|decrease|reduce)\s+(?:the\s+)?volume|quieter)\b",
            "mute": r"\b(?:mute|silence)(?:\s+(?:the\s+)?(?:audio|sound|volume))?\b",
            "unmute": r"\b(?:unmute|restore)(?:\s+(?:the\s+)?(?:audio|sound|volume))?\b",
        }
        pattern = patterns.get(str(action.get("action")))
        return bool(pattern and re.search(pattern, binding_text))
    return False


@dataclass(frozen=True)
class ProviderFailure:
    code: str
    message: str
    retryable: bool
    reconnect_required: bool


def provider_failure(code: str) -> ProviderFailure:
    """Build one failure payload from the generated cross-layer contract."""
    contract = CONNECTION_FAILURES.get(code, CONNECTION_FAILURES["PROVIDER_FAILED"])
    return ProviderFailure(
        code,
        contract["messageEn"],
        contract["retryable"],
        contract["reconnectRequired"],
    )


def classify_provider_failure(
    detail: str,
    *,
    http_status: int | None = None,
) -> ProviderFailure:
    """Convert provider-specific failures into a small, secret-free contract."""
    normalized = f"{http_status or ''} {detail}".casefold()
    for matcher in FAILURE_MATCHERS:
        if re.search(matcher["pattern"], normalized):
            return provider_failure(matcher["runtimeCode"])
    return provider_failure("PROVIDER_FAILED")


class OpenClawError(RuntimeError):
    """A safe, user-displayable OpenClaw integration failure."""

    def __init__(self, message: str, *, failure: ProviderFailure | None = None) -> None:
        super().__init__(message)
        self.failure = failure


def provider_openclaw_error(detail: str, *, http_status: int | None = None) -> OpenClawError:
    failure = classify_provider_failure(detail, http_status=http_status)
    return OpenClawError(failure.message, failure=failure)


SAFE_RUNTIME_STALLS = frozenset({
    ("voice_pipeline", "external_playback_gate_stalled"),
    ("model_stream", "first_delta_stalled"),
    ("speech_output", "audio_playback_stalled"),
})


def openclaw_user_approval_request(
    event: object,
    *,
    agent_id: str,
    safe_session: str,
) -> dict[str, object] | None:
    """Return one sanitized approval belonging to the current owner turn."""
    if not isinstance(event, dict):
        return None
    event_name = event.get("event")
    if event_name not in {"exec.approval.requested", "plugin.approval.requested"}:
        return None
    kind = "exec" if event_name == "exec.approval.requested" else "plugin"
    payload = event.get("payload")
    if not isinstance(payload, dict):
        return None
    approval_id = payload.get("id")
    request = payload.get("request")
    if (
        not isinstance(approval_id, str)
        or not approval_id
        or len(approval_id) > 300
        or not isinstance(request, dict)
    ):
        return None
    request_agent = request.get("agentId")
    if agent_id != "main" or request_agent not in {None, agent_id}:
        return None
    expected_session = f"agent:{agent_id}:openresponses:{safe_session}"
    if request.get("sessionKey") not in {safe_session, expected_session}:
        return None
    allowed = request.get("allowedDecisions", [])
    allowed_decisions = [
        decision
        for decision in (allowed if isinstance(allowed, list) else [])
        if decision in {"allow-once", "allow-always", "deny"}
    ]
    # OpenClaw intentionally omits ``allowedDecisions`` for the common
    # plugin-approval case. Its protocol default is the complete owner choice
    # set; treating omission as invalid silently strands native MCP requests.
    if kind == "plugin" and not allowed_decisions:
        allowed_decisions = ["allow-once", "allow-always", "deny"]
    if not allowed_decisions:
        return None
    if kind == "exec":
        command = request.get("command")
        cwd = request.get("cwd")
        if not isinstance(command, str) or not command.strip():
            return None
        description = command.strip()[:4_000]
        if isinstance(cwd, str) and cwd.strip():
            description += f"\n\n{cwd.strip()[:1_000]}"
        title = "Run this command?"
        severity = "warning"
    else:
        title = request.get("title")
        description = request.get("description")
        if not isinstance(title, str) or not title.strip():
            title = "Allow this OpenClaw action?"
        if not isinstance(description, str) or not description.strip():
            description = str(request.get("detail") or request.get("toolName") or "OpenClaw requested permission.")
        severity = request.get("severity")
        if severity not in {"info", "warning", "critical"}:
            severity = "warning"
        title = title.strip()[:300]
        description = description.strip()[:5_000]
    return {
        "id": approval_id,
        "kind": kind,
        "title": title,
        "description": description,
        "severity": severity,
        "allowed_decisions": list(dict.fromkeys(allowed_decisions)),
    }


class OpenClawGateway:
    """Own startup, authenticated streaming, and scoped memory persistence."""

    def __init__(self) -> None:
        self.state_dir = Path(os.getenv("OPENCLAW_STATE_DIR", DEFAULT_STATE_DIR))
        self.config_path = Path(
            os.getenv("OPENCLAW_CONFIG_PATH", self.state_dir / "openclaw.json")
        )
        self.token_path = Path(
            os.getenv("OPENCLAW_TOKEN_FILE", self.state_dir / ".gateway-token")
        )
        self.action_secret_path = Path(
            os.getenv("OPENCLAW_ACTION_SECRET_FILE", self.state_dir / ".action-secret")
        )
        self.owner_path = self.state_dir / ".gateway-owner.json"
        self.base_url = ""
        self.port: int | None = None
        self.process: asyncio.subprocess.Process | None = None
        self._startup_lock = asyncio.Lock()
        self._prewarm_lock = asyncio.Lock()
        self._prewarm_task: asyncio.Task | None = None
        self._stall_recovery_lock = asyncio.Lock()
        self._action_invoke_lock = asyncio.Lock()
        self._client_lock = asyncio.Lock()
        self._http_client: httpx.AsyncClient | None = None
        self._log_handle = None
        self.gateway_rpc = OpenClawGatewayRPC(
            project_root=PROJECT_ROOT,
            node_path=self._expected_node_path(),
        )

    async def _client(self) -> httpx.AsyncClient:
        """Return one warm loopback client shared by all MERRICK turns."""
        async with self._client_lock:
            if self._http_client is None or self._http_client.is_closed:
                self._http_client = httpx.AsyncClient(
                    limits=httpx.Limits(
                        max_connections=12,
                        max_keepalive_connections=8,
                        keepalive_expiry=90.0,
                    )
                )
            return self._http_client

    async def _close_client(self) -> None:
        async with self._client_lock:
            client, self._http_client = self._http_client, None
        if client is not None and not client.is_closed:
            await client.aclose()

    def _token(self) -> str:
        try:
            token = self.token_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise OpenClawError("OpenClaw has not been set up yet.") from exc
        if not re.fullmatch(r"[0-9a-fA-F]{64}", token):
            raise OpenClawError("OpenClaw's local gateway token is invalid.")
        return token

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token()}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def gateway_session_key(session_key: str, *, agent_id: str = "main") -> str:
        """Return the canonical OpenClaw owner key used by HTTP and RPC lanes."""
        raw = str(session_key or "").strip()
        if raw.startswith("agent:"):
            return raw
        safe_session = SAFE_SESSION_RE.sub("-", raw).strip("-") or "jarvis-desktop"
        if agent_id == "main":
            return f"agent:main:openresponses:{safe_session}"
        safe_agent = SAFE_SESSION_RE.sub("-", agent_id).strip("-") or "main"
        return f"agent:{safe_agent}:{safe_session}"

    @staticmethod
    def _rpc_tool_payload(output: object) -> dict:
        """Unwrap the official Gateway ``tools.invoke`` response envelope."""
        if not isinstance(output, dict):
            raise OpenClawError("OpenClaw returned an invalid tool response.")
        for key in ("details", "structuredContent"):
            value = output.get(key)
            if isinstance(value, dict):
                return value
        content = output.get("content")
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "text":
                    continue
                raw = item.get("text")
                if not isinstance(raw, str):
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    return parsed
        return {}

    async def invoke_rpc_tool(
        self,
        tool: str,
        args: dict,
        *,
        session_key: str,
        agent_id: str = "main",
        timeout: float = 30.0,
    ) -> dict:
        """Invoke a session-scoped tool through the official Gateway RPC."""
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw's local gateway is unavailable.")
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        try:
            response = await self.gateway_rpc.request(
                "tools.invoke",
                {
                    "name": tool,
                    "args": args,
                    "sessionKey": self.gateway_session_key(session_key, agent_id=agent_id),
                    "agentId": agent_id,
                },
                timeout=timeout,
            )
        except OpenClawGatewayRPCError as exc:
            raise OpenClawError(str(exc)) from exc
        if not isinstance(response, dict) or response.get("ok") is not True:
            error = response.get("error") if isinstance(response, dict) else None
            message = error.get("message") if isinstance(error, dict) else None
            raise OpenClawError(message or f"OpenClaw tool {tool} failed.")
        return self._rpc_tool_payload(response.get("output"))

    async def list_tasks(
        self,
        *,
        session_key: str,
        agent_id: str = "main",
        statuses: Sequence[str] | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """List owner-visible durable tasks from the Gateway ledger."""
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw's local gateway is unavailable.")
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        params: dict[str, object] = {
            "sessionKey": self.gateway_session_key(session_key, agent_id=agent_id),
            "agentId": agent_id,
            "limit": max(1, min(int(limit), 250)),
        }
        if statuses:
            params["status"] = list(statuses)
        try:
            response = await self.gateway_rpc.request("tasks.list", params, timeout=15.0)
        except OpenClawGatewayRPCError as exc:
            raise OpenClawError(str(exc)) from exc
        tasks = response.get("tasks") if isinstance(response, dict) else None
        return [task for task in tasks if isinstance(task, dict)] if isinstance(tasks, list) else []

    async def cancel_task(self, task_id: str) -> dict:
        """Cancel one exact durable OpenClaw task."""
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw's local gateway is unavailable.")
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        try:
            response = await self.gateway_rpc.request(
                "tasks.cancel", {"taskId": task_id}, timeout=10.0,
            )
        except OpenClawGatewayRPCError as exc:
            raise OpenClawError(str(exc)) from exc
        return response if isinstance(response, dict) else {}

    def ensure_computer_use_runtime(self) -> Path | None:
        """Seed the bundled native component into MERRICK's private Codex home.

        The official client launcher resolves only through ``CODEX_HOME``.  A
        private seed keeps MERRICK independent from the user's global Codex
        installation while leaving the signed app bundle immutable at runtime.
        """
        resource_root = PROJECT_ROOT / "codex-computer-use"
        client_source = resource_root / "client" / "Codex Computer Use.app"
        marketplace_source = resource_root / "marketplace"
        manifest_source = marketplace_source / ".agents" / "plugins" / "marketplace.json"
        executable_source = (
            client_source
            / "Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
        )
        plugin_manifest = marketplace_source / "plugins" / "computer-use/.codex-plugin/plugin.json"
        if not (
            executable_source.is_file()
            and os.access(executable_source, os.X_OK)
            and manifest_source.is_file()
            and plugin_manifest.is_file()
        ):
            log.warning("Computer Use bundle assets are unavailable; leaving it disabled.")
            return None

        codex_home = self.state_dir / "agents" / "main" / "agent" / "codex-home"
        client_target = codex_home / "computer-use" / "Codex Computer Use.app"
        marketplace_target = codex_home / "marketplaces" / "jarvis-bundled"
        marketplace_manifest = marketplace_target / ".agents" / "plugins" / "marketplace.json"

        def provision_model_agent_runtimes() -> None:
            """Expose the one signed client to every model-backed agent home.

            OpenClaw gives each Codex agent its own ``CODEX_HOME``.  The
            Computer Use plugin is initialized before OpenClaw applies that
            agent's tool deny-list, so even tool-free agents need the client
            to exist at their private home path. OpenClaw 2 rejects a service
            path that traverses a symlink, so use real per-agent directories
            backed by hard-linked immutable files.
            """
            shared_runtime = client_target.parent.resolve()
            for agent_id in ("conversation", "screen-reader", "action-planner", "researcher"):
                agent_home = self.state_dir / "agents" / agent_id / "agent" / "codex-home"
                agent_home.mkdir(parents=True, exist_ok=True, mode=0o700)
                runtime_target = agent_home / "computer-use"
                private_executable = (
                    runtime_target
                    / "Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
                )
                if runtime_target.is_dir() and not runtime_target.is_symlink() and private_executable.is_file():
                    continue
                if runtime_target.exists() or runtime_target.is_symlink():
                    if runtime_target.is_dir() and not runtime_target.is_symlink():
                        shutil.rmtree(runtime_target)
                    else:
                        runtime_target.unlink()
                staging = agent_home / f".computer-use-staging-{secrets.token_hex(8)}"

                def hardlink_or_copy(source: str, destination: str) -> str:
                    try:
                        os.link(source, destination)
                    except OSError:
                        shutil.copy2(source, destination)
                    return destination

                try:
                    shutil.copytree(
                        shared_runtime,
                        staging,
                        copy_function=hardlink_or_copy,
                        symlinks=True,
                    )
                    staged_executable = (
                        staging
                        / "Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
                    )
                    if not staged_executable.is_file():
                        raise OpenClawError("Computer Use agent runtime verification failed.")
                    os.replace(staging, runtime_target)
                finally:
                    if staging.exists():
                        shutil.rmtree(staging)

        if client_target.is_dir() and marketplace_manifest.is_file():
            provision_model_agent_runtimes()
            return marketplace_manifest

        codex_home.mkdir(parents=True, exist_ok=True, mode=0o700)
        staging_root = codex_home / f".computer-use-staging-{secrets.token_hex(8)}"
        try:
            staged_client_root = staging_root / "computer-use"
            staged_marketplace = staging_root / "marketplace"
            shutil.copytree(client_source.parent, staged_client_root)
            shutil.copytree(marketplace_source, staged_marketplace)
            staged_executable = (
                staged_client_root
                / "Codex Computer Use.app/Contents/SharedSupport/SkyComputerUseClient.app/Contents/MacOS/SkyComputerUseClient"
            )
            staged_manifest = staged_marketplace / ".agents" / "plugins" / "marketplace.json"
            if not (staged_executable.is_file() and os.access(staged_executable, os.X_OK) and staged_manifest.is_file()):
                raise OpenClawError("Computer Use bundle verification failed.")
            client_target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            marketplace_target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            if client_target.parent.exists():
                shutil.rmtree(client_target.parent)
            if marketplace_target.exists():
                shutil.rmtree(marketplace_target)
            os.replace(staged_client_root, client_target.parent)
            os.replace(staged_marketplace, marketplace_target)
            provision_model_agent_runtimes()
            log.info("Seeded the app-owned Codex Computer Use runtime.")
            return marketplace_manifest
        except OSError as exc:
            log.warning("Could not seed the app-owned Computer Use runtime: %s", exc)
            return None
        finally:
            shutil.rmtree(staging_root, ignore_errors=True)

    def _action_secret(self) -> bytes:
        try:
            secret = self.action_secret_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise OpenClawError("OpenClaw's desktop action authorization is unavailable.") from exc
        if not re.fullmatch(r"[0-9a-fA-F]{64}", secret):
            raise OpenClawError("OpenClaw's desktop action authorization is invalid.")
        return bytes.fromhex(secret)

    def _sign_action_capability(self, payload: dict) -> str:
        body = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        encoded = base64.urlsafe_b64encode(body.encode("utf-8")).decode("ascii").rstrip("=")
        signed = f"v1.{encoded}"
        signature = hmac.new(self._action_secret(), signed.encode("ascii"), hashlib.sha256).digest()
        encoded_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        return f"{signed}.{encoded_signature}"

    @staticmethod
    def validate_action_plan(
        arguments: object,
        user_text: str,
        *,
        recent_media_player: str | None = None,
    ) -> list[dict]:
        """Validate semantic planner output against a small host-owned schema."""
        if not isinstance(arguments, dict) or set(arguments) != {"actions"}:
            return []
        raw_actions = arguments.get("actions")
        if not isinstance(raw_actions, list) or len(raw_actions) > 6:
            return []
        explicit_urls = {
            match.group(0).rstrip(".,!?;:)]}，。！？；：")
            for match in EXPLICIT_URL_RE.finditer(user_text)
        }
        actions: list[dict] = []
        for raw in raw_actions:
            if not isinstance(raw, dict) or raw.get("type") not in ACTION_TYPES:
                return []
            kind = raw["type"]
            normalized: dict
            if kind in {"open_app", "close_app"}:
                app = raw.get("app")
                if set(raw) != {"type", "app"} or not _valid_application_name(app):
                    return []
                canonical_app = str(app).strip().casefold()
                canonical_app = APPLICATION_NAME_ALIASES.get(canonical_app, canonical_app)
                normalized = {
                    "type": kind,
                    # Normalize familiar vocabulary for the legacy native
                    # adapter, but never reject an unfamiliar installed app.
                    "app": canonical_app if canonical_app in APP_UTTERANCE_NAMES else str(app),
                }
            elif kind == "media_control":
                if (
                    set(raw) != {"type", "player", "action"}
                    or raw.get("player") not in MEDIA_PLAYERS
                    or raw.get("action") not in MEDIA_ACTIONS
                ):
                    return []
                normalized = {
                    "type": kind,
                    "player": raw["player"],
                    "action": raw["action"],
                }
                # The native desktop bridge intentionally supports only an
                # active-player pause. Resolve harmless play/resume references
                # to a concrete recent player (or Apple Music for “play
                # music”) before they reach that bridge.
                if (
                    normalized["player"] == "active"
                    and normalized["action"] != "pause"
                ):
                    normalized_text = _normalize_text(user_text)
                    deictic_media = bool(
                        re.search(
                            r"\b(?:play|resume|continue|pause|stop|skip|next|previous|go\s+back)\b"
                            r"\s+(?:it|that|this)\b",
                            normalized_text,
                        )
                    )
                    generic_music = bool(
                        re.search(r"\b(?:music|audio|playback)\b", normalized_text)
                    )
                    if deictic_media and recent_media_player in {"music", "spotify"}:
                        normalized["player"] = recent_media_player
                    elif generic_music and normalized["action"] in {"play", "toggle"}:
                        normalized["player"] = "music"
                    else:
                        return []
                if (
                    normalized["player"] == "music"
                    and normalized["action"] == "pause"
                    and re.search(
                        r"\b(?:pause|stop|turn\s+off|shut\s+off)\s+"
                        r"(?:the\s+)?(?:music|audio|sound|playback)\b",
                        _normalize_text(user_text),
                    )
                    and not re.search(
                        r"\bapple\s+music\b|"
                        r"\b(?:in|on|using)\s+(?:the\s+)?music\s+app\b",
                        _normalize_text(user_text),
                    )
                ):
                    normalized["player"] = "active"
            elif kind == "play_music":
                query = raw.get("query")
                if (
                    set(raw) != {"type", "player", "query"}
                    or raw.get("player") != "music"
                    or not isinstance(query, str)
                    or not query.strip()
                    or len(query.strip()) > 160
                    or _contains_control_character(query)
                ):
                    return []
                normalized = {"type": kind, "player": "music", "query": query.strip()}
            elif kind == "browser_search":
                query = raw.get("query")
                if (
                    set(raw) != {"type", "browser", "query"}
                    or not (
                        raw.get("browser") == "default"
                        or _valid_application_name(raw.get("browser"))
                    )
                    or not isinstance(query, str)
                    or not query.strip()
                    or len(query.strip()) > 300
                    or _contains_control_character(query)
                ):
                    return []
                normalized = {
                    "type": kind,
                    "browser": raw["browser"],
                    "query": query.strip(),
                }
            elif kind == "maps_search":
                query = raw.get("query")
                if (
                    set(raw) != {"type", "query"}
                    or not isinstance(query, str)
                    or not query.strip()
                    or len(query.strip()) > 300
                    or _contains_control_character(query)
                ):
                    return []
                normalized = {"type": kind, "query": query.strip()}
            elif kind == "spotify_search":
                query = raw.get("query")
                if (
                    set(raw) != {"type", "query"}
                    or not isinstance(query, str)
                    or not query.strip()
                    or len(query.strip()) > 160
                    or _contains_control_character(query)
                ):
                    return []
                normalized = {"type": kind, "query": query.strip()}
            elif kind == "web_research":
                query = raw.get("query")
                if (
                    set(raw) != {"type", "query"}
                    or not isinstance(query, str)
                    or not query.strip()
                    or len(query.strip()) > 300
                    or _contains_control_character(query)
                ):
                    return []
                normalized = {"type": kind, "query": query.strip()}
            elif kind == "open_web_page":
                url = raw.get("url")
                if (
                    set(raw) != {"type", "url"}
                    or not isinstance(url, str)
                    or url not in explicit_urls
                ):
                    return []
                normalized = {"type": kind, "url": url}
            elif kind == "volume_control":
                if (
                    set(raw) != {"type", "action"}
                    or raw.get("action") not in {"up", "down", "mute", "unmute"}
                ):
                    return []
                normalized = {"type": kind, "action": raw["action"]}
            elif kind == "gui_task":
                if set(raw) != {"type"}:
                    return []
                normalized = {"type": "gui_task"}
            else:
                if set(raw) != {"type"}:
                    return []
                normalized = {"type": "inspect_current_view"}
            is_deictic_media_context = bool(
                kind == "media_control"
                and raw.get("player") == "active"
                and normalized.get("player") in {"music", "spotify"}
                and recent_media_player == normalized.get("player")
                and re.search(
                    r"\b(?:play|resume|continue|pause|stop|skip|next|previous|go\s+back)\b"
                    r"\s+(?:it|that|this)\b",
                    _normalize_text(user_text),
                )
            )
            if not _action_is_bound_to_utterance(
                normalized,
                user_text,
                allow_deictic_media_context=is_deictic_media_context,
            ):
                return []
            if normalized not in actions:
                actions.append(normalized)

        action_target_apps: set[str] = set()
        for action in actions:
            if action["type"] == "browser_search":
                action_target_apps.add(action["browser"])
            elif action["type"] == "maps_search":
                action_target_apps.add("maps")
            elif action["type"] == "spotify_search":
                action_target_apps.add("spotify")
            elif action["type"] in {"media_control", "play_music"}:
                action_target_apps.add(action["player"])
        # Compound actions already activate their target application. Removing only
        # a matching open_app is semantics-preserving; unrelated requested opens stay.
        actions = [
            action
            for action in actions
            if not (
                action["type"] == "open_app"
                and action["app"] in action_target_apps
            )
        ]
        # Screen inspection remains a one-step read-only operation. A GUI task
        # may safely follow one application/search prerequisite, e.g. Maps
        # search -> zoom the visible map. This is still an ordered, bounded
        # two-step plan; it is not an unbounded agent loop.
        if any(action["type"] == "inspect_current_view" for action in actions) and len(actions) != 1:
            return []
        gui_positions = [
            index for index, action in enumerate(actions)
            if action["type"] == "gui_task"
        ]
        if gui_positions:
            allowed_gui_compound = (
                len(actions) == 2
                and gui_positions == [1]
                and actions[0]["type"] in {
                    "open_app", "browser_search", "maps_search", "spotify_search",
                }
            )
            if len(actions) != 1 and not allowed_gui_compound:
                return []
        # A user may naturally combine one visible desktop action with a
        # public answer, e.g. "open Maps to Tate Modern and tell me London's
        # weather".  Public research must be final because execution returns
        # its streamed answer once it begins.
        research_positions = [
            index for index, action in enumerate(actions)
            if action["type"] == "web_research"
        ]
        if research_positions and (
            len(research_positions) != 1
            or research_positions[0] != len(actions) - 1
        ):
            return []
        return actions

    async def plan_actions(
        self,
        text: str,
        *,
        recent_media_player: str | None = None,
    ) -> list[dict]:
        """Legacy tool-less fallback for host-bound action proposals."""
        await self.ensure_ready()
        payload = {
            "model": "openclaw",
            "input": text,
            "instructions": ACTION_PLANNER_PROMPT,
            "stream": False,
            "max_output_tokens": 400,
        }
        headers = {**self._headers(), "x-openclaw-agent-id": "action-planner"}
        try:
            client = await self._client()
            response = await client.post(
                f"{self.base_url}/v1/responses",
                headers=headers,
                json=payload,
                timeout=ACTION_PLANNER_HTTP_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            raise OpenClawError("OpenClaw's action planner connection failed.") from exc
        try:
            response_payload = response.json()
        except ValueError as exc:
            raise OpenClawError("OpenClaw returned an invalid action plan.") from exc
        if response.status_code != 200:
            error = response_payload.get("error")
            message = error.get("message") if isinstance(error, dict) else None
            raise OpenClawError(message or "OpenClaw could not plan that request.")
        output_text = ""
        for item in response_payload.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for content in item.get("content") or []:
                if isinstance(content, dict) and content.get("type") == "output_text":
                    output_text += str(content.get("text") or "")
        start, end = output_text.find("{"), output_text.rfind("}")
        if start < 0 or end <= start:
            return []
        try:
            arguments = json.loads(output_text[start : end + 1])
        except json.JSONDecodeError:
            return []
        return self.validate_action_plan(
            arguments,
            text,
            recent_media_player=recent_media_player,
        )

    def action_capabilities_for_plan(self, actions: Sequence[dict]) -> list[dict]:
        """Mint exact machine capabilities only for a host-validated plan."""
        now = int(time.time())
        expires = now + 240
        capabilities: list[dict] = []

        def add(
            tool: str,
            arguments: dict,
            *,
            selection_constraints: dict | None = None,
            **constraints: str,
        ) -> None:
            payload = {
                "exp": expires,
                "jti": secrets.token_hex(16),
                "tool": tool,
                **constraints,
            }
            record = {
                "tool": tool,
                "fixedArguments": arguments,
                "authorization": self._sign_action_capability(payload),
            }
            if selection_constraints:
                record["selectionConstraints"] = selection_constraints
            capabilities.append(record)

        for action in actions[:6]:
            kind = action.get("type")
            if kind == "open_app" and _valid_application_name(action.get("app")):
                app = action["app"]
                add("jarvis_open_app", {"app": app}, app=app)
            elif (
                kind == "media_control"
                and action.get("player") in {"music", "spotify"}
                and action.get("action") in MEDIA_ACTIONS
            ):
                player, media_action = action["player"], action["action"]
                add(
                    "jarvis_media_control",
                    {"player": player, "action": media_action},
                    player=player,
                    action=media_action,
                )
            elif kind == "play_music" and action.get("player") == "music":
                query = action.get("query")
                if (
                    isinstance(query, str)
                    and query == query.strip()
                    and 0 < len(query) <= 160
                    and not any(ord(char) < 32 for char in query)
                ):
                    add(
                        "jarvis_play_music",
                        {"player": "music", "query": query},
                        player="music",
                        query=query,
                    )
            elif (
                kind == "open_web_page"
                and isinstance(action.get("url"), str)
                and EXPLICIT_URL_RE.fullmatch(action["url"])
            ):
                url = action["url"]
                add(
                    "jarvis_open_web_page",
                    {"url": url},
                    scope="public_web_page",
                    url=url,
                )
        return capabilities

    def public_page_capability(self, tool: str, url: str) -> dict:
        """Mint one exact, short-lived capability for a host-selected public URL."""
        if tool not in {"jarvis_open_web_page", "jarvis_read_web_page"}:
            raise OpenClawError("The requested public-page operation is unsupported.")
        if not isinstance(url, str) or not EXPLICIT_URL_RE.fullmatch(url):
            raise OpenClawError("The selected search result URL is invalid.")
        now = int(time.time())
        payload = {
            "exp": now + 240,
            "jti": secrets.token_hex(16),
            "tool": tool,
            "scope": "public_web_page",
            "url": url,
        }
        return {
            "tool": tool,
            "fixedArguments": {"url": url},
            "authorization": self._sign_action_capability(payload),
        }

    async def _invoke_bounded_public_page(
        self,
        tool: str,
        url: str,
        *,
        agent_id: str,
    ) -> dict:
        async with self._action_invoke_lock:
            for attempt in range(2):
                await self.ensure_ready()
                capability = self.public_page_capability(tool, url)
                arguments = dict(capability["fixedArguments"])
                arguments["authorization"] = capability["authorization"]
                try:
                    return await self.invoke_tool(tool, arguments, agent_id=agent_id)
                except OpenClawError as exc:
                    if (
                        attempt == 0
                        and "desktop action authorization is invalid"
                        in str(exc).lower()
                    ):
                        continue
                    raise
        raise OpenClawError("The selected public page could not be accessed safely.")

    async def invoke_bounded_web_page(self, action: dict) -> dict:
        """Mint and invoke one literal-page capability against one ready Gateway.

        A Gateway crash between minting and invocation rotates the host secret.
        Retry only the explicit pre-execution invalid-signature case, never an
        expired/reused capability or an ambiguous transport failure.
        """
        capabilities = self.action_capabilities_for_plan([action])
        if (
            len(capabilities) != 1
            or capabilities[0].get("tool") != "jarvis_open_web_page"
        ):
            raise OpenClawError(
                "The validated page no longer matches its safe capability."
            )
        return await self._invoke_bounded_public_page(
            "jarvis_open_web_page",
            str(action.get("url", "")),
            agent_id="action-executor",
        )

    async def invoke_bounded_read_page(self, url: str) -> dict:
        """Read one exact public result URL without browser cookies or active content."""
        return await self._invoke_bounded_public_page(
            "jarvis_read_web_page",
            url,
            agent_id="page-reader-executor",
        )

    async def _run_setup(self) -> None:
        script = PROJECT_ROOT / "scripts" / "setup-openclaw.sh"
        if not script.is_file():
            raise OpenClawError("The OpenClaw setup script is missing.")
        process = await asyncio.create_subprocess_exec(
            str(script),
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await process.communicate()
        if process.returncode != 0:
            detail = stdout.decode("utf-8", errors="replace")[-600:]
            raise OpenClawError(f"OpenClaw setup failed: {detail}")

    def _obsolete_codex_install_record_present(self) -> bool:
        """Find only the stale provider record superseded by our bundled copy."""
        bundled_manifest = (
            PROJECT_ROOT
            / "node_modules/openclaw/dist/extensions/codex/openclaw.plugin.json"
        )
        if not bundled_manifest.is_file():
            return False
        projects_root = self.state_dir / "npm" / "projects"
        for candidate in projects_root.glob("openclaw-codex-*"):
            package = candidate / "node_modules/@openclaw/codex/package.json"
            manifest = candidate / "node_modules/@openclaw/codex/openclaw.plugin.json"
            try:
                package_data = json.loads(package.read_text(encoding="utf-8"))
                manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, ValueError, TypeError):
                continue
            if (
                isinstance(package_data, dict)
                and isinstance(manifest_data, dict)
                and package_data.get("name") == "@openclaw/codex"
                and manifest_data.get("id") == "codex"
            ):
                return True
        database_path = self.state_dir / "state" / "openclaw.sqlite"
        if not database_path.is_file():
            return False
        try:
            with sqlite3.connect(database_path, timeout=0.25) as connection:
                row = connection.execute(
                    "SELECT install_records_json FROM installed_plugin_index "
                    "WHERE index_key = ?",
                    ("installed-plugin-index",),
                ).fetchone()
            records = json.loads(row[0]) if row and isinstance(row[0], str) else {}
            return isinstance(records, dict) and isinstance(records.get("codex"), dict)
        except (sqlite3.Error, OSError, ValueError, TypeError):
            return False

    async def _migrate_obsolete_codex_install_record(self) -> bool:
        """Let OpenClaw remove its old record without touching OAuth state."""
        if not self._obsolete_codex_install_record_present():
            return False
        script = PROJECT_ROOT / "scripts" / "migrate-openclaw-codex-plugin.sh"
        if not script.is_file() or not os.access(script, os.X_OK):
            raise OpenClawError("The OpenClaw Codex migration helper is missing.")
        process = await asyncio.create_subprocess_exec(
            str(script),
            cwd=str(PROJECT_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=20.0)
        except asyncio.TimeoutError as exc:
            process.kill()
            await process.wait()
            raise OpenClawError("The OpenClaw Codex migration timed out.") from exc
        if process.returncode != 0:
            detail = stdout.decode("utf-8", errors="replace")[-600:]
            raise OpenClawError(f"The OpenClaw Codex migration failed: {detail}")
        if self._obsolete_codex_install_record_present():
            raise OpenClawError("The obsolete OpenClaw Codex record is still present.")
        log.info("Migrated the legacy Codex plugin record to the signed bundled provider.")
        return True

    async def _authenticated_ready(self) -> bool:
        if not self.base_url or not self.token_path.is_file():
            return False
        try:
            client = await self._client()
            response = await client.get(
                f"{self.base_url}/v1/models", headers=self._headers(), timeout=1.5
            )
            return response.status_code == 200
        except (httpx.HTTPError, OpenClawError):
            return False

    async def _prewarm_once(self) -> None:
        """Keep HTTP and the Gateway event channel hot without a model call."""
        started = time.monotonic()
        await self.ensure_ready()
        client = await self._client()
        try:
            response = await client.get(
                f"{self.base_url}/v1/models", headers=self._headers(), timeout=1.5
            )
            if response.status_code != 200:
                raise OpenClawError("OpenClaw did not accept its warm connection.")
        except httpx.HTTPError as exc:
            raise OpenClawError("OpenClaw's warm connection failed.") from exc
        if self.port is not None:
            await self.gateway_rpc.start(
                url=f"ws://127.0.0.1:{self.port}",
                token=self._token(),
            )
        log.info("OpenClaw warm loopback ready in %.0f ms", (time.monotonic() - started) * 1000)

    async def prewarm(self) -> None:
        """Share one startup across reconnecting WebSocket clients.

        A native WebKit reload may cancel the Session waiting for startup. The
        Gateway migration must keep running: cancelling and immediately
        restarting it leaves OpenClaw's five-minute migration lease behind and
        makes a successful OAuth handoff look like a broken installation.
        """
        async with self._prewarm_lock:
            task = self._prewarm_task
            if task is None or task.done():
                task = asyncio.create_task(self._prewarm_once())
                self._prewarm_task = task
        await asyncio.shield(task)

    async def _command_output(self, *args: str) -> tuple[int, str]:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await process.communicate()
        return process.returncode or 0, stdout.decode("utf-8", errors="replace")

    def _expected_node_path(self) -> Path:
        node_bin_dir = Path(
            os.getenv(
                "NODE_BIN_DIR",
                Path.home()
                / ".cache"
                / "codex-runtimes"
                / "codex-primary-runtime"
                / "dependencies"
                / "node"
                / "bin",
            )
        )
        return (node_bin_dir / "node").resolve()

    async def _process_fingerprint_matches(self, pid: int) -> bool:
        """Verify the local runtime even after OpenClaw renames its process."""
        if pid <= 1:
            return False
        _, process_row = await self._command_output(
            "/bin/ps", "-p", str(pid), "-o", "uid=", "-o", "command="
        )
        fields = process_row.strip().split(maxsplit=1)
        if len(fields) != 2:
            return False
        try:
            if int(fields[0]) != os.getuid():
                return False
        except ValueError:
            return False

        command = fields[1].strip()
        cli_path = (PROJECT_ROOT / "node_modules" / "openclaw" / "openclaw.mjs").resolve()
        # OpenClaw 2026.7 renamed its macOS process title from `openclaw` to
        # `openclaw-gateway`. Both names still undergo the path fingerprint
        # below; accepting the new title prevents every HUD reconnect from
        # mistaking its own live Gateway for an unrelated process.
        command_is_expected = command in {"openclaw", "openclaw-gateway"} or (
            str(cli_path) in command and "gateway run" in command
        )
        if not command_is_expected:
            return False

        _, open_files = await self._command_output(
            "/usr/sbin/lsof", "-nP", "-p", str(pid), "-Fn"
        )
        names = {
            line[1:]
            for line in open_files.splitlines()
            if line.startswith("n") and len(line) > 1
        }
        expected_paths = {
            str(PROJECT_ROOT.resolve()),
            str(self._expected_node_path()),
            str(self.config_path.resolve()),
        }
        return expected_paths.issubset(names)

    async def _process_owns_listener(self, pid: int, port: int) -> bool:
        if pid <= 1 or not (1024 <= port <= 65535):
            return False
        if not await self._process_fingerprint_matches(pid):
            return False
        _, listeners = await self._command_output(
            "/usr/sbin/lsof",
            "-nP",
            "-a",
            "-p",
            str(pid),
            f"-iTCP:{port}",
            "-sTCP:LISTEN",
            "-t",
        )
        return {line.strip() for line in listeners.splitlines() if line.strip()} == {str(pid)}

    async def _managed_gateway_processes(self) -> list[int]:
        _, output = await self._command_output(
            "/usr/sbin/lsof", "-nP", "-t", str(self.config_path.resolve())
        )
        matches: list[int] = []
        for raw_pid in output.splitlines():
            try:
                pid = int(raw_pid.strip())
            except ValueError:
                continue
            if await self._process_fingerprint_matches(pid):
                matches.append(pid)
        return sorted(set(matches))

    async def _legacy_orphaned_gateway_matches(self, pid: int) -> bool:
        """Recognise an orphan made by an older bundled MERRICK build.

        The normal fingerprint deliberately includes the exact bundled Node
        binary and resource directory, which prevents us from ever stopping a
        user's independent OpenClaw installation.  That also means a gateway
        left behind by a *previous* MERRICK bundle cannot be reclaimed
        after an app upgrade.  Admit this narrowly-scoped legacy form only
        when it is an orphan, uses our private config plus state database, and
        has OpenClaw's intentionally generic macOS process name.
        """
        if pid <= 1 or await self._process_parent_pid(pid) != 1:
            return False
        _, process_row = await self._command_output(
            "/bin/ps", "-p", str(pid), "-o", "uid=", "-o", "command="
        )
        fields = process_row.strip().split(maxsplit=1)
        if len(fields) != 2:
            return False
        try:
            # OpenClaw 2026.7 renamed its macOS process title from
            # `openclaw` to `openclaw-gateway`.  Accept both only after the
            # private config, SQLite state, log file, owner UID, and orphan
            # parent have all matched. Otherwise an old MERRICK gateway can
            # survive an app upgrade and contend with the new gateway for the
            # same isolated Codex app-server home.
            if int(fields[0]) != os.getuid() or fields[1].strip() not in {
                "openclaw",
                "openclaw-gateway",
            }:
                return False
        except ValueError:
            return False
        _, open_files = await self._command_output(
            "/usr/sbin/lsof", "-nP", "-p", str(pid), "-Fn"
        )
        names = {
            line[1:]
            for line in open_files.splitlines()
            if line.startswith("n") and len(line) > 1
        }
        required_paths = {
            str(self.config_path.resolve()),
            str((self.state_dir / "state" / "openclaw.sqlite").resolve()),
            str((self.state_dir / "gateway.log").resolve()),
        }
        return required_paths.issubset(names)

    async def _legacy_orphaned_gateway_processes(self) -> list[int]:
        _, output = await self._command_output(
            "/usr/sbin/lsof", "-nP", "-t", str(self.config_path.resolve())
        )
        matches: list[int] = []
        for raw_pid in output.splitlines():
            try:
                pid = int(raw_pid.strip())
            except ValueError:
                continue
            if await self._legacy_orphaned_gateway_matches(pid):
                matches.append(pid)
        return sorted(set(matches))

    @staticmethod
    def _choose_loopback_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((_OPENCLAW_SERVICE["host"], 0))
            return int(sock.getsockname()[1])

    async def _wait_for_pid_exit(self, pid: int, timeout: float) -> bool:
        deadline = asyncio.get_running_loop().time() + timeout
        while asyncio.get_running_loop().time() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            except PermissionError:
                return False
            await asyncio.sleep(0.1)
        return False

    async def _process_parent_pid(self, pid: int) -> int | None:
        """Return a same-user process's parent PID without trusting its name."""
        if pid <= 1:
            return None
        _, output = await self._command_output(
            "/bin/ps", "-p", str(pid), "-o", "ppid="
        )
        try:
            parent_pid = int(output.strip())
        except ValueError:
            return None
        return parent_pid if parent_pid >= 0 else None

    async def _terminate_verified_gateway(
        self, pid: int, *, listener_port: int | None = None
    ) -> bool:
        """Stop only a Gateway proved to belong to this MERRICK runtime."""
        is_current = (
            await self._process_owns_listener(pid, listener_port)
            if listener_port is not None
            else await self._process_fingerprint_matches(pid)
        )
        if not is_current:
            return False
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        if await self._wait_for_pid_exit(pid, 5.0):
            return True
        # Recheck the strict project/config fingerprint before escalation.
        if not await self._process_fingerprint_matches(pid):
            return True
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return await self._wait_for_pid_exit(pid, 2.0)

    async def _terminate_legacy_orphaned_gateway(self, pid: int) -> bool:
        """Terminate only a re-validated orphan from an older app bundle."""
        if not await self._legacy_orphaned_gateway_matches(pid):
            return False
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        if await self._wait_for_pid_exit(pid, 5.0):
            return True
        if not await self._legacy_orphaned_gateway_matches(pid):
            return True
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        return await self._wait_for_pid_exit(pid, 2.0)

    async def _clean_previous_owner(self) -> None:
        owner: dict = {}
        try:
            owner = json.loads(self.owner_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            owner = {}
        pid = owner.get("pid")
        port = owner.get("port")
        if isinstance(pid, int) and isinstance(port, int):
            owner_released = await self._terminate_verified_gateway(
                pid, listener_port=port
            )
            if owner_released:
                self.owner_path.unlink(missing_ok=True)
        else:
            self.owner_path.unlink(missing_ok=True)
        unmanaged = await self._managed_gateway_processes()
        # A normal managed gateway has an owner record. A verified runtime with
        # no record and launchd (PID 1) as its parent can only be a MERRICK
        # process left behind after an abnormal desktop/backend exit. Recover
        # it automatically, but never touch a process still attached to a user
        # shell or another parent.
        recovered: list[int] = []
        for candidate in unmanaged:
            if await self._process_parent_pid(candidate) != 1:
                continue
            if await self._terminate_verified_gateway(candidate):
                recovered.append(candidate)
        if recovered:
            log.warning("Recovered orphaned MERRICK OpenClaw gateway(s): %s", recovered)
            unmanaged = await self._managed_gateway_processes()
        # After an app update, the strict fingerprint above intentionally no
        # longer matches the old bundle. Recover only the narrower legacy
        # signature so its private state lock cannot stall a fresh launch.
        legacy_recovered: list[int] = []
        for candidate in await self._legacy_orphaned_gateway_processes():
            if await self._terminate_legacy_orphaned_gateway(candidate):
                legacy_recovered.append(candidate)
        if legacy_recovered:
            log.warning(
                "Recovered legacy MERRICK OpenClaw gateway(s): %s",
                legacy_recovered,
            )
            unmanaged = await self._managed_gateway_processes()
        if unmanaged:
            raise OpenClawError(
                "Another OpenClaw Gateway is already running outside this MERRICK app. "
                "Stop it before reopening MERRICK"
            )

    async def _clear_unowned_startup_migration_lease(self) -> bool:
        """Remove only OpenClaw's abandoned global startup-migration lease.

        This runs after strict process ownership cleanup. It does not touch
        OAuth credentials, sessions, plugin data, or any other state row.
        """
        if self.process is not None and self.process.returncode is None:
            return False
        if self.owner_path.exists():
            return False
        database_path = self.state_dir / "state" / "openclaw.sqlite"
        if not database_path.is_file():
            return False

        def clear() -> bool:
            try:
                with sqlite3.connect(database_path, timeout=0.25) as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    cursor = connection.execute(
                        "DELETE FROM state_leases WHERE scope = ? AND lease_key = ?",
                        ("startup-migrations", "global"),
                    )
                    connection.commit()
                    return cursor.rowcount > 0
            except sqlite3.Error:
                return False

        removed = await asyncio.to_thread(clear)
        if removed:
            log.warning("Cleared an abandoned OpenClaw startup migration lease.")
        return removed

    def _write_owner_record(self, pid: int, port: int) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.owner_path.with_name(f"{self.owner_path.name}.{pid}.tmp")
        temporary.write_text(
            json.dumps({"pid": pid, "port": port}, separators=(",", ":")),
            encoding="utf-8",
        )
        temporary.chmod(0o600)
        os.replace(temporary, self.owner_path)

    async def repair_owner_record_if_owned(self) -> bool:
        """Restore a missing owner receipt only for this live authenticated child."""
        if self.owner_path.exists():
            return False
        process = self.process
        port = self.port
        if process is None or process.returncode is not None or port is None:
            return False
        if not await self._process_owns_listener(process.pid, port):
            return False
        if not await self._authenticated_ready():
            return False
        if self.owner_path.exists():
            return False
        self._write_owner_record(process.pid, port)
        log.warning(
            "Restored missing MERRICK OpenClaw owner record for pid=%s port=%s",
            process.pid,
            port,
        )
        return True

    async def _owned_ready(self) -> bool:
        process = self.process
        if process is None or process.returncode is not None or self.port is None:
            return False
        if not await self._process_owns_listener(process.pid, self.port):
            return False
        authenticated = await self._authenticated_ready()
        if authenticated and not self.owner_path.exists():
            self._write_owner_record(process.pid, self.port)
        return authenticated

    async def _gateway_environment(self, *, port: int | None = None) -> dict[str, str]:
        """Build the one isolated environment used by Gateway and repair CLI calls."""
        environment = os.environ.copy()
        native_home = self.state_dir / "native-home"
        native_home.mkdir(parents=True, exist_ok=True, mode=0o700)
        environment["HOME"] = str(native_home)
        marketplace_manifest = await asyncio.to_thread(self.ensure_computer_use_runtime)
        environment["OPENCLAW_CODEX_COMPUTER_USE"] = "true" if marketplace_manifest else "false"
        environment["JARVIS_CODEX_COMPUTER_USE_MARKETPLACE_PATH"] = str(
            marketplace_manifest or (
                self.state_dir
                / "agents/main/agent/codex-home/marketplaces/jarvis-bundled/.agents/plugins/marketplace.json"
            )
        )
        environment["XDG_CONFIG_HOME"] = str(native_home / "config")
        environment["XDG_CACHE_HOME"] = str(native_home / "cache")
        environment["XDG_DATA_HOME"] = str(native_home / "data")
        environment["OPENCLAW_STATE_DIR"] = str(self.state_dir)
        environment["OPENCLAW_CONFIG_PATH"] = str(self.config_path)
        environment["OPENCLAW_TOKEN_FILE"] = str(self.token_path)
        environment["OPENCLAW_ACTION_SECRET_FILE"] = str(self.action_secret_path)
        environment["JARVIS_BACKEND_PORT"] = os.getenv("JARVIS_BACKEND_PORT", "8765")
        environment["JARVIS_WORKSPACE_DIR"] = str(
            self.state_dir.parent / "Workspace" / "Documents"
        )
        if port is not None:
            environment["OPENCLAW_PORT"] = str(port)
            environment["JARVIS_OPENCLAW_PUBLIC_ORIGIN"] = f"http://127.0.0.1:{port}"
        return environment

    async def ensure_session(
        self,
        *,
        session_key: str,
        agent_id: str = "main",
        label: str = "MERRICK Agent Board",
    ) -> dict:
        """Idempotently create/adopt the persistent parent used by visible children."""
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw's local gateway is unavailable.")
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        canonical = self.gateway_session_key(session_key, agent_id=agent_id)
        try:
            response = await self.gateway_rpc.request(
                "sessions.create",
                {
                    "key": canonical,
                    "agentId": agent_id,
                    "label": label[:120],
                },
                timeout=15.0,
            )
        except OpenClawGatewayRPCError as exc:
            raise OpenClawError(str(exc)) from exc
        if not isinstance(response, dict):
            raise OpenClawError("OpenClaw did not confirm the Agent Board session.")
        return response

    def _gateway_log_requires_offline_migration(
        self,
        log_path: Path,
        start_offset: int,
    ) -> bool:
        """Recognize only the explicit OpenClaw stopped-writer migration failure."""
        try:
            with log_path.open("rb") as handle:
                handle.seek(max(0, start_offset))
                output = handle.read(256_000).decode("utf-8", errors="replace")
        except OSError:
            return False
        stopped_writer_migration = (
            "OpenClaw startup migrations did not complete cleanly" in output
            and "Agent identity migration requires stopped-writer maintenance" in output
            and "openclaw doctor --fix" in output
        )
        legacy_session_migration = (
            "Legacy session store requires migration" in output
            and "openclaw doctor --fix" in output
        )
        return stopped_writer_migration or legacy_session_migration

    async def _run_offline_upgrade_repair(
        self,
        environment: dict[str, str],
        log_path: Path,
    ) -> bool:
        """Run OpenClaw's official bounded repair only while no writer is alive."""
        if self.process is not None and self.process.returncode is None:
            return False
        if self.owner_path.exists():
            return False
        node = self._expected_node_path()
        cli = PROJECT_ROOT / "node_modules" / "openclaw" / "openclaw.mjs"
        if not node.is_file() or not cli.is_file():
            return False
        try:
            with log_path.open("ab", buffering=0) as log_handle:
                process = await asyncio.create_subprocess_exec(
                    str(node),
                    str(cli),
                    "doctor",
                    "--fix",
                    "--non-interactive",
                    "--yes",
                    cwd=str(PROJECT_ROOT),
                    env=environment,
                    stdout=log_handle,
                    stderr=asyncio.subprocess.STDOUT,
                )
                try:
                    await asyncio.wait_for(process.communicate(), timeout=45.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return False
        except OSError:
            return False
        if process.returncode != 0:
            return False
        log.warning("Completed OpenClaw's offline upgrade repair; retrying Gateway once.")
        return True

    async def ensure_ready(self) -> None:
        if await self._owned_ready():
            return
        async with self._startup_lock:
            if await self._owned_ready():
                return
            # Stop only a strictly identified prior MERRICK gateway before any
            # setup repair touches the shared OpenClaw state database.
            await self._clean_previous_owner()
            migrated_codex_provider = await self._migrate_obsolete_codex_install_record()
            if not (
                self.config_path.is_file()
                and self.token_path.is_file()
                and self.action_secret_path.is_file()
            ) or migrated_codex_provider:
                await self._run_setup()
            await self._clear_unowned_startup_migration_lease()

            script = PROJECT_ROOT / "scripts" / "run-openclaw-gateway.sh"
            if not script.is_file():
                raise OpenClawError("The OpenClaw gateway launcher is missing.")
            self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            log_path = self.state_dir / "gateway.log"
            # OpenClaw upgrades can expose agent-database and legacy-session
            # migrations in consecutive startup passes. Permit one bounded
            # official Doctor repair for each, never an unbounded restart loop.
            for attempt in range(3):
                try:
                    log_offset = log_path.stat().st_size
                except OSError:
                    log_offset = 0
                self.port = self._choose_loopback_port()
                self.base_url = f"http://{_OPENCLAW_SERVICE['host']}:{self.port}"
                environment = await self._gateway_environment(port=self.port)
                self._log_handle = log_path.open("ab", buffering=0)
                self.process = await asyncio.create_subprocess_exec(
                    str(script),
                    cwd=str(PROJECT_ROOT),
                    env=environment,
                    stdout=self._log_handle,
                    stderr=asyncio.subprocess.STDOUT,
                )
                self._write_owner_record(self.process.pid, self.port)

                loop = asyncio.get_running_loop()
                startup_deadline = loop.time() + GATEWAY_STARTUP_TIMEOUT_SECONDS
                while loop.time() < startup_deadline:
                    if self.process.returncode is not None:
                        break
                    if await self._owned_ready():
                        return
                    await asyncio.sleep(0.25)
                await self.shutdown()
                if (
                    attempt < 2
                    and self._gateway_log_requires_offline_migration(log_path, log_offset)
                    and await self._run_offline_upgrade_repair(environment, log_path)
                ):
                    continue
                break
            raise OpenClawError(
                "OpenClaw Gateway did not become ready. Check its local gateway log."
            )

    async def shutdown(self) -> None:
        """Stop only the Gateway process started by this backend instance."""
        await self.gateway_rpc.stop()
        prewarm_task = self._prewarm_task
        current_task = asyncio.current_task()
        if (
            prewarm_task is not None
            and prewarm_task is not current_task
            and not prewarm_task.done()
        ):
            prewarm_task.cancel()
            await asyncio.gather(prewarm_task, return_exceptions=True)
        if prewarm_task is not current_task:
            self._prewarm_task = None
        process, self.process = self.process, None
        process_stopped = process is None or process.returncode is not None
        if process is not None and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            process_stopped = process.returncode is not None
        try:
            owner = json.loads(self.owner_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            owner = {}
        # A secondary client may be attached to a Gateway owned by the desktop
        # backend without holding its Process object. Never let that client
        # orphan the live runtime by unlinking the shared owner record.
        if process is not None and owner.get("pid") == process.pid:
            # Retain the owner record if termination could not be confirmed.
            # The next MERRICK launch can then reclaim exactly that PID
            # instead of treating it as an unrelated external gateway.
            if process_stopped:
                self.owner_path.unlink(missing_ok=True)
            else:
                log.error("Gateway %s did not confirm shutdown; preserving owner record", process.pid)
        self.port = None
        self.base_url = ""
        await self._close_client()
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None

    async def gateway_request(
        self,
        method: str,
        params: dict | None = None,
        *,
        timeout: float = 30.0,
    ) -> object:
        """Forward any protocol method to OpenClaw; OpenClaw owns authorization."""
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw Gateway is unavailable.")
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        return await self.gateway_rpc.request(method, params, timeout=timeout)

    async def recover_after_repeated_first_delta_stall(self) -> None:
        """Replace a repeatedly wedged Gateway, then let startup recovery drain."""
        async with self._stall_recovery_lock:
            await self.shutdown()
            await self.ensure_ready()
            # OpenClaw schedules interrupted-main-session recovery five seconds
            # after startup. Starting our final retry immediately would put it
            # behind that recovered session on the same global main lane—the
            # exact failure mode this recovery is meant to escape.
            await asyncio.sleep(6.5)

    async def self_heal_runtime_stall(self, *, subsystem: str, code: str) -> str:
        """Check OpenClaw and apply only the host-approved recovery sequence."""
        if (subsystem, code) not in SAFE_RUNTIME_STALLS:
            return "ignored"
        # A loopback health endpoint can remain responsive while the model
        # session lane itself is wedged. Once the host's no-progress watchdog
        # fires, replacing that owned Gateway is the bounded recovery action.
        if (subsystem, code) == ("model_stream", "first_delta_stalled"):
            await self.recover_after_repeated_first_delta_stall()
            return "gateway_restarted"
        try:
            await self.prewarm()
            return "gateway_ready"
        except Exception:
            await self.recover_after_repeated_first_delta_stall()
            return "gateway_restarted"

    async def _forward_openclaw_user_approvals(
        self,
        *,
        agent_id: str,
        safe_session: str,
        ready: asyncio.Event,
        authorize: Callable[[dict[str, object]], Awaitable[str]],
    ) -> None:
        """Forward current-turn exec/plugin approvals to the MERRICK owner."""
        seen: set[str] = set()
        try:
            if self.port is None:
                return
            await self.gateway_rpc.start(
                url=f"ws://127.0.0.1:{self.port}",
                token=self._token(),
            )
            async with self.gateway_rpc.event_subscription() as events:
                # The HTTP request must not start until this live subscription
                # exists, otherwise a fast approval event can be missed.
                ready.set()
                while True:
                    event = await events.get()
                    approval = openclaw_user_approval_request(
                        event,
                        agent_id=agent_id,
                        safe_session=safe_session,
                    )
                    if approval is None or approval["id"] in seen:
                        continue
                    approval_id = str(approval["id"])
                    seen.add(approval_id)
                    decision = await authorize(approval)
                    allowed = approval["allowed_decisions"]
                    if decision not in allowed:
                        decision = "deny"
                    await self.gateway_rpc.request(
                        "approval.resolve",
                        {
                            "id": approval_id,
                            "kind": approval["kind"],
                            "decision": decision,
                        },
                        timeout=5.0,
                    )
        except asyncio.CancelledError:
            raise
        except (OpenClawError, OpenClawGatewayRPCError, OSError) as exc:
            # Approval transport failure must not break an otherwise valid
            # OpenClaw response. OpenClaw retains its own expiry/denial path.
            log.warning("OpenClaw user approval transport failed: %s", exc)
        finally:
            ready.set()

    async def stream_response(
        self,
        text: str,
        *,
        instructions: str,
        session_key: str = "jarvis-desktop",
        max_output_tokens: int | None = None,
        image_base64: str | None = None,
        image_mime: str = "image/jpeg",
        ephemeral_session: bool = False,
        agent_id: str = "main",
        request_user_approval: Callable[[dict[str, object]], Awaitable[str]] | None = None,
    ) -> AsyncIterator[str]:
        """Yield text deltas from OpenClaw's loopback OpenResponses endpoint."""
        await self.ensure_ready()
        safe_session = SAFE_SESSION_RE.sub("-", session_key).strip("-") or "jarvis-desktop"
        gateway_session = self.gateway_session_key(session_key, agent_id=agent_id)
        headers = {
            **self._headers(),
            "x-openclaw-agent-id": agent_id,
        }
        if not ephemeral_session:
            # Give OpenClaw's multi-agent session store an explicit owner.
            # A bare key reaches the selected agent initially but can lose its
            # owner during later event dispatch and fail mid-stream with
            # AGENT_SELECTION_REQUIRED.
            headers["x-openclaw-session-key"] = gateway_session
        request_input: str | list[dict] = text
        if image_base64:
            if image_mime not in {"image/jpeg", "image/png"}:
                raise OpenClawError("The screen capture image type is invalid.")
            request_input = [{
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": text},
                    {
                        "type": "input_image",
                        "source": {
                            "type": "base64",
                            "media_type": image_mime,
                            "data": image_base64,
                        },
                    },
                ],
            }]
        payload = {
            "model": f"openclaw/{agent_id}",
            "input": request_input,
            "instructions": instructions,
            "stream": True,
        }
        if not ephemeral_session:
            payload["user"] = "jarvis-desktop-owner"
        native_agent_runtime = any(
            value and value not in {"openclaw", "auto", "default"}
            for value in (
                os.getenv("JARVIS_OPENAI_RUNTIME", "").strip().lower(),
                os.getenv("JARVIS_ANTHROPIC_RUNTIME", "").strip().lower(),
            )
        )
        # OpenClaw treats a host-authored output cap as an embedded-provider
        # request override. Supplying it therefore replaces an explicitly
        # selected native harness (Codex/Claude CLI) with the OpenClaw loop.
        # Let the native runtime own its response budget instead.
        if max_output_tokens is not None and not native_agent_runtime:
            payload["max_output_tokens"] = max_output_tokens
        # Native MCP approvals remain pending in OpenClaw for 120 seconds. A
        # shorter HTTP read deadline disconnects the runtime while the owner is
        # still looking at MERRICK's approval surface, invalidating the very
        # authority the user is being asked to exercise.
        stream_read_timeout = 150.0 if request_user_approval is not None else 90.0
        timeout = httpx.Timeout(
            connect=5.0,
            read=stream_read_timeout,
            write=15.0,
            pool=5.0,
        )
        event_type = ""
        approval_task: asyncio.Task | None = None
        if request_user_approval is not None:
            approval_ready = asyncio.Event()
            approval_task = asyncio.create_task(
                self._forward_openclaw_user_approvals(
                    agent_id=agent_id,
                    safe_session=safe_session,
                    ready=approval_ready,
                    authorize=request_user_approval,
                )
            )
            await approval_ready.wait()
        try:
            client = await self._client()
            async with client.stream(
                "POST",
                f"{self.base_url}/v1/responses",
                headers=headers,
                json=payload,
                timeout=timeout,
            ) as response:
                    if response.status_code != 200:
                        body = (await response.aread()).decode("utf-8", errors="replace")
                        try:
                            message = json.loads(body).get("error", {}).get("message")
                        except json.JSONDecodeError:
                            message = None
                        raise provider_openclaw_error(
                            message or f"Provider returned HTTP {response.status_code}.",
                            http_status=response.status_code,
                        )
                    content_type = response.headers.get("content-type", "").lower()
                    if not content_type.startswith("text/event-stream"):
                        raise OpenClawError("OpenClaw returned a non-streaming response.")

                    async for line in response.aiter_lines():
                        if not line:
                            event_type = ""
                            continue
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            continue
                        if not line.startswith("data:"):
                            continue
                        raw = line[5:].strip()
                        if raw == "[DONE]":
                            return
                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        kind = event.get("type") or event_type
                        if kind == "response.output_text.delta":
                            delta = event.get("delta")
                            if isinstance(delta, str) and delta:
                                yield delta
                        elif kind == "response.completed":
                            return
                        elif kind == "response.failed":
                            error = event.get("response", {}).get("error") or event.get("error") or {}
                            if isinstance(error, dict):
                                message = " ".join(
                                    str(error.get(field, ""))
                                    for field in ("status", "code", "type", "message")
                                ).strip()
                            else:
                                message = str(error)
                            raise provider_openclaw_error(
                                message or "The provider could not complete the response."
                            )
                    raise OpenClawError("OpenClaw's response stream ended before completion.")
        except httpx.TimeoutException as exc:
            failure = classify_provider_failure("provider request timed out")
            raise OpenClawError(failure.message, failure=failure) from exc
        except httpx.HTTPError as exc:
            failure = ProviderFailure(
                "LOCAL_GATEWAY_UNREACHABLE",
                "MERRICK’s local model gateway disconnected. It will be recovered without changing your provider connection.",
                True,
                False,
            )
            raise OpenClawError(failure.message, failure=failure) from exc
        finally:
            if approval_task is not None:
                approval_task.cancel()
                await asyncio.gather(approval_task, return_exceptions=True)

    async def stream_conversation_response(
        self,
        text: str,
        *,
        instructions: str,
        session_key: str = "jarvis-desktop",
        max_output_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream chat-only output over OpenClaw's resident Gateway socket.

        Static persona, privacy, language, and tool-free policy belong to the
        dedicated conversation agent. ``instructions`` is retained for the
        compatible OpenResponses fallback used by older Gateway builds.
        """
        await self.ensure_ready()
        if self.port is None:
            raise OpenClawError("OpenClaw Gateway is unavailable.")
        safe_session = SAFE_SESSION_RE.sub("-", session_key).strip("-") or "jarvis-desktop"
        gateway_session = f"agent:conversation:{safe_session}"
        await self.gateway_rpc.start(
            url=f"ws://127.0.0.1:{self.port}",
            token=self._token(),
        )
        run_id = ""
        finished = False
        subscribed = False
        try:
            async with self.gateway_rpc.event_subscription() as events:
                try:
                    await self.gateway_rpc.request(
                        "sessions.messages.subscribe",
                        {"key": gateway_session, "agentId": "conversation"},
                        timeout=5.0,
                    )
                    subscribed = True
                    ack = await self.gateway_rpc.request(
                        "chat.send",
                        {
                            "sessionKey": gateway_session,
                            "agentId": "conversation",
                            "message": text,
                            "thinking": "off",
                            "fastMode": True,
                            "queueMode": "interrupt",
                            "deliver": False,
                            "suppressCommandInterpretation": True,
                            "idempotencyKey": secrets.token_hex(16),
                        },
                        timeout=15.0,
                    )
                except OpenClawGatewayRPCError:
                    async for delta in self.stream_response(
                        text,
                        instructions=instructions,
                        session_key=session_key,
                        max_output_tokens=max_output_tokens,
                        agent_id="conversation",
                    ):
                        yield delta
                    finished = True
                    return
                if not isinstance(ack, dict) or not isinstance(ack.get("runId"), str):
                    raise OpenClawError("OpenClaw did not start the conversation run.")
                run_id = ack["runId"]
                accumulated = ""
                while True:
                    frame = await events.get()
                    if frame.get("event") != "chat":
                        continue
                    payload = frame.get("payload")
                    if not isinstance(payload, dict) or payload.get("runId") != run_id:
                        continue
                    state = payload.get("state")
                    if state == "delta":
                        delta = payload.get("deltaText")
                        if not isinstance(delta, str) or not delta:
                            continue
                        if payload.get("replace") is True:
                            if delta.startswith(accumulated):
                                delta = delta[len(accumulated):]
                            elif accumulated.startswith(delta):
                                continue
                            else:
                                raise OpenClawError(
                                    "OpenClaw rewrote an already streamed conversation response."
                                )
                        if delta:
                            accumulated += delta
                            yield delta
                        continue
                    if state == "final":
                        finished = True
                        return
                    if state == "aborted":
                        raise asyncio.CancelledError(
                            str(payload.get("errorMessage") or "Conversation interrupted.")
                        )
                    if state == "error":
                        raise OpenClawError(
                            str(payload.get("errorMessage") or "OpenClaw conversation failed.")
                        )
        finally:
            if run_id and not finished:
                try:
                    await self.gateway_rpc.request(
                        "chat.abort",
                        {
                            "sessionKey": gateway_session,
                            "agentId": "conversation",
                            "runId": run_id,
                        },
                        timeout=3.0,
                    )
                except (Exception, asyncio.CancelledError):
                    pass
            if subscribed:
                try:
                    await self.gateway_rpc.request(
                        "sessions.messages.unsubscribe",
                        {"key": gateway_session, "agentId": "conversation"},
                        timeout=3.0,
                    )
                except (Exception, asyncio.CancelledError):
                    pass

    async def invoke_tool(
        self,
        tool: str,
        args: dict,
        *,
        agent_id: str = "main",
    ) -> dict:
        """Invoke one OpenClaw tool through the authenticated loopback API."""
        await self.ensure_ready()
        client = await self._client()
        response = await client.post(
            f"{self.base_url}/tools/invoke",
            headers=self._headers(),
            json={"tool": tool, "args": args, "agentId": agent_id},
            timeout=30.0,
        )
        try:
            payload = response.json()
        except ValueError as exc:
            raise OpenClawError("OpenClaw returned an invalid tool response.") from exc
        if response.status_code != 200 or not payload.get("ok"):
            message = (payload.get("error") or {}).get("message")
            raise OpenClawError(message or f"OpenClaw tool {tool} failed.")
        return payload.get("result") or {}

    async def save_transcript(
        self,
        turns: Sequence[tuple[str, str]],
        *,
        session_id: str,
        title: str = "MERRICK conversation",
    ) -> dict:
        """Save one bounded conversation chunk using OpenClaw's scoped tool."""
        lines: list[str] = []
        for user_text, assistant_text in turns:
            user_line = " ".join(user_text.split())[:4000]
            assistant_line = " ".join(assistant_text.split())[:6000]
            if user_line:
                lines.append(f"User: {user_line}")
            if assistant_line:
                lines.append(f"MERRICK: {assistant_line}")
        transcript = "\n".join(lines)
        if not transcript:
            return {}
        safe_id = SAFE_SESSION_RE.sub("-", session_id).strip("-")[:100]
        return await self.invoke_tool(
            "transcripts",
            {
                "action": "import",
                "sessionId": safe_id,
                "title": title[:120],
                "providerId": "manual-transcript",
                "transcript": transcript[:100_000],
            },
            agent_id="memory-writer",
        )


gateway = OpenClawGateway()
