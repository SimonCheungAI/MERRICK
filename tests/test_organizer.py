from __future__ import annotations

import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "server"))

from organizer import OrganizerStore, parse_local_datetime, parse_organizer_command  # noqa: E402


LONDON_SUMMER = timezone(timedelta(hours=1))
NOW = datetime(2026, 8, 22, 16, 30, tzinfo=LONDON_SUMMER)


class OrganizerTests(unittest.TestCase):
    def test_native_notification_backup_and_dashboard_wiring(self) -> None:
        swift = (PROJECT_ROOT / "desktop" / "MerrickApp.swift").read_text(encoding="utf-8")
        build = (PROJECT_ROOT / "scripts" / "build-macos-app.sh").read_text(encoding="utf-8")
        backup = (PROJECT_ROOT / "scripts" / "backup-merrick-memory.sh").read_text(encoding="utf-8")
        html = (PROJECT_ROOT / "web" / "index.html").read_text(encoding="utf-8")
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("import UserNotifications", swift)
        self.assertIn('case "scheduleLocalNotification"', swift)
        self.assertIn("-framework UserNotifications", build)
        self.assertIn("jarvis-organizer.db", backup)
        self.assertIn('id="organizer-panel"', html)
        self.assertIn('id="organizer-page-intelligence"', html)
        self.assertIn('id="organizer-page-journal"', html)
        self.assertIn('case "meeting_summary_ready"', frontend)
        self.assertIn('type: "organizer_update_briefing"', frontend)
        self.assertIn('type: "organizer_create_intelligence"', frontend)

    def test_briefing_frontend_uses_responsive_editorial_html(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        styles = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")

        self.assertIn('organizerNode("article", `briefing-newspaper', frontend)
        self.assertIn('organizerNode("figure", "briefing-data-figure")', frontend)
        self.assertIn('art.setAttribute("role", "img")', frontend)
        self.assertIn("briefing-analysis-panel", frontend)
        self.assertIn(".briefing-editorial-grid", styles)
        self.assertIn(".briefing-metrics { grid-template-columns: repeat(2", styles)

    def test_intelligence_delete_uses_an_inline_confirmation_in_native_webview(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        styles = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")

        self.assertNotIn("window.confirm(oc(\"intelligenceConfirmDelete\"))", frontend)
        self.assertIn('"intelligence-delete-confirm"', frontend)
        self.assertIn('type: "organizer_delete_intelligence"', frontend)
        self.assertIn(".intelligence-delete-confirm", styles)

    def test_intelligence_editor_is_labelled_focused_and_scrolled_into_view(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn('title.setAttribute("aria-label", t("intelligence_title"))', frontend)
        self.assertIn('prompt.setAttribute("aria-label", t("intelligence_goal"))', frontend)
        self.assertIn('editor.scrollIntoView({ behavior: "smooth", block: "nearest" })', frontend)
        self.assertIn("title.focus({ preventScroll: true })", frontend)

    def test_space_voice_shortcut_does_not_intercept_forms_or_ime_input(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function shouldStartListeningFromSpace(event)", frontend)
        self.assertIn("event.isComposing", frontend)
        self.assertIn("target.closest(SPACE_SHORTCUT_INTERACTIVE_SELECTOR)", frontend)
        self.assertIn('[contenteditable]:not([contenteditable="false"])', frontend)
        self.assertNotIn("document.activeElement !== textInput", frontend)

    def test_organizer_pointer_click_explicitly_focuses_editable_controls(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")

        self.assertIn("function focusOrganizerEditableFromPointer(event)", frontend)
        self.assertIn("editable.focus({ preventScroll: true })", frontend)
        self.assertIn("event.stopPropagation()", frontend)
        self.assertIn(
            'organizerPanel?.addEventListener("pointerdown", focusOrganizerEditableFromPointer)',
            frontend,
        )

    def test_bilingual_commands_and_reminder_times_are_deterministic(self) -> None:
        chinese = parse_organizer_command("MERRICK，明早九点提醒我提交周报", now=NOW)
        self.assertIsNotNone(chinese)
        self.assertEqual(chinese.kind, "create_reminder")
        self.assertEqual(chinese.payload["title"], "提交周报")
        self.assertEqual(
            datetime.fromisoformat(chinese.payload["fire_at"]),
            datetime(2026, 8, 23, 9, 0, tzinfo=LONDON_SUMMER),
        )

        english = parse_organizer_command(
            "Remind me tomorrow at 9 a.m. to submit the weekly report", now=NOW
        )
        self.assertIsNotNone(english)
        self.assertEqual(english.kind, "create_reminder")
        self.assertEqual(english.payload["title"], "submit the weekly report")

        self.assertEqual(
            parse_local_datetime("2026-08-25 at 9", now=NOW),
            datetime(2026, 8, 25, 9, 0, tzinfo=LONDON_SUMMER),
        )
        self.assertEqual(
            parse_local_datetime("Remind me at 18:00", now=NOW),
            datetime(2026, 8, 22, 18, 0, tzinfo=LONDON_SUMMER),
        )
        london = ZoneInfo("Europe/London")
        before_dst_change = datetime(2026, 10, 24, 20, 0, tzinfo=london)
        self.assertEqual(
            parse_local_datetime("tomorrow at 9 a.m.", now=before_dst_change),
            datetime(2026, 10, 25, 9, 0, tzinfo=london),
        )
        self.assertEqual(parse_organizer_command("新建项目叫产品发布").kind, "create_project")
        self.assertEqual(
            parse_organizer_command("Create a project called Product launch").kind,
            "create_project",
        )
        self.assertEqual(parse_organizer_command("完成任务提交周报").kind, "complete_task")
        self.assertIsNone(parse_organizer_command("这个工作什么时候完成"))

        newspaper = parse_organizer_command(
            "Create a daily morning newspaper about agent design at 10 a.m.", now=NOW
        )
        self.assertIsNotNone(newspaper)
        self.assertEqual(newspaper.kind, "create_intelligence")
        self.assertTrue(newspaper.payload["enabled"])
        self.assertEqual(newspaper.payload["local_time"], "10:00")
        self.assertTrue(newspaper.payload["generate_now"])

        chinese_newspaper = parse_organizer_command("给我做一份关于人工智能代理的报纸", now=NOW)
        self.assertIsNotNone(chinese_newspaper)
        self.assertEqual(chinese_newspaper.kind, "create_intelligence")
        self.assertFalse(chinese_newspaper.payload["enabled"])

        for phrase in (
            "Please mark the task Prepare test data as done",
            "I've finished the task Prepare test data",
            "Prepare test data is done",
            "把准备测试数据这个任务搞定了",
            "麻烦完成一下任务准备测试数据",
        ):
            with self.subTest(phrase=phrase):
                command = parse_organizer_command(phrase)
                self.assertIsNotNone(command)
                self.assertEqual(command.kind, "complete_task")

        natural_create = parse_organizer_command(
            "Put prepare test data on my task list"
        )
        self.assertEqual(natural_create.kind, "create_task")
        self.assertEqual(natural_create.payload["title"], "prepare test data")

    def test_natural_chinese_work_done_statement_completes_the_named_task(self) -> None:
        command = parse_organizer_command("检查生命周期这项工作已经做好了")

        self.assertIsNotNone(command)
        self.assertEqual(command.kind, "complete_task")
        self.assertEqual(command.payload["title"], "检查生命周期")

    def test_natural_dashboard_requests_stay_inside_jarvis(self) -> None:
        for phrase in (
            "Can you open the Assistant Dashboard",
            "Please bring up my personal assistant panel.",
            "I'd like to view my task list",
            "打开 Assistant Dashboard",
            "帮我打开个人助理工作台",
            "能不能调出我的提醒列表",
        ):
            with self.subTest(phrase=phrase):
                command = parse_organizer_command(phrase)
                self.assertIsNotNone(command)
                self.assertEqual(command.kind, "show_dashboard")

        for discussion in (
            "How do I open the Assistant Dashboard?",
            "Don't open the assistant dashboard",
            "Write a Personal Assistant assessment report for the Display.",
            "如何打开个人助理工作台",
            "不要打开任务列表",
            "生成一份个人助理评估报告并美观展示。",
        ):
            with self.subTest(discussion=discussion):
                self.assertIsNone(parse_organizer_command(discussion))

    def test_project_rename_and_archive_commands_are_bilingual(self) -> None:
        cases = {
            "Rename project Merrick test to Personal OS": ("rename_project", "Merrick test", "Personal OS"),
            "把项目 Merrick test 改名为个人中枢": ("rename_project", "Merrick test", "个人中枢"),
            "Archive project Personal OS": ("archive_project", "Personal OS", None),
            "删除项目个人中枢": ("archive_project", "个人中枢", None),
        }
        for phrase, expected in cases.items():
            with self.subTest(phrase=phrase):
                command = parse_organizer_command(phrase)
                self.assertIsNotNone(command)
                self.assertEqual(command.kind, expected[0])
                self.assertEqual(command.payload["title"], expected[1])
                if expected[2] is not None:
                    self.assertEqual(command.payload["new_title"], expected[2])

    def test_project_archive_preserves_tasks_and_can_be_recreated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            project = store.create_project("Merrick test")
            task = store.create_task("Keep this task", project_title=project["title"])

            renamed = store.rename_project(project["id"], "Personal OS")
            self.assertEqual(renamed["title"], "Personal OS")
            archived = store.archive_project(project["id"])
            self.assertEqual(archived["status"], "archived")
            self.assertEqual(archived["detached_tasks"], 1)

            snapshot = store.snapshot()
            saved_task = next(item for item in snapshot["tasks"] if item["id"] == task["id"])
            self.assertIsNone(saved_task["project_id"])
            self.assertIsNone(saved_task["project_title"])
            self.assertFalse(any(item["status"] == "active" for item in snapshot["projects"]))

            restored = store.create_project("Personal OS")
            self.assertEqual(restored["id"], project["id"])
            self.assertEqual(restored["status"], "active")

    def test_projects_tasks_reminders_and_completion_are_structured(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            store.initialise()
            self.assertEqual(stat.S_IMODE(store.path.stat().st_mode), 0o600)

            project = store.create_project("Product launch")
            task = store.create_task(
                "Confirm venue",
                project_title=project["title"],
                due_at=(NOW + timedelta(days=1)).isoformat(),
            )
            reminder = store.create_reminder(
                task["title"], task["due_at"], task_id=task["id"]
            )

            snapshot = store.snapshot(now=NOW)
            self.assertEqual(snapshot["stats"]["open_tasks"], 1)
            self.assertEqual(snapshot["projects"][0]["open_tasks"], 1)
            self.assertEqual(snapshot["reminders"][0]["notification_state"], "pending")
            self.assertEqual(store.pending_reminders(now=NOW)[0]["id"], reminder["id"])
            store.update_notification_state(reminder["id"], ok=True)
            self.assertEqual(
                store.pending_reminders(now=datetime.fromisoformat(reminder["fire_at"]) + timedelta(seconds=1)),
                [],
            )
            self.assertEqual(store.snapshot(now=NOW)["reminders"][0]["status"], "delivered")
            later_reminder = store.create_reminder(
                task["title"],
                (NOW + timedelta(days=2)).isoformat(),
                task_id=task["id"],
            )

            completed = store.complete_task(task["id"])
            self.assertIsNotNone(completed)
            self.assertEqual(completed["status"], "completed")
            self.assertEqual(
                store.cancelled_notification_ids_for_task(task["id"]),
                [later_reminder["id"]],
            )
            self.assertEqual(store.snapshot(now=NOW)["stats"]["completed_tasks"], 1)

    def test_exact_open_task_check_does_not_accept_partial_titles(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            task = store.create_task("Prepare test data")

            self.assertTrue(store.has_exact_open_task("prepare TEST data"))
            self.assertFalse(store.has_exact_open_task("test data"))
            store.complete_task(task["id"])
            self.assertFalse(store.has_exact_open_task("Prepare test data"))

    def test_spoken_task_title_resolver_handles_asr_variation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            task = store.create_task("Prepare test data")

            for spoken in (
                "prepare the test data",
                "prepared test data",
                "prepare test dat",
                "test data",
            ):
                with self.subTest(spoken=spoken):
                    result = store.resolve_open_task(spoken)
                    self.assertEqual(result["status"], "matched")
                    self.assertEqual(result["task"]["id"], task["id"])

            self.assertEqual(
                store.resolve_open_task("prepare production release")["status"],
                "not_found",
            )

    def test_spoken_task_title_resolver_asks_when_match_is_ambiguous(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            store.create_task("Prepare test data")
            store.create_task("Prepare test database")

            result = store.resolve_open_task("prepared test data")
            self.assertEqual(result["status"], "ambiguous")
            self.assertEqual(len(result["candidates"]), 2)

    def test_meeting_actions_require_confirmation_before_becoming_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            meeting = store.start_meeting(now=NOW)
            store.append_meeting_transcript(
                meeting["id"], "We decided to ship Friday.", recorded_at=NOW
            )
            store.finish_meeting(
                meeting["id"],
                summary="The team selected the release date.",
                decisions=["Ship on Friday."],
                action_items=[
                    {
                        "title": "Prepare release notes",
                        "owner": "Alex",
                        "due_text": "tomorrow at 9 a.m.",
                    },
                    {"title": "Run the final checks", "owner": "Sam", "due_text": ""},
                ],
                now=NOW,
            )

            review = store.snapshot(now=NOW)["meetings"][0]
            self.assertEqual(review["status"], "review")
            self.assertEqual(review["transcript_count"], 1)
            self.assertEqual(
                [item["status"] for item in review["action_items"]],
                ["proposed", "proposed"],
            )
            self.assertEqual(store.snapshot(now=NOW)["stats"]["open_tasks"], 0)

            self.assertEqual(store.confirm_meeting_actions(meeting["id"], []), [])
            created = store.confirm_meeting_actions(meeting["id"], [0])
            self.assertEqual([task["title"] for task in created], ["Prepare release notes"])
            self.assertEqual(store.snapshot(now=NOW)["meetings"][0]["status"], "review")

            remaining = store.confirm_meeting_actions(meeting["id"], None)
            self.assertEqual([task["title"] for task in remaining], ["Run the final checks"])
            self.assertEqual(
                store.snapshot(now=NOW)["meetings"][0]["status"], "completed"
            )

    def test_briefings_are_opt_in_scheduled_and_regenerable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            store.initialise()
            initial = store.snapshot(now=NOW)["briefing_settings"]
            self.assertTrue(all(not row["enabled"] for row in initial))

            store.create_task("Review launch plan", due_at=NOW.replace(hour=18).isoformat())
            setting = store.update_briefing_setting(
                "morning", enabled=True, local_time="08:00"
            )
            self.assertEqual(setting["enabled"], 1)
            self.assertEqual(store.due_briefing_kinds(now=NOW), ["morning"])

            briefing = store.generate_briefing("morning", now=NOW)
            self.assertEqual(briefing["content"]["metrics"]["primary"], 1)
            self.assertEqual(briefing["content"]["schema_version"], 2)
            self.assertEqual(
                briefing["content"]["publication"]["masthead"],
                "The Daily MERRICK",
            )
            self.assertEqual(briefing["content"]["visual"]["score"], 93)
            self.assertEqual(briefing["content"]["context"]["open_tasks"], 1)
            self.assertEqual(len(briefing["content"]["analysis"]["items"]), 3)
            self.assertEqual(
                briefing["content"]["sections"][0]["items"][0]["title"],
                "Review launch plan",
            )
            self.assertEqual(store.due_briefing_kinds(now=NOW), [])

            store.create_task("Second launch task", due_at=NOW.replace(hour=19).isoformat())
            refreshed = store.generate_briefing("morning", now=NOW, force=True)
            self.assertEqual(refreshed["id"], briefing["id"])
            self.assertEqual(refreshed["content"]["metrics"]["primary"], 2)

            disabled = store.update_briefing_setting("morning", enabled=False)
            self.assertEqual(disabled["enabled"], 0)

    def test_intelligence_subscriptions_keep_arbitrary_editorial_goals(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            prompt = (
                "Make a weekly field journal about urban pollinator ecology. "
                "Compare new research methods, disputed findings, and practical observations."
            )
            subscription = store.create_intelligence_subscription(
                title="Pollinator Field Journal",
                prompt=prompt,
                enabled=True,
                local_time="07:15",
            )
            self.assertEqual(subscription["prompt"], prompt)
            self.assertNotIn("ticker", subscription)
            self.assertEqual(
                [item["id"] for item in store.due_intelligence_subscriptions(now=NOW)],
                [subscription["id"]],
            )

            content = {
                "schema_version": 1,
                "headline": "Habitat edges become the week's central question",
                "stories": [{"title": "A field observation", "source_indices": [1]}],
            }
            edition = store.save_intelligence_edition(
                subscription["id"],
                title=content["headline"],
                content=content,
                sources=[{"title": "Ecology source", "url": "https://example.org/ecology"}],
                now=NOW,
            )
            self.assertEqual(edition["content"]["headline"], content["headline"])
            self.assertEqual(edition["sources"][0]["title"], "Ecology source")
            self.assertEqual(store.due_intelligence_subscriptions(now=NOW), [])

            updated = store.update_intelligence_subscription(
                subscription["id"],
                prompt="Build a comparative newspaper about fermentation cultures.",
                enabled=False,
            )
            self.assertIn("fermentation", updated["prompt"])
            self.assertEqual(updated["enabled"], 0)
            snapshot = store.snapshot(now=NOW)
            self.assertEqual(snapshot["intelligence_subscriptions"][0]["edition_count"], 1)
            self.assertEqual(snapshot["intelligence_editions"][0]["id"], edition["id"])

    def test_work_journal_aggregates_structured_events_by_calendar_day(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            project = store.create_project("Daily operations")
            task = store.create_task(
                "Prepare the test edition",
                project_title=project["title"],
                due_at=(NOW + timedelta(days=1)).isoformat(),
            )
            reminder = store.create_reminder(
                "Review the edition", (NOW + timedelta(hours=2)).isoformat(), task_id=task["id"]
            )
            meeting = store.start_meeting(title="Editorial review", now=NOW)
            connection = store._connect()
            try:
                with connection:
                    connection.execute(
                        "UPDATE tasks SET created_at=?, completed_at=?, status='completed' WHERE id=?",
                        (NOW.isoformat(), NOW.isoformat(), task["id"]),
                    )
                    connection.execute(
                        "UPDATE projects SET created_at=? WHERE id=?",
                        (NOW.isoformat(), project["id"]),
                    )
            finally:
                connection.close()

            day = next(item for item in store.work_journal_days(now=NOW) if item["date"] == "2026-08-22")
            self.assertEqual(day["created_tasks"][0]["title"], "Prepare the test edition")
            self.assertEqual(day["completed_tasks"][0]["id"], task["id"])
            self.assertEqual(day["reminders"][0]["id"], reminder["id"])
            self.assertEqual(day["meetings"][0]["id"], meeting["id"])
            self.assertGreaterEqual(day["metrics"]["activity"], 4)
            scheduled_day = next(
                item for item in store.work_journal_days(now=NOW) if item["date"] == "2026-08-23"
            )
            self.assertEqual(scheduled_day["scheduled_tasks"][0]["id"], task["id"])
            self.assertGreaterEqual(scheduled_day["metrics"]["activity"], 1)

    def test_open_task_and_pending_reminder_can_be_edited_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            store = OrganizerStore(Path(temporary))
            task = store.create_task("Prepare first draft", due_at=(NOW + timedelta(days=1)).isoformat())
            reminder = store.create_reminder(
                "Review first draft", (NOW + timedelta(hours=2)).isoformat(), task_id=task["id"]
            )

            updated_task = store.update_task(
                task["id"],
                title="Prepare revised draft",
                due_at=(NOW + timedelta(days=2)).isoformat(),
                due_at_provided=True,
            )
            self.assertEqual(updated_task["title"], "Prepare revised draft")
            self.assertEqual(
                datetime.fromisoformat(updated_task["due_at"]), NOW + timedelta(days=2)
            )
            self.assertEqual(store.snapshot()["reminders"][0]["fire_at"], reminder["fire_at"])

            updated_reminder = store.update_reminder(
                reminder["id"], fire_at=(NOW + timedelta(hours=4)).isoformat()
            )
            self.assertEqual(updated_reminder["notification_state"], "pending")
            self.assertEqual(
                datetime.fromisoformat(updated_reminder["fire_at"]), NOW + timedelta(hours=4)
            )

            cleared_due_time = store.update_task(
                task["id"], due_at=None, due_at_provided=True
            )
            self.assertIsNone(cleared_due_time["due_at"])
            store.complete_task(task["id"])
            self.assertIsNone(store.update_task(task["id"], title="Do not edit"))
            self.assertIsNone(store.update_reminder(reminder["id"], fire_at=(NOW + timedelta(hours=5)).isoformat()))

    def test_organizer_frontend_exposes_inline_task_and_reminder_editors(self) -> None:
        frontend = (PROJECT_ROOT / "web" / "app.js").read_text(encoding="utf-8")
        styles = (PROJECT_ROOT / "web" / "style.css").read_text(encoding="utf-8")

        self.assertIn('type: "organizer_update_task"', frontend)
        self.assertIn('type: "organizer_update_reminder"', frontend)
        self.assertIn('organizerDateTimeLocalValue', frontend)
        self.assertIn(".organizer-task-editor, .organizer-reminder-editor", styles)


if __name__ == "__main__":
    unittest.main()
