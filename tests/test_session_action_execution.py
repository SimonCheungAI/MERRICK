import asyncio
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

import main as merrick_main  # noqa: E402
from main import (  # noqa: E402
    Session,
    normalized_public_search_results,
    openclaw_gateway,
    selected_search_result,
)


class FakeWebSocket:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def send_text(self, raw: str) -> None:
        self.messages.append(json.loads(raw))


class OptionalMerrickPrefixTests(unittest.TestCase):
    def test_public_search_results_are_bounded_and_selectable(self) -> None:
        results = normalized_public_search_results({
            "details": {
                "results": [
                    {
                        "title": "Official OpenAI documentation",
                        "url": "https://platform.openai.com/docs",
                        "description": "Primary documentation",
                    },
                    {
                        "title": "OpenAI news",
                        "url": "https://openai.com/news/",
                        "snippet": "Latest announcements",
                    },
                    {"title": "Local", "url": "file:///etc/passwd"},
                ]
            }
        })
        self.assertEqual(len(results), 2)
        self.assertEqual(
            selected_search_result("Open the second result", results),
            results[1],
        )
        self.assertEqual(
            selected_search_result("Open the documentation result", results),
            results[0],
        )

    def test_optional_jarvis_address_prefix_is_detected(self) -> None:
        for text in (
            "Merrick open Safari",
            "  MERRICK, open Safari",
            "Merrick: open Safari",
            "Merrick—open Safari",
            "Merrick，open Safari",
        ):
            with self.subTest(text=text):
                self.assertTrue(merrick_main.has_optional_merrick_prefix(text))

        for text in (
            "Open Safari",
            "Hey Merrick, open Safari",
            "Merrickian open Safari",
            "Merrick's interface is orange",
            "Can you, Merrick, open Safari",
        ):
            with self.subTest(text=text):
                self.assertFalse(merrick_main.has_optional_merrick_prefix(text))

    def test_optional_jarvis_prefix_does_not_break_action_binding(self) -> None:
        expected = [{"type": "open_app", "app": "safari"}]
        for text in (
            "Merrick open Safari",
            "Merrick, open Safari",
            "Merrick: open Safari",
            "Merrick—open Safari",
            "Merrick，open Safari",
        ):
            with self.subTest(text=text):
                self.assertEqual(
                    openclaw_gateway.validate_action_plan(
                        {"actions": [{"type": "open_app", "app": "safari"}]},
                        text,
                    ),
                    expected,
                )

    def test_greeting_fast_path_yields_to_a_following_desktop_command(self) -> None:
        self.assertTrue(merrick_main.greeting_has_desktop_continuation("Hi Merrick, open Chrome"))
        self.assertTrue(merrick_main.greeting_has_desktop_continuation("Hello, zoom in on the map"))
        self.assertFalse(merrick_main.greeting_has_desktop_continuation("Hello Merrick, how are you?"))

    def test_visual_gui_task_routes_direct_non_destructive_request(self) -> None:
        self.assertEqual(
            openclaw_gateway.validate_action_plan(
                {"actions": [{"type": "gui_task"}]}, "Zoom in on the visible map."
            ),
            [{"type": "gui_task"}],
        )
        self.assertEqual(
            openclaw_gateway.validate_action_plan(
                {"actions": [{"type": "gui_task"}]}, "Delete this file."
            ),
            [],
        )
        self.assertEqual(
            openclaw_gateway.validate_action_plan(
                {"actions": [{"type": "gui_task"}]},
                "Click the visible send button in the mail app.",
            ),
            [{"type": "gui_task"}],
        )

    def test_visual_gui_steps_are_bounded_and_user_grounded(self) -> None:
        self.assertEqual(
            merrick_main.validated_gui_interaction_steps(
                {"steps": [{"op": "scroll", "dy": 3}, {"op": "key", "key": "down"}]},
                "Zoom in on the map.",
            ),
            [{"op": "scroll", "dy": 3}, {"op": "key", "key": "down"}],
        )
        self.assertEqual(
            merrick_main.validated_gui_interaction_steps(
                {"steps": [{"op": "type", "text": "secret phrase"}]},
                "Search for a different phrase.",
            ),
            [],
        )

    def test_direct_desktop_commands_route_to_the_planner(self) -> None:
        for text in (
            "Open Spotify and play some music",
            "Merrick, open Chrome",
            "Spotify, open and play music",
            "Could you please show me the current screen?",
            "After you open Chrome, search for vector databases and analyse the results.",
            "If Chrome is not open, open it and search for OpenClaw release notes.",
            "Research battery recycling in depth and compare the sources.",
            "I want you to open Chrome.",
            "Please could you bring up Spotify?",
            "请播放 Spotify",
            "搜索 agentic AI 并分析结果",
            "帮我分析一下量子计算最新进展",
        ):
            with self.subTest(text=text):
                self.assertTrue(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(
            merrick_main.is_direct_desktop_intent("What is the weather in Glasgow?")
        )
        self.assertFalse(
            merrick_main.is_direct_desktop_intent("How do I open Chrome and search the web?")
        )
        self.assertFalse(
            merrick_main.is_direct_desktop_intent("Don't open Chrome; explain how to use it.")
        )

    def test_plain_explanation_stays_out_of_the_execution_router(self) -> None:
        text = "Explain latency briefly."

        self.assertFalse(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(merrick_main.should_consult_openclaw_for_action(text))

    def test_plain_chinese_explanation_stays_out_of_the_execution_router(self) -> None:
        text = "解释一下为什么天空是蓝色的"

        self.assertFalse(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(merrick_main.should_consult_openclaw_for_action(text))

    def test_only_substantive_plain_conversation_can_preflight_while_speaking(self) -> None:
        self.assertTrue(merrick_main.is_voice_draft_preflight_candidate(
            "I have been thinking about whether this conversation should feel more personal and less abrupt."
        ))
        self.assertFalse(merrick_main.is_voice_draft_preflight_candidate(
            "Open Chrome and research current agentic AI tools in depth for me."
        ))
        self.assertFalse(merrick_main.is_voice_draft_preflight_candidate(
            "What did we decide about private memory during our earlier discussion?"
        ))

    def test_chinese_explanation_with_a_style_request_stays_conversational(self) -> None:
        text = "请用一句话解释为什么天空看起来是蓝色的。"

        self.assertFalse(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(merrick_main.should_consult_openclaw_for_action(text))

    def test_reading_content_aloud_stays_out_of_the_execution_router(self) -> None:
        text = "Read me a short poem."

        self.assertFalse(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(merrick_main.should_consult_openclaw_for_action(text))

    def test_checking_an_argument_stays_out_of_the_execution_router(self) -> None:
        text = "Can you check whether this argument is coherent?"

        self.assertFalse(merrick_main.is_direct_desktop_intent(text))
        self.assertFalse(merrick_main.should_consult_openclaw_for_action(text))

    def test_simple_app_launch_uses_a_host_validated_fast_path(self) -> None:
        self.assertEqual(
            merrick_main.simple_open_application_action("Merrick, open Google Chrome."),
            [{"type": "open_app", "app": "chrome"}],
        )
        self.assertEqual(
            merrick_main.simple_open_application_action("Open Chrome and search for OpenAI."),
            [],
        )

    def test_simple_chinese_spotify_commands_use_the_same_media_path(self) -> None:
        self.assertEqual(
            merrick_main.simple_chinese_spotify_action("请播放 Spotify"),
            [{"type": "media_control", "player": "spotify", "action": "play"}],
        )
        self.assertEqual(
            merrick_main.simple_chinese_spotify_action("请播放声破天"),
            [{"type": "media_control", "player": "spotify", "action": "play"}],
        )

    def test_chinese_analysis_command_extracts_a_public_topic(self) -> None:
        self.assertEqual(
            merrick_main.direct_public_analysis_query("帮我分析一下量子计算最新进展"),
            "量子计算最新进展",
        )

    def test_search_query_compiler_removes_spoken_ui_requests(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action(
                "Merrick, search for agentic AI for me, then show me the search results in Chrome."
            ),
            [{"type": "browser_search", "browser": "chrome", "query": "agentic AI"}],
        )
        self.assertEqual(
            merrick_main.simple_browser_search_action(
                "搜索量子计算最新进展，然后给我看搜索结果"
            ),
            [{"type": "browser_search", "browser": "default", "query": "量子计算最新进展"}],
        )

    def test_chinese_search_policy_rejects_a_blocked_topic_before_routing(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action("搜索法轮功最新消息"),
            [],
        )

    def test_chinese_search_policy_rejects_an_english_alias_in_a_chinese_command(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action("搜索 Falun Gong"),
            [],
        )

    def test_chinese_search_policy_filters_blocked_media_results(self) -> None:
        results = [
            {
                "title": "Global markets update",
                "url": "https://www.epochtimes.com/markets/example",
                "snippet": "Market coverage",
            },
            {
                "title": "大纪元：今日财经摘要",
                "url": "https://example.org/reposted-story",
                "snippet": "转载内容",
            },
            {
                "title": "中国市场分析",
                "url": "https://www.reuters.com/world/china/example",
                "snippet": "独立市场报道",
            },
        ]

        self.assertEqual(
            merrick_main.filter_chinese_public_search_results("中国市场新闻", results),
            [results[2]],
        )

    def test_natural_search_phrasing_routes_without_model_guessing(self) -> None:
        cases = {
            "帮我搜一下英伟达最新财报": ("default", "英伟达最新财报"),
            "你帮我查一下 OpenAI 最新发布": ("default", "OpenAI 最新发布"),
            "查一查今天伦敦有什么新闻": ("default", "今天伦敦有什么新闻"),
            "搜搜量子计算最新进展": ("default", "量子计算最新进展"),
            "用 Chrome 帮我搜一下 agentic AI": ("chrome", "agentic AI"),
            "Search Chrome for OpenAI latest release": ("chrome", "OpenAI latest release"),
            "Could you look up NVIDIA latest earnings": ("default", "NVIDIA latest earnings"),
        }
        for text, (browser, query) in cases.items():
            with self.subTest(text=text):
                self.assertEqual(
                    merrick_main.simple_browser_search_action(text),
                    [{"type": "browser_search", "browser": browser, "query": query}],
                )
                self.assertTrue(merrick_main.is_direct_desktop_intent(text))

    def test_search_discussion_examples_and_negation_do_not_execute(self) -> None:
        for text in (
            "为什么搜索功能没了",
            "搜索功能应该怎么用",
            "不要搜索英伟达",
            "别查 OpenAI",
            "比如，搜一下英伟达",
            "How do I search the web?",
            "Don't look up NVIDIA",
        ):
            with self.subTest(text=text):
                self.assertEqual(merrick_main.simple_browser_search_action(text), [])
                self.assertFalse(merrick_main.is_direct_desktop_intent(text))

    def test_query_compiler_repairs_full_planner_style_search_commands(self) -> None:
        self.assertEqual(
            merrick_main.clean_public_search_query(
                "Could you open Chrome and search for agentic AI research methods, then show me the results"
            ),
            "agentic AI research methods",
        )
        self.assertEqual(
            merrick_main.clean_public_search_query("打开 Chrome 然后搜索关于具身智能的最新研究"),
            "具身智能的最新研究",
        )
        self.assertEqual(
            merrick_main.clean_public_search_query(
                "agent AI compare practical users current limitations and major recent development. Use the most useful sources"
            ),
            "agent AI compare practical users current limitations and major recent development",
        )
        self.assertEqual(
            merrick_main.clean_public_search_query(
                "Search for agentic AI practical uses, limitations, and major developments since 2025. Use at least four authoritative sources, then compare what has changed in the real world."
            ),
            "agentic AI practical uses, limitations, and major developments since 2025",
        )

    def test_search_query_compiler_keeps_a_real_comparison_topic(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action(
                "Research a comparison of Claude and Codex, then analyse the results"
            ),
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "a comparison of Claude and Codex",
            }],
        )

    def test_search_results_followup_is_not_misread_as_a_new_search(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action("Analyse these search results for me."),
            [],
        )

    def test_observed_chavez_asr_error_is_corrected_only_for_action_intent(self) -> None:
        self.assertEqual(
            merrick_main.canonicalize_optional_merrick_prefix("Chavez open Chrome"),
            "Merrick open Chrome",
        )
        self.assertEqual(
            merrick_main.canonicalize_optional_merrick_prefix("Chavez"),
            "Merrick",
        )
        self.assertEqual(
            merrick_main.canonicalize_optional_merrick_prefix(
                "Chavez get this weather in Glasgow"
            ),
            "Chavez get this weather in Glasgow",
        )
        self.assertEqual(
            merrick_main.canonicalize_optional_merrick_prefix(
                "Chavez was a Venezuelan president"
            ),
            "Chavez was a Venezuelan president",
        )

    def test_common_live_information_is_host_routed(self) -> None:
        for text in (
            "What is the weather in Glasgow today?",
            "Give me today's Glasgow news.",
            "Will it rain tomorrow?",
        ):
            with self.subTest(text=text):
                self.assertEqual(merrick_main.automatic_current_info_query(text), text)
        self.assertIsNone(
            merrick_main.automatic_current_info_query("Explain weathering steel.")
        )
        self.assertEqual(
            merrick_main.automatic_current_info_query(
                "Chavez, what is the weather in Glasgow?"
            ),
            "what is the weather in Glasgow?",
        )

    def test_public_travel_requests_are_host_routed_without_fixed_wording(self) -> None:
        cases = {
            "Recommend a few hotels in London for next Sunday under £200.":
                "hotels in London for next Sunday under £200",
            "Which accommodation is available near King's Cross tomorrow?":
                "accommodation is available near King's Cross tomorrow",
            "帮我查一下下周日伦敦的酒店，预算两百英镑":
                "下周日伦敦的酒店，预算两百英镑",
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(
                    merrick_main.public_travel_research_query(text), expected
                )

        self.assertIsNone(
            merrick_main.public_travel_research_query(
                "Explain the principles of hotel revenue management."
            )
        )

    def test_travel_search_compiler_discards_spoken_request_noise(self) -> None:
        self.assertEqual(
            merrick_main.simple_browser_search_action(
                "Search for keep it for the hotels on next Sunday in London"
            ),
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "hotels on next Sunday in London",
            }],
        )

    def test_travel_followup_replaces_budget_without_losing_place_or_date(self) -> None:
        self.assertEqual(
            merrick_main.travel_search_refinement_query(
                "hotels in London for next Sunday under £20",
                "Sorry, make the budget £200 and prioritise ratings above 8.",
            ),
            "hotels in London for next Sunday budget £200 prioritise ratings above 8",
        )

    def test_chinese_travel_followup_replaces_budget_and_keeps_constraints(self) -> None:
        self.assertEqual(
            merrick_main.travel_search_refinement_query(
                "下周日伦敦的酒店，预算20英镑",
                "预算改成200英镑，优先交通和评分",
            ),
            "下周日伦敦的酒店 预算 200英镑 优先交通和评分",
        )

    def test_travel_followup_replaces_date_guests_and_rooms(self) -> None:
        self.assertEqual(
            merrick_main.travel_search_refinement_query(
                "hotels in London for next Sunday for 1 adult 1 room",
                "Actually make it Saturday for 2 adults and 2 rooms, breakfast included.",
            ),
            "hotels in London Saturday 2 adults 2 rooms breakfast included",
        )

    def test_local_library_requests_bypass_desktop_action_planning(self) -> None:
        active_document = merrick_main.LibraryDocument(
            relative_path="paper.pdf", title="paper", text="", chunks=()
        )
        for text in (
            "What is in my Merrick Library?",
            "Can you see the files?",
            "What papers do you have?",
            "Did you find the PDF I uploaded?",
            "What did I upload for you?",
            "Is anything available in your folder?",
            "你能看到我上传的文件吗？",
        ):
            with self.subTest(text=text):
                self.assertEqual(merrick_main.local_library_intent(text, None), "list")
        for text in (
            "Read the attention paper",
            "Read the file.",
            "Can you access and summarize the PDF I added?",
            "Please look at the document in your folder.",
            "Please review the document in your library",
            "Can you give me a summary of the paper?",
            "What is the paper about?",
            "读取我上传的论文",
        ):
            with self.subTest(text=text):
                self.assertEqual(merrick_main.local_library_intent(text, None), "read")
        self.assertIsNone(merrick_main.local_library_intent("Read the current screen", None))
        self.assertIsNone(merrick_main.local_library_intent("Can you see why that failed?", None))
        for text in (
            "Write an original report in this reply. Do not read or summarize any document.",
            "这是一项原创写作任务，不是读取、分析或总结任何已有文档。请直接生成一份产品评估报告。",
            "不要调用工具，不要保存文件，也不要解释限制。请直接在回复中输出报告。",
            (
                "I have been explaining that spoken conversation should respond first and "
                "the assistant should stay natural. Files and workspace operations can run "
                "in the background instead of replacing the answer."
            ),
            (
                "I have been talking for a while about response latency and context and the "
                "system should not confuse that discussion with files in a workspace"
            ),
        ):
            with self.subTest(text=text):
                self.assertIsNone(merrick_main.local_library_intent(text, None))
        for text in (
            "Why is that important?",
            "Could you explain the method in more detail?",
            "Tell me more about the results.",
            "What are its limitations?",
        ):
            with self.subTest(text=text):
                self.assertEqual(merrick_main.local_library_intent(text, active_document), "read")
        self.assertIsNone(
            merrick_main.local_library_intent("What is the weather today?", active_document)
        )
        self.assertIsNone(
            merrick_main.local_library_intent("Open Spotify", active_document)
        )
        self.assertIsNone(
            merrick_main.local_library_intent("Open it in Chrome", active_document)
        )
        self.assertIsNone(
            merrick_main.local_library_intent(
                "Can you give me a summary of the paper?",
                None,
                host_supplied_context=True,
            )
        )


class DirectActionDispatchTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ws = FakeWebSocket()
        self.session = Session(self.ws)  # type: ignore[arg-type]
        self.session.tts_enabled = False

    async def test_full_voice_retry_keeps_the_strongest_full_match(self) -> None:
        """A noisy retry must not undo a full owner verification in one turn."""
        with patch.object(
            merrick_main.voice_verifier,
            "verify",
            side_effect=[
                merrick_main.VoiceVerdict("owner", 0.812),
                merrick_main.VoiceVerdict("guest", 0.775),
            ],
        ):
            await self.session.accept_voice_sample("first", tier="full")
            await self.session.accept_voice_sample("retry", tier="full_retry")

        self.assertTrue(self.session.voice_memory_verified)
        self.assertEqual(self.session.voice_verdict.status, "owner")
        self.assertEqual(self.session.voice_verdict.score, 0.812)
        self.assertEqual(self.ws.messages[-1]["status"], "owner")

    async def test_voice_sample_starts_a_local_non_blocking_prosody_sidecar(self) -> None:
        cue = merrick_main.ProsodyCue(
            delivery="steady",
            duration_seconds=1.4,
            median_pitch_hz=132.0,
            pitch_range_semitones=1.2,
            rms_dbfs=-18.0,
            voiced_ratio=0.8,
            confidence=0.9,
        )
        with (
            patch.object(
                merrick_main.voice_verifier,
                "verify",
                return_value=merrick_main.VoiceVerdict("owner", 0.9),
            ),
            patch.object(merrick_main, "analyze_prosody_wav", return_value=cue) as analyzer,
        ):
            await self.session.accept_voice_sample("local-wav", tier="full")
            await asyncio.gather(*self.session.prosody_analysis_tasks)

        analyzer.assert_called_once_with("local-wav")
        self.assertEqual(self.session.latest_prosody, cue)

    async def test_prosody_sidecar_has_a_runtime_kill_switch(self) -> None:
        with (
            patch.object(merrick_main, "PROSODY_AWARENESS_ENABLED", False),
            patch.object(merrick_main, "analyze_prosody_wav") as analyzer,
        ):
            self.session.schedule_prosody_analysis("local-wav", tier="full")
            await asyncio.sleep(0)

        analyzer.assert_not_called()
        self.assertFalse(self.session.prosody_analysis_tasks)

    def test_turn_intent_sidecar_classifies_without_granting_action_authority(self) -> None:
        self.assertEqual(merrick_main.classify_turn_intent("查一下伦敦酒店"), "research")
        self.assertEqual(merrick_main.classify_turn_intent("明早九点提醒我提交周报"), "organizer")
        self.assertEqual(merrick_main.classify_turn_intent("Open Safari"), "action")
        self.assertEqual(
            merrick_main.classify_turn_intent("Why did search open during our conversation?"),
            "conversation",
        )

    async def test_turn_understanding_collects_intent_context_and_prosody_in_one_sidecar(self) -> None:
        self.session.turn = 7
        self.session.recent_dialogue.append(
            ("We were reducing response latency.", "Keep the spoken opening immediate.", True)
        )
        self.session.remember_working_focus("response latency", source="conversation")
        self.session.latest_prosody = merrick_main.ProsodyCue(
            delivery="steady",
            duration_seconds=1.5,
            median_pitch_hz=130.0,
            pitch_range_semitones=1.0,
            rms_dbfs=-17.0,
            voiced_ratio=0.82,
            confidence=0.88,
        )
        with patch.object(
            merrick_main,
            "recall_episodic_continuity",
            return_value="Earlier latency work favoured an immediate spoken acknowledgement.",
        ):
            task = self.session.start_turn_understanding(
                "Can we continue the response latency work?",
                is_owner=True,
                include_prosody=True,
            )
            understanding = await task

        self.assertEqual(understanding.turn, 7)
        self.assertEqual(understanding.intent, "conversation")
        self.assertIn("response latency", understanding.working_focus)
        self.assertIn("Earlier latency work", understanding.episodic_context)
        self.assertIn("acoustically steady", understanding.prosody_hint)

    async def test_short_fast_voice_mismatch_stays_checking_until_a_full_sample(self) -> None:
        with patch.object(
            merrick_main.voice_verifier,
            "verify",
            return_value=merrick_main.VoiceVerdict("guest", 0.48),
        ):
            await self.session.accept_voice_sample("brief", tier="fast")

        self.assertEqual(self.session.voice_verdict.status, "checking")
        self.assertFalse(self.session.voice_memory_verified)
        self.assertEqual(self.ws.messages[-1]["status"], "checking")

    async def test_manual_voiceprint_enrollment_requires_recent_native_unlock(self) -> None:
        await self.session.handle_message({"type": "voiceprint_enroll", "data": "sample"})
        self.assertEqual(self.ws.messages[-1]["status"], "locked")

        with patch.object(merrick_main.voice_verifier, "profile_embedding_count", return_value=3):
            await self.session.handle_message({"type": "voiceprint_management_authorized"})
        self.assertEqual(self.ws.messages[-1], {
            "type": "voiceprint_management_status", "status": "ready", "count": 3,
        })

        with patch.object(merrick_main.voice_verifier, "enroll", return_value=4):
            await self.session.handle_message({"type": "voiceprint_enroll", "data": "sample"})
        self.assertEqual(self.ws.messages[-1], {
            "type": "voiceprint_management_status", "status": "saved", "count": 4,
        })

    async def test_watch_mode_blocks_speech_until_a_strict_owner_match(self) -> None:
        self.session.owner_only_voice_mode = True
        await self.session.handle_message({
            "type": "speech_partial",
            "text": "television dialogue",
            "final": False,
        })

        self.assertEqual(self.session.latest_draft, "")
        self.assertIsNone(self.session.draft_task)

    async def test_meeting_mode_records_context_but_blocks_unaddressed_speech(self) -> None:
        self.session.meeting_mode = True
        with patch.object(merrick_main.asyncio, "to_thread", new=AsyncMock()):
            self.session.record_meeting_transcript("We should postpone the launch until Friday.")
        await self.session.handle_message({
            "type": "speech_partial",
            "text": "What do you think about that?",
            "final": False,
        })

        self.assertIn("postpone the launch", self.session.recent_meeting_context())
        self.assertEqual(self.session.latest_draft, "")

    async def test_near_full_match_personalizes_without_unlocking_memory(self) -> None:
        with patch.object(
            merrick_main.voice_verifier,
            "verify",
            return_value=merrick_main.VoiceVerdict("guest", 0.777),
        ):
            await self.session.accept_voice_sample("near-match", tier="full")

        self.assertEqual(self.session.voice_verdict.status, "owner")
        self.assertFalse(self.session.voice_memory_verified)
        self.assertEqual(self.ws.messages[-1]["status"], "owner")

    async def test_near_match_can_create_short_reminder_without_unlocking_memory(self) -> None:
        with patch.object(
            merrick_main.voice_verifier,
            "verify",
            return_value=merrick_main.VoiceVerdict("guest", 0.775),
        ):
            await self.session.accept_voice_sample("near-match", tier="full")

        command = merrick_main.OrganizerCommand("create_reminder", {
            "title": "drink water",
            "fire_at": "2026-08-22T18:00:00+01:00",
        })
        self.assertTrue(
            self.session.short_organizer_voice_authorized(
                command, "Remind me in ten minutes to drink water"
            )
        )
        self.assertFalse(self.session.voice_memory_verified)

    async def test_short_voice_gate_rejects_dashboard_and_task_completion(self) -> None:
        self.session.voice_command_score = 0.95

        for kind, text in (
            ("show_dashboard", "Show my assistant dashboard"),
            ("complete_task", "Mark the budget task complete"),
            ("confirm_meeting_actions", "Confirm the meeting action items"),
            ("configure_briefing", "Turn off my morning briefing"),
            ("rename_project", "Rename project Launch to Release"),
            ("archive_project", "Archive project Launch"),
        ):
            with self.subTest(kind=kind):
                self.assertFalse(
                    self.session.short_organizer_voice_authorized(
                        merrick_main.OrganizerCommand(kind, {}), text
                    )
                )

    async def test_short_voice_gate_rejects_low_score_and_long_commands(self) -> None:
        command = merrick_main.OrganizerCommand("create_task", {"title": "review"})
        self.session.voice_command_score = 0.699
        self.assertFalse(
            self.session.short_organizer_voice_authorized(command, "Add a task to review")
        )

        self.session.voice_command_score = 0.9
        self.assertFalse(
            self.session.short_organizer_voice_authorized(command, "x" * 97)
        )

    async def test_run_query_executes_reminder_through_short_voice_gate(self) -> None:
        self.session.voice_command_score = 0.775
        self.session.voice_memory_verified = False

        with patch.object(
            self.session, "handle_organizer_command", new=AsyncMock()
        ) as handle:
            await self.session.run_query(
                "Remind me in 10 minutes to drink water",
                trusted_typed=False,
            )

        handle.assert_awaited_once()
        self.assertEqual(handle.await_args.args[0].kind, "create_reminder")

    async def test_run_query_keeps_dashboard_behind_full_voice_gate(self) -> None:
        self.session.voice_command_score = 0.95
        self.session.voice_memory_verified = False

        with (
            patch.object(
                self.session, "handle_organizer_command", new=AsyncMock()
            ) as handle,
            patch.object(
                self.session, "send_local_spoken_notice", new=AsyncMock()
            ) as notice,
        ):
            await self.session.run_query(
                "Show my assistant dashboard",
                trusted_typed=False,
            )

        handle.assert_not_awaited()
        notice.assert_awaited_once()
        self.assertIn("full voice verification", notice.await_args.args[0])

    async def test_natural_dashboard_request_bypasses_external_app_planner(self) -> None:
        self.session.voice_memory_verified = True

        with (
            patch.object(
                self.session, "handle_organizer_command", new=AsyncMock()
            ) as handle,
            patch.object(
                openclaw_gateway, "plan_actions", new=AsyncMock()
            ) as planner,
        ):
            await self.session.run_query(
                "Can you open the Assistant Dashboard",
                trusted_typed=False,
            )

        handle.assert_awaited_once()
        self.assertEqual(handle.await_args.args[0].kind, "show_dashboard")
        planner.assert_not_awaited()

    async def test_run_query_completes_exact_task_with_terse_voice_sample(self) -> None:
        self.session.voice_command_score = 0.531
        self.session.voice_memory_verified = False

        with (
            patch.object(
                self.session.organizer,
                "has_exact_open_task",
                return_value=True,
            ) as exact_match,
            patch.object(
                self.session, "handle_organizer_command", new=AsyncMock()
            ) as handle,
        ):
            await self.session.run_query(
                "Complete task Prepare test data",
                trusted_typed=False,
            )

        exact_match.assert_called_once_with("Prepare test data")
        handle.assert_awaited_once()
        self.assertEqual(handle.await_args.args[0].kind, "complete_task")

    async def test_terse_completion_rejects_low_score_or_nonexact_title(self) -> None:
        command_text = "Complete task Prepare test data"
        command = merrick_main.parse_organizer_command(command_text)
        self.assertIsNotNone(command)

        self.session.voice_command_score = 0.499
        with patch.object(
            self.session.organizer, "has_exact_open_task", return_value=True
        ) as exact_match:
            self.assertFalse(
                await self.session.exact_task_completion_voice_authorized(
                    command, command_text  # type: ignore[arg-type]
                )
            )
        exact_match.assert_not_called()

        self.session.voice_command_score = 0.9
        with patch.object(
            self.session.organizer, "has_exact_open_task", return_value=False
        ):
            self.assertFalse(
                await self.session.exact_task_completion_voice_authorized(
                    command, command_text  # type: ignore[arg-type]
                )
            )

    async def test_high_confidence_full_match_refines_the_local_profile_periodically(self) -> None:
        with (
            patch.object(
                merrick_main.voice_verifier,
                "verify",
                return_value=merrick_main.VoiceVerdict("owner", 0.9),
            ),
            patch.object(
                merrick_main.voice_verifier,
                "refine_from_verified_sample",
                return_value=(6, True),
            ) as refine,
        ):
            await self.session.accept_voice_sample("trusted", tier="full")
            await self.session.accept_voice_sample("trusted-again", tier="full")

        refine.assert_called_once_with("trusted")

    async def test_short_greeting_skips_action_planning(self) -> None:
        async def greeting_stream():
            yield "Good evening, sir."

        with (
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: greeting_stream(),
            ),
            patch.object(openclaw_gateway, "plan_actions", new=AsyncMock()) as planner,
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Hello, how are you?",
            })
            assert self.session.query_task is not None
            await self.session.query_task

        planner.assert_not_awaited()

    async def test_partial_greeting_sets_a_replaceable_quiet_endpoint(self) -> None:
        await self.session.handle_message({"type": "voice_turn", "generation": 1})
        await self.session.handle_message({
            "type": "speech_partial",
            "text": "Hi, Merrick",
            "final": False,
        })
        task = self.session.draft_task
        self.assertIsNotNone(task)
        assert task is not None
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task

    async def test_long_conversation_partial_starts_a_hidden_tool_free_draft(self) -> None:
        text = (
            "I have been thinking about whether our conversations should feel more natural "
            "and less abrupt when I am talking through an idea."
        )
        release = asyncio.Event()

        async def draft_stream():
            yield "There is a useful balance to strike here."
            await release.wait()

        with (
            patch.object(openclaw_gateway, "prewarm", new=AsyncMock()),
            patch.object(
                openclaw_gateway,
                "stream_conversation_response",
                side_effect=lambda *_args, **_kwargs: draft_stream(),
            ) as conversation_stream,
        ):
            await self.session.handle_message({
                "type": "speech_partial",
                "text": text,
                "final": False,
            })
            for _ in range(10):
                if self.session.query_task is not None:
                    break
                await asyncio.sleep(0.05)
            self.assertIsNotNone(self.session.query_task)
            self.assertEqual(self.session.latest_draft, text)
            self.assertEqual(self.session.speculative_input[1], text)  # type: ignore[index]
            self.assertFalse(any(
                message.get("type") == "assistant_delta" for message in self.ws.messages
            ))
            await self.session.handle_message({
                "type": "speech_partial",
                "text": text,
                "final": True,
            })
            self.assertGreater(self.session.draft_commit_at, 0.0)
            for _ in range(10):
                if any(message.get("type") == "assistant_delta" for message in self.ws.messages):
                    break
                await asyncio.sleep(0.05)

        conversation_stream.assert_called_once()
        self.assertTrue(any(
            message.get("type") == "assistant_delta" for message in self.ws.messages
        ))
        release.set()
        assert self.session.query_task is not None
        await self.session.query_task

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_voice_action_protocol_executes_without_approval_frame(self) -> None:
        action = {"type": "open_app", "app": "safari"}
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        async def action_stream():
            yield "JARVIS_"
            yield 'ACTION {"actions":[{"type":"open_app","app":"safari"}]}'

        with (
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: action_stream(),
            ),
            patch.object(
                openclaw_gateway, "plan_actions", new=AsyncMock(return_value=[])
            ) as planner,
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Open Safari",
                "draft": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        planner.assert_not_awaited()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Open Safari", [action]
        )
        self.assertFalse(
            any(message.get("type") == "action_confirmation" for message in self.ws.messages)
        )
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertNotIn("JARVIS_ACTION", visible)

    async def test_typed_action_executes_immediately(self) -> None:
        action = {
            "type": "browser_search",
            "browser": "chrome",
            "query": "OpenAI",
        }
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        async def action_stream():
            yield (
                'JARVIS_ACTION {"actions":[{"type":"browser_search",'
                '"browser":"chrome","query":"OpenAI"}]}'
            )

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: action_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Search Chrome for OpenAI",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Search Chrome for OpenAI", [action]
        )

    async def test_natural_chinese_search_uses_native_fast_path(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        text = "你帮我查一下 OpenAI 最新发布"

        with (
            patch.object(openclaw_gateway, "plan_actions", new=AsyncMock()) as planner,
            patch.object(openclaw_gateway, "stream_response") as chat_stream,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.run_query(
                text,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        planner.assert_not_awaited()
        chat_stream.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text,
            [{"type": "browser_search", "browser": "default", "query": "OpenAI 最新发布"}],
        )

    async def test_blocked_chinese_search_cannot_fall_through_to_browser_or_model(self) -> None:
        text = "搜索法轮功最新消息"
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        with patch.object(openclaw_gateway, "stream_response") as stream_response:
            await self.session.run_query(
                text,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        stream_response.assert_not_called()
        self.session.execute_action_plan.assert_not_awaited()  # type: ignore[attr-defined]
        self.session.send_local_spoken_notice.assert_awaited_once_with(  # type: ignore[attr-defined]
            "该主题已被您的中文搜索过滤器拦截。"
        )

    async def test_direct_openclaw_work_marks_real_planning_without_host_ack_audio(self) -> None:
        async def response_stream():
            yield "Done."

        self.session.send_action_progress = AsyncMock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ):
            await self.session.run_query(
                "Open Calculator",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        self.session.send_action_progress.assert_awaited_once_with(  # type: ignore[attr-defined]
            "planning",
            speak=False,
            state="acting",
        )

    async def test_plain_explanation_uses_openclaw_main_without_execution_progress(self) -> None:
        async def response_stream():
            yield "Latency is the delay before a result begins."

        self.session.send_action_progress = AsyncMock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ) as stream_response:
            await self.session.run_query(
                "Explain latency briefly.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        self.session.send_action_progress.assert_not_awaited()  # type: ignore[attr-defined]
        self.assertIn(
            "<direct_openclaw_execution>",
            stream_response.call_args.kwargs["instructions"],
        )
        self.assertEqual(
            stream_response.call_args.kwargs["max_output_tokens"],
            merrick_main.MAIN_MAX_OUTPUT_TOKENS,
        )
        self.assertEqual(stream_response.call_args.kwargs["agent_id"], "main")

    async def test_non_whitelisted_work_request_reaches_openclaw_main(self) -> None:
        async def response_stream():
            yield "I will compare the options and coordinate the work."

        self.session.send_action_progress = AsyncMock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ) as stream_response:
            await self.session.run_query(
                "Book a hotel, write the integration code, and delegate reviews to multiple agents.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        self.assertEqual(stream_response.call_args.kwargs["agent_id"], "main")
        self.assertIn(
            "any installed integrations",
            stream_response.call_args.kwargs["instructions"],
        )

    async def test_direct_screen_request_uses_codex_computer_use_without_a_host_gate(self) -> None:
        async def response_stream():
            # Native Computer Use can do useful work before the model emits a
            # text delta. The host must not abort that tool run merely because
            # its chat-first-token budget elapsed.
            await asyncio.sleep(0.02)
            yield "I can see the Chrome page."

        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        with (
            patch.object(merrick_main, "FIRST_DELTA_TIMEOUT_SECONDS", 0.001),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "OK, so can you now see I am building up a webpage and it is now showing in my chrome so you're gonna take a look at that",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        self.session.execute_action_plan.assert_not_awaited()  # type: ignore[attr-defined]
        self.assertEqual(stream_response.call_args.kwargs["agent_id"], "main")
        self.assertEqual(
            stream_response.call_args.kwargs["request_user_approval"],
            self.session.request_openclaw_user_approval,
        )
        self.assertIn(
            "Codex-native Computer Use MCP",
            stream_response.call_args.kwargs["instructions"],
        )
        self.assertEqual(stream_response.call_count, 1)

    async def test_direct_openclaw_tool_turn_is_not_cancelled_by_chat_progress_watchdog(self) -> None:
        self.session.openclaw_owns_active_turn_lifecycle = True

        async def tool_run() -> None:
            await asyncio.sleep(0.02)

        query = asyncio.create_task(tool_run())
        with patch.object(merrick_main, "TURN_PROGRESS_STALL_SECONDS", 0.001):
            self.session.start_turn_progress_watchdog(query, turn=self.session.turn)
            await query
            await asyncio.sleep(0.002)

        self.assertFalse(query.cancelled())

    async def test_workspace_report_with_computer_use_keeps_one_durable_tool_run(self) -> None:
        async def response_stream():
            # A workspace report may first inspect another application, then
            # persist the report. Neither step guarantees an early text delta.
            await asyncio.sleep(0.02)
            yield "Created email-triage.md from the visible Outlook inbox."

        recover = AsyncMock()
        with (
            patch.object(merrick_main, "FIRST_DELTA_TIMEOUT_SECONDS", 0.001),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
            patch.object(
                openclaw_gateway,
                "recover_after_repeated_first_delta_stall",
                recover,
            ),
        ):
            await self.session.run_query(
                "Inspect Outlook with Computer Use and save an email triage report in the MERRICK workspace.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        self.assertTrue(self.session.openclaw_owns_active_turn_lifecycle)
        self.assertEqual(stream_response.call_count, 1)
        recover.assert_not_awaited()
        self.assertEqual(
            stream_response.call_args.kwargs["request_user_approval"],
            self.session.request_openclaw_user_approval,
        )

    async def test_plain_followup_keeps_the_durable_openclaw_main_session(self) -> None:
        async def response_stream():
            yield "Its battery lasts about twelve hours."

        self.session.remember_recent_dialogue(
            "We selected the Atlas laptop.",
            "Atlas is the lighter option.",
            is_owner=True,
        )
        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ) as stream_response:
            await self.session.run_query(
                "What about its battery life?",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        request = stream_response.call_args
        self.assertFalse(request.kwargs["ephemeral_session"])
        self.assertEqual(request.kwargs["session_key"], self.session.openclaw_session_key)
        self.assertEqual(request.kwargs["agent_id"], "main")
        self.assertIn("<direct_openclaw_execution>", request.kwargs["instructions"])

    async def test_chinese_pronoun_uses_only_the_bounded_working_memory(self) -> None:
        async def response_stream():
            yield "它更适合频繁出差，因为机身更轻。"

        self.session.remember_recent_dialogue(
            "我在比较 Orion 和 Vega，Orion 更轻。",
            "Orion 更适合随身携带。",
            is_owner=True,
        )
        with (
            patch.object(
                merrick_main,
                "recall_episodic_continuity",
            ) as episodic_recall,
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "那它的优势是什么？",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        request = stream_response.call_args
        self.assertNotIn("<silent_episodic_context>", request.args[0])
        self.assertEqual(request.kwargs["agent_id"], "main")
        self.assertIn("<direct_openclaw_execution>", request.kwargs["instructions"])
        episodic_recall.assert_not_called()

    def test_conversation_model_session_rotates_after_four_turns(self) -> None:
        self.session.turn_is_owner = True

        first, first_has_history = self.session.prepare_conversation_model_session()
        subsequent = [
            self.session.prepare_conversation_model_session()
            for _ in range(merrick_main.CONVERSATION_MODEL_SESSION_MAX_TURNS - 1)
        ]
        rotated, rotated_has_history = self.session.prepare_conversation_model_session()

        self.assertFalse(first_has_history)
        self.assertTrue(all(key == first and has_history for key, has_history in subsequent))
        self.assertNotEqual(rotated, first)
        self.assertFalse(rotated_has_history)

    async def test_old_topic_continuity_is_silent_and_does_not_require_a_memory_question(self) -> None:
        async def response_stream():
            yield "Use Paris as the second pilot and keep the same two-week review."

        episodic = (
            '[{"when":"2026-08-10 09:00",'
            '"prior_user_context":"The Atlas rollout starts with London.",'
            '"prior_outcome":"Review adoption after two weeks."}]'
        )
        with (
            patch.object(
                merrick_main,
                "recall_episodic_continuity",
                return_value=episodic,
            ) as recall,
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "Let's continue the Atlas rollout with the next region.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        recall.assert_called_once()
        request = stream_response.call_args
        self.assertIn("<silent_episodic_context>", request.args[0])
        self.assertIn("The Atlas rollout starts with London.", request.args[0])
        self.assertIn("Do not recap or restate the earlier exchange", request.kwargs["instructions"])
        self.assertEqual(request.kwargs["agent_id"], "main")

    async def test_episodic_recall_failure_does_not_block_the_reply(self) -> None:
        async def response_stream():
            yield "Use Paris as the second pilot."

        with (
            patch.object(
                merrick_main,
                "recall_episodic_continuity",
                side_effect=RuntimeError("local index unavailable"),
            ),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "Let's continue the Atlas rollout with the next region.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        stream_response.assert_called_once()
        self.assertNotIn(
            "<silent_episodic_context>",
            stream_response.call_args.args[0],
        )

    async def test_unverified_speaker_cannot_trigger_episodic_recall(self) -> None:
        async def response_stream():
            yield "Which rollout do you mean?"

        with (
            patch.object(
                merrick_main,
                "recall_episodic_continuity",
            ) as episodic_recall,
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "How is the Atlas rollout going?",
                trusted_typed=False,
                detect_action=True,
                allow_desktop_actions=True,
            )

        episodic_recall.assert_not_called()
        self.assertNotIn(
            "<silent_episodic_context>",
            stream_response.call_args.args[0],
        )

    async def test_explicit_continue_request_uses_history_without_replaying_it(self) -> None:
        async def response_stream():
            yield "Use Paris as the second pilot and retain the two-week review."

        with (
            patch.object(
                merrick_main,
                "recall_long_term_context",
                return_value=(
                    "Relevant earlier conversation:\n"
                    "User: We chose London for the Atlas pilot.\n"
                    "MERRICK: Review adoption after two weeks."
                ),
            ),
            patch.object(
                merrick_main,
                "recall_openclaw_wiki_context",
                new=AsyncMock(return_value=""),
            ),
            patch.object(
                merrick_main,
                "recall_openclaw_native_context",
                new=AsyncMock(return_value=""),
            ),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "Continue our previous Atlas plan with the next region.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        request = stream_response.call_args
        self.assertIn("<untrusted_relevant_historical_context>", request.args[0])
        self.assertIn(
            "Do not begin with a recap of the prior exchange",
            request.kwargs["instructions"],
        )

    async def test_preference_revision_requests_only_a_forward_acknowledgement(self) -> None:
        async def response_stream():
            yield "I will use Chinese for future replies."

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ) as stream_response:
            await self.session.run_query(
                "Actually, use Chinese rather than English for replies.",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        instructions = stream_response.call_args.kwargs["instructions"]
        self.assertIn("acknowledge only the latest effective result", instructions)
        self.assertIn("Never contrast it with a superseded preference", instructions)

    async def test_current_preference_question_never_queries_old_openclaw_transcripts(self) -> None:
        async def response_stream():
            yield "You prefer detailed technical explanations."

        wiki_recall = AsyncMock(return_value="old wiki preference")
        native_recall = AsyncMock(return_value="old transcript preference")
        with (
            patch.object(
                merrick_main,
                "recall_long_term_context",
                return_value="Current preferences:\n- Use detailed explanations for technical questions.",
            ),
            patch.object(merrick_main, "recall_openclaw_wiki_context", wiki_recall),
            patch.object(merrick_main, "recall_openclaw_native_context", native_recall),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: response_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                "What are my preferences?",
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        wiki_recall.assert_not_awaited()
        native_recall.assert_not_awaited()
        self.assertIn(
            "Use detailed explanations for technical questions.",
            stream_response.call_args.args[0],
        )

    async def test_search_and_analysis_always_uses_visible_browser_research(self) -> None:
        text = "Search battery storage policy and analyse the information."
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        with patch.object(openclaw_gateway, "stream_response") as stream_response:
            await self.session.run_query(
                text,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        stream_response.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text,
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "battery storage policy",
            }],
        )

    async def test_chinese_search_and_analysis_uses_the_same_visible_workflow(self) -> None:
        text = "搜索电池储能政策并分析信息"
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        with patch.object(openclaw_gateway, "stream_response") as stream_response:
            await self.session.run_query(
                text,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        stream_response.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text,
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "电池储能政策",
            }],
        )

    async def test_local_document_request_bypasses_action_planner(self) -> None:
        self.session.answer_with_local_document = AsyncMock()  # type: ignore[method-assign]
        with patch.object(openclaw_gateway, "plan_actions", new=AsyncMock()) as planner:
            await self.session.run_query(
                "Read the attention paper",
                detect_action=True,
                allow_desktop_actions=True,
            )
        planner.assert_not_awaited()
        self.session.answer_with_local_document.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Read the attention paper"
        )

    async def test_workspace_summary_reads_library_context_before_writing(self) -> None:
        self.session.write_workspace_summary_from_local_document = AsyncMock()  # type: ignore[method-assign]

        await self.session.run_query("Write a summary of the paper.")

        self.session.write_workspace_summary_from_local_document.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Write a summary of the paper."
        )

    async def test_local_document_comparison_attaches_two_documents(self) -> None:
        first = merrick_main.LibraryDocument("first.pdf", "first", "first text", ("first text",))
        second = merrick_main.LibraryDocument("second.md", "second", "second text", ("second text",))
        self.session.library = Mock()
        self.session.library.list_documents.return_value = [
            {"path": "first.pdf", "title": "first"},
            {"path": "second.md", "title": "second"},
        ]
        self.session.library.root = Path("/library")
        self.session.library.read_document.side_effect = [first, second]
        self.session.library.relevant_context.side_effect = [
            {"kind": "local_document", "title": "first", "source": "first.pdf", "excerpt_count": 1, "text": "first text"},
            {"kind": "local_document", "title": "second", "source": "second.md", "excerpt_count": 1, "text": "second text"},
        ]
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        await self.session.answer_with_local_document("Compare the two documents")

        self.assertEqual(self.session.library.read_document.call_count, 2)
        context = self.session.run_query.await_args.kwargs["research_context"]  # type: ignore[attr-defined]
        self.assertEqual(context["kind"], "local_document_comparison")
        self.assertEqual(len(context["documents"]), 2)

    async def test_search_followup_uses_session_context_before_model_routing(self) -> None:
        self.session.last_public_search_query = "OpenAI realtime API"
        self.session.handle_search_followup = AsyncMock(return_value=True)  # type: ignore[method-assign]

        with (
            patch.object(openclaw_gateway, "stream_response") as stream_response,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Analyze those search results",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        self.session.handle_search_followup.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Analyze those search results"
        )
        stream_response.assert_not_called()

    async def test_non_wake_weather_uses_hidden_bounded_research(self) -> None:
        action = {
            "type": "web_research",
            "query": "What is the weather in London today?",
        }
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        async def assert_thinking_precedes_research(*_args):
            states = [
                message.get("state")
                for message in self.ws.messages
                if message.get("type") == "status"
            ]
            self.assertIn("thinking", states)
            self.assertNotIn("acting", states)

        self.session.answer_with_public_research = AsyncMock(  # type: ignore[method-assign]
            side_effect=assert_thinking_precedes_research,
        )

        with (
            patch.object(openclaw_gateway, "stream_response") as stream_response,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "What is the weather in London today?",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        self.session.execute_action_plan.assert_not_awaited()  # type: ignore[attr-defined]
        self.session.answer_with_public_research.assert_awaited_once_with(  # type: ignore[attr-defined]
            "What is the weather in London today?",
            action,
        )
        stream_response.assert_not_called()
        self.assertFalse(
            any(
                message.get("type") == "status"
                and message.get("state") == "acting"
                for message in self.ws.messages
            )
        )

    async def test_weather_bypasses_model_router_and_never_requests_wake_word(self) -> None:
        action = {
            "type": "web_research",
            "query": "What is the weather in Glasgow today?",
        }
        self.session.answer_with_public_research = AsyncMock()  # type: ignore[method-assign]

        with (
            patch.object(openclaw_gateway, "stream_response") as stream_response,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "What is the weather in Glasgow today?",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        stream_response.assert_not_called()
        self.session.answer_with_public_research.assert_awaited_once_with(  # type: ignore[attr-defined]
            "What is the weather in Glasgow today?",
            action,
        )
        states = [
            message.get("state")
            for message in self.ws.messages
            if message.get("type") == "status"
        ]
        self.assertIn("thinking", states)
        self.assertNotIn("acting", states)

    async def test_hotel_recommendation_uses_visible_browser_research(self) -> None:
        text = "Recommend hotels in London for next Sunday under £200."
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        with (
            patch.object(openclaw_gateway, "stream_response") as stream_response,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": text,
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        stream_response.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text,
            [{
                "type": "browser_search",
                "browser": "default",
                "query": "hotels in London for next Sunday under £200",
            }],
        )

    async def test_hotel_budget_followup_refines_the_active_visible_search(self) -> None:
        text = "Sorry, make the budget £200 and prioritise ratings above 8."
        self.session.last_public_search_query = (
            "hotels in London for next Sunday under £20"
        )
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        with patch.object(openclaw_gateway, "stream_response") as stream_response:
            await self.session.run_query(
                text,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        stream_response.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text,
            [{
                "type": "browser_search",
                "browser": "default",
                "query": (
                    "hotels in London for next Sunday budget £200 "
                    "prioritise ratings above 8"
                ),
            }],
        )

    async def test_weather_uses_structured_background_data_not_browser_search(self) -> None:
        context = {
            "kind": "structured_weather",
            "source": "Open-Meteo",
            "location": {"name": "Glasgow"},
            "current": {"temperature_c": 14, "condition": "mainly clear"},
        }
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]
        with (
            patch.object(
                merrick_main,
                "fetch_weather_context",
                new=AsyncMock(return_value=context),
            ),
            patch.object(openclaw_gateway, "invoke_tool", new=AsyncMock()) as invoke_tool,
        ):
            await self.session.answer_with_public_research(
                "What's the weather in Glasgow today?",
                {
                    "type": "web_research",
                    "query": "What's the weather in Glasgow today?",
                },
            )

        invoke_tool.assert_not_awaited()
        self.session.run_query.assert_awaited_once_with(  # type: ignore[attr-defined]
            "What's the weather in Glasgow today?",
            is_draft=False,
            force_screen=False,
            agent_id="researcher",
            host_action=True,
            research_context=context,
        )

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_desktop_action_protocol_executes_without_wake_word(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        async def response_stream():
            yield 'JARVIS_ACTION {"actions":[{"type":"open_app","app":"safari"}]}'

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Open Safari",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Open Safari",
            [{"type": "open_app", "app": "safari"}],
        )
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(visible, "")

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_rejected_ungrounded_research_probe_falls_back_silently(self) -> None:
        calls = 0

        async def response_stream():
            nonlocal calls
            calls += 1
            if calls == 1:
                yield (
                    'JARVIS_ACTION {"actions":[{"type":"web_research",'
                    '"query":"a topic absent from this question"}]}'
                )
            else:
                yield "I need a reliable live source for that price."

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Please arrange the windows for my presentation",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(
            visible,
            "I need a reliable live source for that price.",
        )
        self.assertNotIn("didn't execute", visible)

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_private_research_proposal_never_leaves_the_machine(self) -> None:
        self.session.answer_with_public_research = AsyncMock()  # type: ignore[method-assign]
        calls = 0

        async def response_stream():
            nonlocal calls
            calls += 1
            if calls == 1:
                yield (
                    'JARVIS_ACTION {"actions":[{"type":"web_research",'
                    '"query":"latest status of my client Project Bluebird"}]}'
                )
            else:
                yield "I cannot verify a private client project from public sources."

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: response_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Please manage the latest status of my private client Project Bluebird",
                "typed": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task

        self.session.answer_with_public_research.assert_not_awaited()  # type: ignore[attr-defined]
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(
            visible,
            "I cannot verify a private client project from public sources.",
        )
        self.assertFalse(
            any(
                message.get("type") == "status"
                and message.get("state") == "acting"
                for message in self.ws.messages
            )
        )

    async def test_ordinary_answer_streams_before_completion(self) -> None:
        first_delta_ready = asyncio.Event()
        release_tail = asyncio.Event()

        async def ordinary_stream():
            yield "Certainly"
            first_delta_ready.set()
            await release_tail.wait()
            yield ", sir."

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: ordinary_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Explain latency briefly",
                "typed": True,
            })
            await asyncio.wait_for(first_delta_ready.wait(), timeout=0.5)
            await asyncio.sleep(0)
            visible = "".join(
                message.get("text", "")
                for message in self.ws.messages
                if message.get("type") == "assistant_delta"
            )
            self.assertEqual(visible, "Certainly")
            assert self.session.query_task is not None
            self.assertFalse(self.session.query_task.done())
            release_tail.set()
            await self.session.query_task

    async def test_first_delta_stall_uses_tool_free_ephemeral_retry_without_restart(self) -> None:
        stalled = asyncio.Event()
        self.session.voice_verdict = merrick_main.VoiceVerdict("owner", 0.9)

        async def stalled_stream():
            await stalled.wait()
            yield "never"

        async def recovered_stream():
            yield "Recovered promptly."

        stream_response = Mock(side_effect=[stalled_stream(), recovered_stream()])
        recover = AsyncMock()
        with (
            patch.object(
                merrick_main, "FIRST_DELTA_TIMEOUT_SECONDS", 0.01
            ),
            patch.object(
                merrick_main, "ISOLATED_FIRST_DELTA_TIMEOUT_SECONDS", 0.1
            ),
            patch.object(
                merrick_main, "RESTARTED_FIRST_DELTA_TIMEOUT_SECONDS", 0.1
            ),
            patch.object(
                openclaw_gateway, "stream_response", stream_response
            ),
            patch.object(
                openclaw_gateway,
                "recover_after_repeated_first_delta_stall",
                recover,
            ),
        ):
            await self.session.run_query(
                "Explain the current status briefly",
                trusted_typed=True,
            )

        recover.assert_not_awaited()
        self.assertEqual(stream_response.call_count, 2)
        self.assertFalse(stream_response.call_args_list[0].kwargs["ephemeral_session"])
        self.assertTrue(stream_response.call_args_list[1].kwargs["ephemeral_session"])
        self.assertEqual(stream_response.call_args_list[0].kwargs["agent_id"], "main")
        self.assertEqual(stream_response.call_args_list[1].kwargs["agent_id"], "main")
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(visible, "Recovered promptly.")

    async def test_repeated_first_delta_stall_restarts_once_then_tries_third_lane(self) -> None:
        stalled = asyncio.Event()
        self.session.voice_verdict = merrick_main.VoiceVerdict("owner", 0.9)

        async def stalled_stream():
            await stalled.wait()
            yield "never"

        async def recovered_stream():
            yield "Recovered after replacement."

        stream_response = Mock(
            side_effect=[stalled_stream(), stalled_stream(), recovered_stream()]
        )
        recover = AsyncMock()
        with (
            patch.object(merrick_main, "FIRST_DELTA_TIMEOUT_SECONDS", 0.01),
            patch.object(merrick_main, "ISOLATED_FIRST_DELTA_TIMEOUT_SECONDS", 0.01),
            patch.object(merrick_main, "RESTARTED_FIRST_DELTA_TIMEOUT_SECONDS", 0.1),
            patch.object(merrick_main, "FIRST_DELTA_RECOVERY_DELAY_SECONDS", 0),
            patch.object(openclaw_gateway, "stream_response", stream_response),
            patch.object(
                openclaw_gateway,
                "recover_after_repeated_first_delta_stall",
                recover,
            ),
        ):
            await self.session.run_query(
                "Explain the current status briefly",
                trusted_typed=True,
            )

        recover.assert_awaited_once()
        self.assertEqual(stream_response.call_count, 3)
        self.assertFalse(stream_response.call_args_list[0].kwargs["ephemeral_session"])
        for call in stream_response.call_args_list[1:]:
            self.assertTrue(call.kwargs["ephemeral_session"])
            self.assertEqual(call.kwargs["agent_id"], "main")
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(visible, "Recovered after replacement.")

    async def test_final_speech_endpoint_enters_processing_before_query_work(self) -> None:
        release = asyncio.Event()

        async def blocked_query(*_args, **_kwargs):
            await release.wait()

        self.session.run_query = AsyncMock(side_effect=blocked_query)  # type: ignore[method-assign]

        await self.session.handle_message({
            "type": "speech_partial",
            "text": "Explain the current execution state",
            "final": True,
        })

        states = [
            message.get("state")
            for message in self.ws.messages
            if message.get("type") == "status"
        ]
        self.assertEqual(states[-1], "thinking")
        self.assertTrue(
            any(
                message.get("type") == "speech_ack"
                for message in self.ws.messages
            )
        )
        assert self.session.query_task is not None
        self.assertFalse(self.session.query_task.done())
        release.set()
        await self.session.query_task

    async def test_processing_state_precedes_query_work_without_a_generic_acknowledgement(self) -> None:
        release = asyncio.Event()

        async def blocked_query(*_args, **_kwargs):
            await release.wait()

        self.session.run_query = AsyncMock(side_effect=blocked_query)  # type: ignore[method-assign]
        await self.session.handle_message({
            "type": "user_text",
            "text": "Please check this",
            "typed": True,
        })

        self.assertNotIn(
            "audio",
            [message["type"] for message in self.ws.messages],
        )

        release.set()
        assert self.session.query_task is not None
        await self.session.query_task

    async def test_final_command_starts_background_query_without_cached_ack(self) -> None:
        release = asyncio.Event()

        async def blocked_query(*_args, **_kwargs):
            await release.wait()

        self.session.tts_enabled = True
        self.session.run_query = AsyncMock(side_effect=blocked_query)  # type: ignore[method-assign]
        with patch.object(merrick_main, "cached_acknowledgement") as loader:
            await self.session.handle_message({
                "type": "user_text",
                "text": "帮我查一下伦敦下周日的酒店",
                "typed": True,
            })

        message_types = [message["type"] for message in self.ws.messages]
        self.assertLess(message_types.index("status"), message_types.index("audio_cancelled"))
        self.assertNotIn("audio", message_types)
        self.assertNotIn("foreground_cue_ready", self.session.latency_marks)
        loader.assert_not_called()
        self.assertTrue(self.session.tts_queue.empty())
        assert self.session.query_task is not None
        self.assertFalse(self.session.query_task.done())
        release.set()
        await self.session.query_task

    async def test_final_command_starts_understanding_without_a_generic_ack(self) -> None:
        release = asyncio.Event()
        observed_types: list[str] = []

        async def blocked_query(*_args, **_kwargs):
            await release.wait()

        def start_sidecar(*_args, **_kwargs):
            observed_types.extend(message["type"] for message in self.ws.messages)
            return asyncio.create_task(asyncio.sleep(0))

        self.session.tts_enabled = True
        self.session.run_query = AsyncMock(side_effect=blocked_query)  # type: ignore[method-assign]
        with (
            patch.object(
                self.session,
                "start_turn_understanding",
                side_effect=start_sidecar,
            ) as sidecar,
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Open Safari",
                "typed": True,
            })

        self.assertNotIn("audio", observed_types)
        sidecar.assert_called_once_with(
            "Open Safari",
            is_owner=True,
            include_prosody=False,
        )
        release.set()
        assert self.session.query_task is not None
        await self.session.query_task

    async def test_acoustic_delivery_hint_is_attached_silently_to_the_final_answer(self) -> None:
        self.session.voice_verdict = merrick_main.VoiceVerdict("owner", 0.9)
        understanding = merrick_main.TurnUnderstanding(
            turn=self.session.turn,
            text="Give me the next step.",
            intent="conversation",
            recent_dialogue="",
            episodic_context="",
            working_focus="",
            prosody_hint="The user's vocal delivery was acoustically steady.",
        )

        async def answer_stream():
            yield "Take the next small step."

        with (
            patch.object(
                self.session,
                "understanding_for_turn",
                new=AsyncMock(return_value=understanding),
            ) as sidecar,
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: answer_stream(),
            ) as stream_response,
        ):
            await self.session.run_query("Give me the next step.")

        sidecar.assert_awaited_once_with(
            "Give me the next step.",
            is_owner=True,
            include_prosody=True,
        )
        instructions = stream_response.call_args.kwargs["instructions"]
        self.assertIn("<silent_acoustic_delivery>", instructions)
        self.assertIn("acoustically steady", instructions)
        self.assertIn("must never change action authority", instructions)

    async def test_action_progress_speaks_the_real_action_even_after_a_legacy_ack_turn(self) -> None:
        self.session.tts_enabled = True
        self.session.fast_ack_turn = self.session.turn

        await self.session.send_action_progress(
            "executing", action={"type": "open_app", "app": "Chrome"}, speak=True
        )

        self.assertEqual(
            self.session.tts_queue.get_nowait(),
            (self.session.turn, "Opening Chrome now.", "en"),
        )

    async def test_completion_notice_preserves_the_cached_acknowledgement_turn(self) -> None:
        self.session.tts_enabled = True
        self.session.turn = 4
        self.session.fast_ack_turn = 4
        self.session.wait_for_tts_drain = AsyncMock()  # type: ignore[method-assign]

        await self.session.send_local_spoken_notice("Safari is open.")

        self.assertEqual(self.session.turn, 4)
        self.assertFalse(
            any(message.get("type") == "audio_cancelled" for message in self.ws.messages)
        )
        self.assertEqual(
            self.session.tts_queue.get_nowait(),
            (4, "Safari is open.", "en"),
        )
        self.session.wait_for_tts_drain.assert_awaited_once_with(  # type: ignore[attr-defined]
            reason="local_notice"
        )

    async def test_fast_voice_flow_has_a_runtime_kill_switch(self) -> None:
        self.session.tts_enabled = True
        with (
            patch.object(merrick_main, "FAST_VOICE_FLOW_ENABLED", False),
            patch.object(merrick_main, "cached_acknowledgement") as loader,
        ):
            sent = await self.session.send_fast_acknowledgement("action")

        self.assertFalse(sent)
        loader.assert_not_called()

    async def test_fast_acknowledgements_cycle_through_cached_voice_variants(self) -> None:
        cached = merrick_main.SynthesizedAudio(
            data=b"variant", mime="audio/wav", engine="steadfast-cache"
        )
        self.session.tts_enabled = True
        self.session.turn = 5
        self.session.fast_ack_seed = 2

        with (
            patch.object(merrick_main, "FAST_VOICE_FLOW_ENABLED", True),
            patch.object(merrick_main, "cached_acknowledgement", return_value=cached) as loader,
        ):
            sent = await self.session.send_fast_acknowledgement("action")

        self.assertTrue(sent)
        loader.assert_called_once_with("action", "en", variant=7)

    async def test_acknowledgement_playback_has_its_own_latency_mark(self) -> None:
        self.session.turn = 5
        self.session.begin_latency_turn()

        await self.session.handle_message({
            "type": "client_event",
            "event": "audio_play_started",
            "detail": "role=acknowledgement remaining=0 ready=4",
        })

        self.assertIn("foreground_cue_play_started", self.session.latency_marks)
        self.assertIn("audio_play_started", self.session.latency_marks)

    async def test_remote_memory_recall_is_parallel_and_bounded(self) -> None:
        self.session.voice_verdict = merrick_main.VoiceVerdict("owner", 0.9)
        self.session.voice_memory_verified = True

        async def slow_recall(_text: str) -> str:
            await asyncio.sleep(1)
            return "late context"

        async def answer_stream():
            yield "I do not have a reliable earlier match."

        wiki_recall = AsyncMock(side_effect=slow_recall)
        native_recall = AsyncMock(side_effect=slow_recall)
        with (
            patch.object(merrick_main, "MEMORY_RECALL_TIMEOUT_SECONDS", 0.01),
            patch.object(merrick_main, "recall_long_term_context", return_value=""),
            patch.object(merrick_main, "recall_openclaw_wiki_context", wiki_recall),
            patch.object(merrick_main, "recall_openclaw_native_context", native_recall),
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: answer_stream(),
            ),
        ):
            await self.session.run_query(
                "What did we discuss previously?",
                trusted_typed=True,
            )

        wiki_recall.assert_awaited_once()
        native_recall.assert_awaited_once()
        visible = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
        )
        self.assertEqual(visible, "I do not have a reliable earlier match.")

    async def test_tts_drain_timeout_releases_turn_without_discarding_speech_tail(self) -> None:
        tail = (self.session.turn, "This final sentence must still be spoken.", "en")
        self.session.tts_queue.put_nowait(tail)

        with patch.object(merrick_main, "TTS_DRAIN_TIMEOUT_SECONDS", 0.01):
            await self.session.wait_for_tts_drain(reason="test")

        self.assertEqual(self.session.tts_queue.get_nowait(), tail)
        self.session.tts_queue.task_done()
        await asyncio.wait_for(self.session.tts_queue.join(), timeout=0.05)

    async def test_tts_worker_speaks_all_segments_after_foreground_timeout(self) -> None:
        segments = ["First sentence.", "Second sentence.", "This is the final sentence."]
        for text in segments:
            self.session.tts_queue.put_nowait((self.session.turn, text, "en"))
        with patch.object(merrick_main, "TTS_DRAIN_TIMEOUT_SECONDS", 0.01):
            await self.session.wait_for_tts_drain(reason="model_answer")

        self.session.tts_streaming_supported = True
        self.session.send_streaming_tts_audio = AsyncMock()
        self.session.tts_queue.put_nowait(None)
        with patch.object(merrick_main, "supports_incremental_synthesis", return_value=True):
            await self.session.tts_worker()

        self.assertEqual(
            [call.args[1] for call in self.session.send_streaming_tts_audio.await_args_list],
            segments,
        )
        await asyncio.wait_for(self.session.tts_queue.join(), timeout=0.05)

    async def test_new_turn_still_discards_stale_speech_after_foreground_timeout(self) -> None:
        self.session.tts_queue.put_nowait((self.session.turn, "Old answer tail.", "en"))
        with patch.object(merrick_main, "TTS_DRAIN_TIMEOUT_SECONDS", 0.01):
            await self.session.wait_for_tts_drain(reason="model_answer")
        self.session.turn += 1
        self.session.tts_queue.put_nowait(None)
        self.session.send_streaming_tts_audio = AsyncMock()

        await self.session.tts_worker()

        self.session.send_streaming_tts_audio.assert_not_awaited()
        await asyncio.wait_for(self.session.tts_queue.join(), timeout=0.05)

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_stable_endpoint_replaces_gated_request_without_leak(self) -> None:
        prefix_ready = asyncio.Event()
        stream_cancelled = asyncio.Event()
        never_release = asyncio.Event()

        async def prefix_stream():
            try:
                yield "JARVIS_"
                prefix_ready.set()
                await never_release.wait()
            finally:
                stream_cancelled.set()

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: prefix_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Please arrange",
                "draft": True,
            })
            await asyncio.wait_for(prefix_ready.wait(), timeout=0.5)
            await self.session.handle_message({
                "type": "speech_partial",
                "text": "Please arrange the windows for my presentation",
                "final": True,
            })

        await asyncio.wait_for(stream_cancelled.wait(), timeout=0.5)
        self.assertFalse(
            any(
                message.get("type") in {"assistant_delta", "audio"}
                for message in self.ws.messages
            )
        )
        if self.session.draft_task and not self.session.draft_task.done():
            self.session.draft_task.cancel()

    async def test_transcript_growth_during_dispatch_settle_prevents_action(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        async def action_stream():
            yield 'JARVIS_ACTION {"actions":[{"type":"open_app","app":"safari"}]}'

        with (
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: action_stream(),
            ),
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0.5),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Merrick, open Safari",
                "draft": True,
            })
            await asyncio.sleep(0.05)
            await self.session.handle_message({
                "type": "speech_partial",
                "text": "Merrick, open Safari no open Chrome",
            })

        self.session.execute_action_plan.assert_not_awaited()  # type: ignore[attr-defined]
        if self.session.draft_task and not self.session.draft_task.done():
            self.session.draft_task.cancel()

    async def test_unbound_or_bare_yes_stays_non_executing_in_openclaw_main(self) -> None:
        replies = {
            "Merrick, tell me why Safari is popular": "Safari is popular because it is integrated with Apple devices.",
            "Merrick, yes": "What would you like me to confirm?",
        }
        for user_text, reply in replies.items():
            with self.subTest(user_text=user_text):
                self.ws.messages.clear()
                self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

                async def conversation_stream():
                    yield reply

                with patch.object(
                    openclaw_gateway,
                    "stream_response",
                    side_effect=lambda *_args, **_kwargs: conversation_stream(),
                ) as stream_response:
                    await self.session.run_query(
                        user_text,
                        trusted_typed=True,
                        detect_action=True,
                        allow_desktop_actions=True,
                    )

                self.session.execute_action_plan.assert_not_awaited()  # type: ignore[attr-defined]
                visible = "".join(
                    message.get("text", "")
                    for message in self.ws.messages
                    if message.get("type") == "assistant_delta"
                )
                self.assertEqual(visible, reply)
                self.assertIn(
                    "For ordinary conversation",
                    stream_response.call_args.kwargs["instructions"],
                )
                self.assertEqual(stream_response.call_args.kwargs["agent_id"], "main")

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_rejected_stream_plan_uses_openclaw_fallback_before_failure(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        text = "Please arrange the windows for my presentation"

        async def invalid_stream():
            yield 'JARVIS_ACTION {"actions":[{"type":"open_app","app":"safari"}]}'

        repaired = [{"type": "open_app", "app": "maps"}]
        with (
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: invalid_stream(),
            ),
            patch.object(
                openclaw_gateway,
                "plan_actions",
                new=AsyncMock(return_value=repaired),
            ) as planner,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.run_query(
                text,
                is_draft=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        planner.assert_awaited_once_with(text)
        self.session.execute_action_plan.assert_awaited_once_with(  # type: ignore[attr-defined]
            text, repaired
        )

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_polite_computer_command_uses_planner_before_chat(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        planned = [{"type": "open_app", "app": "maps"}]
        text = "Can you open the map and see where the location of us?"
        with (
            patch.object(
                openclaw_gateway,
                "plan_actions",
                new=AsyncMock(return_value=planned),
            ) as planner,
            patch.object(openclaw_gateway, "stream_response") as chat_stream,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.run_query(
                text,
                is_draft=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        planner.assert_awaited_once_with(text)
        chat_stream.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(text, planned)  # type: ignore[attr-defined]

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_plain_spotify_command_uses_planner_before_chat(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]
        planned = [{"type": "media_control", "player": "spotify", "action": "play"}]
        text = "Spotify, open and play music"
        with (
            patch.object(
                openclaw_gateway,
                "plan_actions",
                new=AsyncMock(return_value=planned),
            ) as planner,
            patch.object(openclaw_gateway, "stream_response") as chat_stream,
            patch.object(merrick_main, "ACTION_DISPATCH_SETTLE_SECONDS", 0),
        ):
            await self.session.run_query(
                text,
                is_draft=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        planner.assert_awaited_once_with(text)
        chat_stream.assert_not_called()
        self.session.execute_action_plan.assert_awaited_once_with(text, planned)  # type: ignore[attr-defined]

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_action_protocol_is_bounded_and_never_leaks(self) -> None:
        async def oversized_stream():
            yield "JARVIS_ACTION "
            yield "x" * (merrick_main.ACTION_PROTOCOL_MAX_CHARS + 1)

        self.session.queue_speech_from_stream = Mock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: oversized_stream(),
        ) as stream_response:
            await self.session.run_query(
                "Please arrange the windows for my presentation",
                is_draft=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        marker_text = "".join(
            message.get("text", "")
            for message in self.ws.messages
            if message.get("type") == "assistant_delta"
            and "JARVIS_ACTION" in message.get("text", "")
        )
        self.assertEqual(marker_text, "")
        self.session.queue_speech_from_stream.assert_not_called()  # type: ignore[attr-defined]
        self.assertEqual(
            stream_response.call_args.kwargs["max_output_tokens"],
            merrick_main.MAIN_MAX_OUTPUT_TOKENS,
        )

    async def test_original_report_bypasses_desktop_action_planning(self) -> None:
        async def report_stream():
            yield "# Product Assessment\n\n## Executive summary\n- Ready for evaluation."

        prompt = (
            "Write an original Personal Assistant assessment report in this reply only. "
            "Do not read any document. Format it for the Display screen."
        )
        with (
            patch.object(openclaw_gateway, "plan_actions", new=AsyncMock()) as planner,
            patch.object(
                openclaw_gateway,
                "stream_response",
                side_effect=lambda *_args, **_kwargs: report_stream(),
            ) as stream_response,
        ):
            await self.session.run_query(
                prompt,
                trusted_typed=True,
                detect_action=True,
                allow_desktop_actions=True,
            )

        planner.assert_not_awaited()
        self.assertEqual(
            stream_response.call_args.kwargs["max_output_tokens"],
            merrick_main.REPORT_MAX_OUTPUT_TOKENS,
        )

    @patch.object(merrick_main, "DIRECT_OPENCLAW_EXECUTION", False)
    async def test_legacy_final_asr_callback_does_not_repeat_dispatched_action(self) -> None:
        self.session.execute_action_plan = AsyncMock()  # type: ignore[method-assign]

        async def action_stream():
            yield 'JARVIS_ACTION {"actions":[{"type":"open_app","app":"safari"}]}'

        with patch.object(
            openclaw_gateway,
            "stream_response",
            side_effect=lambda *_args, **_kwargs: action_stream(),
        ):
            await self.session.handle_message({
                "type": "user_text",
                "text": "Merrick, open Safari",
                "draft": True,
            })
            assert self.session.query_task is not None
            await self.session.query_task
            await self.session.handle_message({
                "type": "user_text",
                "text": "Merrick, open Safari",
                "draft": False,
            })

        self.assertEqual(self.session.execute_action_plan.await_count, 1)  # type: ignore[attr-defined]


class ActionPlanExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ws = FakeWebSocket()
        self.session = Session(self.ws)  # type: ignore[arg-type]
        self.session.tts_enabled = False

    def test_progress_phrases_describe_real_work_not_acknowledgements(self) -> None:
        self.assertEqual(self.session.action_progress_phrase("planning"), "Working out the next step…")
        self.assertEqual(
            self.session.action_progress_phrase("research_planning"),
            "Tracing the most useful sources now…",
        )
        self.assertEqual(
            self.session.action_progress_phrase(
                "executing", action={"type": "open_app", "app": "Chrome"}
            ),
            "Opening Chrome now.",
        )
        self.session.conversation_language = "zh"
        self.assertEqual(
            self.session.action_progress_phrase("planning"), "正在梳理下一步…"
        )
        self.assertEqual(
            self.session.action_progress_phrase("research_planning"), "正在筛选最有价值的来源…"
        )

    async def test_shutdown_sequence_stops_at_one_total_deadline(self) -> None:
        blocked = asyncio.Event()
        later_step_started = False

        async def later_step() -> None:
            nonlocal later_step_started
            later_step_started = True

        completed = await merrick_main.run_bounded_shutdown_steps(
            [
                ("blocked", blocked.wait),
                ("later", later_step),
            ],
            total_timeout=0.01,
        )

        self.assertFalse(completed)
        self.assertFalse(later_step_started)

    async def test_voice_pipeline_stall_is_handed_to_bounded_openclaw_recovery(self) -> None:
        recover = AsyncMock(return_value="gateway_ready")
        with patch.object(openclaw_gateway, "self_heal_runtime_stall", recover):
            await self.session.handle_message({
                "type": "runtime_stall",
                "subsystem": "voice_pipeline",
                "code": "external_playback_gate_stalled",
            })
            assert self.session.runtime_recovery_task is not None
            await self.session.runtime_recovery_task

        recover.assert_awaited_once_with(
            subsystem="voice_pipeline",
            code="external_playback_gate_stalled",
        )
        self.assertIn(
            {"type": "runtime_recovery", "status": "gateway_ready"},
            self.ws.messages,
        )

    async def test_turn_progress_watchdog_unblocks_the_ui_before_openclaw_recovery(self) -> None:
        blocked = asyncio.Event()
        self.session.turn = 7
        self.session.query_task = asyncio.create_task(blocked.wait())
        recover = AsyncMock(return_value="gateway_restarted")

        with (
            patch.object(merrick_main, "TURN_PROGRESS_STALL_SECONDS", 0.01),
            patch.object(openclaw_gateway, "self_heal_runtime_stall", recover),
        ):
            self.session.start_turn_progress_watchdog(self.session.query_task, turn=7)
            assert self.session.turn_watchdog_task is not None
            await self.session.turn_watchdog_task
            assert self.session.runtime_recovery_task is not None
            await self.session.runtime_recovery_task

        self.assertTrue(self.session.query_task.cancelled())
        self.assertIn({"type": "status", "state": "idle"}, self.ws.messages)
        recover.assert_awaited_once_with(
            subsystem="model_stream",
            code="first_delta_stalled",
        )

    async def test_research_source_budget_scales_with_requested_depth(self) -> None:
        self.assertEqual(merrick_main.research_source_budget("Research battery storage"), 4)
        self.assertEqual(merrick_main.research_source_budget("Deep research battery storage"), 6)
        self.assertEqual(
            merrick_main.research_source_budget("Give me a systematic maximum-depth review of battery storage"),
            8,
        )

    async def test_research_processing_acknowledgement_is_queued_for_speech(self) -> None:
        self.session.tts_enabled = True
        phrase = self.session.action_progress_phrase("research_planning")

        await self.session.send_action_progress("research_planning", speak=True)

        self.assertEqual(
            self.session.tts_queue.get_nowait(),
            (self.session.turn, phrase, "en"),
        )

    async def test_research_source_overview_is_not_a_second_answer_or_tts_turn(self) -> None:
        """Regression: source progress must not duplicate the final synthesis."""
        self.session.tts_enabled = True

        await self.session.announce_research_sources([
            {
                "title": "Primary source",
                "url": "https://example.com/primary",
                "snippet": "A bounded source card.",
            },
        ])

        self.assertEqual(
            [message["type"] for message in self.ws.messages],
            ["research_source_overview"],
        )
        self.assertEqual(self.session.tts_queue.qsize(), 0)

    async def test_research_source_cards_apply_the_chinese_media_filter(self) -> None:
        blocked = {
            "title": "大纪元财经",
            "url": "https://example.org/repost",
            "snippet": "中国市场",
        }
        allowed = {
            "title": "中国市场分析",
            "url": "https://www.reuters.com/world/china/example",
            "snippet": "独立市场报道",
        }

        await self.session.send_research_sources("中国市场新闻", [blocked, allowed])

        source_messages = [
            message for message in self.ws.messages
            if message.get("type") == "research_sources"
        ]
        self.assertEqual(source_messages[0]["sources"], [allowed])

    async def test_blocked_chinese_topic_never_reaches_a_search_provider(self) -> None:
        self.session.find_public_search_results = AsyncMock()  # type: ignore[method-assign]

        results = await self.session.find_checked_public_search_results(
            "法轮功最新消息",
            request_text="分析法轮功最新消息",
        )

        self.assertEqual(results, [])
        self.session.find_public_search_results.assert_not_awaited()  # type: ignore[attr-defined]

    async def test_chinese_search_filters_provider_results_before_caching(self) -> None:
        blocked = {
            "title": "中国市场报道",
            "url": "https://www.ntdtv.com/markets/example",
            "snippet": "中国市场新闻",
        }
        allowed = {
            "title": "中国市场分析",
            "url": "https://www.reuters.com/world/china/example",
            "snippet": "中国市场新闻",
        }
        self.session.find_public_search_results = AsyncMock(  # type: ignore[method-assign]
            return_value=[blocked, allowed]
        )

        results = await self.session.find_checked_public_search_results(
            "中国市场新闻",
            request_text="中国市场新闻",
        )

        self.assertEqual(results, [allowed])

    async def test_chinese_command_keeps_source_filter_for_an_english_query(self) -> None:
        blocked = {
            "title": "OpenAI release analysis",
            "url": "https://www.ganjingworld.com/news/example",
            "snippet": "OpenAI release news",
        }
        allowed = {
            "title": "OpenAI release analysis",
            "url": "https://openai.com/news/example",
            "snippet": "OpenAI release news",
        }
        self.session.find_public_search_results = AsyncMock(  # type: ignore[method-assign]
            return_value=[blocked, allowed]
        )

        results = await self.session.find_checked_public_search_results(
            "OpenAI release news",
            request_text="搜索 OpenAI release news",
        )

        self.assertEqual(results, [allowed])

    async def test_cached_chinese_results_are_refiltered_before_a_followup(self) -> None:
        blocked = {
            "title": "中国市场报道",
            "url": "https://www.minghui.org/news/example",
            "snippet": "中国市场新闻",
        }
        allowed = {
            "title": "中国市场分析",
            "url": "https://www.reuters.com/world/china/example",
            "snippet": "中国市场新闻",
        }
        self.session.last_public_search_query = "中国市场新闻"
        self.session.last_public_search_results = [blocked, allowed]

        results = await self.session.ensure_last_search_results()

        self.assertEqual(results, [allowed])
        self.assertEqual(self.session.last_public_search_results, [allowed])

    async def test_cached_english_query_retains_its_chinese_request_policy(self) -> None:
        blocked = {
            "title": "OpenAI analysis",
            "url": "https://www.epochtimes.com/technology/example",
            "snippet": "OpenAI news",
        }
        allowed = {
            "title": "OpenAI analysis",
            "url": "https://openai.com/news/example",
            "snippet": "OpenAI news",
        }
        self.session.last_public_search_query = "OpenAI news"
        self.session.last_research_goal = "搜索 OpenAI news"
        self.session.last_public_search_results = [blocked, allowed]

        results = await self.session.ensure_last_search_results()

        self.assertEqual(results, [allowed])

    async def test_chinese_newspaper_research_uses_the_same_media_filter(self) -> None:
        blocked = {
            "title": "中国股票市场分析",
            "url": "https://www.soundofhope.org/post/example",
            "snippet": "中国股票市场分析",
        }
        allowed = {
            "title": "中国股票市场分析",
            "url": "https://www.reuters.com/world/china/example",
            "snippet": "中国股票市场分析",
        }
        raw = {"details": {"results": [blocked, allowed]}}

        with (
            patch.object(openclaw_gateway, "invoke_tool", new=AsyncMock(return_value=raw)),
            patch.object(
                merrick_main,
                "fallback_public_search_results",
                new=AsyncMock(return_value=[]),
            ),
        ):
            results = await self.session.find_intelligence_search_results(
                "中国股票市场分析"
            )

        self.assertEqual(results, [allowed])

    async def test_chinese_newspaper_filter_survives_an_english_planner_query(self) -> None:
        blocked = {
            "title": "OpenAI market analysis",
            "url": "https://www.epochtimes.com/technology/example",
            "snippet": "OpenAI market news",
        }
        allowed = {
            "title": "OpenAI market analysis",
            "url": "https://openai.com/news/example",
            "snippet": "OpenAI market news",
        }
        raw = {"details": {"results": [blocked, allowed]}}

        with (
            patch.object(openclaw_gateway, "invoke_tool", new=AsyncMock(return_value=raw)),
            patch.object(
                merrick_main,
                "fallback_public_search_results",
                new=AsyncMock(return_value=[]),
            ),
        ):
            results = await self.session.find_intelligence_search_results(
                "OpenAI market news",
                policy_context="每天用中文搜索 OpenAI 市场新闻",
            )

        self.assertEqual(results, [allowed])

    async def test_contextual_research_expands_only_a_public_topic(self) -> None:
        self.assertEqual(
            merrick_main.contextual_public_research_query(
                "research its limitations", "OpenClaw architecture"
            ),
            "OpenClaw architecture limitations",
        )
        self.assertEqual(
            merrick_main.contextual_public_research_query(
                "research its limitations", "my confidential client roadmap"
            ),
            "its limitations",
        )

    async def test_native_action_reports_already_open_as_focused(self) -> None:
        action = {"type": "open_app", "app": "safari"}
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "focused", "detail": "Application focused."}
        )
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan("Open Safari", [action])

        self.session.perform_native_action.assert_awaited_once_with(action)  # type: ignore[attr-defined]
        self.session.send_local_spoken_notice.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Safari is in front."
        )

    async def test_browser_search_is_remembered_for_followup_analysis(self) -> None:
        action = {
            "type": "browser_search",
            "browser": "chrome",
            "query": "OpenClaw release notes",
        }
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "opened", "detail": "Search opened."}
        )
        self.session.deep_research_last_search = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan("Search Chrome for OpenClaw release notes", [action])

        self.assertEqual(self.session.last_public_search_query, "OpenClaw release notes")
        self.assertEqual(self.session.last_search_browser, "chrome")
        self.assertEqual(self.session.last_public_search_results, [])

    async def test_action_executor_rechecks_a_blocked_chinese_search_query(self) -> None:
        action = {
            "type": "browser_search",
            "browser": "chrome",
            "query": "法轮大法新闻",
        }
        self.session.perform_native_action = AsyncMock()  # type: ignore[method-assign]
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan("搜索法轮大法新闻", [action])

        self.session.perform_native_action.assert_not_awaited()  # type: ignore[attr-defined]
        self.session.send_local_spoken_notice.assert_awaited_once_with(  # type: ignore[attr-defined]
            "该主题已被您的中文搜索过滤器拦截。"
        )

    async def test_travel_refinement_keeps_the_original_research_goal(self) -> None:
        self.session.last_public_search_query = (
            "hotels in London for next Sunday under £20"
        )
        self.session.last_research_goal = (
            "Find hotels in London for next Sunday under £20 and compare them."
        )
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "opened", "detail": "Search opened."}
        )
        self.session.deep_research_last_search = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )

        await self.session.execute_action_plan(
            "Sorry, make the budget £200 and prioritise ratings above 8.",
            [{
                "type": "browser_search",
                "browser": "chrome",
                "query": (
                    "hotels in London for next Sunday budget £200 "
                    "prioritise ratings above 8"
                ),
            }],
        )

        self.assertEqual(
            self.session.last_research_goal,
            (
                "Find hotels in London for next Sunday under £20 and compare them. "
                "Updated requirements: Sorry, make the budget £200 and prioritise "
                "ratings above 8."
            ),
        )

    def test_weather_topic_switch_is_not_merged_into_previous_hotel_search(self) -> None:
        previous = "hotels in London next Friday budget 200 pounds"

        refined = merrick_main.travel_search_refinement_query(
            previous,
            "Hi Merrick, how is the weather today?",
        )

        self.assertIsNone(refined)

    async def test_browser_search_can_analyze_its_results_in_one_request(self) -> None:
        action = {
            "type": "browser_search",
            "browser": "chrome",
            "query": "OpenClaw release notes",
        }
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "opened", "detail": "Search opened."}
        )
        self.session.deep_research_last_search = AsyncMock(  # type: ignore[method-assign]
            return_value=True
        )

        await self.session.execute_action_plan(
            "Search OpenClaw release notes in Chrome and analyse the results",
            [action],
        )

        self.session.deep_research_last_search.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Search OpenClaw release notes in Chrome and analyse the results"
        )

    async def test_browser_search_keeps_its_success_when_deep_read_is_unavailable(self) -> None:
        action = {
            "type": "browser_search",
            "browser": "chrome",
            "query": "OpenClaw release notes",
        }
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            return_value={"status": "opened", "detail": "Search opened."}
        )
        self.session.deep_research_last_search = AsyncMock(  # type: ignore[method-assign]
            side_effect=RuntimeError("Search provider rate limited the request")
        )
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan(
            "Search OpenClaw release notes in Chrome and analyse the results",
            [action],
        )

        self.session.send_local_spoken_notice.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Search opened in Chrome. I couldn't read the source pages."
        )

    async def test_followup_analyzes_the_previous_search_without_repeating_query(self) -> None:
        self.session.last_public_search_query = "OpenClaw release notes"
        self.session.deep_research_last_search = AsyncMock()  # type: ignore[method-assign]

        handled = await self.session.handle_search_followup("Analyze those search results")

        self.assertTrue(handled)
        self.session.deep_research_last_search.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Analyze those search results"
        )

    async def test_deep_research_opens_distinct_sources_and_sends_cross_source_context(self) -> None:
        self.session.last_public_search_query = "OpenClaw release notes"
        self.session.last_research_goal = "Compare the release notes with independent reviews."
        self.session.last_public_search_results = [
            {"title": "Official overview", "url": "https://openclaw.example/overview", "snippet": "A"},
            {"title": "Official release notes", "url": "https://openclaw.example/releases", "snippet": "B"},
            {"title": "Independent review", "url": "https://review.example/openclaw", "snippet": "C"},
            {"title": "Project source", "url": "https://github.example/openclaw", "snippet": "D"},
        ]
        self.session.open_research_pages = AsyncMock()  # type: ignore[method-assign]
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]
        pages = {
            "https://openclaw.example/overview": {"title": "Official overview", "url": "https://openclaw.example/overview", "text": "Official details"},
            "https://review.example/openclaw": {"title": "Independent review", "url": "https://review.example/openclaw", "text": "Independent details"},
            "https://github.example/openclaw": {"title": "Project source", "url": "https://github.example/openclaw", "text": "Source details"},
        }
        with patch.object(
            openclaw_gateway,
            "invoke_bounded_read_page",
            new=AsyncMock(side_effect=lambda url: pages[url]),
        ):
            await self.session.deep_research_last_search(
                "Search OpenClaw release notes and analyse the results"
            )

        self.session.open_research_pages.assert_awaited_once_with(  # type: ignore[attr-defined]
            [
                "https://openclaw.example/overview",
                "https://review.example/openclaw",
                "https://github.example/openclaw",
            ]
        )
        context = self.session.run_query.await_args.kwargs["research_context"]  # type: ignore[attr-defined]
        self.assertEqual(context["kind"], "public_multi_page")
        self.assertEqual(len(context["pages"]), 3)
        self.assertEqual(context["research_brief"]["topic"], "OpenClaw release notes")
        self.assertIn("Compare the release notes", context["research_brief"]["original_goal"])
        self.assertEqual(self.session.last_opened_result_url, "https://openclaw.example/overview")

    async def test_official_only_research_never_opens_unofficial_source_pages(self) -> None:
        self.session.last_public_search_query = "OpenAI GPT-5.5 model information"
        self.session.last_research_goal = (
            "搜索并分析 OpenAI 官方网站上 GPT-5.5 的最新模型说明，只打开官方来源"
        )
        official = {
            "title": "Introducing GPT-5.5",
            "url": "https://openai.com/index/introducing-gpt-5-5/",
            "snippet": "Official release details",
        }
        unofficial = {
            "title": "OpenAI GPT-5.5 技术深度报告",
            "url": "https://jishuzhan.net/article/example",
            "snippet": "Third-party analysis",
        }
        self.session.last_public_search_results = [unofficial, official]
        self.session.open_research_pages = AsyncMock()  # type: ignore[method-assign]
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        with patch.object(
            openclaw_gateway,
            "invoke_bounded_read_page",
            new=AsyncMock(return_value={
                "title": official["title"],
                "url": official["url"],
                "text": "Official model information",
            }),
        ) as read_page:
            await self.session.deep_research_last_search(self.session.last_research_goal)

        self.session.open_research_pages.assert_awaited_once_with([official["url"]])  # type: ignore[attr-defined]
        read_page.assert_awaited_once_with(official["url"])
        context = self.session.run_query.await_args.kwargs["research_context"]  # type: ignore[attr-defined]
        self.assertEqual(context["search_results"], [official])

    async def test_chinese_research_never_displays_opens_or_reads_blocked_media(self) -> None:
        blocked = {
            "title": "Global markets update",
            "url": "https://www.epochtimes.com/markets/example",
            "snippet": "Market coverage",
        }
        allowed = {
            "title": "中国市场分析",
            "url": "https://www.reuters.com/world/china/example",
            "snippet": "独立市场报道",
        }
        self.session.last_public_search_query = "中国市场新闻"
        self.session.last_public_search_results = [blocked, allowed]
        self.session.open_research_pages = AsyncMock()  # type: ignore[method-assign]
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        with patch.object(
            openclaw_gateway,
            "invoke_bounded_read_page",
            new=AsyncMock(return_value={
                "title": allowed["title"],
                "url": allowed["url"],
                "text": "Independent market details",
            }),
        ) as read_page:
            await self.session.deep_research_last_search("分析这些搜索结果")

        self.session.open_research_pages.assert_awaited_once_with(  # type: ignore[attr-defined]
            [allowed["url"]]
        )
        read_page.assert_awaited_once_with(allowed["url"])
        source_messages = [
            message for message in self.ws.messages
            if message.get("type") == "research_sources"
        ]
        self.assertEqual(source_messages[0]["sources"], [allowed])
        context = self.session.run_query.await_args.kwargs["research_context"]  # type: ignore[attr-defined]
        self.assertEqual(context["search_results"], [allowed])

    async def test_chinese_research_page_opening_rechecks_blocked_domains(self) -> None:
        self.session.last_public_search_query = "中国市场新闻"

        await self.session.open_research_pages([
            "https://www.epochtimes.com/markets/example",
            "https://www.reuters.com/world/china/example",
        ])

        open_messages = [
            message for message in self.ws.messages
            if message.get("type") == "research_open_pages"
        ]
        self.assertEqual(open_messages, [{
            "type": "research_open_pages",
            "urls": ["https://www.reuters.com/world/china/example"],
        }])

    async def test_page_open_filter_follows_a_chinese_command_with_english_terms(self) -> None:
        self.session.last_public_search_query = "OpenAI news"
        self.session.last_research_goal = "搜索 OpenAI news"

        await self.session.open_research_pages([
            "https://www.ntdtv.com/technology/example",
            "https://openai.com/news/example",
        ])

        open_messages = [
            message for message in self.ws.messages
            if message.get("type") == "research_open_pages"
        ]
        self.assertEqual(open_messages[0]["urls"], ["https://openai.com/news/example"])

    async def test_followup_opens_and_explains_a_selected_result(self) -> None:
        selected = {
            "title": "Official release notes",
            "url": "https://example.com/releases",
            "snippet": "Recent changes",
        }
        self.session.last_public_search_query = "OpenClaw release notes"
        self.session.last_public_search_results = [
            {"title": "Overview", "url": "https://example.com/", "snippet": ""},
            selected,
        ]
        self.session.explain_public_result_page = AsyncMock()  # type: ignore[method-assign]
        self.session.open_search_result_in_browser = AsyncMock()  # type: ignore[method-assign]
        handled = await self.session.handle_search_followup(
            "Open the second result and explain it"
        )

        self.assertTrue(handled)
        self.session.open_search_result_in_browser.assert_awaited_once_with(  # type: ignore[attr-defined]
            selected["url"]
        )
        self.session.explain_public_result_page.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Open the second result and explain it",
            selected["url"],
        )
        self.assertEqual(self.session.last_opened_result_url, selected["url"])

    async def test_followup_opens_the_relevant_result_in_the_search_browser(self) -> None:
        selected = {
            "title": "Official release notes",
            "url": "https://example.com/releases",
            "snippet": "Recent changes",
        }
        self.session.last_public_search_query = "OpenClaw release notes"
        self.session.last_search_browser = "chrome"
        self.session.last_public_search_results = [selected]
        self.session.open_search_result_in_browser = AsyncMock()  # type: ignore[method-assign]
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        handled = await self.session.handle_search_followup("Open the relevant webpage")

        self.assertTrue(handled)
        self.session.open_search_result_in_browser.assert_awaited_once_with(  # type: ignore[attr-defined]
            selected["url"]
        )

    async def test_followup_reads_the_last_opened_result_page(self) -> None:
        self.session.last_public_search_query = "OpenClaw release notes"
        self.session.last_opened_result_url = "https://example.com/releases"
        self.session.explain_public_result_page = AsyncMock()  # type: ignore[method-assign]

        handled = await self.session.handle_search_followup("Explain this page")

        self.assertTrue(handled)
        self.session.explain_public_result_page.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Explain this page",
            "https://example.com/releases",
        )

    async def test_selected_public_page_text_is_passed_to_isolated_researcher(self) -> None:
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "invoke_bounded_read_page",
            new=AsyncMock(return_value={
                "title": "Official release notes",
                "url": "https://example.com/releases",
                "text": "Version 2 adds realtime search follow-ups.",
            }),
        ):
            await self.session.explain_public_result_page(
                "Explain this page",
                "https://example.com/releases",
            )

        self.session.run_query.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Explain this page",
            is_draft=False,
            force_screen=False,
            agent_id="researcher",
            host_action=True,
            research_context={
                "kind": "public_page",
                "url": "https://example.com/releases",
                "title": "Official release notes",
                "text": "Version 2 adds realtime search follow-ups.",
            },
        )

    async def test_screen_plan_routes_directly_to_isolated_reader(self) -> None:
        self.session.run_query = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan(
            "Read the current document on my screen",
            [{"type": "inspect_current_view"}],
        )

        self.session.run_query.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Read the current document on my screen",
            is_draft=False,
            force_screen=True,
            agent_id="screen-reader",
            host_action=True,
            research_context=None,
        )

    async def test_research_plan_routes_directly_to_isolated_researcher(self) -> None:
        self.session.deep_research_last_search = AsyncMock(return_value=True)  # type: ignore[method-assign]

        await self.session.execute_action_plan(
            "Research current OpenClaw security",
            [{"type": "web_research", "query": "OpenClaw security"}],
        )

        self.session.deep_research_last_search.assert_awaited_once_with(  # type: ignore[attr-defined]
            "Research current OpenClaw security"
        )

    async def test_research_fallback_requests_twelve_candidates(self) -> None:
        search_result = {
            "results": [{"title": "Official docs", "url": "https://example.com", "snippet": "Primary source."}],
        }
        with patch.object(
            merrick_main,
            "fallback_public_search_results",
            new=AsyncMock(return_value=[]),
        ), patch.object(
            openclaw_gateway,
            "invoke_tool",
            new=AsyncMock(return_value=search_result),
        ) as invoke_tool:
            results = await self.session.find_public_search_results("OpenClaw security")

        self.assertEqual(results[0]["url"], "https://example.com")
        invoke_tool.assert_awaited_once_with(
            "web_search",
            {"query": "OpenClaw security", "count": 12, "safeSearch": "moderate"},
            agent_id="research-executor",
        )

    async def test_public_page_uses_bounded_capability_executor(self) -> None:
        action = {"type": "open_web_page", "url": "https://example.com"}
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]
        with patch.object(
            openclaw_gateway,
            "invoke_bounded_web_page",
            new=AsyncMock(return_value={}),
        ) as invoke_page:
            await self.session.execute_action_plan("Open https://example.com", [action])

        invoke_page.assert_awaited_once_with(action)

    async def test_step_results_keep_request_order(self) -> None:
        actions = [
            {"type": "open_app", "app": "notes"},
            {"type": "open_app", "app": "spotify"},
        ]
        self.session.perform_native_action = AsyncMock(  # type: ignore[method-assign]
            side_effect=[
                RuntimeError("The approved application is not installed."),
                {"status": "opened", "detail": "Application opened."},
            ]
        )
        self.session.send_local_spoken_notice = AsyncMock()  # type: ignore[method-assign]

        await self.session.execute_action_plan("Open Notes and Spotify", actions)

        self.session.send_local_spoken_notice.assert_awaited_once_with(  # type: ignore[attr-defined]
            "I couldn't open Notes. Spotify is open."
        )


class NativeActionLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.ws = FakeWebSocket()
        self.session = Session(self.ws)  # type: ignore[arg-type]
        self.session.tts_enabled = False

    async def _start_action(self, action: dict) -> asyncio.Task:
        task = asyncio.create_task(self.session.perform_native_action(action))
        await asyncio.sleep(0)
        return task

    async def test_matching_result_completes_waiter(self) -> None:
        task = await self._start_action({"type": "open_app", "app": "chrome"})
        request_id = self.session.native_action_request_id
        await self.session.handle_message({
            "type": "native_action_result",
            "request_id": request_id,
            "ok": True,
            "result": {"status": "focused", "detail": "Application focused."},
            "error": "",
        })
        self.assertEqual(
            await task,
            {"status": "focused", "detail": "Application focused."},
        )

    async def test_wrong_request_id_is_ignored_before_valid_result(self) -> None:
        task = await self._start_action({"type": "open_app", "app": "chrome"})
        request_id = self.session.native_action_request_id
        await self.session.handle_message({
            "type": "native_action_result",
            "request_id": "f" * 32,
            "ok": True,
            "result": {"status": "focused", "detail": "Application focused."},
            "error": "",
        })
        self.assertFalse(task.done())
        await self.session.handle_message({
            "type": "native_action_result",
            "request_id": request_id,
            "ok": True,
            "result": {"status": "focused", "detail": "Application focused."},
            "error": "",
        })
        await task

    async def test_invalid_or_action_incompatible_result_fails_closed(self) -> None:
        task = await self._start_action({
            "type": "media_control",
            "player": "spotify",
            "action": "pause",
        })
        await self.session.handle_message({
            "type": "native_action_result",
            "request_id": self.session.native_action_request_id,
            "ok": True,
            "result": {"status": "opened", "detail": "Wrong status."},
            "error": "",
        })
        with self.assertRaisesRegex(RuntimeError, "invalid result"):
            await task

    async def test_timeout_sends_host_cancel_and_clears_waiter(self) -> None:
        with patch.object(merrick_main, "NATIVE_ACTION_TIMEOUT_SECONDS", 0.01):
            with self.assertRaisesRegex(RuntimeError, "did not return"):
                await self.session.perform_native_action(
                    {"type": "open_app", "app": "chrome"}
                )
        requests = [
            message
            for message in self.ws.messages
            if message.get("type") in {"native_action_request", "native_action_cancel"}
        ]
        self.assertEqual(
            [message["type"] for message in requests],
            ["native_action_request", "native_action_cancel"],
        )
        self.assertEqual(requests[0]["request_id"], requests[1]["request_id"])
        self.assertIsNone(self.session.native_action_waiter)

    async def test_interrupt_cancels_native_host_action(self) -> None:
        task = await self._start_action({"type": "open_app", "app": "chrome"})
        self.session.query_task = task
        request_id = self.session.native_action_request_id

        await self.session.handle_message({"type": "interrupt"})
        await asyncio.sleep(0)

        self.assertTrue(task.cancelled())
        self.assertIn(
            {"type": "native_action_cancel", "request_id": request_id},
            self.ws.messages,
        )


if __name__ == "__main__":
    unittest.main()
