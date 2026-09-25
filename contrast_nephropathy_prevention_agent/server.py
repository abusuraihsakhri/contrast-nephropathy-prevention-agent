"""FastAPI application exposing the canonical CA-AKI calculator."""

from typing import List


def create_app():
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel, Field
    except ImportError as exc:
        raise RuntimeError('Install server dependencies with: pip install -e ".[server]"') from exc

    from cin_guard import CINGuardEngine, ValidationError

    app = FastAPI(
        title="Contrast Nephropathy Prevention Calculator",
        description=(
            "Research and educational calculator for the original Mehran PCI risk score, "
            "contrast-dose heuristics, and hydration planning."
        ),
        version="2.1.0",
    )

    class EvaluateRequest(BaseModel):
        patient_id: str = "PT-001"
        weight_kg: float = Field(default=70.0, gt=0)
        age_years: int = Field(default=65, ge=0, le=150)
        serum_creatinine_mg_dl: float = Field(default=1.2, gt=0)
        egfr_ml_min: float = Field(default=55.0, ge=0)
        contrast_volume_ml: float = Field(default=150.0, ge=0)
        hypotension: bool = False
        iabp: bool = False
        congestive_heart_failure: bool = False
        anemia: bool = False
        diabetes: bool = False
        is_urgent: bool = False
        preferred_fluid: str = "SALINE"
        medications: List[str] = Field(default_factory=list)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "service": "contrast-nephropathy-prevention-agent",
            "version": "2.1.0",
        }

    @app.post("/api/evaluate")
    def evaluate(req: EvaluateRequest):
        try:
            report = CINGuardEngine.evaluate_case(**req.model_dump())
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return report.to_dict()

    return app


app = create_app()
