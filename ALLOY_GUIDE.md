# Grafana Alloy Observability Guide

## Overview

TheReview uses **Grafana Alloy** for complete observability - collecting metrics, logs, and traces in one unified pipeline. Alloy is Grafana's OpenTelemetry-based collector that replaces Prometheus Agent.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  Observability Pipeline                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  FastAPI ──┐                                             │
│  PostgreSQL├─► Grafana Alloy ──┐                        │
│  MongoDB  ─┤                    ├─► Grafana Dashboards  │
│  Redis    ─┘                    │                        │
│                                  ├─► Grafana Cloud       │
│                                  └─► Local Storage       │
│                                                           │
│  Metrics + Logs + Traces = Full Observability            │
└──────────────────────────────────────────────────────────┘
```

---

##  Quick Start

### 1. Enable Telemetry

Update your `.env`:

```env
ENABLE_TELEMETRY=true
ALLOY_ENVIRONMENT=production
ALLOY_OTLP_ENDPOINT=http://alloy:4317
```

### 2. Start with Monitoring

```bash
# Development
make dev-up

# Production with monitoring
make prod-up-monitoring

# Or manually
docker-compose -f docker-compose.prod.yml --profile monitoring up -d
```

### 3. Access Dashboards

| Service | URL | Purpose |
|---------|-----|---------|
| **Alloy UI** | http://localhost:12345 | Pipeline status |
| **Grafana** | http://localhost:3000 | Dashboards |
| **Metrics Endpoint** | http://localhost:8000/metrics | Prometheus scrape |

---

##  What Gets Collected?

### 1. Application Metrics (OpenTelemetry)

**Automatic:**
- HTTP request duration
- Request rate & latency
- Error rates (4xx, 5xx)
- Active connections
- Request/response sizes

**Custom (via code):**
```python
from app.utils.telemetry import get_meter

meter = get_meter("my_service")
counter = meter.create_counter("reviews_processed")
counter.add(1, {"platform": "google"})
```

### 2. Distributed Tracing

**Automatic:**
- API endpoint traces
- Database query spans
- Redis cache operations
- Cross-service calls

**View in Grafana:**
- Request flow visualization
- Bottleneck identification
- Error tracking

### 3. Database Metrics

**PostgreSQL:**
- Connection pool stats
- Query performance
- Transaction rates
- Cache hit rates

**MongoDB:**
- Operations per second
- Collection stats
- Replication lag

**Redis:**
- Hit/miss rates
- Memory usage
- Connected clients
- Command statistics

### 4. Container Metrics

- CPU usage
- Memory usage
- Network I/O
- Disk I/O

---

## Configuration

### Alloy Configuration (River Syntax)

Located at: `docker/alloy/config.alloy`

```river
// Enable OTLP receiver
otelcol.receiver.otlp "api" {
  grpc {
    endpoint = "0.0.0.0:4317"
  }
  http {
    endpoint = "0.0.0.0:4318"
  }
}

// Scrape Prometheus metrics
prometheus.scrape "fastapi" {
  targets = [
    {"__address__" = "api:8000"},
  ]
  forward_to = [prometheus.remote_write.default.receiver]
}
```

### Application Instrumentation

In `app/main.py`:

```python
from app.utils.telemetry import setup_telemetry

app = FastAPI(lifespan=lifespan)
setup_telemetry(app)  # Automatic instrumentation
```

---

## Grafana Dashboards

### Pre-built Dashboards

1. **FastAPI Overview**
   - Request rate
   - Response times (p50, p95, p99)
   - Error rates
   - Active connections

2. **Database Performance**
   - Query latency
   - Connection pool usage
   - Cache hit rates
   - Slow queries

3. **Redis Performance**
   - Cache hit/miss ratio
   - Memory usage
   - Command statistics
   - Eviction rates

4. **Container Resources**
   - CPU utilization
   - Memory usage
   - Network throughput
   - Disk I/O

### Access Dashboards

```bash
# Login to Grafana
URL: http://localhost:3000
Username: admin
Password: (from .env GRAFANA_ADMIN_PASSWORD)

