# OpenTelemetry Data Flow - Complete Guide

**Project:** TheReview Backend
**Purpose:** Understanding how telemetry data flows from application code to observability platforms

This document explains every step of the telemetry pipeline, from instrumentation in your FastAPI application to final visualization in monitoring systems.

---

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Component Responsibilities](#component-responsibilities)
3. [Data Flow Diagram](#data-flow-diagram)
4. [Detailed Flow Walkthrough](#detailed-flow-walkthrough)
5. [Tracing Deep Dive](#tracing-deep-dive)
6. [Metrics Deep Dive](#metrics-deep-dive)
7. [Code Examples](#code-examples)
8. [Background Processes](#background-processes)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          YOUR FASTAPI APPLICATION                    │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    APPLICATION CODE                           │  │
│  │  • HTTP Requests come in                                      │  │
│  │  • Business logic executes                                    │  │
│  │  • Database calls happen                                      │  │
│  │  • External API calls made                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              OPENTELEMETRY INSTRUMENTATION                    │  │
│  │                                                                │  │
│  │  AUTO-INSTRUMENTATION:                                        │  │
│  │  • FastAPIInstrumentor (wraps HTTP handlers)                 │  │
│  │  • Automatically creates spans for requests                   │  │
│  │  • Adds HTTP metadata (method, URL, status)                  │  │
│  │                                                                │  │
│  │  MANUAL INSTRUMENTATION:                                      │  │
│  │  • tracer.start_span() in your code                          │  │
│  │  • meter.create_counter() for custom metrics                 │  │
│  │                                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   OPENTELEMETRY SDK                           │  │
│  │                                                                │  │
│  │  TRACES:                                                       │  │
│  │  • SpanProcessor collects spans                               │  │
│  │  • BatchSpanProcessor batches them                            │  │
│  │  • OTLPSpanExporter sends to collector                        │  │
│  │                                                                │  │
│  │  METRICS:                                                      │  │
│  │  • MeterProvider collects metrics                             │  │
│  │  • PeriodicExportingMetricReader aggregates                   │  │
│  │  • OTLPMetricExporter sends to collector                      │  │
│  │                                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                              ↓                                        │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              PROMETHEUS INSTRUMENTATOR                        │  │
│  │  • Separate from OpenTelemetry                                │  │
│  │  • Exposes /metrics endpoint                                  │  │
│  │  • Returns Prometheus format                                  │  │
│  │  • Scraped by Collector                                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
                                ↓ OTLP/gRPC (port 4317)
                                ↓ HTTP/Prometheus scrape (port 8000/metrics)
                                │
┌───────────────────────────────┴───────────────────────────────────┐
│                   OPENTELEMETRY COLLECTOR                          │
│                   (otel-collector:4317)                            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                        RECEIVERS                              ││
│  │  • otlp/grpc (4317) - Receives OTLP data from app           ││
│  │  • otlp/http (4318) - Alternative HTTP endpoint             ││
│  │  • prometheus - Scrapes /metrics from app                    ││
│  │  • hostmetrics - Collects system metrics                     ││
│  └──────────────────────────────────────────────────────────────┘│
│                              ↓                                      │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                        PROCESSORS                             ││
│  │  1. memory_limiter - Prevents OOM                            ││
│  │  2. batch - Groups data for efficient sending                ││
│  │  3. resource - Adds environment metadata                     ││
│  │  4. attributes - Enriches spans/metrics                      ││
│  │  5. span - Modifies span names                               ││
│  │  6. metricstransform - Renames/aggregates metrics            ││
│  └──────────────────────────────────────────────────────────────┘│
│                              ↓                                      │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                        EXPORTERS                              ││
│  │  • otlp/alloy - Sends to Grafana Alloy                      ││
│  │  • prometheus - Exposes metrics on :8889/metrics             ││
│  │  • logging - Logs to stdout for debugging                    ││
│  └──────────────────────────────────────────────────────────────┘│
└─────────────────────────────┬───────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ↓                 ↓                 ↓
    ┌───────────────┐  ┌──────────────┐  ┌──────────────┐
    │ Grafana Alloy │  │  Prometheus  │  │    Stdout    │
    │ (Production)  │  │  (Scraping)  │  │  (Debugging) │
    └───────────────┘  └──────────────┘  └──────────────┘
            ↓
    ┌───────────────┐
    │ Grafana Cloud │
    │   (Storage &  │
    │ Visualization)│
    └───────────────┘
```

---

## Component Responsibilities

### 1. FastAPI Application
**What it does:**
- Runs your business logic
- Handles HTTP requests
- Executes database queries
- Calls external APIs

**Telemetry role:**
- Contains instrumentation code
- Generates telemetry data
- Sends data to collector

### 2. OpenTelemetry SDK (In-Process)
**What it does:**
- Lives inside your application process
- Collects telemetry without blocking app
- Batches data for efficiency
- Handles retries and errors

**Key components:**
- `TracerProvider` - Creates tracers
- `MeterProvider` - Creates meters
- `Resource` - Identifies your service

### 3. OpenTelemetry Collector (Separate Process)
**What it does:**
- Runs as independent container
- Receives from multiple sources
- Processes and enriches data
- Routes to multiple destinations

**Why use it:**
- Decouples app from monitoring backend
- Handles buffering and retries
- Can process data from many apps
- Single configuration point

### 4. Prometheus Instrumentator
**What it does:**
- Independent from OpenTelemetry
- Provides /metrics endpoint
- Tracks HTTP request metrics
- Uses Prometheus format

**Why separate:**
- Pull-based model (scraping)
- Standard Prometheus format
- Immediate access to metrics
- No dependency on collector

---

## Data Flow Diagram

### Request Flow with Tracing

```
1. HTTP Request arrives
   GET /api/v1/reviews
        ↓
2. FastAPIInstrumentor intercepts
   • Creates span: "GET /api/v1/reviews"
   • Records start time
   • Sets span context
        ↓
3. Your handler executes
   async def get_reviews():
        ↓
4. Child spans created automatically
   • Database query span
   • Cache lookup span
        ↓
5. Response returned
   • HTTP status recorded
   • End time recorded
        ↓
6. Span completed
   • BatchSpanProcessor queues it
        ↓
7. Every 10 seconds (configured)
   • Batch sent to collector via gRPC
        ↓
8. Collector processes
   • Adds environment labels
   • Enriches with metadata
        ↓
9. Exported to destinations
   • Grafana Alloy (production)
   • Console logs (debug)
```

### Metrics Flow

```
1. Prometheus Instrumentator counts request
   http_requests_total{method="GET", path="/api/v1/reviews"}++
        ↓
2. Stored in memory
   • Counters increment
   • Histograms record latency
        ↓
3. Collector scrapes /metrics endpoint
   • Every 30 seconds (configured)
   • HTTP GET http://api:8000/metrics
        ↓
4. Returns Prometheus format
   # HELP http_requests_total ...
   # TYPE http_requests_total counter
   http_requests_total{...} 42
        ↓
5. Collector processes metrics
   • Transforms names
   • Adds labels
        ↓
6. Exports to Prometheus exporter
   • Available at :8889/metrics
        ↓
7. Grafana/Prometheus scrapes collector
   • Stores in time-series database
```

---

## Detailed Flow Walkthrough

### Phase 1: Application Startup

**File: `app/main.py`**
```python
app = FastAPI(lifespan=lifespan)

# This line triggers the entire telemetry setup
setup_telemetry(app)
```

**What happens:**

1. **Check if enabled**
   ```python
   if os.getenv("ENABLE_TELEMETRY", "false").lower() != "true":
       return  # Exit if disabled
   ```

2. **Create Resource (Service Identity)**
   ```python
   resource = Resource.create({
       "service.name": "thereview-backend",
       "service.version": "0.1.0",
       "deployment.environment": "development",
   })
   ```

   **Background:** This object is attached to ALL telemetry data. It tells monitoring systems "this data came from TheReview backend v0.1.0 in development environment."

3. **Setup Tracing**
   ```python
   trace_exporter = OTLPSpanExporter(
       endpoint="http://otel-collector:4317",
       insecure=True,
   )
   ```

   **Background:** Creates exporter that knows how to send spans to collector using gRPC.

   ```python
   tracer_provider = TracerProvider(resource=resource)
   tracer_provider.add_span_processor(
       BatchSpanProcessor(trace_exporter)
   )
   trace.set_tracer_provider(tracer_provider)
   ```

   **Background process started:**
   - BatchSpanProcessor creates a background thread
   - Thread wakes up every 5 seconds (default)
   - Collects all spans created since last batch
   - Sends batch to collector via gRPC
   - If send fails, queues for retry

4. **Setup Metrics**
   ```python
   metric_exporter = OTLPMetricExporter(
       endpoint="http://otel-collector:4317",
       insecure=True,
   )

   metric_reader = PeriodicExportingMetricReader(
       exporter=metric_exporter,
       export_interval_millis=30000,  # Every 30 seconds
   )
   ```

   **Background process started:**
   - PeriodicExportingMetricReader creates background thread
   - Thread wakes up every 30 seconds
   - Reads all metric data from meters
   - Aggregates (sums counters, calculates histogram buckets)
   - Sends to collector via gRPC

5. **Auto-Instrumentation**
   ```python
   FastAPIInstrumentor.instrument_app(
       app,
       tracer_provider=tracer_provider,
   )
   ```

   **What this does:**
   - Wraps every route handler with tracing code
   - Intercepts requests before they reach your code
   - Intercepts responses before they leave
   - Automatically creates spans for each request

6. **Prometheus Metrics**
   ```python
   instrumentator = Instrumentator()
   instrumentator.instrument(app)
   instrumentator.expose(app, endpoint="/metrics")
   ```

   **What this does:**
   - Wraps every route with metric collection
   - Increments counters on each request
   - Records latency in histograms
   - Creates `/metrics` endpoint for scraping

### Phase 2: Request Handling

**When a request comes in: `GET /api/v1/reviews`**

1. **Uvicorn receives request**
   - TCP connection accepted
   - HTTP headers parsed
   - Request object created

2. **FastAPI middleware chain starts**
   - CORS middleware
   - Other middleware
   - **FastAPIInstrumentor middleware** ← THIS IS WHERE TRACING STARTS

3. **FastAPIInstrumentor creates span**
   ```python
   # This happens automatically, you don't write this code
   span = tracer.start_span(
       name="GET /api/v1/reviews",
       kind=SpanKind.SERVER,
       attributes={
           "http.method": "GET",
           "http.url": "/api/v1/reviews",
           "http.scheme": "http",
           "http.target": "/api/v1/reviews",
       }
   )

   # Sets this span as "active" - child spans will link to it
   with trace.use_span(span, end_on_exit=False):
       # Your handler code runs inside this context
   ```

4. **Your handler executes**
   ```python
   async def get_reviews():
       # If you create manual spans:
       with tracer.start_as_current_span("database-query"):
           results = await db.execute(query)

       return results
   ```

   **Background:**
   - The "database-query" span is automatically a child of "GET /api/v1/reviews"
   - Span context propagated via thread-local storage (async context in Python)
   - Each span records: start time, end time, attributes, events

5. **Response generated**
   - Your function returns response
   - FastAPIInstrumentor intercepts

6. **Span finalized**
   ```python
   # Automatic
   span.set_attribute("http.status_code", 200)
   span.end()  # Records end time
   ```

7. **Span handed to BatchSpanProcessor**
   ```python
   # Background thread running
   while True:
       time.sleep(5)  # Wait 5 seconds

       # Collect all spans from queue
       spans = self.span_queue.get_all()

       if spans:
           # Send to exporter
           self.exporter.export(spans)
   ```

8. **Sent to Collector**
   - gRPC call to `otel-collector:4317`
   - OTLP protocol (OpenTelemetry Protocol)
   - Binary efficient format

### Phase 3: Collector Processing

**When collector receives data:**

1. **OTLP Receiver accepts connection**
   ```yaml
   # In otel-collector-config.yaml
   receivers:
     otlp:
       protocols:
         grpc:
           endpoint: 0.0.0.0:4317
   ```

   **Background:**
   - gRPC server listening on port 4317
   - Accepts spans, metrics, logs
   - Validates protocol buffer format

2. **Pipeline processing**
   ```yaml
   service:
     pipelines:
       traces:
         receivers: [otlp]
         processors:
           - memory_limiter
           - resource
           - batch
         exporters:
           - otlp/alloy
           - logging
   ```

3. **Processor chain executes**

   **Step 1: memory_limiter**
   ```go
   // Pseudocode of what happens
   if memory_usage > 512MB:
       drop_data()  // Prevent OOM
   ```

   **Step 2: resource processor**
   ```go
   // Adds attributes to every span
   span.attributes["deployment.environment"] = "development"
   span.attributes["collector.version"] = "0.91.0"
   ```

   **Step 3: batch processor**
   ```go
   // Groups spans for efficient export
   batch = []
   for span in incoming_spans:
       batch.append(span)
       if len(batch) >= 8192 or timeout:
           export(batch)
           batch = []
   ```

4. **Exported to destinations**

   **To Grafana Alloy:**
   ```go
   // gRPC call to Alloy
   grpc.call("alloy:4317", spans)

   // With retry logic
   if error:
       backoff = 5s
       retry()
   ```

   **To logging:**
   ```go
   // Just prints to stdout
   for span in batch:
       log.info(f"Span: {span.name} duration={span.duration}")
   ```

### Phase 4: Metrics Collection

**Prometheus scraping happens separately:**

1. **Collector scrapes /metrics endpoint**
   ```yaml
   receivers:
     prometheus:
       config:
         scrape_configs:
           - job_name: 'thereview-api'
             scrape_interval: 30s
             static_configs:
               - targets: ['api:8000']
   ```

2. **Every 30 seconds:**
   ```
   HTTP GET http://api:8000/metrics
   ↓
   Response:
   # HELP http_requests_total ...
   http_requests_total{method="GET",path="/api/v1/reviews"} 42
   ```

3. **Collector processes metrics**
   - Converts Prometheus format to OTLP
   - Adds resource attributes
   - Batches with other metrics

4. **Exports to Prometheus exporter**
   ```yaml
   exporters:
     prometheus:
       endpoint: 0.0.0.0:8889
   ```

   - Exposes metrics at `collector:8889/metrics`
   - External Prometheus can scrape this

---

## Tracing Deep Dive

### What is a Span?

A span represents a single operation in your application.

**Structure:**
```json
{
  "trace_id": "a1b2c3d4e5f6...",    // Links related spans
  "span_id": "1a2b3c4d...",         // Unique span ID
  "parent_span_id": "9z8y7x...",    // Parent in call chain
  "name": "GET /api/v1/reviews",    // What operation
  "kind": "SERVER",                  // Type of span
  "start_time": "2025-11-17T12:00:00Z",
  "end_time": "2025-11-17T12:00:00.125Z",
  "attributes": {
    "http.method": "GET",
    "http.status_code": 200,
    "db.statement": "SELECT * FROM reviews"
  },
  "events": [
    {
      "time": "2025-11-17T12:00:00.050Z",
      "name": "cache_miss",
      "attributes": {"key": "reviews:all"}
    }
  ],
  "status": {"code": "OK"}
}
```

### Span Lifecycle

```python
# 1. Create span
span = tracer.start_span("operation-name")

# 2. Set as active (for context propagation)
with trace.use_span(span):
    # 3. Add attributes
    span.set_attribute("user.id", "123")

    # 4. Record events
    span.add_event("processing-started", {"items": 10})

    # 5. Child spans automatically link
    with tracer.start_as_current_span("sub-operation"):
        do_work()

    # 6. Handle errors
    try:
        risky_operation()
    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise

# 7. Span ends automatically (or call span.end())
```

### Trace Context Propagation

**Within a single service:**
```python
# Request handler
async def get_reviews():
    # Span A is active
    with tracer.start_as_current_span("database"):
        # Span B inherits parent from context
        # B.parent_span_id = A.span_id
        # B.trace_id = A.trace_id
        await query_db()
```

**Across services (HTTP calls):**
```python
# Service A (your app)
with tracer.start_as_current_span("call-service-b"):
    # Inject trace context into HTTP headers
    headers = {}
    inject(headers, context=context)
    # headers now contain:
    # traceparent: 00-trace_id-span_id-01

    response = await http_client.get(
        "http://service-b/api",
        headers=headers
    )

# Service B
# Extracts trace context from headers
# Creates child span with same trace_id
```

### How Auto-Instrumentation Works

FastAPIInstrumentor wraps your routes:

```python
# Your code
@app.get("/reviews")
async def get_reviews():
    return reviews

# What actually runs (simplified)
@app.get("/reviews")
async def get_reviews():
    # Instrumentation wrapper
    span = tracer.start_span("GET /reviews")
    span.set_attribute("http.method", "GET")

    try:
        # Your actual function
        result = await original_get_reviews()

        span.set_attribute("http.status_code", 200)
        return result

    except Exception as e:
        span.record_exception(e)
        span.set_status(Status(StatusCode.ERROR))
        raise

    finally:
        span.end()
```

---

## Metrics Deep Dive

### Types of Metrics

#### 1. Counter (Always Increasing)
```python
meter = metrics.get_meter("my-app")

# Create counter
request_counter = meter.create_counter(
    name="http.requests",
    description="Total HTTP requests",
    unit="1",
)

# Increment
request_counter.add(1, {"method": "GET", "path": "/reviews"})
request_counter.add(1, {"method": "POST", "path": "/reviews"})

# Result in Prometheus:
# http_requests{method="GET",path="/reviews"} 42
# http_requests{method="POST",path="/reviews"} 15
```

**Use cases:**
- Total requests
- Total errors
- Total bytes sent
- Total records processed

#### 2. UpDownCounter (Can Increase/Decrease)
```python
active_requests = meter.create_up_down_counter(
    name="http.active_requests",
    description="Currently active requests",
)

# Request starts
active_requests.add(1)

# Request completes
active_requests.add(-1)

# Result:
# http_active_requests 5  (current value)
```

**Use cases:**
- Active connections
- Queue size
- Memory usage
- Cache entries

#### 3. Histogram (Distribution)
```python
latency_histogram = meter.create_histogram(
    name="http.duration",
    description="HTTP request duration",
    unit="ms",
)

# Record values
latency_histogram.record(125, {"method": "GET"})
latency_histogram.record(250, {"method": "GET"})
latency_histogram.record(50, {"method": "GET"})

# Result in Prometheus:
# http_duration_bucket{method="GET",le="100"} 1
# http_duration_bucket{method="GET",le="200"} 2
# http_duration_bucket{method="GET",le="500"} 3
# http_duration_sum{method="GET"} 425
# http_duration_count{method="GET"} 3
```

**Use cases:**
- Request latency
- Response sizes
- Processing time
- Database query duration

#### 4. Observable Gauge (Current Value)
```python
def get_memory_usage():
    import psutil
    return psutil.virtual_memory().percent

memory_gauge = meter.create_observable_gauge(
    name="system.memory.usage",
    callbacks=[lambda: [Observation(get_memory_usage())]],
    description="Memory usage percentage",
    unit="%",
)

# Called automatically by metric reader every 30s
# Result:
# system_memory_usage 75.3
```

**Use cases:**
- CPU usage
- Memory usage
- Queue depth
- Cache hit rate

### Metric Aggregation

**What happens in the background:**

```python
# When you call:
counter.add(1, {"method": "GET"})

# SDK does:
labels = {"method": "GET"}
if labels not in aggregations:
    aggregations[labels] = 0
aggregations[labels] += 1

# Every 30 seconds (export interval):
for labels, value in aggregations.items():
    export_metric(name="http.requests", value=value, labels=labels)
```

### Prometheus Format

When collector scrapes `/metrics`:

```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/reviews",status="200"} 42 1700000000000

# Components:
# - Metric name: http_requests_total
# - Labels: {method="GET",path="/reviews",status="200"}
# - Value: 42
# - Timestamp: 1700000000000 (milliseconds since epoch)
```

---

## Code Examples

### Example 1: Manual Tracing

```python
from app.utils.telemetry import get_tracer

tracer = get_tracer("review-service")

async def process_review(review_id: str):
    # Create parent span
    with tracer.start_as_current_span("process-review") as span:
        # Add context
        span.set_attribute("review.id", review_id)

        # Child span for validation
        with tracer.start_as_current_span("validate-review"):
            is_valid = await validate_review(review_id)
            span.set_attribute("validation.result", is_valid)

        if not is_valid:
            span.add_event("validation-failed")
            span.set_status(Status(StatusCode.ERROR, "Invalid review"))
            raise ValueError("Invalid review")

        # Child span for database
        with tracer.start_as_current_span("save-to-database"):
            await db.save(review_id)

        # Child span for cache
        with tracer.start_as_current_span("update-cache"):
            await cache.set(f"review:{review_id}", data)

        span.add_event("processing-complete", {"duration_ms": 125})
        return {"status": "success"}
```

**Resulting trace:**
```
process-review (250ms)
├── validate-review (50ms)
├── save-to-database (150ms)
└── update-cache (50ms)
```

### Example 2: Custom Metrics

```python
from app.utils.telemetry import get_meter

meter = get_meter("review-service")

# Create instruments
review_counter = meter.create_counter(
    name="reviews.created",
    description="Total reviews created",
)

review_rating = meter.create_histogram(
    name="reviews.rating",
    description="Review ratings distribution",
)

processing_time = meter.create_histogram(
    name="reviews.processing_time",
    description="Time to process review",
    unit="ms",
)

async def create_review(data: ReviewCreate):
    start_time = time.time()

    # Your logic
    review = await db.create(data)

    # Record metrics
    review_counter.add(1, {
        "entity_type": data.entity_type,
        "user_tier": "premium",
    })

    review_rating.record(data.rating, {
        "entity_type": data.entity_type,
    })

    duration = (time.time() - start_time) * 1000
    processing_time.record(duration, {
        "operation": "create",
    })

    return review
```

### Example 3: Error Tracking

```python
async def risky_operation():
    with tracer.start_as_current_span("risky-operation") as span:
        try:
            result = await external_api_call()
            span.set_attribute("api.response.size", len(result))
            return result

        except TimeoutError as e:
            # Record exception with stack trace
            span.record_exception(e)

            # Set error status
            span.set_status(
                Status(StatusCode.ERROR, "API timeout")
            )

            # Add event for timeline
            span.add_event("timeout-occurred", {
                "timeout_seconds": 30,
                "retry_count": 3,
            })

            # Increment error counter
            error_counter.add(1, {
                "error_type": "timeout",
                "service": "external-api",
            })

            raise
```

---

## Background Processes

### 1. BatchSpanProcessor Thread

**Purpose:** Batch spans for efficient export

```python
class BatchSpanProcessor:
    def __init__(self):
        self.queue = Queue()
        self.thread = Thread(target=self._worker)
        self.thread.daemon = True
        self.thread.start()

    def _worker(self):
        while True:
            # Wait for batch timeout (5 seconds)
            time.sleep(self.schedule_delay_millis / 1000)

            # Collect spans from queue
            spans = []
            while not self.queue.empty() and len(spans) < self.max_export_batch_size:
                spans.append(self.queue.get())

            if spans:
                try:
                    # Export batch
                    self.span_exporter.export(spans)
                except Exception as e:
                    # Log error but don't crash
                    logger.error(f"Export failed: {e}")
```

**Configuration:**
```python
BatchSpanProcessor(
    span_exporter,
    max_queue_size=2048,           # Max spans to queue
    schedule_delay_millis=5000,    # Export every 5s
    max_export_batch_size=512,     # Max spans per batch
    export_timeout_millis=30000,   # Timeout for export
)
```

### 2. PeriodicExportingMetricReader Thread

**Purpose:** Periodically read and export metrics

```python
class PeriodicExportingMetricReader:
    def __init__(self):
        self.thread = Thread(target=self._ticker)
        self.thread.daemon = True
        self.thread.start()

    def _ticker(self):
        while True:
            time.sleep(self.export_interval_millis / 1000)

            # Collect from all meters
            metrics_data = self.collect()

            # Export
            try:
                self.metric_exporter.export(metrics_data)
            except Exception as e:
                logger.error(f"Metric export failed: {e}")
```

**Configuration:**
```python
PeriodicExportingMetricReader(
    exporter,
    export_interval_millis=30000,  # Export every 30s
    export_timeout_millis=30000,   # Timeout for export
)
```

### 3. Prometheus Scraper (in Collector)

**Purpose:** Pull metrics from /metrics endpoint

```go
// Simplified pseudocode
func scrapeLoop() {
    ticker := time.NewTicker(30 * time.Second)

    for range ticker.C {
        // HTTP GET to /metrics
        resp, err := http.Get("http://api:8000/metrics")
        if err != nil {
            log.Error("Scrape failed")
            continue
        }

        // Parse Prometheus format
        metrics := parsePrometheusText(resp.Body)

        // Send to pipeline
        for _, metric := range metrics {
            pipeline.Process(metric)
        }
    }
}
```

### 4. Collector Pipeline Processors

Each processor runs in its own goroutine:

```go
// Batch processor
func batchProcessor(input chan Data, output chan []Data) {
    batch := []Data{}
    ticker := time.NewTicker(10 * time.Second)

    for {
        select {
        case data := <-input:
            batch = append(batch, data)
            if len(batch) >= 8192 {
                output <- batch
                batch = []Data{}
            }

        case <-ticker.C:
            if len(batch) > 0 {
                output <- batch
                batch = []Data{}
            }
        }
    }
}
```

---

## Performance Considerations

### Memory Usage

**Application:**
- Each span: ~1-2KB
- Queue size: 2048 spans = ~4MB max
- Metric aggregations: ~100 bytes per label set
- Total: ~10-20MB overhead

**Collector:**
- Receives from multiple apps
- Buffers in memory
- Memory limit: 512MB (configured)

### CPU Usage

**Application:**
- Span creation: Microseconds
- Context propagation: Negligible
- Batching: Minimal (background thread)
- Export: Only during batch send (5s intervals)

**Collector:**
- Processing: ~1-5% CPU
- Scraping: Minimal
- Exporting: Depends on backend

### Network Usage

**From app to collector:**
- Traces: ~50KB per batch (every 5s)
- Metrics: ~10KB per export (every 30s)
- Total: ~15KB/s average

**From collector to backends:**
- Compressed with gzip
- Batched efficiently
- ~50% reduction in bandwidth

---

## Debugging Telemetry

### Check if telemetry is working

```bash
# 1. Check app logs for setup
docker compose logs api | grep -i telemetry

# Should see:
# Setting up telemetry → http://otel-collector:4317
# ✓ Telemetry setup complete

# 2. Check /metrics endpoint
curl http://localhost:8000/metrics | head -20

# Should return Prometheus format

# 3. Check collector is receiving data
curl http://localhost:8888/metrics | grep otelcol_receiver

# Should show received spans/metrics

# 4. Check collector is exporting
curl http://localhost:8888/metrics | grep otelcol_exporter

# Should show sent spans/metrics
```

### Common Issues

**No spans being created:**
- Check ENABLE_TELEMETRY=true
- Verify FastAPIInstrumentor is called
- Check for exceptions in setup

**Spans created but not sent:**
- Check collector is reachable
- Verify endpoint: otel-collector:4317
- Check collector logs for errors

**Metrics endpoint 404:**
- Check ENABLE_METRICS=true
- Verify Instrumentator.expose() is called
- Check FastAPI route registration

---

## Summary

**Data flows through these stages:**

1. **Instrumentation** - Captures telemetry in your app
2. **SDK** - Batches and exports in background
3. **Collector** - Receives, processes, routes
4. **Backends** - Store and visualize

**Key background processes:**

- BatchSpanProcessor: Exports spans every 5s
- PeriodicExportingMetricReader: Exports metrics every 30s
- Prometheus scraper: Polls /metrics every 30s
- Collector pipeline: Processes continuously

**Key benefits:**

- **Decoupled** - App doesn't depend on backends
- **Efficient** - Batching reduces overhead
- **Reliable** - Retries and buffering handle failures
- **Flexible** - One collector, many backends

This architecture is production-ready and follows OpenTelemetry best practices! 🚀
