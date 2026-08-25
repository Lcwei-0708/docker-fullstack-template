import io
import logging
import re

import pytest
from httpx import ASGITransport, AsyncClient
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from core.telemetry import EXCLUDED_URLS, SkipSpanProcessor, TraceIdFormatter
from main import app


def _install_span_exporter() -> InMemorySpanExporter:
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SkipSpanProcessor(SimpleSpanProcessor(exporter)))
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE._done = False
    trace.set_tracer_provider(provider)
    return exporter


@pytest.mark.asyncio
async def test_skip_paths_are_not_traced_and_api_log_has_trace_id():
    exporter = _install_span_exporter()
    FastAPIInstrumentor.instrument_app(app, excluded_urls=EXCLUDED_URLS)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(
        TraceIdFormatter("%(message)s traceID=%(otelTraceID)s")
    )
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
        FastAPIInstrumentor.uninstrument_app(app)


def test_otel_excluded_urls_match_full_request_url():
    from core.config import otel_excluded_urls

    regex = re.compile("|".join(otel_excluded_urls().split(",")))
    assert regex.search("http://localhost:5000/healthz")
    assert regex.search("http://127.0.0.1:5000/")
    assert regex.search("http://localhost:5000/docs")
    assert regex.search("http://localhost:5000/openapi.json")
    assert not regex.search("http://localhost:5000/api/roles")
    assert not regex.search("http://localhost:5000/api/health")
