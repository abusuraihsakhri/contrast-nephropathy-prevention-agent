#!/usr/bin/env python3
"""
Comprehensive Unit Test Suite for CIN-Guard: Contrast-Associated AKI & Hydration Engine
Tests Mehran Risk Score calculation, Cigarroa Maximum Contrast Dose (MCD), Gurm eGFR Ratio,
KDIGO/ESUR hydration regimens, and nephrotoxic drug hold auditing.
"""

import unittest
from cin_guard import (
    CINGuardEngine,
    MehranScoreResult,
    ContrastDosingSafetyResult,
    HydrationProtocol,
    MedicationAdjustmentRecommendation,
    CINGuardReport,
    main,
    ValidationError,
)


class TestMehranRiskScoring(unittest.TestCase):
    """Test suite for Mehran Risk Score algorithm and risk tiers."""

    def test_low_risk_patient(self):
        # 50yo, normal renal function, low contrast volume (50mL) -> 0 points
        res = CINGuardEngine.calculate_mehran_score(
            hypotension=False,
            iabp=False,
            congestive_heart_failure=False,
            age_years=50,
            anemia=False,
            diabetes=False,
            contrast_volume_ml=50.0,
            egfr_ml_min=90.0,
        )
        self.assertEqual(res.total_score, 0)
        self.assertEqual(res.risk_category, "Low")
        self.assertEqual(res.cin_risk_percent, 7.5)
        self.assertEqual(res.dialysis_risk_percent, 0.04)

    def test_moderate_risk_patient(self):
        # Diabetes (+3), Age 78 (+4), Contrast 120mL (+1) -> 8 points
        res = CINGuardEngine.calculate_mehran_score(
            age_years=78,
            diabetes=True,
            contrast_volume_ml=120.0,
            egfr_ml_min=75.0,
        )
        self.assertEqual(res.total_score, 8)
        self.assertEqual(res.risk_category, "Moderate")
        self.assertEqual(res.cin_risk_percent, 14.0)

    def test_high_risk_patient(self):
        # Hypotension (+5), Anemia (+3), CKD Stage 3b (eGFR 35 -> +4), Contrast 150mL (+1) -> 13 points
        res = CINGuardEngine.calculate_mehran_score(
            hypotension=True,
            anemia=True,
            egfr_ml_min=35.0,
            contrast_volume_ml=150.0,
        )
        self.assertEqual(res.total_score, 13)
        self.assertEqual(res.risk_category, "High")
        self.assertEqual(res.cin_risk_percent, 26.1)
        self.assertEqual(res.dialysis_risk_percent, 1.09)

    def test_very_high_risk_patient(self):
        # IABP (+5), CHF (+5), Severe CKD (eGFR 18 -> +6), Diabetes (+3), Contrast 250mL (+2) -> 21 points
        res = CINGuardEngine.calculate_mehran_score(
            iabp=True,
            congestive_heart_failure=True,
            egfr_ml_min=18.0,
            diabetes=True,
            contrast_volume_ml=250.0,
        )
        self.assertGreaterEqual(res.total_score, 16)
        self.assertEqual(res.risk_category, "Very High")
        self.assertEqual(res.cin_risk_percent, 57.3)
        self.assertEqual(res.dialysis_risk_percent, 12.60)

    def test_creatinine_fallback_when_egfr_missing(self):
        # Creatinine 2.0 mg/dL without eGFR, 50mL contrast -> +4 points
        res = CINGuardEngine.calculate_mehran_score(
            serum_creatinine_mg_dl=2.0,
            contrast_volume_ml=50.0,
            egfr_ml_min=None,
        )
        self.assertEqual(res.total_score, 4)
        self.assertIn("elevated_creatinine", res.score_breakdown)

    def test_egfr_tier_boundaries(self):
        # eGFR 55, 50mL contrast -> +2
        res55 = CINGuardEngine.calculate_mehran_score(egfr_ml_min=55.0, contrast_volume_ml=50.0)
        self.assertEqual(res55.score_breakdown.get("egfr_impairment"), 2)

        # eGFR 30, 50mL contrast -> +4
        res30 = CINGuardEngine.calculate_mehran_score(egfr_ml_min=30.0, contrast_volume_ml=50.0)
        self.assertEqual(res30.score_breakdown.get("egfr_impairment"), 4)

        # eGFR 15, 50mL contrast -> +6
        res15 = CINGuardEngine.calculate_mehran_score(egfr_ml_min=15.0, contrast_volume_ml=50.0)
        self.assertEqual(res15.score_breakdown.get("egfr_impairment"), 6)


