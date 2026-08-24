from __future__ import annotations

import sys
import unittest

from collectors.browser_runner import (
    BrowserRunner,
    BrowserRunnerError,
    BrowserRunnerTimeout,
)
from collectors.regional_profile import RegionalAction


HOME_URL = "https://regional.example.test/"
ACTIONS = (
    RegionalAction("goto", HOME_URL, None),
    RegionalAction("observe_detail", f"{HOME_URL}policies/1", None),
)


class BrowserRunnerTests(unittest.TestCase):
    def test_json_boundary_returns_only_validated_result(self) -> None:
        script = (
            "import json,sys; request=json.load(sys.stdin.buffer); "
            "json.dump({'status':'ok','final_url':request['home_url'],"
            "'observations':request['actions'],'sample_external_id':'1',"
            "'sample_title':'fixture'},sys.stdout)"
        )

        result = BrowserRunner(
            (sys.executable, "-c", script),
            timeout_seconds=5,
        ).run(home_url=HOME_URL, actions=ACTIONS)

        self.assertEqual(HOME_URL, result.final_url)
        self.assertEqual("1", result.sample_external_id)
        self.assertEqual(2, len(result.observations))

    def test_failure_does_not_expose_subprocess_output(self) -> None:
        runner = BrowserRunner(
            (
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('private-page-content'); sys.exit(2)",
            ),
            timeout_seconds=5,
        )

        with self.assertRaises(BrowserRunnerError) as raised:
            runner.run(home_url=HOME_URL, actions=ACTIONS)

        self.assertNotIn("private-page-content", str(raised.exception))

    def test_timeout_is_classified_without_process_output(self) -> None:
        runner = BrowserRunner(
            (
                sys.executable,
                "-c",
                "import time; time.sleep(2)",
            ),
            timeout_seconds=1,
        )

        with self.assertRaises(BrowserRunnerTimeout):
            runner.run(home_url=HOME_URL, actions=ACTIONS)

    def test_invalid_success_payload_is_rejected(self) -> None:
        script = "import json; print(json.dumps({'status':'ok'}))"
        runner = BrowserRunner(
            (sys.executable, "-c", script),
            timeout_seconds=5,
        )

        with self.assertRaises(BrowserRunnerError):
            runner.run(home_url=HOME_URL, actions=ACTIONS)

    def test_action_replay_drift_is_rejected(self) -> None:
        script = (
            "import json,sys; request=json.load(sys.stdin.buffer); "
            "json.dump({'status':'ok','final_url':request['home_url'],"
            "'observations':request['actions'][:-1]},sys.stdout)"
        )
        runner = BrowserRunner(
            (sys.executable, "-c", script),
            timeout_seconds=5,
        )

        with self.assertRaisesRegex(BrowserRunnerError, "replay drifted"):
            runner.run(home_url=HOME_URL, actions=ACTIONS)

    def test_final_url_outside_allowlist_is_rejected(self) -> None:
        script = (
            "import json,sys; request=json.load(sys.stdin.buffer); "
            "json.dump({'status':'ok','final_url':'https://outside.test/',"
            "'observations':request['actions']},sys.stdout)"
        )

        with self.assertRaisesRegex(BrowserRunnerError, "allowed hosts"):
            BrowserRunner(
                (sys.executable, "-c", script),
                timeout_seconds=5,
            ).run(home_url=HOME_URL, actions=ACTIONS)


if __name__ == "__main__":
    unittest.main()
