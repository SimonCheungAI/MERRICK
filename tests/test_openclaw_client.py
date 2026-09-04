import asyncio
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

import openclaw_client  # noqa: E402
from openclaw_client import (  # noqa: E402
    OpenClawGateway,
    openclaw_user_approval_request,
)


class ActionPlanValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gateway = OpenClawGateway()
        self.gateway.action_secret_path = Path(self.temp_dir.name) / ".action-secret"
        self.gateway.action_secret_path.write_text("a" * 64, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_planner_is_told_not_to_invent_search_terms(self) -> None:
        self.assertIn(
            "Never add a date, year, month, product name, or qualifier",
            openclaw_client.ACTION_SCHEMA_PROMPT,
        )

    def test_valid_plans_are_normalized_and_deduplicated(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "open_app", "app": "spotify"},
                        {"type": "open_app", "app": "spotify"},
                    ]
                },
                "Please open Spotify.",
            ),
            [{"type": "open_app", "app": "spotify"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {
                            "type": "media_control",
                            "player": "spotify",
                            "action": "next",
                        },
                        {
                            "type": "play_music",
                            "player": "music",
                            "query": "  Heroes by David Bowie  ",
                        },
                    ]
                },
                "Skip Spotify, then play Heroes by David Bowie in Music.",
            ),
            [
                {"type": "media_control", "player": "spotify", "action": "next"},
                {
                    "type": "play_music",
                    "player": "music",
                    "query": "Heroes by David Bowie",
                },
            ],
        )

    def test_natural_application_aliases_are_canonicalized(self) -> None:
        cases = (
            ("Open map.", "map", "maps"),
            ("Open Apple Maps.", "Apple Maps", "maps"),
            ("Open Google Chrome.", "Google Chrome", "chrome"),
            ("Open Apple Music.", "Apple Music", "music"),
            ("Open iMessage.", "iMessage", "messages"),
        )
        for utterance, planner_name, expected_name in cases:
            with self.subTest(planner_name=planner_name):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [{"type": "open_app", "app": planner_name}]},
                        utterance,
                    ),
                    [{"type": "open_app", "app": expected_name}],
                )

    def test_read_only_semantic_actions_are_accepted(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "web_research", "query": "OpenClaw security"}]},
                "Research current OpenClaw security information.",
            ),
            [{"type": "web_research", "query": "OpenClaw security"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "inspect_current_view"}]},
                "Read the document currently visible on my screen.",
            ),
            [{"type": "inspect_current_view"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "inspect_current_view"}]},
                "So what can you see on this on this webpage?",
            ),
            [{"type": "inspect_current_view"}],
        )

    def test_deep_research_can_start_a_visible_default_browser_search(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "default",
                        "query": "battery recycling",
                    }]
                },
                "Research battery recycling in depth and compare the sources.",
            ),
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "battery recycling",
            }],
        )

    def test_public_research_can_follow_a_separate_visible_action(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "maps_search", "query": "Tate Modern"},
                        {"type": "web_research", "query": "weather in London"},
                    ]
                },
                "Find Tate Modern in Maps and tell me the weather in London.",
            ),
            [
                {"type": "maps_search", "query": "Tate Modern"},
                {"type": "web_research", "query": "weather in London"},
            ],
        )
        for utterance in (
            "Can you take a look at the screen and see what is happening in the screen here?",
            "Analyze the current screen for me.",
            "Could you explain what is on this screen?",
            "Do you know what is happening in the screen here?",
            "Can you can you see the screen and describe what is happening?",
            "Look at my screen and tell me what these emails are about.",
            "Please analyse the subject lines in the visible inbox.",
            "Can you check the current window and summarise the email about the meeting?",
        ):
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [{"type": "inspect_current_view"}]},
                        utterance,
                    ),
                    [{"type": "inspect_current_view"}],
                )

    def test_compound_app_actions_are_normalized_and_deduplicated(self) -> None:
        cases = (
            (
                {
                    "actions": [
                        {
                            "type": "browser_search",
                            "browser": "chrome",
                            "query": "  OpenClaw release notes  ",
                        },
                        {
                            "type": "browser_search",
                            "browser": "chrome",
                            "query": "OpenClaw release notes",
                        },
                    ]
                },
                [
                    {
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "OpenClaw release notes",
                    }
                ],
                "Search Chrome for OpenClaw release notes.",
            ),
            (
                {"actions": [{"type": "maps_search", "query": "  Tate Modern  "}]},
                [{"type": "maps_search", "query": "Tate Modern"}],
                "Find Tate Modern in Maps.",
            ),
            (
                {
                    "actions": [
                        {"type": "spotify_search", "query": "  Space Oddity  "}
                    ]
                },
                [{"type": "spotify_search", "query": "Space Oddity"}],
                "Search Spotify for Space Oddity.",
            ),
        )
        for arguments, expected, utterance in cases:
            with self.subTest(arguments=arguments):
                self.assertEqual(
                    self.gateway.validate_action_plan(arguments, utterance),
                    expected,
                )

    def test_natural_spotify_play_requests_do_not_confuse_music_with_the_app(self) -> None:
        plan = {
            "actions": [
                {"type": "media_control", "player": "spotify", "action": "play"}
            ]
        }
        for utterance in (
            "Can you play some music for me from Spotify?",
            "Play some music for me on Spotify",
            "Merrick, play some music on Spotify.",
            "Hi Merrick play some music from Spotify for me",
            "Okay Merrick, play some music on Spotify",
            "Open Spotify and play music for me",
        ):
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(plan, utterance),
                    [{"type": "media_control", "player": "spotify", "action": "play"}],
                )

    def test_plain_english_spotify_play_is_not_sent_through_chinese_binding(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "media_control", "player": "spotify", "action": "play"}]},
                "Play Spotify",
            ),
            [{"type": "media_control", "player": "spotify", "action": "play"}],
        )

    def test_chinese_natural_action_plans_are_bound_to_the_utterance(self) -> None:
        cases = (
            (
                "帮我打开谷歌浏览器",
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                [{"type": "open_app", "app": "chrome"}],
            ),
            (
                "请在地图里放大并显示附近咖啡店",
                {
                    "actions": [
                        {"type": "maps_search", "query": "附近咖啡店"},
                        {"type": "gui_task"},
                    ]
                },
                [
                    {"type": "maps_search", "query": "附近咖啡店"},
                    {"type": "gui_task"},
                ],
            ),
            (
                "帮我搜索 agentic AI 并分析",
                {"actions": [{"type": "browser_search", "browser": "default", "query": "agentic AI"}]},
                [{"type": "browser_search", "browser": "default", "query": "agentic AI"}],
            ),
            (
                "你帮我查一下 OpenAI 最新发布",
                {"actions": [{"type": "browser_search", "browser": "default", "query": "OpenAI 最新发布"}]},
                [{"type": "browser_search", "browser": "default", "query": "OpenAI 最新发布"}],
            ),
            (
                "查一查今天伦敦新闻",
                {"actions": [{"type": "browser_search", "browser": "default", "query": "今天伦敦新闻"}]},
                [{"type": "browser_search", "browser": "default", "query": "今天伦敦新闻"}],
            ),
        )
        for utterance, plan, expected in cases:
            with self.subTest(utterance=utterance):
                self.assertEqual(self.gateway.validate_action_plan(plan, utterance), expected)

    def test_turn_off_media_phrasing_targets_explicit_or_active_player(self) -> None:
        cases = (
            (
                "Turn off the music on Spotify",
                {"type": "media_control", "player": "spotify", "action": "pause"},
                {"type": "media_control", "player": "spotify", "action": "pause"},
            ),
            (
                "Help me turn off the music",
                {"type": "media_control", "player": "music", "action": "pause"},
                {"type": "media_control", "player": "active", "action": "pause"},
            ),
            (
                "Stop the music",
                {"type": "media_control", "player": "active", "action": "pause"},
                {"type": "media_control", "player": "active", "action": "pause"},
            ),
        )
        for utterance, proposed, expected in cases:
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [proposed]}, utterance
                    ),
                    [expected],
                )

    def test_broader_natural_action_matrix(self) -> None:
        cases = (
            ("Bring Xcode to the front", {"type": "open_app", "app": "Xcode"}),
            (
                "Search the web for latest SpaceX launch news",
                {
                    "type": "browser_search",
                    "browser": "default",
                    "query": "latest SpaceX launch news",
                },
            ),
            (
                "Find the British Museum in Maps",
                {"type": "maps_search", "query": "British Museum"},
            ),
            (
                "Search Spotify for Heroes",
                {"type": "spotify_search", "query": "Heroes"},
            ),
            ("Make it quieter", {"type": "volume_control", "action": "down"}),
            ("Mute the sound", {"type": "volume_control", "action": "mute"}),
            ("What is on my screen?", {"type": "inspect_current_view"}),
        )
        for utterance, action in cases:
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [action]}, utterance
                    ),
                    [action],
                )

        nearby_action = {"type": "maps_search", "query": "what is nearby"}
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [nearby_action]},
                "Can you open the map and let's see what is nearby",
            ),
            [nearby_action],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "open_app", "app": "maps"}]},
                "Can you open the map and see where the location of us?",
            ),
            [{"type": "open_app", "app": "maps"}],
        )

    def test_natural_maps_navigation_and_media_followups_are_bound(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "maps_search", "query": "Head Street"}]},
                "Take me to Head Street.",
            ),
            [{"type": "maps_search", "query": "Head Street"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "maps_search", "query": "Tate Modern"}]},
                "Go to Tate Modern.",
            ),
            [{"type": "maps_search", "query": "Tate Modern"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "media_control", "player": "active", "action": "play"}
                    ]
                },
                "Play some music.",
            ),
            [{"type": "media_control", "player": "music", "action": "play"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "media_control", "player": "active", "action": "play"}
                    ]
                },
                "Play it again.",
                recent_media_player="spotify",
            ),
            [{"type": "media_control", "player": "spotify", "action": "play"}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "media_control", "player": "active", "action": "play"}
                    ]
                },
                "Play it again.",
            ),
            [],
        )

    def test_natural_open_browser_and_check_request_is_bound(self) -> None:
        plan = {
            "actions": [
                {"type": "browser_search", "browser": "chrome", "query": "SpaceX"}
            ]
        }
        for utterance in (
            "Can you open the Chrome and have a check on SpaceX?",
            "Open Chrome and check SpaceX.",
        ):
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(plan, utterance),
                    [{"type": "browser_search", "browser": "chrome", "query": "SpaceX"}],
                )

    def test_any_user_named_installed_browser_is_schema_valid(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "Firefox",
                        "query": "OpenClaw",
                    }]
                },
                "Search Firefox for OpenClaw",
            ),
            [{"type": "browser_search", "browser": "Firefox", "query": "OpenClaw"}],
        )

    def test_exact_user_named_installed_gui_apps_are_schema_valid(self) -> None:
        for app_name in ("Visual Studio Code", "Xcode", "GarageBand", "NordVPN"):
            with self.subTest(app_name=app_name):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [{"type": "open_app", "app": app_name}]},
                        f"Please open {app_name}.",
                    ),
                    [{"type": "open_app", "app": app_name}],
                )

    def test_dynamic_app_target_rejects_paths_but_not_installed_app_names(self) -> None:
        for app_name in ("/Applications/Xcode.app", "../Xcode"):
            with self.subTest(app_name=app_name):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [{"type": "open_app", "app": app_name}]},
                        f"Open {app_name}",
                    ),
                    [],
                )
        for app_name in ("Terminal", "iTerm2", "Script Editor", "Automator"):
            with self.subTest(app_name=app_name):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": [{"type": "open_app", "app": app_name}]},
                        f"Open {app_name}",
                    ),
                    [{"type": "open_app", "app": app_name}],
                )

    def test_default_browser_and_user_word_reordering_are_accepted(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {
                            "type": "browser_search",
                            "browser": "default",
                            "query": "latest SpaceX launch news",
                        }
                    ]
                },
                "Search the web for the latest news on the SpaceX launch.",
            ),
            [
                {
                    "type": "browser_search",
                    "browser": "default",
                    "query": "latest SpaceX launch news",
                }
            ],
        )

    def test_natural_volume_commands_are_accepted(self) -> None:
        cases = (
            ("Turn the volume up", "up"),
            ("Make it louder", "up"),
            ("Lower the volume please", "down"),
            ("Make it quieter", "down"),
            ("Mute the sound", "mute"),
            ("Unmute the audio", "unmute"),
        )
        for utterance, action in cases:
            with self.subTest(utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {
                            "actions": [
                                {"type": "volume_control", "action": action}
                            ]
                        },
                        utterance,
                    ),
                    [{"type": "volume_control", "action": action}],
                )

    def test_redundant_open_app_is_collapsed_into_same_app_operation(self) -> None:
        cases = (
            (
                [
                    {"type": "open_app", "app": "chrome"},
                    {
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "Alan Turing",
                    },
                ],
                {
                    "type": "browser_search",
                    "browser": "chrome",
                    "query": "Alan Turing",
                },
                "Open Chrome and search Chrome for Alan Turing.",
            ),
            (
                [
                    {"type": "maps_search", "query": "British Museum"},
                    {"type": "open_app", "app": "maps"},
                ],
                {"type": "maps_search", "query": "British Museum"},
                "Open Maps and find the British Museum in Maps.",
            ),
            (
                [
                    {"type": "open_app", "app": "spotify"},
                    {"type": "spotify_search", "query": "David Bowie"},
                ],
                {"type": "spotify_search", "query": "David Bowie"},
                "Open Spotify and search Spotify for David Bowie.",
            ),
            (
                [
                    {"type": "open_app", "app": "music"},
                    {"type": "play_music", "player": "music", "query": "Heroes"},
                ],
                {"type": "play_music", "player": "music", "query": "Heroes"},
                "Open Music and play Heroes in Music.",
            ),
            (
                [
                    {"type": "media_control", "player": "spotify", "action": "pause"},
                    {"type": "open_app", "app": "spotify"},
                ],
                {"type": "media_control", "player": "spotify", "action": "pause"},
                "Open Spotify and pause Spotify.",
            ),
        )
        for actions, expected, utterance in cases:
            with self.subTest(actions=actions):
                self.assertEqual(
                    self.gateway.validate_action_plan(
                        {"actions": actions}, utterance
                    ),
                    [expected],
                )

    def test_unrelated_open_app_is_not_collapsed(self) -> None:
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "open_app", "app": "notes"},
                        {"type": "maps_search", "query": "British Museum"},
                    ]
                },
                "Open Notes and search Maps for the British Museum.",
            ),
            [
                {"type": "open_app", "app": "notes"},
                {"type": "maps_search", "query": "British Museum"},
            ],
        )

    def test_open_web_page_must_be_literal_in_the_user_request(self) -> None:
        exact_url = "https://example.com/source"
        self.assertEqual(
            self.gateway.validate_action_plan(
                {"actions": [{"type": "open_web_page", "url": exact_url}]},
                f"Open {exact_url}.",
            ),
            [{"type": "open_web_page", "url": exact_url}],
        )
        self.assertEqual(
            self.gateway.validate_action_plan(
                {
                    "actions": [
                        {"type": "open_web_page", "url": "https://invented.example"}
                    ]
                },
                "Open the source page.",
            ),
            [],
        )

    def test_malformed_or_overbroad_plans_fail_closed(self) -> None:
        rejected = (
            (None, "Open Safari"),
            ({"actions": [], "extra": True}, "Open Safari"),
            ({"actions": "open Safari"}, "Open Safari"),
            (
                {
                    "actions": [
                        {"type": "open_app", "app": "safari"},
                        {"type": "open_app", "app": "notes"},
                        {"type": "open_app", "app": "maps"},
                    ]
                },
                "Open Safari, Notes, and Maps",
            ),
            (
                {"actions": [{"type": "media_control", "player": "spotify", "action": "delete"}]},
                "Delete the Spotify track",
            ),
            (
                {
                    "actions": [
                        {"type": "web_research", "query": "weather"},
                        {"type": "inspect_current_view"},
                    ]
                },
                "Research the weather and inspect my screen",
            ),
            ({"actions": [{"type": "inspect_current_view", "again": True}]}, "Read my screen"),
            (
                {
                    "actions": [
                        {
                            "type": "browser_search",
                            "browser": "chrome",
                            "query": "OpenClaw",
                            "extra": True,
                        }
                    ]
                },
                "Search Chrome for OpenClaw",
            ),
            (
                {"actions": [{"type": "maps_search", "query": "x" * 301}]},
                "Search Maps",
            ),
            (
                {"actions": [{"type": "spotify_search", "query": "x" * 161}]},
                "Search Spotify",
            ),
            (
                {
                    "actions": [
                        {
                            "type": "browser_search",
                            "browser": "safari",
                            "query": "safe\u007funsafe",
                        }
                    ]
                },
                "Search Safari",
            ),
            (
                {"actions": [{"type": "maps_search", "query": "line one\nline two"}]},
                "Search Maps",
            ),
            (
                {
                    "actions": [
                        {
                            "type": "browser_search",
                            "browser": "chrome",
                            "query": "weather",
                        },
                        {"type": "web_research", "query": "weather"},
                    ]
                },
                "Search for and research the weather",
            ),
        )
        for arguments, utterance in rejected:
            with self.subTest(arguments=arguments):
                self.assertEqual(
                    self.gateway.validate_action_plan(arguments, utterance),
                    [],
                )

    def test_immediate_actions_are_bound_to_the_current_utterance(self) -> None:
        rejected = (
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Why does Chrome take so long to open?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Do not open Chrome.",
            ),
            (
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "OpenAI private project codename",
                    }]
                },
                "Search Chrome for OpenAI.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Tell me a joke.",
            ),
            (
                {"actions": [{"type": "web_research", "query": "secret merger"}]},
                "What is the weather today?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "What if you open Chrome?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "I wonder what happens when you open Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Say the words open Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Repeat after me: open Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "The command is “open Chrome”.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "If I said open Chrome, what would happen?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Can you tell me how to open Chrome?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Don’t open Chrome.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "What is a browser window?",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Can malware see my screen?",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "What size is my screen?",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "The phrase “read my screen” is an example.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "If I ask you to read my screen, what would happen?",
            ),
            (
                {"actions": [{"type": "web_research", "query": "secret merger"}]},
                "Do not research secret merger.",
            ),
            (
                {"actions": [{"type": "web_research", "query": "secret merger"}]},
                "Hypothetically research secret merger.",
            ),
            (
                {"actions": [{"type": "web_research", "query": "password hunter2"}]},
                "Don't search for my password hunter2.",
            ),
            (
                {"actions": [{"type": "browser_search", "browser": "default", "query": "英伟达"}]},
                "不要搜索英伟达",
            ),
            (
                {"actions": [{"type": "browser_search", "browser": "default", "query": "英伟达"}]},
                "为什么搜索功能没了",
            ),
            (
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "kittens",
                    }]
                },
                "Search Chrome for puppies, not kittens.",
            ),
            (
                {"actions": [{"type": "play_music", "player": "music", "query": "Heroes"}]},
                "Play Heroes on Spotify.",
            ),
            (
                {"actions": [{"type": "maps_search", "query": "route algorithms"}]},
                "Show me why route algorithms are hard.",
            ),
            (
                {
                    "actions": [{
                        "type": "open_web_page",
                        "url": "https://example.com",
                    }]
                },
                "Should I open https://example.com?",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari and tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari, but tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari but tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari while telling me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari before telling me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari because Chrome is slow.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari instead of Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari, tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari: close Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari — tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari and could you tell me about Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Safari and close Chrome.",
            ),
            (
                {"actions": [{"type": "media_control", "player": "music", "action": "pause"}]},
                "Pause Spotify and tell me why Music is popular.",
            ),
            (
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "cats",
                    }]
                },
                "Search Safari for cats and tell me why Chrome is slow.",
            ),
            (
                {"actions": [{"type": "spotify_search", "query": "cats"}]},
                "Search Chrome for cats and tell me about Spotify.",
            ),
            (
                {"actions": [{"type": "maps_search", "query": "Tate Modern"}]},
                "Search Chrome for Tate Modern and tell me about Maps.",
            ),
            (
                {"actions": [{"type": "web_research", "query": "cats"}]},
                "Search Chrome for cats.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Show me how to open Chrome.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Read this article and explain why you would inspect the current document.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Read this text and tell me how to inspect the current window.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Read this text, tell me how to inspect the current window.",
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Read this text but tell me how to inspect the current window.",
            ),
            (
                {"actions": [{"type": "media_control", "player": "spotify", "action": "play"}]},
                "Start Spotify.",
            ),
            (
                {"actions": [{"type": "media_control", "player": "spotify", "action": "previous"}]},
                "Back Spotify up.",
            ),
            (
                {"actions": [{"type": "play_music", "player": "music", "query": "music video"}]},
                "Play the music video in Chrome.",
            ),
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Open Chrome when it is noon.",
            ),
            (
                {"actions": [{"type": "web_research", "query": "alice example com"}]},
                "What is alice@example.com?",
            ),
            (
                {"actions": [{"type": "web_research", "query": "sk proj abcdef0123456789"}]},
                "What is " + "sk-" + "proj-abcdef0123456789?",
            ),
            (
                {"actions": [{"type": "web_research", "query": "melanoma"}]},
                "What is my medical diagnosis melanoma?",
            ),
        )
        for plan, utterance in rejected:
            with self.subTest(plan=plan, utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(plan, utterance),
                    [],
                )

    def test_direct_current_utterance_bindings_are_accepted(self) -> None:
        accepted = (
            (
                {"actions": [{"type": "open_app", "app": "chrome"}]},
                "Please open Chrome.",
                [{"type": "open_app", "app": "chrome"}],
            ),
            (
                {
                    "actions": [{
                        "type": "browser_search",
                        "browser": "chrome",
                        "query": "OpenAI release notes",
                    }]
                },
                "Search Chrome for OpenAI release notes.",
                [{
                    "type": "browser_search",
                    "browser": "chrome",
                    "query": "OpenAI release notes",
                }],
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Read the current document visible on my screen.",
                [{"type": "inspect_current_view"}],
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Can we analyse the maths together on my screen?",
                [{"type": "inspect_current_view"}],
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "Please analyse the formula on the current page.",
                [{"type": "inspect_current_view"}],
            ),
            (
                {"actions": [{"type": "inspect_current_view"}]},
                "I need you to analyse the mathematics displayed on my screen.",
                [{"type": "inspect_current_view"}],
            ),
        )
        for plan, utterance, expected in accepted:
            with self.subTest(plan=plan, utterance=utterance):
                self.assertEqual(
                    self.gateway.validate_action_plan(plan, utterance),
                    expected,
                )

    def test_implicit_research_rejects_private_work_context(self) -> None:
        rejected = (
            "What is the latest status of my client Project Bluebird?",
            "What is happening with our unreleased Project Bluebird?",
            "Could you check my confidential merger Falcon?",
            "Find updates about my project Atlas.",
            "Search for our internal roadmap Orion.",
        )
        for utterance in rejected:
            with self.subTest(utterance=utterance):
                self.assertFalse(
                    openclaw_client.automatic_research_is_public(
                        utterance,
                        utterance.rstrip("?"),
                    )
                )

        self.assertTrue(
            openclaw_client.automatic_research_is_public(
                "What is the latest news about Project Bluebird?",
                "latest news about Project Bluebird",
            )
        )


class BoundedWebPageInvocationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.gateway = OpenClawGateway()
        self.gateway.action_secret_path = Path(self.temp_dir.name) / ".action-secret"
        self.gateway.action_secret_path.write_text("a" * 64, encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    async def test_invalid_signature_is_reminted_once_after_gateway_rotation(self) -> None:
        gateway = self.gateway
        action = {"type": "open_web_page", "url": "https://example.com"}
        capability = {
            "tool": "jarvis_open_web_page",
            "fixedArguments": {"url": "https://example.com"},
            "authorization": "signed-capability",
        }
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway.action_capabilities_for_plan = Mock(  # type: ignore[method-assign]
            return_value=[capability]
        )
        gateway.public_page_capability = Mock(  # type: ignore[method-assign]
            return_value=capability
        )
        gateway.invoke_tool = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                openclaw_client.OpenClawError(
                    "The desktop action authorization is invalid."
                ),
                {"content": [{"type": "text", "text": "opened"}]},
            ]
        )

        result = await gateway.invoke_bounded_web_page(action)

        self.assertEqual(result["content"][0]["text"], "opened")
        self.assertEqual(gateway.ensure_ready.await_count, 2)  # type: ignore[attr-defined]
        self.assertEqual(gateway.action_capabilities_for_plan.call_count, 1)  # type: ignore[attr-defined]
        self.assertEqual(gateway.public_page_capability.call_count, 2)  # type: ignore[attr-defined]
        self.assertEqual(gateway.invoke_tool.await_count, 2)  # type: ignore[attr-defined]

    async def test_ambiguous_failure_is_never_retried(self) -> None:
        gateway = self.gateway
        action = {"type": "open_web_page", "url": "https://example.com"}
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway.action_capabilities_for_plan = Mock(  # type: ignore[method-assign]
            return_value=[{
                "tool": "jarvis_open_web_page",
                "fixedArguments": {"url": "https://example.com"},
                "authorization": "signed-capability",
            }]
        )
        gateway.public_page_capability = Mock(  # type: ignore[method-assign]
            return_value={
                "tool": "jarvis_open_web_page",
                "fixedArguments": {"url": "https://example.com"},
                "authorization": "signed-capability",
            }
        )
        gateway.invoke_tool = AsyncMock(  # type: ignore[method-assign]
            side_effect=openclaw_client.OpenClawError("Connection failed.")
        )

        with self.assertRaisesRegex(openclaw_client.OpenClawError, "Connection failed"):
            await gateway.invoke_bounded_web_page(action)

        self.assertEqual(gateway.invoke_tool.await_count, 1)  # type: ignore[attr-defined]

    async def test_selected_result_page_is_read_with_an_exact_capability(self) -> None:
        self.gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        self.gateway.invoke_tool = AsyncMock(  # type: ignore[method-assign]
            return_value={
                "title": "Example",
                "url": "https://example.com/result",
                "text": "Readable source text",
            }
        )

        result = await self.gateway.invoke_bounded_read_page(
            "https://example.com/result"
        )

        self.assertEqual(result["text"], "Readable source text")
        invoked_tool, arguments = self.gateway.invoke_tool.await_args.args  # type: ignore[attr-defined]
        self.assertEqual(invoked_tool, "jarvis_read_web_page")
        self.assertEqual(arguments["url"], "https://example.com/result")
        self.assertTrue(arguments["authorization"].startswith("v1."))
        self.assertEqual(
            self.gateway.invoke_tool.await_args.kwargs["agent_id"],  # type: ignore[attr-defined]
            "page-reader-executor",
        )

    def test_validated_plan_mints_only_exact_host_capabilities(self) -> None:
        actions = [
            {"type": "open_app", "app": "safari"},
            {"type": "open_app", "app": "Terminal"},
            {"type": "media_control", "player": "spotify", "action": "pause"},
        ]
        capabilities = self.gateway.action_capabilities_for_plan(actions)
        self.assertEqual(
            [item["tool"] for item in capabilities],
            ["jarvis_open_app", "jarvis_open_app", "jarvis_media_control"],
        )
        self.assertEqual(capabilities[0]["fixedArguments"], {"app": "safari"})
        self.assertEqual(capabilities[1]["fixedArguments"], {"app": "Terminal"})
        self.assertEqual(
            capabilities[2]["fixedArguments"],
            {"player": "spotify", "action": "pause"},
        )
        self.assertTrue(
            all(item["authorization"].startswith("v1.") for item in capabilities)
        )

    def test_read_only_actions_do_not_mint_host_tokens(self) -> None:
        self.assertEqual(
            self.gateway.action_capabilities_for_plan(
                [
                    {"type": "web_research", "query": "OpenClaw security"},
                    {"type": "inspect_current_view"},
                ]
            ),
            [],
        )

    def test_native_compound_actions_do_not_mint_openclaw_tokens(self) -> None:
        self.assertEqual(
            self.gateway.action_capabilities_for_plan(
                [
                    {
                        "type": "browser_search",
                        "browser": "safari",
                        "query": "OpenClaw security",
                    },
                    {"type": "maps_search", "query": "Tate Modern"},
                ]
            ),
            [],
        )
        self.assertEqual(
            self.gateway.action_capabilities_for_plan(
                [{"type": "spotify_search", "query": "Heroes"}]
            ),
            [],
        )

    def test_main_agent_protocol_prompt_allows_normal_conversation(self) -> None:
        prompt = openclaw_client.ACTION_RESPONSE_PROTOCOL_PROMPT
        self.assertIn('JARVIS_ACTION {"actions":[...]}', prompt)
        self.assertIn("answer normally", prompt)
        self.assertIn("browser_search", prompt)
        self.assertIn("Only the trusted host may announce", prompt)
        self.assertNotIn("Return exactly one JSON object on one line", prompt)

    def test_music_and_literal_page_capabilities_are_exact(self) -> None:
        capabilities = self.gateway.action_capabilities_for_plan(
            [
                {"type": "play_music", "player": "music", "query": "Heroes"},
                {"type": "open_web_page", "url": "https://example.com/source"},
            ]
        )
        self.assertEqual(
            [item["tool"] for item in capabilities],
            ["jarvis_play_music", "jarvis_open_web_page"],
        )
        self.assertEqual(
            capabilities[0]["fixedArguments"],
            {"player": "music", "query": "Heroes"},
        )
        self.assertEqual(
            capabilities[1]["fixedArguments"],
            {"url": "https://example.com/source"},
        )


class FakePlannerResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self.payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self.payload


class FakePlannerHTTPClient:
    def __init__(self, captured: dict, response: FakePlannerResponse, **_kwargs) -> None:
        self.captured = captured
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, **kwargs):
        self.captured.update({"url": url, **kwargs})
        return self.response


class SemanticPlannerGatewayTests(unittest.IsolatedAsyncioTestCase):
    async def make_plan(self, response_payload: dict, text: str) -> tuple[list[dict], dict]:
        captured: dict = {}
        gateway = OpenClawGateway()
        gateway.base_url = "http://127.0.0.1:12345"
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._headers = lambda: {"Authorization": "Bearer test"}  # type: ignore[method-assign]
        response = FakePlannerResponse(response_payload)
        with patch.object(
            openclaw_client.httpx,
            "AsyncClient",
            side_effect=lambda **kwargs: FakePlannerHTTPClient(
                captured, response, **kwargs
            ),
        ):
            plan = await gateway.plan_actions(text)
        return plan, captured

    async def test_tool_less_json_plan_is_validated(self) -> None:
        plan, captured = await self.make_plan(
            {
                "output": [
                    {
                        "type": "message",
                        "content": [
                            {
                                "type": "output_text",
                                "text": json.dumps(
                                    {
                                        "actions": [
                                            {"type": "open_app", "app": "spotify"}
                                        ]
                                    }
                                ),
                            }
                        ],
                    }
                ]
            },
            "Put Spotify on for me.",
        )
        self.assertEqual(plan, [{"type": "open_app", "app": "spotify"}])
        self.assertEqual(captured["url"], "http://127.0.0.1:12345/v1/responses")
        self.assertEqual(captured["headers"]["x-openclaw-agent-id"], "action-planner")
        self.assertNotIn("tools", captured["json"])
        self.assertNotIn("tool_choice", captured["json"])
        self.assertEqual(captured["json"]["input"], "Put Spotify on for me.")

    async def test_wrong_or_invalid_planner_output_fails_closed(self) -> None:
        cases = (
            {"output": []},
            {
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "not json"}],
                    }
                ]
            },
            {
                "output": [
                    {
                        "type": "function_call",
                        "name": "jarvis_propose_actions",
                        "arguments": '{"actions":[]}',
                    }
                ]
            },
        )
        for response_payload in cases:
            with self.subTest(response_payload=response_payload):
                plan, _ = await self.make_plan(response_payload, "Open Terminal")
                self.assertEqual(plan, [])

    async def test_planner_can_return_any_user_named_installed_app(self) -> None:
        payload = {
            "output": [{
                "type": "message",
                "content": [{
                    "type": "output_text",
                    "text": json.dumps({
                        "actions": [{"type": "open_app", "app": "Terminal"}]
                    }),
                }],
            }],
        }

        plan, _ = await self.make_plan(payload, "Open Terminal")

        self.assertEqual(plan, [{"type": "open_app", "app": "Terminal"}])