class TestContrastSafetyLimits(unittest.TestCase):
    """Test suite for Cigarroa MCD and Gurm Contrast/eGFR ratio."""

    def test_safe_contrast_dosing(self):
        # 70 kg, SCr 1.0 -> MCD = 350 mL. Given: 100 mL, eGFR: 60 -> Ratio: 1.67
        safety = CINGuardEngine.calculate_contrast_safety_limits(
            contrast_volume_ml=100.0,
            weight_kg=70.0,
            serum_creatinine_mg_dl=1.0,
            egfr_ml_min=60.0,
        )
        self.assertEqual(safety.max_contrast_dose_cigarroa_ml, 350.0)
        self.assertAlmostEqual(safety.contrast_egfr_ratio, 1.67, delta=0.01)
        self.assertFalse(safety.is_mcd_exceeded)
        self.assertFalse(safety.is_ratio_high_risk)
        self.assertEqual(safety.safety_verdict, "SAFE")

    def test_mcd_exceeded_borderline(self):
        # 60 kg, SCr 1.5 -> MCD = 200 mL. Given: 250 mL, eGFR: 50 -> Ratio: 5.0
        safety = CINGuardEngine.calculate_contrast_safety_limits(
            contrast_volume_ml=250.0,
            weight_kg=60.0,
            serum_creatinine_mg_dl=1.5,
            egfr_ml_min=50.0,
        )
        self.assertTrue(safety.is_mcd_exceeded)
        self.assertTrue(safety.is_ratio_high_risk)
        self.assertEqual(safety.safety_verdict, "CRITICAL_OVERDOSE_RISK")

    def test_contrast_ratio_severe_ckd_threshold(self):
        # eGFR 25 (<30), contrast 80 mL -> Ratio: 3.2 (>= 3.0 threshold in severe CKD)
        safety = CINGuardEngine.calculate_contrast_safety_limits(
            contrast_volume_ml=80.0,
            weight_kg=70.0,
            serum_creatinine_mg_dl=2.2,
            egfr_ml_min=25.0,
        )
        self.assertTrue(safety.is_ratio_high_risk)


class TestHydrationProtocols(unittest.TestCase):
    """Test suite for standard, urgent, and bicarbonate hydration protocols."""

    def test_standard_saline_protocol(self):
        # 70 kg, 12h pre + 12h post at 1.0 mL/kg/h
        h = CINGuardEngine.generate_hydration_protocol(weight_kg=70.0, is_urgent_procedure=False)
        self.assertEqual(h.regimen_type, "ISOTONIC_SALINE_STANDARD")
        self.assertEqual(h.pre_rate_ml_per_kg_hr, 1.0)
        self.assertEqual(h.pre_total_volume_ml, 840.0)
        self.assertEqual(h.post_total_volume_ml, 840.0)
        self.assertEqual(h.total_hydration_volume_ml, 1680.0)

    def test_urgent_saline_protocol(self):
        # 80 kg, urgent: 3.0 mL/kg/h for 1h pre, 1.5 mL/kg/h for 4h post
        h = CINGuardEngine.generate_hydration_protocol(weight_kg=80.0, is_urgent_procedure=True)
        self.assertEqual(h.regimen_type, "ISOTONIC_SALINE_URGENT")
        self.assertEqual(h.pre_rate_ml_per_kg_hr, 3.0)
        self.assertEqual(h.pre_total_volume_ml, 240.0)
        self.assertEqual(h.post_total_volume_ml, 480.0)
        self.assertEqual(h.total_hydration_volume_ml, 720.0)

    def test_bicarbonate_protocol(self):
        # 70 kg, bicarbonate: 3.0 mL/kg/h for 1h pre, 1.0 mL/kg/h for 6h post
        h = CINGuardEngine.generate_hydration_protocol(weight_kg=70.0, preferred_fluid="BICARBONATE")
        self.assertEqual(h.regimen_type, "SODIUM_BICARBONATE")
        self.assertEqual(h.pre_total_volume_ml, 210.0)
        self.assertEqual(h.post_total_volume_ml, 420.0)
        self.assertEqual(h.total_hydration_volume_ml, 630.0)

    def test_congestive_heart_failure_volume_reduction(self):
        # CHF active -> rates reduced by 50%
        h = CINGuardEngine.generate_hydration_protocol(weight_kg=70.0, congestive_heart_failure=True)
        self.assertEqual(h.pre_rate_ml_per_kg_hr, 0.5)
        self.assertEqual(h.post_rate_ml_per_kg_hr, 0.5)
        self.assertIn("CHF active", h.special_considerations[0])


