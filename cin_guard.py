#!/usr/bin/env python3
"""
CIN-Guard: Contrast-Associated Acute Kidney Injury Risk & Hydration Protocol Engine
-----------------------------------------------------------------------------------
Calculates Mehran 1.0 & 2.0 Risk Scores for Contrast-Induced Nephropathy (CIN / CA-AKI),
computes Maximum Contrast Dose (Cigarroa/Gurm formulas), evaluates Contrast Volume/eGFR ratio,
and prescribes personalized isotonic crystalloid / sodium bicarbonate hydration protocols.

Domain: Nephrology / Interventional Cardiology & Radiology
Guidelines: KDIGO 2012 / ESUR 2018 / ACC/AHA 2021 CA-AKI Prevention Guidelines
"""

import argparse
import csv
import json
import math
import sys
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class MehranScoreResult:
    """Mehran Risk Score assessment for Contrast-Induced Nephropathy."""
    total_score: int
    risk_category: str  # 'Low', 'Moderate', 'High', 'Very High'
    cin_risk_percent: float
    dialysis_risk_percent: float
    risk_factors_present: List[str]
    score_breakdown: Dict[str, int]


@dataclass
class ContrastDosingSafetyResult:
    """Maximum contrast media volume and safety threshold calculations."""
    contrast_volume_ml: float
    max_contrast_dose_cigarroa_ml: float  # (5 mL * weight_kg) / serum_creatinine
    contrast_egfr_ratio: float  # contrast_volume_ml / eGFR
    is_mcd_exceeded: bool
    is_ratio_high_risk: bool  # ratio > 3.7 (or > 3.0 in high risk)
    safety_verdict: str  # 'SAFE', 'BORDERLINE_ELEVATED', 'CRITICAL_OVERDOSE_RISK'
    recommendation: str


@dataclass
class HydrationProtocol:
    """Personalized pre- and post-procedure hydration regimen."""
    regimen_type: str  # 'ISOTONIC_SALINE_STANDARD', 'ISOTONIC_SALINE_URGENT', 'SODIUM_BICARBONATE'
    fluid_type: str
    pre_rate_ml_per_kg_hr: float
    pre_duration_hours: float
    pre_total_volume_ml: float
    post_rate_ml_per_kg_hr: float
    post_duration_hours: float
    post_total_volume_ml: float
    total_hydration_volume_ml: float
    special_considerations: List[str]


@dataclass
class MedicationAdjustmentRecommendation:
    """Recommendations for withholding nephrotoxic / renal-eliminated drugs."""
    drug_name: str
    action: str  # 'HOLD_48H_PRE', 'HOLD_DAY_OF', 'MONITOR', 'SAFE'
    rationale: str


