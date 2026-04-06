import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_tracing(app: FastAPI) -> None:
    service_name = os.getenv('OTEL_SERVICE_NAME', 'auth-service')
    otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://jaeger:4318')
    jaeger_host = os.getenv('JAEGER_HOST', '')
    jaeger_port = int(os.getenv('JAEGER_PORT', '6831'))

    resource = Resource.create({SERVICE_NAME: service_name})
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    if otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=f'{otlp_endpoint}/v1/traces'))
        )
    elif jaeger_host:
        provider.add_span_processor(
            BatchSpanProcessor(
                JaegerExporter(
                    agent_host_name=jaeger_host,
                    agent_port=jaeger_port,
                )
            )
        )

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)