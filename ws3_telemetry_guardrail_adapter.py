from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Type

# =====================================================================
# GOVERNANCE REGISTRY AND DECORATOR
# =====================================================================
MODULE_REGISTRY: Dict[str, Type] = {}


def register_as_module(cls: Type) -> Type:
   """Governance handshake validation decorator."""
   MODULE_REGISTRY[cls.__name__] = cls
   setattr(cls, "_gaps_authenticated", True)
   setattr(cls, "_registered", True)
   return cls


class WS3Violation(Exception):
   """Raised when WS3 attempts any non-observational behavior."""


class WS3Mode(Enum):
   OBSERVE_ONLY = "observe_only"
   DISABLED = "disabled"


class WS3SignalType(Enum):
   CAPACITY = "capacity"
   LOAD = "load"
   ACCURACY = "accuracy"
   DRIFT = "drift"
   SYSTEM_HEALTH = "system_health"


# =====================================================================
# GSA UNIVERSAL ADAPTER MODULES
# =====================================================================
@register_as_module
class WS3SafetyGuardModule:
   """Enforces hard deadman safety guarantees and mutation action detection."""

   FORBIDDEN_ACTIONS = {
       "modify",
       "write_back",
       "alter_policy",
       "influence",
       "control",
       "override",
       "escalate_decision",
   }

   def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
       headers = payload.setdefault(
           "_gaps_headers",
           {"metadata": {}, "risk_metrics": {}, "structural_indices": {}},
       )
       attempted_action = str(payload.get("attempted_action", "observe"))

       violation_detected = any(
           action in attempted_action.lower()
           for action in self.FORBIDDEN_ACTIONS
       )

       if violation_detected:
           headers["risk_metrics"]["deadman_triggered"] = True
           headers["risk_metrics"]["safety_violations"] = 1
           payload["mode"] = WS3Mode.DISABLED.value
           payload["halted"] = True
           raise WS3Violation(
               f"WS3 disabled due to safety violation: forbidden_action_detected ({attempted_action})"
           )

       headers["risk_metrics"]["deadman_triggered"] = False
       headers["risk_metrics"]["safety_violations"] = 0
       payload["mode"] = WS3Mode.OBSERVE_ONLY.value
       payload["halted"] = False
       return payload


@register_as_module
class WS3TelemetryObserveModule:
   """Processes cross-domain observational telemetry signals and generates immutable reports."""

   def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
       if payload.get("halted"):
           return payload

       headers = payload.setdefault(
           "_gaps_headers",
           {"metadata": {}, "risk_metrics": {}, "structural_indices": {}},
       )
       domain = payload.get("domain", "universal_telemetry")
       signal_type_str = payload.get("signal_type", "load")
       metrics = payload.get("metrics", {})
       notes = payload.get("notes", [])

       report_data = {
           "timestamp": time.time(),
           "domain": domain,
           "signal_type": signal_type_str,
           "metrics": dict(metrics),
           "notes": list(notes),
       }

       payload["telemetry_report"] = report_data
       headers["metadata"]["domain"] = domain
       headers["metadata"]["signal_type"] = signal_type_str
       headers["structural_indices"]["metrics_count"] = len(metrics)
       return payload


@register_as_module
class WS3AnalyticsCalculatorModule:
   """Executes pure analytical evaluations for capacity pressure and metric drift."""

   def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
       if payload.get("halted"):
           return payload

       headers = payload.setdefault(
           "_gaps_headers",
           {"metadata": {}, "risk_metrics": {}, "structural_indices": {}},
       )
       metrics = payload.get("metrics", {})
       utilization = float(
           metrics.get("utilization", metrics.get("gpu_utilization", 0.0))
       )

       bounded_util = max(0.0, min(1.0, utilization))
       capacity_pressure = bounded_util**2

       baseline = float(payload.get("baseline", 0.0))
       current = float(payload.get("current", utilization))
       drift_score = (
           0.0 if baseline == 0.0 else abs(current - baseline) / abs(baseline)
       )

       analytics_summary = {
           "capacity_pressure": capacity_pressure,
           "drift_score": drift_score,
       }

       payload["analytics_summary"] = analytics_summary
       headers["risk_metrics"]["capacity_pressure"] = capacity_pressure
       headers["risk_metrics"]["drift_score"] = drift_score
       return payload


# =====================================================================
# CENTRALIZED BINDING ENGINE AND ORCHESTRATOR
# =====================================================================
@register_as_module
class CoreOrchestratorBinder:
   """Centralized binding engine validating handshakes and sequencing execution."""

   def __init__(self) -> None:
       self.safety_guard = WS3SafetyGuardModule()
       self.observe_module = WS3TelemetryObserveModule()
       self.analytics_module = WS3AnalyticsCalculatorModule()

   def validate_handshakes(self) -> bool:
       """Validates module authentication before pipeline execution."""
       modules = [
           WS3SafetyGuardModule,
           WS3TelemetryObserveModule,
           WS3AnalyticsCalculatorModule,
       ]
       for mod in modules:
           if not getattr(mod, "_gaps_authenticated", False):
               raise PermissionError(
                   f"Handshake failed for module: {mod.__name__}"
               )
       return True

   def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
       """Sequences pipeline execution and outputs serialized clinical summary."""
       self.validate_handshakes()

       headers = payload.setdefault(
           "_gaps_headers",
           {
               "metadata": {
                   "orchestrator": self.__class__.__name__,
                   "timestamp": time.time(),
               },
               "risk_metrics": {},
               "structural_indices": {},
           },
       )

       sequence = [
           self.safety_guard,
           self.observe_module,
           self.analytics_module,
       ]
       for module in sequence:
           payload = module.process(payload)

       clinical_summary = {
           "execution_status": "HALTED" if payload.get("halted") else "COMPLETED",
           "mode": payload.get("mode"),
           "domain": headers["metadata"].get("domain"),
           "deadman_triggered": headers["risk_metrics"].get("deadman_triggered"),
           "capacity_pressure": headers["risk_metrics"].get("capacity_pressure"),
           "drift_score": headers["risk_metrics"].get("drift_score"),
           "gaps_headers": headers,
       }

       payload["clinical_summary"] = json.dumps(
           clinical_summary, indent=2, default=str
       )
       return payload


if __name__ == "__main__":
   sample_payload = {
       "domain": "autonomous_fleet",
       "signal_type": WS3SignalType.LOAD.value,
       "metrics": {"gpu_utilization": 0.72, "sensor_latency_ms": 14.3},
       "attempted_action": "observe_telemetry",
       "baseline": 0.50,
       "current": 0.72,
       "notes": ["fleet compute snapshot"],
   }

   binder = CoreOrchestratorBinder()
   result = binder.process(sample_payload)
   print("--- OBSERVABILITY TELEMETRY CYCLE COMPLETED ---")
   print(result["clinical_summary"])