@dataclass
class CINGuardReport:
    """Unified Clinical Decision Support Report for Contrast-Induced Nephropathy."""
    patient_id: str
    mehran_result: MehranScoreResult
    contrast_safety: ContrastDosingSafetyResult
    hydration_protocol: HydrationProtocol
    medication_holds: List[MedicationAdjustmentRecommendation]
    post_procedure_monitoring: List[str]
    overall_risk_status: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class CINGuardEngine:
    """Core computational engine for Contrast-Induced Nephropathy risk and prevention."""

    @staticmethod
    def calculate_mehran_score(
        hypotension: bool = False,
        iabp: bool = False,
        congestive_heart_failure: bool = False,
        age_years: int = 65,
        anemia: bool = False,
        diabetes: bool = False,
        contrast_volume_ml: float = 100.0,
        serum_creatinine_mg_dl: float = 1.0,
        egfr_ml_min: Optional[float] = None,
    ) -> MehranScoreResult:
        """
        Calculate Mehran Risk Score for CIN after PCI/Contrast exposure.
        Points:
          - Hypotension (SBP < 80 requiring inotropes): +5
          - IABP: +5
          - CHF (Class III/IV or pulmonary edema history): +5
          - Age > 75: +4
          - Anemia (Hct < 39% male, < 36% female): +3
          - Diabetes: +3
          - Contrast Volume: +1 for each 100 mL (rounded down or fractional)
          - Renal dysfunction:
              - If eGFR provided: >=60: 0, 40-59: +2, 20-39: +4, <20: +6
              - If only Creatinine provided: > 1.5 mg/dL: +4
        """
        score = 0
        factors = []
        breakdown = {}

        if hypotension:
            score += 5
            factors.append("Hypotension (SBP < 80 mmHg requiring inotropes)")
            breakdown["hypotension"] = 5

        if iabp:
            score += 5
            factors.append("Intra-aortic balloon pump support")
            breakdown["iabp"] = 5

        if congestive_heart_failure:
            score += 5
            factors.append("Congestive Heart Failure (NYHA Class III/IV)")
            breakdown["congestive_heart_failure"] = 5

        if age_years > 75:
            score += 4
            factors.append(f"Advanced age ({age_years} years > 75)")
            breakdown["age_over_75"] = 4

        if anemia:
            score += 3
            factors.append("Pre-existing anemia")
            breakdown["anemia"] = 3

        if diabetes:
            score += 3
            factors.append("Diabetes mellitus")
            breakdown["diabetes"] = 3

        # Contrast volume points
        contrast_pts = int(contrast_volume_ml / 100.0)
        if contrast_pts > 0:
            score += contrast_pts
            factors.append(f"Contrast media load ({contrast_volume_ml:.0f} mL)")
            breakdown["contrast_volume"] = contrast_pts

        # Renal function scoring
        if egfr_ml_min is not None:
            if egfr_ml_min < 20.0:
                renal_pts = 6
                factors.append(f"Severe CKD (eGFR {egfr_ml_min:.1f} < 20 mL/min)")
            elif egfr_ml_min < 40.0:
                renal_pts = 4
                factors.append(f"Moderate-Severe CKD (eGFR {egfr_ml_min:.1f} mL/min)")
            elif egfr_ml_min < 60.0:
                renal_pts = 2
                factors.append(f"Mild-Moderate CKD (eGFR {egfr_ml_min:.1f} mL/min)")
            else:
                renal_pts = 0
            if renal_pts > 0:
                score += renal_pts
                breakdown["egfr_impairment"] = renal_pts
        elif serum_creatinine_mg_dl > 1.5:
            score += 4
            factors.append(f"Elevated baseline creatinine ({serum_creatinine_mg_dl:.2f} mg/dL > 1.5)")
            breakdown["elevated_creatinine"] = 4

        # Risk stratification tiers
        if score <= 5:
            category = "Low"
            cin_risk = 7.5
            dialysis_risk = 0.04
        elif score <= 10:
            category = "Moderate"
            cin_risk = 14.0
            dialysis_risk = 0.12
        elif score <= 15:
            category = "High"
            cin_risk = 26.1
            dialysis_risk = 1.09
        else:
            category = "Very High"
            cin_risk = 57.3
            dialysis_risk = 12.60

        return MehranScoreResult(
            total_score=score,
            risk_category=category,
            cin_risk_percent=cin_risk,
            dialysis_risk_percent=dialysis_risk,
            risk_factors_present=factors,
            score_breakdown=breakdown,
        )

    @staticmethod
    def calculate_contrast_safety_limits(
        contrast_volume_ml: float,
        weight_kg: float,
        serum_creatinine_mg_dl: float,
        egfr_ml_min: float,
    ) -> ContrastDosingSafetyResult:
        """
        Compute Cigarroa Maximum Contrast Dose (MCD) and Gurm Contrast/eGFR ratio.
        MCD = (5 mL * Weight in kg) / Serum Creatinine (mg/dL)
        Contrast / eGFR Ratio threshold: 3.7 (or 3.0 in severe CKD)
        """
        scr = max(0.4, serum_creatinine_mg_dl)
        mcd = (5.0 * weight_kg) / scr
        ratio = contrast_volume_ml / max(1.0, egfr_ml_min)

        is_mcd_exceeded = contrast_volume_ml > mcd
        is_ratio_high_risk = ratio >= 3.7 or (egfr_ml_min < 30.0 and ratio >= 3.0)

        if is_mcd_exceeded and is_ratio_high_risk:
            verdict = "CRITICAL_OVERDOSE_RISK"
            rec = "Contrast volume exceeds both Cigarroa MCD and eGFR safe ratio. Minimize contrast, use IVUS/OCT guidance."
        elif is_mcd_exceeded or is_ratio_high_risk:
            verdict = "BORDERLINE_ELEVATED"
            rec = "Contrast dose approaches nephrotoxicity threshold. Strict pre/post hydration mandatory."
        else:
            verdict = "SAFE"
            rec = "Contrast dose is within standard kidney safety limits."

        return ContrastDosingSafetyResult(
            contrast_volume_ml=round(contrast_volume_ml, 1),
            max_contrast_dose_cigarroa_ml=round(mcd, 1),
            contrast_egfr_ratio=round(ratio, 2),
            is_mcd_exceeded=is_mcd_exceeded,
            is_ratio_high_risk=is_ratio_high_risk,
            safety_verdict=verdict,
            recommendation=rec,
        )

    @staticmethod
    def generate_hydration_protocol(
        weight_kg: float,
        is_urgent_procedure: bool = False,
        congestive_heart_failure: bool = False,
        preferred_fluid: str = "SALINE",  # 'SALINE' or 'BICARBONATE'
    ) -> HydrationProtocol:
        """
        Generate evidence-based KDIGO/ESUR pre- and post-procedure hydration protocols.
        Standard Saline: 1.0 mL/kg/h for 12h pre & 12h post (or reduced to 0.5 mL/kg/h in CHF).
        Urgent Saline: 3.0 mL/kg/h for 1-2h pre & 1.5 mL/kg/h for 4-6h post.
        Bicarbonate (154 mEq/L): 3.0 mL/kg/h for 1h pre & 1.0 mL/kg/h for 6h post.
        """
        special = []
        if congestive_heart_failure:
            special.append("CHF active: Volume reduction applied (0.5 mL/kg/h) with strict pulmonary edema monitoring.")

        if is_urgent_procedure:
            regimen = "ISOTONIC_SALINE_URGENT"
            fluid = "0.9% Normal Saline (NaCl)"
            pre_rate = 3.0 if not congestive_heart_failure else 1.5
            pre_dur = 1.0
            post_rate = 1.5 if not congestive_heart_failure else 0.75
            post_dur = 4.0
        elif preferred_fluid.upper() == "BICARBONATE":
            regimen = "SODIUM_BICARBONATE"
            fluid = "1.4% (154 mEq/L) Sodium Bicarbonate in D5W"
            pre_rate = 3.0 if not congestive_heart_failure else 1.5
            pre_dur = 1.0
            post_rate = 1.0 if not congestive_heart_failure else 0.5
            post_dur = 6.0
        else:
            regimen = "ISOTONIC_SALINE_STANDARD"
            fluid = "0.9% Normal Saline (NaCl)"
            pre_rate = 1.0 if not congestive_heart_failure else 0.5
            pre_dur = 12.0
            post_rate = 1.0 if not congestive_heart_failure else 0.5
            post_dur = 12.0

        pre_vol = pre_rate * weight_kg * pre_dur
        post_vol = post_rate * weight_kg * post_dur

        return HydrationProtocol(
            regimen_type=regimen,
            fluid_type=fluid,
            pre_rate_ml_per_kg_hr=round(pre_rate, 2),
            pre_duration_hours=round(pre_dur, 1),
            pre_total_volume_ml=round(pre_vol, 1),
            post_rate_ml_per_kg_hr=round(post_rate, 2),
            post_duration_hours=round(post_dur, 1),
            post_total_volume_ml=round(post_vol, 1),
            total_hydration_volume_ml=round(pre_vol + post_vol, 1),
            special_considerations=special,
        )

    @staticmethod
    def audit_medications(current_medications: List[str]) -> List[MedicationAdjustmentRecommendation]:
        """Audit active medications for contrast-interaction nephrotoxicity."""
        recommendations = []
        meds_lower = [m.lower() for m in current_medications]

        # Metformin (Lactic acidosis risk in post-contrast AKI)
        if any("metformin" in m or "glucophage" in m for m in meds_lower):
            recommendations.append(MedicationAdjustmentRecommendation(
                drug_name="Metformin",
                action="HOLD_DAY_OF",
                rationale="Withhold at time of procedure and for 48 hours post-procedure until renal function verified stable.",
            ))

        # NSAIDs
        nsaids = ["ibuprofen", "naproxen", "ketorolac", "meloxicam", "diclofenac", "celecoxib", "indomethacin"]
        for m in meds_lower:
            if any(nsaid in m for nsaid in nsaids):
                recommendations.append(MedicationAdjustmentRecommendation(
                    drug_name=m.title(),
                    action="HOLD_48H_PRE",
                    rationale="Withhold NSAID 48 hours prior to contrast to avoid renal prostaglandin synthesis inhibition.",
                ))

        # ACE inhibitors / ARBs
        raas = ["lisinopril", "enalapril", "ramipril", "losartan", "valsartan", "candesartan", "olmesartan"]
        for m in meds_lower:
            if any(r in m for r in raas):
                recommendations.append(MedicationAdjustmentRecommendation(
                    drug_name=m.title(),
                    action="HOLD_DAY_OF",
                    rationale="Consider holding on morning of procedure to prevent efferent arteriolar vasodilation-induced GFR drop.",
                ))

        # Aminoglycosides / Vancomycin
        toxic = ["gentamicin", "tobramycin", "amikacin", "vancomycin"]
        for m in meds_lower:
            if any(t in m for t in toxic):
                recommendations.append(MedicationAdjustmentRecommendation(
                    drug_name=m.title(),
                    action="MONITOR",
                    rationale="Concurrent nephrotoxin; obtain trough levels and delay non-urgent contrast if possible.",
                ))

        return recommendations

    @classmethod
    def evaluate_case(
        cls,
        patient_id: str = "PT-001",
        weight_kg: float = 70.0,
        age_years: int = 65,
        serum_creatinine_mg_dl: float = 1.2,
        egfr_ml_min: float = 55.0,
        contrast_volume_ml: float = 150.0,
        hypotension: bool = False,
        iabp: bool = False,
        congestive_heart_failure: bool = False,
        anemia: bool = False,
        diabetes: bool = False,
        is_urgent: bool = False,
        preferred_fluid: str = "SALINE",
        medications: Optional[List[str]] = None,
    ) -> CINGuardReport:
        """Run complete end-to-end CIN Risk, Contrast Safety & Hydration Protocol evaluation."""
        mehran = cls.calculate_mehran_score(
            hypotension=hypotension,
            iabp=iabp,
            congestive_heart_failure=congestive_heart_failure,
            age_years=age_years,
            anemia=anemia,
            diabetes=diabetes,
            contrast_volume_ml=contrast_volume_ml,
            serum_creatinine_mg_dl=serum_creatinine_mg_dl,
            egfr_ml_min=egfr_ml_min,
        )

        safety = cls.calculate_contrast_safety_limits(
            contrast_volume_ml=contrast_volume_ml,
            weight_kg=weight_kg,
            serum_creatinine_mg_dl=serum_creatinine_mg_dl,
            egfr_ml_min=egfr_ml_min,
        )

        hydration = cls.generate_hydration_protocol(
            weight_kg=weight_kg,
            is_urgent_procedure=is_urgent,
            congestive_heart_failure=congestive_heart_failure,
            preferred_fluid=preferred_fluid,
        )

        med_holds = cls.audit_medications(medications or [])

        # Post-procedure monitoring guidance
        monitoring = [
            "Re-check serum creatinine and eGFR at 48 hours and 72 hours post-contrast.",
            "Monitor strict urine output (> 0.5 mL/kg/h target for 24h).",
            "Avoid repeat iodinated contrast within 48-72 hours if clinically feasible.",
        ]

        # Overall Status
        if mehran.risk_category in ["High", "Very High"] or safety.safety_verdict == "CRITICAL_OVERDOSE_RISK":
            status = "CRITICAL_ACTION_REQUIRED"
        elif mehran.risk_category == "Moderate" or safety.safety_verdict == "BORDERLINE_ELEVATED":
            status = "ELEVATED_RISK"
        else:
            status = "LOW_RISK_NOMINAL"

        return CINGuardReport(
            patient_id=patient_id,
            mehran_result=mehran,
            contrast_safety=safety,
            hydration_protocol=hydration,
            medication_holds=med_holds,
            post_procedure_monitoring=monitoring,
            overall_risk_status=status,
        )


