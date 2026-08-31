import logging
from pathlib import Path

from core.config import (
    SKIP_METHODS,
    SKIP_PATHS,
    otel_excluded_urls,
    settings,
    setup_logging,
)


class TestSkipConfig:
    def test_skip_paths_include_docs_and_health(self):
        assert SKIP_PATHS == frozenset({"/", "/docs", "/redoc", "/openapi.json", "/healthz"})

    def test_skip_methods_include_options(self):
        assert SKIP_METHODS == frozenset({"OPTIONS"})


class TestOtelExcludedUrls:
    def test_root_pattern_matches_host_url_only(self):
        regex = otel_excluded_urls(frozenset({"/"}))
        assert r"https?://[^/?]+/?$" in regex

    def test_custom_paths_are_escaped(self):
        result = otel_excluded_urls(frozenset({"/api/v1.test"}))
        assert r"/api/v1\.test" in result

    def test_sorted_and_comma_joined(self):
        result = otel_excluded_urls(frozenset({"/b", "/a"}))
        assert result == r"/a,/b"


class TestRateLimitWhitelist:
    def test_empty_whitelist(self):
        original = settings.RATE_LIMIT_WHITELIST
        try:
            settings.RATE_LIMIT_WHITELIST = ""
            assert settings.rate_limit_whitelist_ips == set()
            settings.RATE_LIMIT_WHITELIST = "   "
            assert settings.rate_limit_whitelist_ips == set()
        finally:
            settings.RATE_LIMIT_WHITELIST = original

    def test_parses_comma_separated_ips(self):
        original = settings.RATE_LIMIT_WHITELIST
        try:
            settings.RATE_LIMIT_WHITELIST = "1.1.1.1, 8.8.8.8,,  "
            assert settings.rate_limit_whitelist_ips == {"1.1.1.1", "8.8.8.8"}
        finally:
            settings.RATE_LIMIT_WHITELIST = original


class TestSetupLogging:
    def test_setup_logging_overrides_levels(self, tmp_path: Path):
        yaml_path = tmp_path / "logging.yaml"
        yaml_path.write_text(
            "\n".join(
                [
                    "version: 1",
                    "disable_existing_loggers: false",
                    "root:",
                    "  level: DEBUG",
                    "  handlers: []",
                    "loggers:",
                    "  core-test-logger:",
                    "    level: DEBUG",
                    "    handlers: []",
                    "    propagate: no",
                ]
            )
        )
        logs_dir = Path("logs")
        original_level = settings.LOG_LEVEL
        try:
            settings.LOG_LEVEL = "ERROR"
            setup_logging(str(yaml_path))
            assert logs_dir.exists()
            assert logging.getLogger().level == logging.ERROR
            assert logging.getLogger("core-test-logger").level == logging.ERROR
        finally:
            settings.LOG_LEVEL = original_level
