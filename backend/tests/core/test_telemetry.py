import io
import logging
import re
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from core.config import settings
from core.telemetry import (
    EXCLUDED_URLS,
    SkipSpanProcessor,
    TraceIdFormatter,
    _build_resource,
    _traces_endpoint,
    setup_telemetry,
    should_drop_span,
    shutdown_telemetry,
)
from main import app


def _sdk_tracer_provider() -> TracerProvider | None:
    provider = getattr(trace, "_TRACER_PROVIDER", None)
    if isinstance(provider, TracerProvider):
        return provider
    current = trace.get_tracer_provider()
    if isinstance(current, TracerProvider):
        return current
    return None


def _rebuild_app_middleware() -> None:
    # Starlette builds this once on the first request. Later add_middleware calls
    # are ignored until the cache is cleared (CI runs API tests before this file).
    app.middleware_stack = None


def _install_span_exporter() -> tuple[InMemorySpanExporter, bool]:
    """Attach an in-memory exporter without replacing an already-live tracer.

    Replacing the global provider while the app is instrumented sends spans
    to the old tracer and leaves the test exporter empty.
    """
    exporter = InMemorySpanExporter()
    processor = SkipSpanProcessor(SimpleSpanProcessor(exporter))
    already_instrumented = getattr(app, "_is_instrumented_by_opentelemetry", False)
    provider = _sdk_tracer_provider()
    if already_instrumented and provider is not None:
        provider.add_span_processor(processor)
        return exporter, False

    provider = TracerProvider()
    trace._TRACER_PROVIDER = None
    once = getattr(trace, "_TRACER_PROVIDER_SET_ONCE", None)
    if once is not None:
        once._done = False
    trace.set_tracer_provider(provider)
    provider.add_span_processor(processor)
    FastAPIInstrumentor.instrument_app(app, excluded_urls=EXCLUDED_URLS)
    _rebuild_app_middleware()
    return exporter, True


@pytest.mark.asyncio
async def test_skip_paths_are_not_traced_and_api_log_has_trace_id():
    exporter, instrumented_here = _install_span_exporter()

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(TraceIdFormatter("%(message)s traceID=%(otelTraceID)s"))
    api_logger = logging.getLogger("api_logger")
    api_logger.addHandler(handler)
    api_logger.setLevel(logging.INFO)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            assert (await ac.get("/healthz")).status_code == 200
            assert (await ac.get("/openapi.json")).status_code == 200
            assert (await ac.get("/")).status_code == 200
            assert (await ac.get("/redoc")).status_code == 200
            await ac.get("/docs")
            options = await ac.options(
                "/api/debug/test-ip",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )
            assert options.status_code == 200
            response = await ac.get("/api/debug/test-ip")
        assert response.status_code == 200

        output = stream.getvalue()
        match = re.search(r"traceID=([0-9a-fA-F]+)", output)
        assert match is not None, output
        assert int(match.group(1), 16) != 0
        assert re.search(r"API Response:.*duration=\d+\.\d+ms", output), output

        assert "method=OPTIONS" not in output
        names = {span.name for span in exporter.get_finished_spans()}
        assert any(name.startswith("GET /api/") for name in names), names
        assert not any(name.startswith("OPTIONS ") for name in names), names
        assert not any(
            name == "GET /"
            or name.startswith("GET /healthz")
            or name.startswith("GET /docs")
            or name.startswith("GET /redoc")
            or name.startswith("GET /openapi.json")
            for name in names
        ), names
    finally:
        api_logger.removeHandler(handler)
        if instrumented_here:
            FastAPIInstrumentor.uninstrument_app(app)
            _rebuild_app_middleware()


def test_otel_excluded_urls_match_full_request_url():
    from core.config import otel_excluded_urls

    regex = re.compile("|".join(otel_excluded_urls().split(",")))
    assert regex.search("http://localhost:5000/healthz")
    assert regex.search("http://127.0.0.1:5000/")
    assert regex.search("http://localhost:5000/docs")
    assert regex.search("http://localhost:5000/openapi.json")
    assert not regex.search("http://localhost:5000/api/roles")
    assert not regex.search("http://localhost:5000/api/health")


class _FakeSpan:
    def __init__(self, name="", attributes=None):
        self.name = name
        self.attributes = attributes