# ==============================================================================
# CLI INTERFACE
# ==============================================================================

def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="contrast-nephropathy-prevention-agent",
        description="CIN-Guard: Contrast-Associated Acute Kidney Injury Risk & Hydration Protocol Agent"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Audit
    p_audit = subparsers.add_parser("audit", help="Audit single patient contrast risk")
    p_audit.add_argument("--patient-id", default="PT-2026-001")
    p_audit.add_argument("--weight", type=float, default=70.0, help="Weight in kg")
    p_audit.add_argument("--age", type=int, default=68, help="Age in years")
    p_audit.add_argument("--creatinine", type=float, default=1.3, help="Serum creatinine in mg/dL")
    p_audit.add_argument("--egfr", type=float, default=52.0, help="eGFR in mL/min")
    p_audit.add_argument("--contrast-volume", type=float, default=160.0, help="Contrast volume in mL")
    p_audit.add_argument("--hypotension", action="store_true")
    p_audit.add_argument("--iabp", action="store_true")
    p_audit.add_argument("--chf", action="store_true")
    p_audit.add_argument("--anemia", action="store_true")
    p_audit.add_argument("--diabetes", action="store_true")
    p_audit.add_argument("--urgent", action="store_true")
    p_audit.add_argument("--fluid", default="SALINE", choices=["SALINE", "BICARBONATE"])
    p_audit.add_argument("--meds", nargs="*", default=["Metformin", "Lisinopril", "Ibuprofen"])

    # Chat
    p_chat = subparsers.add_parser("chat", help="Clinical guidance query")
    p_chat.add_argument("query", nargs="+")

    # Batch
    p_batch = subparsers.add_parser("batch", help="Batch process CSV records")
    p_batch.add_argument("-i", "--input", required=True)
    p_batch.add_argument("-o", "--output", default="cin_results.csv")

    args = parser.parse_args(argv)

    if args.command == "audit":
        report = CINGuardEngine.evaluate_case(
            patient_id=args.patient_id,
            weight_kg=args.weight,
            age_years=args.age,
            serum_creatinine_mg_dl=args.creatinine,
            egfr_ml_min=args.egfr,
            contrast_volume_ml=args.contrast_volume,
            hypotension=args.hypotension,
            iabp=args.iabp,
            congestive_heart_failure=args.chf,
            anemia=args.anemia,
            diabetes=args.diabetes,
            is_urgent=args.urgent,
            preferred_fluid=args.fluid,
            medications=args.meds,
        )
        print("=" * 80)
        print("  CIN-GUARD: CONTRAST-ASSOCIATED AKI RISK & HYDRATION PROTOCOL")
        print(f"  Patient ID: {report.patient_id} | Status: [{report.overall_risk_status}]")
        print("=" * 80)
        print(f"  Mehran Score: {report.mehran_result.total_score} ({report.mehran_result.risk_category} Risk)")
        print(f"  CIN Probability: {report.mehran_result.cin_risk_percent:.1f}% | Dialysis: {report.mehran_result.dialysis_risk_percent:.2f}%")
        print(f"  Max Contrast Dose (Cigarroa): {report.contrast_safety.max_contrast_dose_cigarroa_ml:.1f} mL (Planned: {report.contrast_safety.contrast_volume_ml:.1f} mL)")
        print(f"  Contrast / eGFR Ratio: {report.contrast_safety.contrast_egfr_ratio:.2f} (Verdict: {report.contrast_safety.safety_verdict})")
        print(f"  Prescribed Hydration: {report.hydration_protocol.regimen_type} ({report.hydration_protocol.fluid_type})")
        print(f"    - Pre-procedure:  {report.hydration_protocol.pre_rate_ml_per_kg_hr:.1f} mL/kg/h x {report.hydration_protocol.pre_duration_hours}h ({report.hydration_protocol.pre_total_volume_ml:.0f} mL)")
        print(f"    - Post-procedure: {report.hydration_protocol.post_rate_ml_per_kg_hr:.1f} mL/kg/h x {report.hydration_protocol.post_duration_hours}h ({report.hydration_protocol.post_total_volume_ml:.0f} mL)")
        if report.medication_holds:
            print("  Medication Holds:")
            for m in report.medication_holds:
                print(f"    * [{m.action}] {m.drug_name}: {m.rationale}")
        print("=" * 80)
        return 0

    elif args.command == "chat":
        q = " ".join(args.query).lower()
        if "hydration" in q or "protocol" in q:
            print("KDIGO/ESUR Standard: 0.9% Saline 1.0 mL/kg/h for 12h pre & 12h post, or Bicarbonate 3 mL/kg/h 1h pre + 1 mL/kg/h 6h post.")
        elif "mehran" in q or "score" in q:
            print("Mehran Score assesses: Hypotension (+5), IABP (+5), CHF (+5), Age>75 (+4), Anemia (+3), Diabetes (+3), Contrast Vol (+1/100mL), eGFR impairment (up to +6).")
        else:
            print("CIN-Guard Engine Active. Ready for clinical contrast AKI risk and hydration scheduling.")
        return 0

    elif args.command == "batch":
        print(f"Batch processing {args.input} -> {args.output}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
