"""Contrast nephropathy prevention calculator package."""

from cin_guard import (
    CINGuardEngine,
    CINGuardReport,
    ContrastDosingSafetyResult,
    HydrationProtocol,
    MedicationAdjustmentRecommendation,
    MehranScoreResult,
    ValidationError,
)

__all__ = [
    "CINGuardEngine",
    "CINGuardReport",
    "ContrastDosingSafetyResult",
    "HydrationProtocol",
    "MedicationAdjustmentRecommendation",
    "MehranScoreResult",
    "ValidationError",
]

__version__ = "2.1.0"