class TestShouldDropSpan:
    def test_drops_options_by_attribute(self):
        span = _FakeSpan(name="GET /api/x", attributes={"http.request.method": "OPTIONS"})
        assert should_drop_span(span) is True

    def test_drops_options_by_legacy_attribute(self):
        span = _FakeSpan(name="POST /api/x", attributes={"http.method": "options"})
        assert should_drop_span(span) is True

    def test_drops_options_by_span_name(self):
        span = _FakeSpan(name="OPTIONS /api/debug/test-ip", attributes={})
        assert should_drop_span(span) is True

    def test_keeps_get_span(self):
        span = _FakeSpan(name="GET /api/debug/test-ip", attributes={"http.request.method": "GET"})
        assert should_drop_span(span) is False


class TestSkipSpanProcessor:
    def test_forwards_non_options_and_lifecycle(self):
        wrapped = MagicMock()
        wrapped.force_flush.return_value = True
        processor = SkipSpanProcessor(wrapped)
        kept = _FakeSpan(name="GET /api/x", attributes={"http.request.method": "GET"})
        dropped = _FakeSpan(name="OPTIONS /api/x", attributes={"http.request.method": "OPTIONS"})

        processor.on_start(kept)
        processor.on_end(kept)
        processor.on_end(dropped)
        processor.shutdown()
        assert processor.force_flush() is True

        wrapped.on_start.assert_called_once_with(kept, None)
        wrapped.on_end.assert_called_once_with(kept)
        wrapped.shutdown.assert_called_once()
        wrapped.force_flush.assert_called_once()


class TestTraceIdFormatter:
    def test_defaults_missing_trace_id(self):
        formatter = TraceIdFormatter("%(message)s %(otelTraceID)s")
        record = logging.LogRecord("n", logging.INFO, __file__, 1, "hello", (), None)
        assert formatter.format(record) == "hello 0"

    def test_keeps_existing_trace_id(self):
        formatter = TraceIdFormatter("%(message)s %(otelTraceID)s")
        record = logging.LogRecord("n", logging.INFO, __file__, 1, "hello", (), None)
        record.otelTraceID = "abc"
        assert formatter.format(record) == "hello abc"


class TestTracesEndpoint:
    def test_appends_v1_traces(self):
        assert _traces_endpoint("http://alloy:4318") == "http://alloy:4318/v1/traces"
        assert _traces_endpoint("http://alloy:4318/") == "http://alloy:4318/v1/traces"

    def test_keeps_existing_v1_traces_path(self):
        assert _traces_endpoint("http://alloy:4318/v1/traces") == "http://alloy:4318/v1/traces"
        assert _traces_endpoint("http://alloy:4318/v1/traces/") == "http://alloy:4318/v1/traces"


class TestBuildResource:
    def test_uses_project_settings(self):
        resource = _build_resource()
        attrs = dict(resource.attributes)
        assert attrs["service.name"] == settings.PROJECT_NAME
        assert attrs["service.version"] == settings.PROJECT_VERSION
        expected_env = "development" if settings.DEBUG_MODE else "production"
        assert attrs["deployment.environment"] == expected_env


class TestSetupAndShutdownTelemetry:
    def test_setup_returns_when_disabled(self):
        test_app = FastAPI()
        with (
            patch("core.telemetry.settings.OTEL_ENABLE", False),
            patch("core.telemetry.LoggingInstrumentor") as logging_instrumentor,
            patch("core.telemetry.FastAPIInstrumentor.instrument_app") as instrument_app,
        ):
            setup_telemetry(test_app)
        logging_instrumentor.return_value.instrument.assert_called_once()
        instrument_app.assert_not_called()

    def test_shutdown_returns_when_disabled(self):
        with (
            patch("core.telemetry.settings.OTEL_ENABLE", False),
            patch("core.telemetry.trace.get_tracer_provider") as get_provider,
        ):
            shutdown_telemetry()
        get_provider.assert_not_called()

    def test_shutdown_calls_provider_shutdown(self):
        provider = MagicMock()
        with (
            patch("core.telemetry.settings.OTEL_ENABLE", True),
            patch("core.telemetry.trace.get_tracer_provider", return_value=provider),
        ):
            shutdown_telemetry()
        provider.shutdown.assert_called_once()
