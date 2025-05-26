import os
from functools import lru_cache
from typing import Any

from opentelemetry import trace
from opentelemetry.context.context import Context
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.resource.detector.container import ContainerResourceDetector
from opentelemetry.sdk.resources import (
    OsResourceDetector,
    Resource,
    get_aggregated_resources,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult
from opentelemetry.semconv.attributes.service_attributes import SERVICE_NAME
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from rclpy.logging import LoggingSeverity, RcutilsLogger

from ros_opentelemetry_interfaces.msg import KeyValue, TraceMetadata

logger = RcutilsLogger(name="open_telemetry")
TRACE_FMT = "[trace_id={trace_id} span_id={span_id}] "


class DropIfNotConnectedOTLPSpanExporter(OTLPSpanExporter):
    def export(self, spans):
        otlp_endpoint = get_otlp_endpoint()
        if otlp_endpoint is None:
            return SpanExportResult.SUCCESS
        return super().export(spans)


@lru_cache(maxsize=1)
def get_otlp_endpoint() -> str | None:
    otlp_endpoint = os.getenv("OTLP_ENDPOINT")
    if otlp_endpoint is None:
        logger.info("OpenTelemetry Collector endpoint is not set.")
        os.environ["OTEL_SDK_DISABLED"] = "1"
    else:
        logger.info(f"OpenTelemetry Collector endpoint is set: {otlp_endpoint}")
    return otlp_endpoint


def inject_trace_context() -> TraceMetadata:
    carrier = {}
    TraceContextTextMapPropagator().inject(carrier=carrier)
    message = TraceMetadata()
    context = []
    for key, value in carrier.items():
        context.append(KeyValue(key=key, value=value))
    message.context = context
    return message


def update_trace_context(
    trace_context: TraceMetadata, data: dict[str, str]
) -> TraceMetadata:
    context = [key_val for key_val in trace_context.context]
    for key, value in data.items():
        context.append(KeyValue(key=key, value=value))
    message = TraceMetadata()
    message.context = context
    return message


def extract_trace_context(trace_context: TraceMetadata | None) -> Context:
    if trace_context is None:
        return Context()
    if len(trace_context.context) == 0:
        return Context()

    return TraceContextTextMapPropagator().extract(
        {key_val.key: key_val.value for key_val in trace_context.context}
    )


def get_resource(component_name: str):
    resource = Resource.create({SERVICE_NAME: component_name})
    resource_detectors = [
        ContainerResourceDetector(raise_on_error=False),
        OsResourceDetector(raise_on_error=False),
    ]
    return get_aggregated_resources(resource_detectors, initial_resource=resource)


@lru_cache(maxsize=1)
def setup_tracer(component_name: str):
    if not get_otlp_endpoint():
        return
    provider = TracerProvider(resource=get_resource(component_name))
    processor = BatchSpanProcessor(
        DropIfNotConnectedOTLPSpanExporter(endpoint=get_otlp_endpoint(), insecure=True)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)


def _trace_prefix() -> str:
    span = trace.get_current_span()
    if span is None:
        return ""
    ctx = span.get_span_context()
    if not ctx or not ctx.is_valid:
        return ""
    trace_id = f"{ctx.trace_id:032x}"
    span_id = f"{ctx.span_id:016x}"
    return TRACE_FMT.format(trace_id=trace_id, span_id=span_id)


class TracingLogger:
    """
    Wraps an rclpy logger and automatically injects the current OTel
    trace/span IDs into each log line (when a valid span is active).
    """

    def __init__(self, ros_logger):
        self._logger = ros_logger

    def debug(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.DEBUG):
            self._logger.debug(_format(msg, *args))

    def info(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.INFO):
            self._logger.info(_format(msg, *args))

    def warn(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.WARN):
            self._logger.warn(_format(msg, *args))

    def warning(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.WARN):
            self._logger.warning(_format(msg, *args))

    def error(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.ERROR):
            self._logger.error(_format(msg, *args))

    def fatal(self, msg: str, *args: Any) -> None:
        if self._logger.is_enabled_for(LoggingSeverity.FATAL):
            self._logger.fatal(_format(msg, *args))

    @property
    def ros_logger(self):
        return self._logger


def _format(message: str, *args: Any) -> str:
    prefix = _trace_prefix()
    if args:
        try:
            message = message % args
        except Exception:
            message = f"{message} {' '.join(map(str, args))}"
    return prefix + message


def wrap_logger(ros_logger) -> TracingLogger:
    return TracingLogger(ros_logger)
