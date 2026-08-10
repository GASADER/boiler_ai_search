# -*- coding: utf-8 -*-
import phoenix as px
from openinference.instrumentation.crewai import CrewAIInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def init_telemetry():
    """เปิด Phoenix App และตั้งค่า OpenTelemetry Tracer"""
    session = px.launch_app()
    print(f"🚀 Phoenix UI running at: {session.url}")

    tracer_provider = TracerProvider()
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:6006/v1/traces"))
    )
    CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)