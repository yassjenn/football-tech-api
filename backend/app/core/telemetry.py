from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import settings


def setup_telemetry(app: FastAPI) -> None:
    resource = Resource.create(
        {
            "service.name": settings.APP_NAME,
            "service.version": settings.APP_VERSION,
            "deployment.environment": settings.ENVIRONMENT,
        }
    )

    provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=settings.OTLP_ENDPOINT,
        insecure=True,
    )

    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(provider)

    # Instrumentación automática de FastAPI y SQLAlchemy
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument()
