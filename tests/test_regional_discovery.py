from __future__ import annotations

import unittest
from pathlib import Path

from collectors.regional_discovery import (
    BrowserDiscoveryEngine,
    DiscoveryDriftError,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "data/fixtures/regional/discovery"
HOME_URL = "https://regional.example.test/"
LIST_URL = "https://regional.example.test/youth-policies"
DETAIL_URL = "https://regional.example.test/youth-policies/fixture-001"


def fixture_pages() -> dict[str, bytes]:
    return {
        HOME_URL: (FIXTURE_ROOT / "home.html").read_bytes(),
        LIST_URL: (FIXTURE_ROOT / "list.html").read_bytes(),
        DETAIL_URL: (FIXTURE_ROOT / "detail.html").read_bytes(),
    }


class RegionalDiscoveryTests(unittest.TestCase):
    def test_unregistered_home_discovers_and_replays_semantic_profile(self) -> None:
        engine = BrowserDiscoveryEngine()
        pages = fixture_pages()

        profile = engine.discover(home_url=HOME_URL, pages=pages)
        replayed = engine.replay(profile, pages=pages)

        self.assertEqual(
            ["goto", "click", "observe_list", "observe_detail"],
            [action.kind for action in profile.actions],
        )
        self.assertEqual("fixture-001", profile.sample_external_id)
        self.assertEqual("지역 청년 교통비 지원사업", replayed.title)
        self.assertEqual(
            "Fixture 지역청년센터", replayed.fields["organization"]
        )
        self.assertEqual(
            "Fixture 지역 거주 청년", replayed.fields["eligibility_text"]
        )
        self.assertEqual("교통비 지원", replayed.fields["support_content"])

    def test_profile_drift_is_an_error_instead_of_zero_policy_success(self) -> None:
        engine = BrowserDiscoveryEngine()
        pages = fixture_pages()
        profile = engine.discover(home_url=HOME_URL, pages=pages)
        pages[LIST_URL] = b"<html><body><p>no policies</p></body></html>"

        with self.assertRaisesRegex(DiscoveryDriftError, "detail link"):
            engine.replay(profile, pages=pages)

    def test_cross_host_policy_navigation_is_not_discovered(self) -> None:
        pages = fixture_pages()
        pages[HOME_URL] = (
            b'<html><body><a href="https://outside.example/policies">'
            b"policy</a></body></html>"
        )

        with self.assertRaises(DiscoveryDriftError):
            BrowserDiscoveryEngine().discover(home_url=HOME_URL, pages=pages)


if __name__ == "__main__":
    unittest.main()
