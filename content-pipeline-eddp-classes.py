import hashlib
import hmac
import json
import logging
import time
from typing import Any, Awaitable, Callable, Dict

class SecureDataIngestionPipeline:
   def __init__(self, cryptographic_secret: str, max_log_capacity: int = 1000):
       self.cryptographic_secret: bytes = cryptographic_secret.encode()
       self.bounded_audit_history: deque = deque(maxlen=max_log_capacity)

   @staticmethod
   def normalize_payload_spacing(payload: Dict[str, Any]) -> Dict[str, Any]:
       copied_payload = dict(payload)
       if "body_content" in copied_payload and isinstance(copied_payload["body_content"], str):
           copied_payload["body_content"] = " ".join(copied_payload["body_content"].split())
       return copied_payload

   @staticmethod
   def validate_schema_constraints(payload: Dict[str, Any]) -> bool:
       if "body_content" not in payload or not isinstance(payload["body_content"], str):
           return False
       content_length = len(payload["body_content"])
       if content_length == 0 or content_length > 5000:
           return False
       if "metadata_context" not in payload or not isinstance(payload["metadata_context"], dict):
           return False
       return True

   def generate_payload_signature(self, payload: Dict[str, Any]) -> str:
       canonical_bytes = json.dumps(
           payload,
           sort_keys=True,
           separators=(",", ":"),
           ensure_ascii=False,
       ).encode()
       return hmac.new(
           self.cryptographic_secret,
           canonical_bytes,
           hashlib.sha256,
       ).hexdigest()

   def verify_signature_integrity(self, payload: Dict[str, Any], provided_signature: str) -> bool:
       expected_signature = self.generate_payload_signature(payload)
       return hmac.compare_digest(expected_signature, provided_signature)

   def record_pipeline_event(self, event_type: str, payload: Dict[str, Any]) -> None:
       self.bounded_audit_history.append(
           {
               "timestamp": time.time(),
               "event_classification": event_type,
               "associated_payload": payload,
           }
       )

   def execute_ingestion_audit(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
       normalized_payload = self.normalize_payload_spacing(raw_payload)
       if not self.validate_schema_constraints(normalized_payload):
           self.record_pipeline_event("TRANSACTION_REJECTED_INVALID_SCHEMA", normalized_payload)
           raise ValueError("Inbound data payload failed structural schema requirements.")
       unsigned_working_payload = dict(normalized_payload)
       computed_signature = self.generate_payload_signature(unsigned_working_payload)
       if not self.verify_signature_integrity(unsigned_working_payload, computed_signature):
           self.record_pipeline_event("TRANSACTION_REJECTED_SIGNATURE_MISMATCH", normalized_payload)
           raise ValueError("Cryptographic verification failed. Payload signature mismatch.")
       signed_output_payload = dict(normalized_payload)
       signed_output_payload["cryptographic_signature"] = computed_signature
       self.record_pipeline_event("TRANSACTION_ACCEPTED_AND_VERIFIED", signed_output_payload)
       return signed_output_payload

class CoreDataPipelineOrchestrator:
   def __init__(
       self,
       boundary_filter: Any,
       evaluation_engine: Any,
       metrics_scorer: Any,
       target_router: Any,
       view_renderer: Any,
       dispatcher: Any,
       audit_ledger: Any,
   ):
       self.boundary_filter = boundary_filter
       self.evaluation_engine = evaluation_engine
       self.metrics_scorer = metrics_scorer
       self.target_router = target_router
       self.view_renderer = view_renderer
       self.dispatcher = dispatcher
       self.audit_ledger = audit_ledger

   def execute_pipeline_cycle(
       self,
       raw_data: Dict[str, Any],
       layout_template: Dict[str, Any],
       context_key: str,
       channel_name: str = "standard_stream",
   ) -> Dict[str, Any]:
       validated_payload = self.boundary_filter.enforce_schema(raw_data)
       layer_results = self.evaluation_engine.process_payload(validated_payload)
       metrics_summary = self.metrics_scorer.calculate_summary(layer_results, validated_payload)
       target_destinations = self.target_router.resolve_targets(context_key)
       rendered_view = self.view_renderer.generate_view(layout_template, validated_payload, metrics_summary)
       dispatch_receipt = self.dispatcher.transmit(target_destinations, rendered_view, channel_name)
       self.audit_ledger.log_transaction_event(validated_payload, metrics_summary, dispatch_receipt)
       return {
           "formatted_view": rendered_view,
           "dispatch_receipt": dispatch_receipt.__dict__,
           "metrics_summary": metrics_summary.__dict__,
           "pipeline_uniqueness_ratio": self.audit_ledger.verify_processing_uniqueness(),
       }