# Datasources pre-configured:
- Alloy-Prometheus (metrics)
- Alloy-Loki (logs, optional)
- Alloy-Tempo (traces, optional)
```

---

## Metrics Examples

### 1. Request Rate

```promql
rate(http_requests_total[5m])
```

### 2. P95 Latency

```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### 3. Error Rate

```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### 4. Cache Hit Rate

```promql
rate(redis_keyspace_hits_total[5m]) /
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

### 5. Database Connection Pool

```promql
pg_stat_database_numbackends
```

---

## Custom Instrumentation

### Add Custom Metrics

```python
from app.utils.telemetry import get_meter

# Create a meter
meter = get_meter("review_service")

# Counter
reviews_counter = meter.create_counter(
    "reviews_processed_total",
    description="Total reviews processed"
)
reviews_counter.add(1, {"platform": "google", "status": "success"})

# Histogram
response_time = meter.create_histogram(
    "review_processing_duration_seconds",
    description="Review processing duration"
)
response_time.record(0.5, {"platform": "google"})

# Gauge
active_scrapers = meter.create_observable_gauge(
    "active_scrapers",
    callbacks=[lambda: get_active_scraper_count()]
)
```

### Add Custom Spans (Tracing)

```python
from app.utils.telemetry import get_tracer

tracer = get_tracer("review_service")

@app.post("/reviews")
async def create_review(review: ReviewCreate):
    with tracer.start_as_current_span("create_review") as span:
        span.set_attribute("platform", review.platform)
        span.set_attribute("entity_type", review.entity_type)

        # Your code here
        result = await save_review(review)

        span.set_attribute("review_id", str(result.id))
        return result
```

---

## Grafana Cloud Integration

### Send Data to Grafana Cloud

1. **Get Credentials**
   - Login to Grafana Cloud
   - Get Prometheus endpoint + API key
   - Get Loki endpoint + API key (optional)
   - Get Tempo endpoint + API key (optional)

2. **Update Environment Variables**

```env
# Prometheus
PROMETHEUS_REMOTE_WRITE_URL=https://prometheus-<region>.grafana.net/api/prom/push
PROMETHEUS_REMOTE_WRITE_USERNAME=<your-username>
PROMETHEUS_REMOTE_WRITE_PASSWORD=<your-api-key>

# Loki (optional)
LOKI_ENDPOINT=https://logs-<region>.grafana.net/loki/api/v1/push

# Tempo (optional)
OTLP_ENDPOINT=https://tempo-<region>.grafana.net:443
```

3. **Restart Alloy**

```bash
docker-compose -f docker-compose.prod.yml restart alloy
```

---

## Security Best Practices

### 1. Use TLS for Production

Update `config.alloy`:

```river
otelcol.exporter.otlp "default" {
  client {
    endpoint = env("OTLP_ENDPOINT")
    tls {
      insecure = false
      ca_file  = "/etc/ssl/certs/ca.pem"
    }
  }
}
```

### 2. Secure Grafana

```env
# Strong admin password
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)

# Enable auth proxy
GF_AUTH_PROXY_ENABLED=true
```

### 3. Restrict Metrics Endpoint

```nginx
location /metrics {
    # Only allow internal network
    allow 172.28.0.0/16;
    deny all;

    proxy_pass http://api:8000/metrics;
}
```

---

##  Troubleshooting

### Alloy Not Receiving Data

```bash
# Check Alloy logs
docker-compose logs alloy

# Check Alloy UI
curl http://localhost:12345/ready

# Test OTLP endpoint
curl http://localhost:4318/v1/traces

# Verify FastAPI metrics
curl http://localhost:8000/metrics
```

### No Metrics in Grafana

```bash
# Check datasource connection
# In Grafana: Configuration → Data Sources → Alloy-Prometheus → Test

# Check if Alloy is scraping
# Visit Alloy UI: http://localhost:12345

# Check Prometheus endpoint
curl http://localhost:9090/api/v1/query?query=up
```

