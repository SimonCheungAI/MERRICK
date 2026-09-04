"""Execute the real uninstall cleanup block with fake OS process boundaries.

Never run the account/data removal half of the uninstaller in a test.
"""

from pathlib import Path
import json
import selectors
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/uninstall-merrick.sh"


class UninstallProcessOwnershipTests(unittest.TestCase):
    def run_cleanup(self, *, owned: bool = False, reused_after_term: bool = False,
                    changed_start: bool = False, wrong_config: bool = False,
                    unreadable: bool = False, argument_only: bool = False):
        with tempfile.TemporaryDirectory(prefix="merrick-uninstall-test-") as directory:
            root = Path(directory).resolve()
            app = root / "MERRICK.app"
            runtime = app / "Contents/Resources/runtime"
            state = root / "private-state"
            state.mkdir()
            (state / ".gateway-owner.json").write_text('{"pid":4242,"port":23456}')
            source = SCRIPT.read_text()
            cleanup = source[source.index("CURRENT_UID="):source.index("# Delete every credential")]
            cleanup = cleanup.replace('$HOME/Library/Application Support/JarvisStark/OpenClaw', str(state))
            for executable in ("/bin/ps", "/bin/kill", "/bin/sleep", "/usr/sbin/lsof"):
                cleanup = cleanup.replace(executable, "fake_" + Path(executable).name)
            signal_log = root / "signals"
            harness = f'''set -u
APP_PATH={shlex.quote(str(app))}
SIGKILL=9
signal_log={shlex.quote(str(signal_log))}
runtime={shlex.quote(str(runtime))}
state_dir={shlex.quote(str(state))}
owned={int(owned)}
reused_after_term={int(reused_after_term)}
changed_start={int(changed_start)}
wrong_config={int(wrong_config)}
unreadable={int(unreadable)}
argument_only={int(argument_only)}
fake_ps() {{
  case "$*" in
    *-axo*) (( argument_only )) && print -r -- "4242 $(/usr/bin/id -u) /usr/bin/tail $APP_PATH/Contents/notes.log"; return 0 ;;
    *lstart*)
      if (( changed_start )) && [[ -s "$signal_log" ]]; then
        print -r -- "Fri Sep 4 12:01:00 2026"
      else
        print -r -- "Fri Sep 4 12:00:00 2026"
      fi ;;
    *"uid="*"command="*)
      if (( argument_only )); then
        print -r -- "$(/usr/bin/id -u) /usr/bin/tail $APP_PATH/Contents/notes.log"
      else
        print -r -- "$(/usr/bin/id -u) openclaw-gateway"
      fi ;;
    *"uid="*) /usr/bin/id -u ;;
    *"command="*) print -r -- "openclaw-gateway" ;;
  esac
}}
fake_lsof() {{
  (( unreadable )) && return 1
  if (( wrong_config )); then
    print -rl -- "p4242" "fcwd" "n$runtime" "ftxt" "n$runtime/node/bin/node" "f22" "n/tmp/independent-openclaw/openclaw.json"
    return 0
  fi
  if (( owned )) && ! {{ (( reused_after_term )) && [[ -s "$signal_log" ]]; }}; then
    print -rl -- "p4242" "fcwd" "n$runtime" "ftxt" "n$runtime/node/bin/node" "f22" "n$state_dir/openclaw.json"
  else
    print -rl -- "p4242" "fcwd" "n/tmp/independent-openclaw" "ftxt" "n/usr/local/bin/node" "f22" "n/tmp/independent-openclaw/openclaw.json"
  fi
}}
fake_kill() {{
  [[ "$1" == "-0" ]] && return 0
  print -r -- "$*" >> "$signal_log"
}}
fake_sleep() {{ :; }}
{cleanup}
'''
            completed = subprocess.run(["/bin/zsh", "-c", harness], capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            return signal_log.read_text().splitlines() if signal_log.exists() else []

    def test_stale_owner_pid_must_not_signal_an_independent_openclaw(self):
        self.assertEqual(self.run_cleanup(), [])

    def test_verified_bundled_gateway_is_stopped(self):
        self.assertEqual(self.run_cleanup(owned=True), ["-TERM 4242", "-9 4242"])

    def test_pid_reused_by_external_gateway_after_term_is_not_killed(self):
        self.assertEqual(self.run_cleanup(owned=True, reused_after_term=True), ["-TERM 4242"])

    def test_restarted_pid_is_not_killed_even_with_matching_paths(self):
        self.assertEqual(self.run_cleanup(owned=True, changed_start=True), ["-TERM 4242"])

    def test_same_bundled_binary_with_independent_config_is_not_signalled(self):
        self.assertEqual(self.run_cleanup(owned=True, wrong_config=True), [])

    def test_unreadable_ownership_evidence_never_authorizes_a_signal(self):
        self.assertEqual(self.run_cleanup(owned=True, unreadable=True), [])

    def test_bundle_path_in_another_process_argument_does_not_confer_ownership(self):
        self.assertEqual(self.run_cleanup(argument_only=True), [])

    def test_live_same_named_gateways_keep_the_independent_instance_running(self):
        node = Path("/Applications/MERRICK.app/Contents/Resources/runtime/node/bin/node")
        if not node.is_file():
            self.skipTest("Installed bundled Node is required for the live process test")
        with tempfile.TemporaryDirectory(prefix="merrick-coexistence-") as directory:
            root = Path(directory).resolve()
            app = root / "MERRICK.app"
            runtime = app / "Contents/Resources/runtime"
            (runtime / "node/bin").mkdir(parents=True)
            bundled_node = runtime / "node/bin/node"
            shutil.copy2(node, bundled_node)
            state = root / "private-state"
            independent = root / "independent-state"
            state.mkdir()
            independent.mkdir()
            (state / "openclaw.json").write_text("{}")
            (independent / "openclaw.json").write_text('{"userSetting":"preserve"}')
            # Real same-titled, same-executable processes with distinct configs
            # and live listeners. No model, account, or user state is involved.
            program = '''const fs = require('fs');
process.title = 'openclaw-gateway';
const fd = fs.openSync(process.argv[1], 'r');
require('http').createServer((req, res) => res.end('ok')).listen(0, '127.0.0.1', function () {
  console.log(this.address().port);
});'''
            processes = []
            try:
                for config in (state / "openclaw.json", independent / "openclaw.json"):
                    process = subprocess.Popen([str(bundled_node), "-e", program, str(config)], cwd=runtime, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    processes.append(process)
                    with selectors.DefaultSelector() as ready:
                        ready.register(process.stdout, selectors.EVENT_READ)
                        self.assertTrue(ready.select(timeout=10), "Fixture listener did not start")
                    self.assertGreater(int(process.stdout.readline()), 0)
                owned, external = processes
                source = SCRIPT.read_text()
                cleanup = source[source.index("CURRENT_UID="):source.index("# Delete every credential")]
                cleanup = cleanup.replace('$HOME/Library/Application Support/JarvisStark/OpenClaw', str(state))
                harness = f"set -u\nAPP_PATH={shlex.quote(str(app))}\nSIGKILL=9\n" + cleanup

                (state / ".gateway-owner.json").write_text(json.dumps({"pid": external.pid, "port": 23456}))
                result = subprocess.run(["/bin/zsh", "-c", harness], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsNone(external.poll(), "Independent OpenClaw was stopped")
                self.assertIsNone(owned.poll())

                (state / ".gateway-owner.json").write_text(json.dumps({"pid": owned.pid, "port": 23456}))
                result = subprocess.run(["/bin/zsh", "-c", harness], capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stderr)
                owned.wait(timeout=5)
                self.assertIsNone(external.poll(), "Independent OpenClaw was stopped during owned cleanup")
                self.assertEqual((independent / "openclaw.json").read_text(), '{"userSetting":"preserve"}')
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.terminate()
                    process.wait(timeout=5)
                    process.stdout.close()
                    process.stderr.close()


if __name__ == "__main__":
    unittest.main()
