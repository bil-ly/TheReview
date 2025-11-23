"""
OpenTelemetry instrumentation for TheReview Backend.

SIMPLIFIED VERSION: Uses OpenTelemetry Collector for all processing.
The app just sends data to the collector, which handles everything else.

Architecture:
  FastAPI App → OpenTelemetry Collector → Grafana Alloy → Grafana Cloud
                ↑
                All processing happens here (batching, filtering, routing)
"""

import os

from fastapi import FastAPI
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_fastapi_instrumentator import Instrumentator

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("Telemetry", log_to_std_out=True)


def setup_telemetry(app: FastAPI) -> None:
    """
    Set up OpenTelemetry instrumentation for FastAPI.

    This configures:
    - Resource identification (who we are)
    - Tracing (what we're doing)
    - Metrics (how we're performing)
    - Auto-instrumentation (automatic trace creation)
    - Prometheus /metrics endpoint

    All data is sent to the OpenTelemetry Collector, which handles:
    - Batching and buffering
    - Filtering and sampling
    - Routing to multiple backends
    - Resource detection
    - Metric transformations
    """
    # Only enable if explicitly requested
    if os.getenv("ENABLE_TELEMETRY", "false").lower() != "true":
        logger.info("Telemetry disabled (set ENABLE_TELEMETRY=true to enable)")
        return

    try:
        collector_endpoint = os.getenv("ALLOY_OTLP_ENDPOINT", "http://otel-collector:4317")
        logger.info(f"Setting up telemetry → {collector_endpoint}")

        # =====================================================================
        # Resource: Service Identification
        # =====================================================================
        resource = Resource.create({
            "service.name": settings.APP_NAME or "thereview-backend",
            "service.version": "0.1.0",
            "deployment.environment": settings.APP_ENVIRONMENT,
            "service.namespace": "thereview",
        })
        logger.info(f"  Resource configured: {settings.APP_NAME}")

        # =====================================================================
        # Tracing: Send traces to collector
        # =====================================================================
        trace_exporter = OTLPSpanExporter(
            endpoint=collector_endpoint,
            insecure=True,
        )

        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        logger.info(f"  Tracing configured → collector")

        # =====================================================================
        # Metrics: Send metrics to collector
        # =====================================================================
        metric_exporter = OTLPMetricExporter(
            endpoint=collector_endpoint,
            insecure=True,
        )

        metric_reader = PeriodicExportingMetricReader(
            exporter=metric_exporter,
            export_interval_millis=30000,  # 30s (collector will batch further)
        )

        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader],
        )
        metrics.set_meter_provider(meter_provider)
        logger.info(f"  Metrics configured → collector")

        # =====================================================================
        # Auto-Instrumentation: Automatic tracing for FastAPI
        # =====================================================================
        FastAPIInstrumentor.instrument_app(
            app,
            tracer_provider=tracer_provider,
            excluded_urls="/health,/health/ready,/health/live,/metrics",
        )
        logger.info(f"  Auto-instrumentation enabled")

        # =====================================================================
        # Prometheus: /metrics endpoint (scraped by collector)
        # =====================================================================
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/metrics", "/health.*"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )

        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
        logger.info(f"  /metrics endpoint exposed (collector scrapes this)")

        logger.info("✓ Telemetry setup complete")
        logger.info("")
        logger.info("  Data flow: FastAPI → Collector → Alloy → Grafana")
        logger.info("  Collector handles: batching, filtering, routing, processing")
        logger.info("")

    except Exception as e:
        logger.error(f"Failed to set up telemetry: {e}", exc_info=True)
        logger.warning("Continuing without telemetry")


def get_tracer(name: str):
    """
    Get a tracer for manual instrumentation.

    Example:
        from app.utils.telemetry import get_tracer

        tracer = get_tracer("review-service")

        with tracer.start_as_current_span("custom-operation"):
            # Your code here
            pass
    """
    return trace.get_tracer(name)


def get_meter(name: str):
    """
    Get a meter for custom metrics.

    Example:
        from app.utils.telemetry import get_meter

        meter = get_meter("review-service")
        counter = meter.create_counter("reviews_created")
        counter.add(1, {"product_id": "123"})
    """
    return metrics.get_meter(name)