### High Memory Usage

```bash
# Check Alloy resource usage
docker stats thereview-alloy-prod

# Reduce scrape frequency in config.alloy:
scrape_interval = "30s"  # Instead of 15s

# Reduce retention:
wal {
  max_age = "2h"  # Instead of 4h
}
```

### Missing Traces

```bash
# Check if OTLP exporter is configured
env | grep ALLOY_OTLP_ENDPOINT

# Enable debug logging in telemetry
# In app/utils/telemetry.py, set log level to DEBUG

# Check trace sampling rate
# Default is 100%, reduce if needed
```

---

## Performance Impact

### Resource Usage

| Component | CPU | Memory | Network |
|-----------|-----|--------|---------|
| Alloy | 0.1-0.5 cores | 256-512 MB | 1-10 Mbps |
| Instrumentation | <1% overhead | <50 MB | Minimal |
| Total | Negligible | ~500 MB | Low |

### Optimization Tips

1. **Reduce Scrape Frequency**
   ```river
   scrape_interval = "30s"  # For non-critical metrics
   ```

2. **Sampling for Traces**
   ```python
   # In telemetry.py
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

   tracer_provider = TracerProvider(
       resource=resource,
       sampler=TraceIdRatioBased(0.1)  # Sample 10% of traces
   )
   ```

3. **Batch Processing**
   ```river
   otelcol.processor.batch "default" {
     timeout = "10s"
     send_batch_size = 2048  # Larger batches
   }
   ```

---

## Learning Resources

### Grafana Alloy

- [Official Docs](https://grafana.com/docs/alloy/latest/)
- [River Configuration Language](https://grafana.com/docs/alloy/latest/concepts/configuration-language/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)

### OpenTelemetry

- [Python SDK](https://opentelemetry.io/docs/instrumentation/python/)
- [FastAPI Instrumentation](https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html)
- [Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)

### Grafana Dashboards

- [Community Dashboards](https://grafana.com/grafana/dashboards/)
- [FastAPI Dashboard](https://grafana.com/grafana/dashboards/16110)
- [PostgreSQL Dashboard](https://grafana.com/grafana/dashboards/9628)

---

## Migration from Prometheus

Already using Prometheus? Alloy is compatible!

### What Changes?

| Feature | Prometheus | Alloy |
|---------|---|-------|
| Scraping | |  Compatible |
| PromQL | | Same queries |
| Recording Rules | |  Supported |
| Alerting | |  + More |
| **Logs** | |  Native |
| **Traces** | |  Native |
| **OpenTelemetry** | Limited |  Full |

### Migration Steps

1. **Keep Prometheus running**
2. **Deploy Alloy alongside**
3. **Configure Alloy to scrape same targets**
4. **Verify data in Grafana**
5. **Switch datasource**
6. **Deprecate Prometheus**

---

## Best Practices

###  DO

- Enable telemetry in production
- Use sampling for high-traffic traces
- Set retention policies
- Monitor Alloy resource usage
- Use Grafana Cloud for long-term storage
- Add custom business metrics
- Set up alerts in Grafana

###  DON'T

- Collect every single span (use sampling)
- Expose /metrics publicly
- Store unlimited metrics locally
- Ignore Alloy health checks
- Hardcode endpoints in config
- Skip TLS in production
- Forget to rotate API keys

---

## Summary

You now have:

**Unified Observability** - Metrics, logs, traces in one place
**Automatic Instrumentation** - FastAPI, databases, containers
**Custom Metrics** - Add your own business metrics
**Distributed Tracing** - See full request flows
**Grafana Dashboards** - Pre-configured visualizations
**Grafana Cloud Ready** - Send data to cloud
**Production Ready** - Secure, scalable, monitored

---

**Access Your Observability Stack:**

- **Alloy UI**: http://localhost:12345
- **Grafana**: http://localhost:3000 (admin/your-password)
- **Metrics**: http://localhost:8000/metrics
- **Health**: http://localhost:8000/health/ready

**Start monitoring!** 