class TestMedicationAudit(unittest.TestCase):
    """Test suite for nephrotoxic drug hold detection."""

    def test_metformin_hold(self):
        recs = CINGuardEngine.audit_medications(["Metformin 1000mg BID", "Atorvastatin 40mg"])
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0].drug_name, "Metformin")
        self.assertEqual(recs[0].action, "HOLD_DAY_OF")

    def test_nsaid_and_acei_holds(self):
        recs = CINGuardEngine.audit_medications(["Ibuprofen 600mg", "Lisinopril 10mg"])
        actions = {r.drug_name: r.action for r in recs}
        self.assertIn("Ibuprofen 600Mg", actions)
        self.assertEqual(actions["Ibuprofen 600Mg"], "HOLD_48H_PRE")
        self.assertEqual(actions["Lisinopril 10Mg"], "HOLD_DAY_OF")

    def test_aminoglycoside_monitoring(self):
        recs = CINGuardEngine.audit_medications(["Gentamicin IV"])
        self.assertEqual(recs[0].action, "MONITOR")


class TestCINGuardEndToEnd(unittest.TestCase):
    """Test suite for full case evaluation and report generation."""

    def test_evaluate_case_full_workflow(self):
        report = CINGuardEngine.evaluate_case(
            patient_id="PT-CASE-123",
            weight_kg=75.0,
            age_years=72,
            serum_creatinine_mg_dl=1.4,
            egfr_ml_min=48.0,
            contrast_volume_ml=180.0,
            diabetes=True,
            medications=["Metformin", "Naproxen"],
        )
        self.assertEqual(report.patient_id, "PT-CASE-123")
        self.assertEqual(report.overall_risk_status, "ELEVATED_RISK")
        self.assertEqual(len(report.medication_holds), 2)
        json_str = report.to_json()
        self.assertIn("PT-CASE-123", json_str)
        self.assertIn("ELEVATED_RISK", json_str)

    def test_cli_execution(self):
        self.assertEqual(main(["audit", "--patient-id", "CLI-TEST", "--contrast-volume", "120"]), 0)
        self.assertEqual(main(["chat", "What", "is", "the", "mehran", "score?"]), 0)


class TestInputValidation(unittest.TestCase):
    """Test suite for input validation in CINGuardEngine."""

    def test_negative_contrast_volume_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(contrast_volume_ml=-50.0)

    def test_negative_weight_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_contrast_safety_limits(
                contrast_volume_ml=100.0,
                weight_kg=-70.0,
                serum_creatinine_mg_dl=1.0,
                egfr_ml_min=60.0,
            )

    def test_negative_creatinine_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(serum_creatinine_mg_dl=-1.0)

    def test_invalid_age_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(age_years=200)

    def test_negative_age_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(age_years=-5)

    def test_invalid_fluid_type_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.generate_hydration_protocol(weight_kg=70.0, preferred_fluid="INVALID")

    def test_nan_input_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(contrast_volume_ml=float("nan"))

    def test_inf_input_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.calculate_mehran_score(contrast_volume_ml=float("inf"))

    def test_empty_patient_id_rejected(self):
        with self.assertRaises(ValidationError):
            CINGuardEngine.evaluate_case(patient_id="")

    def test_valid_inputs_accepted(self):
        # Should not raise
        res = CINGuardEngine.calculate_mehran_score(
            age_years=65,
            contrast_volume_ml=100.0,
            serum_creatinine_mg_dl=1.0,
            egfr_ml_min=60.0,
        )
        self.assertIsInstance(res, MehranScoreResult)


if __name__ == "__main__":
    unittest.main()
