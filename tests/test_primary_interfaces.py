import csv

from contrast_nephropathy_prevention_agent import CINGuardEngine
from contrast_nephropathy_prevention_agent.cli import main


def test_package_exports_canonical_engine():
    report = CINGuardEngine.evaluate_case(
        patient_id="PKG-TEST",
        weight_kg=70,
        age_years=65,
        serum_creatinine_mg_dl=1.0,
        egfr_ml_min=60,
        contrast_volume_ml=100,
    )
    assert report.patient_id == "PKG-TEST"
    assert report.mehran_result.total_score == 1


def test_batch_cli_writes_calculated_columns(tmp_path):
    source = tmp_path / "input.csv"
    output = tmp_path / "output.csv"
    source.write_text(
        "patient_id,weight_kg,age_years,serum_creatinine_mg_dl,egfr_ml_min,contrast_volume_ml,hypotension,iabp,congestive_heart_failure,anemia,diabetes,is_urgent,preferred_fluid,medications\n"
        "BATCH-01,70,78,1.0,75,120,false,false,false,false,true,false,SALINE,Metformin\n",
        encoding="utf-8",
    )

    assert main(["batch", "-i", str(source), "-o", str(output)]) == 0

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 1
    assert rows[0]["patient_id"] == "BATCH-01"
    assert rows[0]["mehran_score"] == "8"
    assert rows[0]["risk_category"] == "Moderate"
    assert rows[0]["overall_risk_status"] == "ELEVATED_RISK"


def test_server_exposes_clinical_evaluate_route():
    from fastapi.testclient import TestClient
    from contrast_nephropathy_prevention_agent.server import app

    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/evaluate" in paths

    response = TestClient(app).post(
        "/api/evaluate",
        json={
            "patient_id": "API-TEST",
            "weight_kg": 70,
            "age_years": 65,
            "serum_creatinine_mg_dl": 1.0,
            "egfr_ml_min": 60,
            "contrast_volume_ml": 100,
            "medications": [],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["patient_id"] == "API-TEST"
    assert payload["mehran_result"]["total_score"] == 1