class OpenClawUserApprovalTests(unittest.IsolatedAsyncioTestCase):
    def approval_event(self, **request_overrides) -> dict:
        request = {
            "pluginId": "codex",
            "toolName": "codex_mcp_tool_approval",
            "agentId": "main",
            "sessionKey": "agent:main:openresponses:jarvis-owner",
            "title": "Allow ChatGPT to use Google Chrome?",
            "description": (
                "Allow ChatGPT to use Google Chrome?\n\n"
                "MCP server: computer-use"
            ),
            "allowedDecisions": ["allow-once", "allow-always", "deny"],
        }
        request.update(request_overrides)
        return {
            "type": "event",
            "event": "plugin.approval.requested",
            "payload": {
                "id": "plugin:computer-use-access",
                "request": request,
            },
        }

    def test_exposes_current_plugin_approval_to_the_user(self) -> None:
        approval = openclaw_user_approval_request(
            self.approval_event(),
            agent_id="main",
            safe_session="jarvis-owner",
        )

        self.assertEqual(approval, {
            "id": "plugin:computer-use-access",
            "kind": "plugin",
            "title": "Allow ChatGPT to use Google Chrome?",
            "description": (
                "Allow ChatGPT to use Google Chrome?\n\n"
                "MCP server: computer-use"
            ),
            "severity": "warning",
            "allowed_decisions": ["allow-once", "allow-always", "deny"],
        })

    def test_uses_openclaw_defaults_when_plugin_decisions_are_omitted(self) -> None:
        approval = openclaw_user_approval_request(
            self.approval_event(allowedDecisions=None),
            agent_id="main",
            safe_session="jarvis-owner",
        )

        self.assertEqual(
            approval["allowed_decisions"] if approval is not None else None,
            ["allow-once", "allow-always", "deny"],
        )

    def test_exposes_current_exec_approval_to_the_user(self) -> None:
        approval = openclaw_user_approval_request({
            "type": "event",
            "event": "exec.approval.requested",
            "payload": {
                "id": "exec:write-report",
                "request": {
                    "agentId": "main",
                    "sessionKey": "agent:main:openresponses:jarvis-owner",
                    "command": "python generate_report.py",
                    "cwd": "/Users/owner/Project",
                    "allowedDecisions": ["allow-once", "deny"],
                },
            },
        }, agent_id="main", safe_session="jarvis-owner")

        self.assertEqual(approval, {
            "id": "exec:write-report",
            "kind": "exec",
            "title": "Run this command?",
            "description": "python generate_report.py\n\n/Users/owner/Project",
            "severity": "warning",
            "allowed_decisions": ["allow-once", "deny"],
        })

    def test_rejects_an_approval_from_another_session(self) -> None:
        self.assertIsNone(openclaw_user_approval_request(
            self.approval_event(
                sessionKey="agent:main:openresponses:someone-else"
            ),
            agent_id="main",
            safe_session="jarvis-owner",
        ))

    async def test_forwards_user_decision_to_the_unified_approval_api(self) -> None:
        gateway = OpenClawGateway()
        gateway.port = 24567
        gateway._token = Mock(return_value="a" * 64)  # type: ignore[method-assign]
        gateway.gateway_rpc.start = AsyncMock()  # type: ignore[method-assign]
        gateway.gateway_rpc.request = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]
        events: asyncio.Queue[dict] = asyncio.Queue()

        @asynccontextmanager
        async def subscription():
            yield events

        gateway.gateway_rpc.event_subscription = Mock(  # type: ignore[attr-defined]
            side_effect=subscription
        )
        ready = asyncio.Event()
        authorize = AsyncMock(return_value="allow-once")
        resolver = asyncio.create_task(
            gateway._forward_openclaw_user_approvals(
                agent_id="main",
                safe_session="jarvis-owner",
                ready=ready,
                authorize=authorize,
            )
        )
        try:
            await asyncio.wait_for(ready.wait(), timeout=1.0)
            await events.put(self.approval_event())
            for _ in range(20):
                if gateway.gateway_rpc.request.await_count:  # type: ignore[attr-defined]
                    break
                await asyncio.sleep(0)

            authorize.assert_awaited_once_with({
                "id": "plugin:computer-use-access",
                "kind": "plugin",
                "title": "Allow ChatGPT to use Google Chrome?",
                "description": (
                    "Allow ChatGPT to use Google Chrome?\n\n"
                    "MCP server: computer-use"
                ),
                "severity": "warning",
                "allowed_decisions": ["allow-once", "allow-always", "deny"],
            })
            gateway.gateway_rpc.request.assert_awaited_once_with(  # type: ignore[attr-defined]
                "approval.resolve",
                {
                    "id": "plugin:computer-use-access",
                    "kind": "plugin",
                    "decision": "allow-once",
                },
                timeout=5.0,
            )
        finally:
            resolver.cancel()
            await asyncio.gather(resolver, return_exceptions=True)


