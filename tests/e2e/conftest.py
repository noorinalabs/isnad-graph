"""E2E test fixtures for Playwright browser tests."""

import os

import pytest


@pytest.fixture(scope="session")
def browser_context_args():
    """Configure browser context for tests."""
    return {
        "viewport": {"width": 1280, "height": 720},
        "base_url": os.environ.get("E2E_BASE_URL", "http://localhost:3000"),
    }


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Auto-apply flaky rerun marker to all e2e tests."""
    for item in items:
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.flaky(reruns=2, reruns_delay=1))
