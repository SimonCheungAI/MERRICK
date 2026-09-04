import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

import main as merrick_main  # noqa: E402


class LongTermMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.memory_dir = Path(self.temp_dir.name)
        self.memory_file = self.memory_dir / "jarvis-memory.jsonl"
        self.preference_file = self.memory_dir / "jarvis-preferences.md"
        self.memory_file.write_text(
            "\n".join(
                json.dumps(row)
                for row in (
                    {
                        "user": "Please make the desktop assistant responsive during spoken interruptions.",
                        "assistant": "I will preserve barge-in while avoiding echo interruptions.",
                    },
                    {
                        "user": "Use a point-cloud interface instead of simple rings.",
                        "assistant": "The interface will use a denser point-cloud shell.",
                    },
                )
            ) + "\n",
            encoding="utf-8",
        )
        self.memory_dir.joinpath("jarvis-preferences.md").write_text(
            "# MERRICK preferences\n- 2026-07-13: Address preference: sir\n",
            encoding="utf-8",
        )
        self.memory_patch = patch.object(merrick_main, "_memory_directory", return_value=self.memory_dir)
        self.memory_patch.start()

    def tearDown(self) -> None:
        self.memory_patch.stop()
        self.temp_dir.cleanup()

    def test_ordinary_messages_do_not_load_long_term_memory(self) -> None:
        self.assertEqual(merrick_main.recall_long_term_context("Tell me a joke."), "")

    def test_fast_greeting_requires_a_short_final_utterance(self) -> None:
        started_at = 100.0
        self.assertTrue(merrick_main.is_fast_greeting(
            "Hi, Merrick", is_final=True, voice_started_at=started_at, now=101.2
        ))
        self.assertFalse(merrick_main.is_fast_greeting(
            "Hi, Merrick", is_final=False, voice_started_at=started_at, now=101.2
        ))
        self.assertFalse(merrick_main.is_fast_greeting(
            "Hi, Merrick", is_final=True, voice_started_at=started_at, now=103.0
        ))
        self.assertFalse(merrick_main.is_fast_greeting(
            "Hi, Merrick, open Chrome", is_final=True, voice_started_at=started_at, now=101.2
        ))

    def test_local_sqlite_memory_retrieves_a_related_old_topic(self) -> None:
        context = merrick_main.recall_long_term_context(
            "What did we decide about spoken interruptions earlier?"
        )
        self.assertIn("spoken interruptions", context)
        self.assertTrue(self.memory_dir.joinpath("jarvis-memory.db").is_file())

    def test_named_old_topic_is_recalled_without_a_memory_question(self) -> None:
        store = merrick_main._local_memory_store()
        store.record_episode(
            "We decided the Atlas rollout should begin with the London team.",
            "London will be the pilot and adoption will be reviewed after two weeks.",
        )
        store.record_episode(
            "Help me choose a birthday cake.",
            "Chocolate is the safer choice.",
        )
        request = "Let's continue the Atlas rollout with the next region."

        context = merrick_main.recall_episodic_continuity(request)

        self.assertFalse(merrick_main.LONG_TERM_RECALL_RE.search(request))
        self.assertIn("Atlas rollout", context)
        self.assertNotIn("birthday cake", context)

    def test_natural_status_question_reopens_a_lowercase_topic(self) -> None:
        store = merrick_main._local_memory_store()
        store.record_episode(
            "The kitchen renovation is waiting for the electrician.",
            "The cabinets are ready, but wiring must finish before installation.",
        )

        context = merrick_main.recall_episodic_continuity(
            "How is the kitchen renovation going?"
        )

        self.assertIn("kitchen renovation", context)

    def test_natural_chinese_status_question_reopens_an_old_topic(self) -> None:
        store = merrick_main._local_memory_store()
        store.record_episode(
            "厨房装修正在等电工完成线路。",
            "橱柜已经到位，布线结束后就能安装。",
        )

        context = merrick_main.recall_episodic_continuity(
            "厨房装修现在怎么样了？"
        )

        self.assertIn("厨房装修", context)

    def test_completed_turn_is_archived_in_a_local_calendar_day_note(self) -> None:
        store = merrick_main._local_memory_store()
        archive = store.append_daily_turn(
            "Please retain the exact project decision.",
            "I will retain that decision with its date.",
            when=datetime(2026, 8, 17, 14, 35, tzinfo=timezone.utc),
        )
        self.assertEqual(archive, self.memory_dir / "daily" / "2026-08-17.md")
        content = archive.read_text(encoding="utf-8")
        self.assertIn("MERRICK conversation — 2026-08-17", content)
        self.assertRegex(content, r"## \d{2}:35")
        self.assertIn("exact project decision", content)
        self.assertIn("retain that decision", content)

    def test_voice_gate_only_marks_explicit_memory_access_as_sensitive(self) -> None:
        self.assertTrue(merrick_main.is_memory_sensitive_request("What did we discuss earlier?"))
        self.assertTrue(merrick_main.is_memory_sensitive_request("Update my preference: concise replies."))
        self.assertTrue(merrick_main.is_memory_sensitive_request("Please call me captain."))
        self.assertFalse(merrick_main.is_memory_sensitive_request("Explain latency briefly."))

    def test_persona_and_recalled_memory_have_separate_silent_guidance(self) -> None:
        self.assertIn("British AI butler", merrick_main.MERRICK_PERSONA_PROMPT)
        self.assertIn("verified owner", merrick_main.identity_presentation_prompt(True))
        self.assertIn("unverified guest", merrick_main.identity_presentation_prompt(False))
        self.assertIn("silent behaviour constraints", merrick_main.MERRICK_PERSONA_PROMPT)
        self.assertNotIn("Remember his name permanently", merrick_main.SYSTEM_PROMPT)

    def test_persona_allows_warm_complete_conversation_without_becoming_verbose(self) -> None:
        self.assertIn("two to four natural spoken sentences", merrick_main.MERRICK_PERSONA_PROMPT)
        self.assertIn("80 to 130 English words", merrick_main.MERRICK_PERSONA_PROMPT)
        self.assertIn("thinking aloud", merrick_main.MERRICK_PERSONA_PROMPT)
        self.assertIn("日常问答默认用两到四句自然口语", merrick_main.MERRICK_PERSONA_PROMPT_ZH)
        self.assertIn("150 到 260 个汉字", merrick_main.MERRICK_PERSONA_PROMPT_ZH)
        self.assertIn("当用户在思考、犹豫", merrick_main.MERRICK_PERSONA_PROMPT_ZH)

    def test_persona_never_uses_a_retired_personal_name(self) -> None:
        workspace_policy = (PROJECT_ROOT / "openclaw" / "workspace" / "AGENTS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("Address the verified owner as sir", workspace_policy)
        self.assertNotIn("Address him naturally as\nAlice", workspace_policy)

    def test_old_topic_request_gets_only_relevant_history(self) -> None:
        context = merrick_main.recall_long_term_context(
            "What did we decide about spoken interruptions earlier?"
        )
        self.assertIn("spoken interruptions", context)
        self.assertNotIn("point-cloud interface", context)

    def test_local_recall_fallback_continues_without_announcing_the_memory_lookup(self) -> None:
        with patch.object(
            merrick_main,
            "recall_long_term_context",
            return_value=(
                "Relevant earlier conversation:\n"
                "User: We chose London for the Atlas pilot.\n"
                "MERRICK: Review adoption after two weeks before expanding."
            ),
        ):
            answer = merrick_main.local_recall_fallback(
                "Continue our previous plan.",
                is_owner=True,
            )

        self.assertEqual(answer, "Review adoption after two weeks before expanding.")
        self.assertNotIn("found", answer.casefold())
        self.assertNotIn("earlier discussion", answer.casefold())

    def test_general_history_request_falls_back_to_recent_turns(self) -> None:
        context = merrick_main.recall_long_term_context("What did we discuss earlier?")
        self.assertIn("point-cloud interface", context)

    def test_preference_question_reads_profile(self) -> None:
        context = merrick_main.recall_long_term_context("What are my preferences?")
        self.assertIn("Address preference: sir", context)

    def test_preference_question_returns_only_the_latest_active_result(self) -> None:
        store = merrick_main._local_memory_store()
        episode_id = store.record_episode(
            "I prefer concise replies.",
            "I will keep that in mind.",
        )
        store.consolidate_episode(int(episode_id))
        merrick_main.update_long_term_preferences(
            "From now on, keep replies detailed."
        )

        context = merrick_main.recall_long_term_context("What are my preferences?")

        self.assertIn("keep replies detailed", context)
        self.assertNotIn("concise replies", context)
        self.assertNotIn("Observed tendencies", context)
        self.assertNotIn("Relevant earlier conversation", context)

    def test_chinese_preference_question_returns_only_current_active_values(self) -> None:
        merrick_main.update_long_term_preferences(
            "From now on, use Chinese for replies."
        )

        context = merrick_main.recall_long_term_context("我现在的偏好是什么？")

        self.assertIn("Use Chinese for replies.", context)
        self.assertNotIn("Relevant earlier conversation", context)

    def test_preference_profile_is_compact_and_available_without_history_recall(self) -> None:
        profile = merrick_main.active_preference_context()
        self.assertIn("Address preference: sir", profile)
        self.assertLessEqual(len(profile), 700)

    def test_legacy_active_preferences_bootstrap_into_level_four_lifecycle(self) -> None:
        merrick_main._bootstrap_local_memory()

        records = merrick_main._local_memory_store().preference_lifecycle(
            "preference.address"
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], "active")
        self.assertEqual(records[0]["value"], "2026-07-13: Address preference: sir")

    def test_selected_chinese_conversation_drops_a_stale_english_language_preference(self) -> None:
        with patch.object(
            merrick_main,
            "_active_preference_values",
            return_value=[
                "Speak English in the composed British MERRICK style.",
                "Address the verified owner as sir. Use no personal name.",
                "Keep spoken answers concise unless the user asks for detail.",
            ],
        ):
            profile = merrick_main.active_preference_context("zh")

        self.assertNotIn("Speak English", profile)
        self.assertNotIn("Address the verified owner as sir", profile)
        self.assertIn("Keep spoken answers concise", profile)

    def test_explicit_preference_is_saved_and_address_is_replaced(self) -> None:
        merrick_main.update_long_term_preferences("From now on, call me captain.")
        saved = self.preference_file.read_text(encoding="utf-8")
        self.assertIn("Address preference: captain", saved)
        self.assertNotIn("Address preference: sir", saved)
        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]
        self.assertEqual(cards["preference.address"]["value"], "Address preference: captain")
        self.assertEqual(cards["preference.address"]["status"], "active")

    def test_natural_language_correction_replaces_the_current_preference(self) -> None:
        merrick_main.update_long_term_preferences("From now on, use English for replies.")
        merrick_main.update_long_term_preferences(
            "Actually, use Chinese rather than English for replies."
        )
        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]
        self.assertEqual(
            cards["preference.language"]["value"],
            "Use Chinese for replies.",
        )
        snapshot = self.preference_file.read_text(encoding="utf-8")
        self.assertIn("Use Chinese for replies.", snapshot)
        self.assertNotIn("English", snapshot)
        self.assertNotIn("rather than", snapshot)

    def test_explicit_preference_revisions_update_the_four_level_lifecycle(self) -> None:
        merrick_main.update_long_term_preferences(
            "From now on, keep replies concise."
        )
        merrick_main.update_long_term_preferences(
            "Change my response preference to detailed technical explanations."
        )

        records = merrick_main._local_memory_store().preference_lifecycle(
            "preference.response_style"
        )

        self.assertEqual(
            [record["value"] for record in records if record["stage"] == "active"],
            ["Use detailed explanations for technical questions."],
        )
        self.assertEqual(
            [record["value"] for record in records if record["stage"] == "superseded"],
            ["Keep replies concise."],
        )

        merrick_main.update_long_term_preferences("Forget response preference.")

        self.assertEqual(
            merrick_main._local_memory_store().preference_lifecycle(
                "preference.response_style"
            ),
            [],
        )

    def test_ordinary_like_is_not_written_as_an_active_preference(self) -> None:
        self.assertIsNone(merrick_main._preference_update("I love jazz and quiet cafés."))
        merrick_main.update_long_term_preferences("I love jazz and quiet cafés.")
        self.assertFalse(self.memory_dir.joinpath("jarvis-memory-cards.json").exists())

    def test_completed_turns_accumulate_implicit_preference_evidence(self) -> None:
        for index in range(3):
            merrick_main._consolidate_local_episode(
                "I prefer a concise response.",
                f"Acknowledgement {index}.",
            )

        records = merrick_main._local_memory_store().preference_lifecycle(
            "preference.response_style"
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], "proposed")
        self.assertEqual(records[0]["evidence_count"], 3)
        self.assertFalse(self.memory_dir.joinpath("jarvis-memory-cards.json").exists())

    def test_chinese_soft_preference_uses_the_same_candidate_lifecycle(self) -> None:
        for index in range(3):
            merrick_main._consolidate_local_episode(
                "我喜欢技术问题给出详细解释。",
                f"收到 {index}。",
            )

        records = merrick_main._local_memory_store().preference_lifecycle(
            "preference.response_style"
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["stage"], "proposed")
        self.assertFalse(self.memory_dir.joinpath("jarvis-memory-cards.json").exists())

    def test_chinese_explicit_correction_stores_only_the_latest_positive_result(self) -> None:
        changed = merrick_main.update_long_term_preferences(
            "以后技术问题请详细解释，不要简短。"
        )

        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]

        self.assertTrue(changed)
        self.assertEqual(
            cards["preference.response_style"]["value"],
            "技术问题使用详细解释。",
        )
        self.assertNotIn("不要简短", cards["preference.response_style"]["value"])

    def test_chinese_forget_removes_the_active_preference_lifecycle(self) -> None:
        merrick_main.update_long_term_preferences(
            "以后技术问题请详细解释，不要简短。"
        )

        changed = merrick_main.update_long_term_preferences("忘掉我的回答偏好。")
        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]

        self.assertTrue(changed)
        self.assertEqual(cards["preference.response_style"]["status"], "revoked")
        self.assertEqual(
            merrick_main._local_memory_store().preference_lifecycle(
                "preference.response_style"
            ),
            [],
        )

    def test_labeled_memory_can_be_revised_and_revoked_without_editing_history(self) -> None:
        merrick_main.update_long_term_preferences(
            "Remember show-spoilers: Do not discuss scenes after episode two."
        )
        merrick_main.update_long_term_preferences(
            "Revise show-spoilers: I have now finished episode three."
        )
        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]
        card_key = next(key for key in cards if key.startswith("fact."))
        self.assertEqual(cards[card_key]["value"], "I have now finished episode three")
        revisions = [
            json.loads(line)
            for line in self.memory_dir.joinpath("jarvis-memory-revisions.jsonl")
                .read_text(encoding="utf-8").splitlines()
        ]
        # The active revision file is intentionally compact: it retains only
        # the current value for each key, not superseded personal details.
        self.assertEqual([record["op"] for record in revisions[-1:]], ["set"])
        self.assertTrue(revisions[-1]["supersedes"])
        context = merrick_main.recall_long_term_context(
            "What did we decide earlier about show spoilers?"
        )
        self.assertIn("finished episode three", context)
        merrick_main.update_long_term_preferences("Forget show-spoilers memory.")
        cards = json.loads(
            self.memory_dir.joinpath("jarvis-memory-cards.json").read_text(encoding="utf-8")
        )["cards"]
        self.assertEqual(cards[card_key]["status"], "revoked")

    def test_transient_or_sensitive_requests_are_not_preferences(self) -> None:
        self.assertIsNone(merrick_main._preference_update("Please open Chrome now."))
        self.assertIsNone(merrick_main._preference_update("I prefer using my API key abc123."))

    def test_exit_backup_publishes_only_the_private_memory_snapshot(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        script = (PROJECT_ROOT / "scripts" / "backup-merrick-memory.sh").read_text(encoding="utf-8")
        self.assertIn("await self.publish_memory_backup()", source)
        self.assertIn('[str(MEMORY_BACKUP_SCRIPT), "--publish"]', source)
        self.assertIn("git -C \"$ROOT\" add -- backups/jarvis-memory", script)
        self.assertIn("JARVIS_MEMORY_BACKUP_REPOSITORY", script)
        self.assertIn("JARVIS_MEMORY_BACKUP_DESTINATION", script)
        self.assertIn("backup-updated-at.txt", script)
        self.assertIn("jarvis-memory.db", script)
        self.assertIn('"$SOURCE/meetings"', script)
        self.assertIn('"$SOURCE/daily"', script)
        self.assertIn("-print0", script)

    def test_meeting_transcripts_rotate_into_local_hour_files(self) -> None:
        source = (PROJECT_ROOT / "server" / "main.py").read_text(encoding="utf-8")
        self.assertIn('_memory_directory() / "meetings"', source)
        self.assertIn("strftime('%Y-%m-%d-%H')", source)