class FakeOpenResponsesStream:
    status_code = 200
    headers = {"content-type": "text/event-stream"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def aiter_lines(self):
        yield 'data: {"type":"response.output_text.delta","delta":"ready"}'
        yield 'data: {"type":"response.completed"}'


class FakeOpenResponsesClient:
    def __init__(self) -> None:
        self.request: dict = {}

    def stream(self, method: str, url: str, **kwargs):
        self.request = {"method": method, "url": url, **kwargs}
        return FakeOpenResponsesStream()


class OpenResponsesRoutingTests(unittest.IsolatedAsyncioTestCase):
    async def test_durable_main_request_has_explicit_agent_model_and_session_owner(self) -> None:
        gateway = OpenClawGateway()
        gateway.base_url = "http://127.0.0.1:24567"
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._headers = Mock(return_value={"Authorization": "Bearer test"})  # type: ignore[method-assign]
        client = FakeOpenResponsesClient()
        gateway._client = AsyncMock(return_value=client)  # type: ignore[method-assign]

        chunks = [
            chunk
            async for chunk in gateway.stream_response(
                "Inspect Chrome",
                instructions="Use Computer Use.",
                session_key="jarvis-owner",
                agent_id="main",
            )
        ]

        self.assertEqual(chunks, ["ready"])
        self.assertEqual(client.request["json"]["model"], "openclaw/main")
        self.assertEqual(client.request["headers"]["x-openclaw-agent-id"], "main")
        self.assertEqual(
            client.request["headers"]["x-openclaw-session-key"],
            "agent:main:openresponses:jarvis-owner",
        )

    async def test_codex_runtime_is_not_forced_back_to_openclaw_by_host_token_cap(self) -> None:
        gateway = OpenClawGateway()
        gateway.base_url = "http://127.0.0.1:24567"
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._headers = Mock(return_value={"Authorization": "Bearer test"})  # type: ignore[method-assign]
        client = FakeOpenResponsesClient()
        gateway._client = AsyncMock(return_value=client)  # type: ignore[method-assign]

        with patch.dict("os.environ", {"JARVIS_OPENAI_RUNTIME": "codex"}):
            chunks = [
                chunk
                async for chunk in gateway.stream_response(
                    "Inspect Chrome",
                    instructions="Use Computer Use.",
                    session_key="jarvis-owner",
                    agent_id="main",
                    max_output_tokens=512,
                )
            ]

        self.assertEqual(chunks, ["ready"])
        self.assertNotIn("max_output_tokens", client.request["json"])

    async def test_owner_approval_can_outlive_openclaw_default_wait(self) -> None:
        gateway = OpenClawGateway()
        gateway.base_url = "http://127.0.0.1:24567"
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._headers = Mock(return_value={"Authorization": "Bearer test"})  # type: ignore[method-assign]
        client = FakeOpenResponsesClient()
        gateway._client = AsyncMock(return_value=client)  # type: ignore[method-assign]

        async def arm_approval_listener(**kwargs) -> None:
            kwargs["ready"].set()

        gateway._forward_openclaw_user_approvals = arm_approval_listener  # type: ignore[method-assign]

        chunks = [
            chunk
            async for chunk in gateway.stream_response(
                "Inspect Finder",
                instructions="Use Computer Use.",
                session_key="jarvis-owner",
                agent_id="main",
                request_user_approval=AsyncMock(return_value="deny"),
            )
        ]

        self.assertEqual(chunks, ["ready"])
        self.assertGreater(client.request["timeout"].read, 120.0)

class PersistentConversationLaneTests(unittest.IsolatedAsyncioTestCase):
    async def test_conversation_uses_gateway_chat_events_on_one_persistent_connection(self) -> None:
        gateway = OpenClawGateway()
        gateway.port = 24567
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._token = Mock(return_value="a" * 64)  # type: ignore[method-assign]
        gateway.gateway_rpc.start = AsyncMock()  # type: ignore[method-assign]
        gateway.gateway_rpc.request = AsyncMock(  # type: ignore[method-assign]
            return_value={"runId": "run-1", "status": "started"}
        )
        events: asyncio.Queue[dict] = asyncio.Queue()
        await events.put({
            "type": "event",
            "event": "chat",
            "payload": {
                "runId": "another-run",
                "sessionKey": "agent:conversation:other",
                "state": "delta",
                "deltaText": "ignore me",
            },
        })
        await events.put({
            "type": "event",
            "event": "chat",
            "payload": {
                "runId": "run-1",
                "sessionKey": "agent:conversation:jarvis-chat",
                "state": "delta",
                "deltaText": "Good ",
            },
        })
        await events.put({
            "type": "event",
            "event": "chat",
            "payload": {
                "runId": "run-1",
                "sessionKey": "agent:conversation:jarvis-chat",
                "state": "delta",
                "deltaText": "morning.",
            },
        })
        await events.put({
            "type": "event",
            "event": "chat",
            "payload": {
                "runId": "run-1",
                "sessionKey": "agent:conversation:jarvis-chat",
                "state": "final",
            },
        })

        @asynccontextmanager
        async def subscription():
            yield events

        gateway.gateway_rpc.event_subscription = Mock(  # type: ignore[attr-defined]
            side_effect=subscription
        )

        chunks = [
            chunk
            async for chunk in gateway.stream_conversation_response(
                "Good morning",
                instructions="Reply briefly.",
                session_key="jarvis-chat",
                max_output_tokens=80,
            )
        ]

        self.assertEqual(chunks, ["Good ", "morning."])
        gateway.gateway_rpc.start.assert_awaited_once_with(  # type: ignore[attr-defined]
            url="ws://127.0.0.1:24567",
            token="a" * 64,
        )
        calls = gateway.gateway_rpc.request.await_args_list  # type: ignore[attr-defined]
        self.assertEqual(
            [call.args[0] for call in calls],
            ["sessions.messages.subscribe", "chat.send", "sessions.messages.unsubscribe"],
        )
        method, params = calls[1].args
        self.assertEqual(method, "chat.send")
        self.assertEqual(params["sessionKey"], "agent:conversation:jarvis-chat")
        self.assertEqual(params["agentId"], "conversation")
        self.assertEqual(params["message"], "Good morning")
        self.assertEqual(params["queueMode"], "interrupt")
        self.assertTrue(params["fastMode"])
        self.assertFalse(params["deliver"])

    async def test_cancelling_conversation_aborts_only_its_gateway_run(self) -> None:
        gateway = OpenClawGateway()
        gateway.port = 24567
        gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        gateway._token = Mock(return_value="a" * 64)  # type: ignore[method-assign]
        gateway.gateway_rpc.start = AsyncMock()  # type: ignore[method-assign]
        gateway.gateway_rpc.request = AsyncMock(  # type: ignore[method-assign]
            return_value={"runId": "run-cancel", "status": "started"}
        )
        events: asyncio.Queue[dict] = asyncio.Queue()

        @asynccontextmanager
        async def subscription():
            yield events

        gateway.gateway_rpc.event_subscription = Mock(  # type: ignore[attr-defined]
            side_effect=subscription
        )
        stream = gateway.stream_conversation_response(
            "Tell me something",
            instructions="Reply briefly.",
            session_key="jarvis-chat",
        )
        pending = asyncio.create_task(anext(stream))
        await asyncio.sleep(0)
        pending.cancel()
        await asyncio.gather(pending, return_exceptions=True)
        await stream.aclose()

        abort_calls = [
            call for call in gateway.gateway_rpc.request.await_args_list
            if call.args and call.args[0] == "chat.abort"
        ]  # type: ignore[attr-defined]
        self.assertEqual(len(abort_calls), 1)
        self.assertEqual(abort_calls[0].args[1]["runId"], "run-cancel")


class RuntimeSelfHealingTests(unittest.IsolatedAsyncioTestCase):
    def test_upgrade_retries_belong_to_gateway_startup_not_page_actions(self) -> None:
        source = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )
        startup = source[
            source.index("async def ensure_ready"):
            source.index("async def shutdown")
        ]
        public_page = source[
            source.index("async def _invoke_bounded_public_page"):
            source.index("async def invoke_bounded_web_page")
        ]

        self.assertIn("for attempt in range(3):", startup)
        self.assertIn("for attempt in range(2):", public_page)
        self.assertNotIn("for attempt in range(3):", public_page)

    def test_gateway_cold_start_budget_covers_plugin_and_auth_migrations(self) -> None:
        source = (PROJECT_ROOT / "server" / "openclaw_client.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("GATEWAY_STARTUP_TIMEOUT_SECONDS = 45.0", source)
        self.assertIn("loop.time() + GATEWAY_STARTUP_TIMEOUT_SECONDS", source)

    def test_obsolete_codex_install_record_is_detected_without_touching_oauth(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gateway.state_dir = root / "state"
            database = gateway.state_dir / "state/openclaw.sqlite"
            database.parent.mkdir(parents=True)
            bundled_manifest = (
                root / "node_modules/openclaw/dist/extensions/codex/openclaw.plugin.json"
            )
            bundled_manifest.parent.mkdir(parents=True)
            bundled_manifest.write_text('{"id":"codex"}', encoding="utf-8")
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE installed_plugin_index "
                    "(index_key TEXT PRIMARY KEY, install_records_json TEXT NOT NULL)"
                )
                connection.execute(
                    "INSERT INTO installed_plugin_index VALUES (?, ?)",
                    (
                        "installed-plugin-index",
                        json.dumps(
                            {
                                "codex": {
                                    "source": "path",
                                    "installPath": "/old/MERRICK/@openclaw/codex",
                                }
                            }
                        ),
                    ),
                )

            with patch("openclaw_client.PROJECT_ROOT", root):
                self.assertTrue(gateway._obsolete_codex_install_record_present())
                with sqlite3.connect(database) as connection:
                    connection.execute(
                        "UPDATE installed_plugin_index SET install_records_json = ?",
                        ("{}",),
                    )
                self.assertFalse(gateway._obsolete_codex_install_record_present())

                cached_plugin = (
                    gateway.state_dir
                    / "npm/projects/openclaw-codex-old/node_modules/@openclaw/codex"
                )
                cached_plugin.mkdir(parents=True)
                (cached_plugin / "package.json").write_text(
                    '{"name":"@openclaw/codex"}', encoding="utf-8"
                )
                (cached_plugin / "openclaw.plugin.json").write_text(
                    '{"id":"codex"}', encoding="utf-8"
                )
                self.assertTrue(gateway._obsolete_codex_install_record_present())

    async def test_reconnecting_clients_share_one_cancellation_safe_prewarm(self) -> None:
        gateway = OpenClawGateway()
        startup_entered = asyncio.Event()
        release_startup = asyncio.Event()
        startup_calls = 0

        async def slow_startup() -> None:
            nonlocal startup_calls
            startup_calls += 1
            startup_entered.set()
            await release_startup.wait()

        client = Mock()
        client.get = AsyncMock(return_value=Mock(status_code=200))
        gateway.ensure_ready = slow_startup  # type: ignore[method-assign]
        gateway._client = AsyncMock(return_value=client)  # type: ignore[method-assign]

        disconnected_client = asyncio.create_task(gateway.prewarm())
        await startup_entered.wait()
        disconnected_client.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await disconnected_client

        reconnected_client = asyncio.create_task(gateway.prewarm())
        release_startup.set()
        await reconnected_client

        self.assertEqual(startup_calls, 1)
        self.assertEqual(client.get.await_count, 1)

    async def test_gateway_request_uses_official_rpc_without_a_jarvis_method_allowlist(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            gateway.token_path = Path(temporary) / ".gateway-token"
            gateway.token_path.write_text("a" * 64, encoding="utf-8")
            gateway.port = 24567
            gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
            gateway.gateway_rpc.start = AsyncMock()  # type: ignore[method-assign]
            gateway.gateway_rpc.request = AsyncMock(return_value={"ok": True})  # type: ignore[method-assign]

            result = await gateway.gateway_request(
                "worktrees.create",
                {"repoRoot": "/tmp/example"},
                timeout=12.0,
            )

            self.assertEqual(result, {"ok": True})
            gateway.gateway_rpc.start.assert_awaited_once_with(  # type: ignore[attr-defined]
                url="ws://127.0.0.1:24567",
                token="a" * 64,
            )
            gateway.gateway_rpc.request.assert_awaited_once_with(  # type: ignore[attr-defined]
                "worktrees.create",
                {"repoRoot": "/tmp/example"},
                timeout=12.0,
            )

    async def test_unowned_startup_migration_lease_is_removed_before_retry(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            gateway.state_dir = Path(temporary)
            gateway.owner_path = gateway.state_dir / ".gateway-owner.json"
            database = gateway.state_dir / "state" / "openclaw.sqlite"
            database.parent.mkdir(parents=True)
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "CREATE TABLE state_leases (scope TEXT, lease_key TEXT)"
                )
                connection.execute(
                    "INSERT INTO state_leases(scope, lease_key) VALUES (?, ?)",
                    ("startup-migrations", "global"),
                )

            removed = await gateway._clear_unowned_startup_migration_lease()

            self.assertTrue(removed)
            with sqlite3.connect(database) as connection:
                remaining = connection.execute(
                    "SELECT COUNT(*) FROM state_leases WHERE scope = ? AND lease_key = ?",
                    ("startup-migrations", "global"),
                ).fetchone()[0]
            self.assertEqual(remaining, 0)

    def test_stopped_writer_upgrade_failure_is_detected_only_in_new_gateway_output(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "gateway.log"
            old_output = (
                "Agent identity migration requires stopped-writer maintenance; "
                "stop active agents and run openclaw doctor --fix.\n"
            )
            log_path.write_text(old_output, encoding="utf-8")
            offset = log_path.stat().st_size

            self.assertFalse(
                gateway._gateway_log_requires_offline_migration(log_path, offset)
            )

            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(
                    "OpenClaw startup migrations did not complete cleanly.\n"
                    "Agent identity migration requires stopped-writer maintenance; "
                    "stop active agents and run openclaw doctor --fix.\n"
                )

            self.assertTrue(
                gateway._gateway_log_requires_offline_migration(log_path, offset)
            )

    def test_legacy_session_store_upgrade_also_uses_the_official_offline_repair(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            log_path = Path(temporary) / "gateway.log"
            log_path.write_text(
                "Gateway failed to start: Legacy session store requires migration: "
                "/private/state/agents/main/sessions/sessions.json. "
                "Run openclaw doctor --fix against the same state/config before starting OpenClaw.\n",
                encoding="utf-8",
            )

            self.assertTrue(
                gateway._gateway_log_requires_offline_migration(log_path, 0)
            )

    async def test_offline_upgrade_repair_runs_the_bounded_official_doctor(self) -> None:
        gateway = OpenClawGateway()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            gateway.state_dir = root / "state"
            gateway.state_dir.mkdir()
            gateway.owner_path = gateway.state_dir / ".gateway-owner.json"
            node = root / "node"
            cli = root / "node_modules/openclaw/openclaw.mjs"
            cli.parent.mkdir(parents=True)
            node.write_text("", encoding="utf-8")
            cli.write_text("", encoding="utf-8")
            log_path = gateway.state_dir / "gateway.log"
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"", b"")

            with (
                patch.object(gateway, "_expected_node_path", return_value=node),
                patch("openclaw_client.PROJECT_ROOT", root),
                patch(
                    "openclaw_client.asyncio.create_subprocess_exec",
                    AsyncMock(return_value=process),
                ) as create_process,
            ):
                repaired = await gateway._run_offline_upgrade_repair(
                    {"OPENCLAW_STATE_DIR": str(gateway.state_dir)},
                    log_path,
                )

            self.assertTrue(repaired)
            create_process.assert_awaited_once()
            arguments = create_process.await_args.args
            self.assertEqual(arguments[:2], (str(node), str(cli)))
            self.assertEqual(
                arguments[2:],
                ("doctor", "--fix", "--non-interactive", "--yes"),
            )

    async def test_healthy_gateway_is_not_restarted_for_a_local_voice_recovery(self) -> None:
        gateway = OpenClawGateway()
        gateway.prewarm = AsyncMock()  # type: ignore[method-assign]
        gateway.recover_after_repeated_first_delta_stall = AsyncMock()  # type: ignore[method-assign]

        outcome = await gateway.self_heal_runtime_stall(
            subsystem="voice_pipeline",
            code="external_playback_gate_stalled",
        )

        self.assertEqual(outcome, "gateway_ready")
        gateway.recover_after_repeated_first_delta_stall.assert_not_awaited()  # type: ignore[attr-defined]

    async def test_failed_health_check_uses_the_bounded_gateway_recovery(self) -> None:
        gateway = OpenClawGateway()
        gateway.prewarm = AsyncMock(side_effect=RuntimeError("stalled"))  # type: ignore[method-assign]
        gateway.recover_after_repeated_first_delta_stall = AsyncMock()  # type: ignore[method-assign]

        outcome = await gateway.self_heal_runtime_stall(
            subsystem="voice_pipeline",
            code="external_playback_gate_stalled",
        )

        self.assertEqual(outcome, "gateway_restarted")
        gateway.recover_after_repeated_first_delta_stall.assert_awaited_once()  # type: ignore[attr-defined]

    async def test_model_progress_stall_replaces_even_a_health_checkable_gateway(self) -> None:
        gateway = OpenClawGateway()
        gateway.prewarm = AsyncMock()  # type: ignore[method-assign]
        gateway.recover_after_repeated_first_delta_stall = AsyncMock()  # type: ignore[method-assign]

        outcome = await gateway.self_heal_runtime_stall(
            subsystem="model_stream",
            code="first_delta_stalled",
        )

        self.assertEqual(outcome, "gateway_restarted")
        gateway.prewarm.assert_not_awaited()  # type: ignore[attr-defined]
        gateway.recover_after_repeated_first_delta_stall.assert_awaited_once()  # type: ignore[attr-defined]


class ProviderFailureClassificationTests(unittest.TestCase):
    def test_permanent_provider_failures_request_reconnection(self) -> None:
        for detail, expected_code in (
            ("HTTP 401 invalid authentication credentials", "AUTH_REJECTED"),
            ("403 forbidden", "AUTH_REJECTED"),
            ("Claude CLI is not logged in", "AUTH_REJECTED"),
            ("404 unknown model gpt-example", "MODEL_UNAVAILABLE"),
        ):
            with self.subTest(detail=detail):
                failure = openclaw_client.classify_provider_failure(detail)
                self.assertEqual(failure.code, expected_code)
                self.assertTrue(failure.reconnect_required)
                self.assertFalse(failure.retryable)

    def test_transient_provider_failures_do_not_discard_a_good_connection(self) -> None:
        for detail, expected_code in (
            ("429 rate limit exceeded", "RATE_LIMITED"),
            ("503 upstream service unavailable", "PROVIDER_UNAVAILABLE"),
            ("request timed out", "PROVIDER_TIMEOUT"),
            ("TLS certificate connection failure", "ENDPOINT_UNREACHABLE"),
        ):
            with self.subTest(detail=detail):
                failure = openclaw_client.classify_provider_failure(detail)
                self.assertEqual(failure.code, expected_code)
                self.assertFalse(failure.reconnect_required)
                self.assertTrue(failure.retryable)

    def test_unknown_errors_are_sanitized_and_not_misreported_as_auth(self) -> None:
        failure = openclaw_client.classify_provider_failure(
            "provider emitted an unfamiliar internal condition"
        )

        self.assertEqual(failure.code, "PROVIDER_FAILED")
        self.assertFalse(failure.reconnect_required)
        self.assertNotIn("internal condition", failure.message)


class GatewayToolRPCContractTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.gateway = OpenClawGateway()
        self.gateway.port = 18789
        self.gateway.ensure_ready = AsyncMock()  # type: ignore[method-assign]
        self.gateway._token = Mock(return_value="a" * 64)  # type: ignore[method-assign]
        self.gateway.gateway_rpc.start = AsyncMock()  # type: ignore[method-assign]

    async def test_agent_board_parent_is_created_idempotently_before_visible_spawn(self) -> None:
        self.gateway.gateway_rpc.request = AsyncMock(return_value={
            "key": "agent:main:openresponses:desktop-owner",
            "sessionId": "session-parent",
        })  # type: ignore[method-assign]

        result = await self.gateway.ensure_session(
            session_key="desktop-owner", label="MERRICK Agent Board"
        )

        self.assertEqual(result["sessionId"], "session-parent")
        self.gateway.gateway_rpc.start.assert_awaited_once_with(  # type: ignore[attr-defined]
            url="ws://127.0.0.1:18789", token="a" * 64
        )
        self.gateway.gateway_rpc.request.assert_awaited_once_with(  # type: ignore[attr-defined]
            "sessions.create",
            {
                "key": "agent:main:openresponses:desktop-owner",
                "agentId": "main",
                "label": "MERRICK Agent Board",
            },
            timeout=15.0,
        )

    async def test_session_tools_use_the_same_canonical_owner_key_as_streaming(self) -> None:
        self.gateway.gateway_rpc.request = AsyncMock(return_value={
            "ok": True,
            "output": {
                "content": [{"type": "text", "text": "accepted"}],
                "details": {"status": "accepted", "runId": "run-1"},
            },
        })  # type: ignore[method-assign]

        result = await self.gateway.invoke_rpc_tool(
            "sessions_spawn",
            {"task": "Research option A", "collect": True, "groupId": "plan-1"},
            session_key="desktop-owner",
        )

        self.assertEqual(result, {"status": "accepted", "runId": "run-1"})
        method, params = self.gateway.gateway_rpc.request.await_args.args  # type: ignore[attr-defined]
        self.assertEqual(method, "tools.invoke")
        self.assertEqual(params["sessionKey"], "agent:main:openresponses:desktop-owner")
        self.assertEqual(params["name"], "sessions_spawn")

    async def test_text_json_is_used_when_gateway_details_are_absent(self) -> None:
        self.gateway.gateway_rpc.request = AsyncMock(return_value={
            "ok": True,
            "output": {
                "content": [{
                    "type": "text",
                    "text": '{"completed":[{"runId":"run-1","status":"done"}],"pending":[]}',
                }],
            },
        })  # type: ignore[method-assign]

        result = await self.gateway.invoke_rpc_tool(
            "agents_wait", {"ids": ["run-1"]}, session_key="desktop-owner",
        )

        self.assertEqual(result["completed"][0]["status"], "done")

    async def test_task_ledger_list_and_cancel_use_gateway_rpc(self) -> None:
        self.gateway.gateway_rpc.request = AsyncMock(side_effect=[
            {"tasks": [{"id": "task-1", "runId": "run-1"}]},
            {"ok": True, "taskId": "task-1"},
        ])  # type: ignore[method-assign]

        tasks = await self.gateway.list_tasks(
            session_key="desktop-owner", statuses=["queued", "running"]
        )
        cancelled = await self.gateway.cancel_task("task-1")

        self.assertEqual(tasks[0]["runId"], "run-1")
        self.assertEqual(cancelled["taskId"], "task-1")
        first_call = self.gateway.gateway_rpc.request.await_args_list[0]  # type: ignore[attr-defined]
        self.assertEqual(first_call.args[0], "tasks.list")
        self.assertEqual(first_call.args[1]["sessionKey"], "agent:main:openresponses:desktop-owner")
        self.assertEqual(first_call.args[1]["status"], ["queued", "running"])
        self.assertNotIn("statuses", first_call.args[1])


if __name__ == "__main__":
    unittest.main()
