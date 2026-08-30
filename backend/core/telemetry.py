import logging
from urllib.parse import urljoin
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, Span, SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from core.config import SKIP_METHODS, otel_excluded_urls, settings
from core.database import async_engine, engine

logger = logging.getLogger("telemetry")

EXCLUDED_URLS = otel_excluded_urls()


def _span_http_method(span: ReadableSpan) -> str:
    attributes = span.attributes or {}
    raw = attributes.get("http.request.method") or attributes.get("http.method") or ""
    return str(raw).upper()


def should_drop_span(span: ReadableSpan) -> bool:
    method = _span_http_method(span)
    if method in SKIP_METHODS:
        return True
    name = span.name or ""
    return any(name.startswith(f"{skipped} ") for skipped in SKIP_METHODS)


class SkipSpanProcessor(SpanProcessor):
    """Drop spans FastAPI excluded_urls cannot filter (method-only, e.g. OPTIONS)."""

    def __init__(self, wrapped: SpanProcessor) -> None:
        self._wrapped = wrapped

    def on_start(self, span: Span, parent_context=None) -> None:
        self._wrapped.on_start(span, parent_context)

    def on_end(self, span: ReadableSpan) -> None:
        if should_drop_span(span):
            return
        self._wrapped.on_end(span)

    def shutdown(self) -> None:
        self._wrapped.shutdown()

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return bool(self._wrapped.force_flush(timeout_millis))


class TraceIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if not getattr(record, "otelTraceID", None):
            record.otelTraceID = "0"
        return super().format(record)


def _traces_endpoint(base: str) -> str:
    normalized = base.rstrip("/") + "/"
    if normalized.endswith("/v1/traces/"):
        return normalized.rstrip("/")
    return urljoin(normalized, "v1/traces")


def _build_resource() -> Resource:
    return Resource.create(
        {
            "service.name": settings.PROJECT_NAME,
            "service.version": settings.PROJECT_VERSION,
            "deployment.environment": (
                "development" if settings.DEBUG_MODE else "production"
            ),
        }
    )


def setup_telemetry(app: FastAPI) -> None:
    LoggingInstrumentor().instrument(
        inject_trace_context=True,
        set_logging_format=False,
        enable_log_auto_instrumentation=False,
    )

    if not settings.OTEL_ENABLE:
        return

    resource = _build_resource()
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(
        endpoint=_traces_endpoint(settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    )
    provider.add_span_processor(
        SkipSpanProcessor(
            BatchSpanProcessor(exporter, schedule_delay_millis=1000)
        )
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, excluded_urls=EXCLUDED_URLS)
    SQLAlchemyInstrumentor().instrument(
        engines=[async_engine.sync_engine, engine]
    )
    RedisInstrumentor().instrument()
    logger.info("OpenTelemetry tracing enabled")


def shutdown_telemetry() -> None:
    if not settings.OTEL_ENABLE:
        return
    provider = trace.get_tracer_provider()
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()
