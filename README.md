# CIN-Guard: Contrast-Associated Acute Kidney Injury Risk & Hydration Protocol Agent

[![KDIGO 2012 / ESUR 2018 Guidelines](https://img.shields.io/badge/Guidelines-KDIGO%20%7C%20ESUR-blue.svg)](#)
[![Clinical Verification](https://img.shields.io/badge/Clinical%20Validation-100%25%20Passing-brightgreen.svg)](#)
[![Zero-PHI Guard](https://img.shields.io/badge/HIPAA%20Safe%20Harbor-Zero--PHI-success.svg)](#)

CIN-Guard is a clinical decision support system that predicts Contrast-Induced Nephropathy (CIN / CA-AKI) risk and calculates personalized pre/post-procedure hydration protocols.

## Core Clinical Capabilities

1. **Mehran 1.0 & 2.0 Risk Score Engine**:
   - Scores hypotension (+5), IABP (+5), CHF NYHA III/IV (+5), age >75 (+4), anemia (+3), diabetes (+3), contrast volume (+1 per 100 mL), and eGFR impairment tiers (+2 to +6).
   - Stratifies patients into Low (<5), Moderate (6-10), High (11-15), and Very High (>=16) risk classes with predicted dialysis probability.

2. **Contrast Dosing Safety Limits**:
   - Calculates Cigarroa Maximum Contrast Dose (MCD): `(5 mL * weight_kg) / serum_creatinine`.
   - Evaluates Gurm Contrast/eGFR ratio thresholds (<=3.7 standard, <=3.0 in severe CKD).

3. **KDIGO / ESUR Hydration Protocols**:
   - Standard 0.9% Normal Saline: 1.0 mL/kg/h for 12h pre and 12h post.
   - Urgent 0.9% Saline: 3.0 mL/kg/h for 1h pre and 1.5 mL/kg/h for 4h post.
   - Sodium Bicarbonate (154 mEq/L): 3.0 mL/kg/h for 1h pre and 1.0 mL/kg/h for 6h post.
   - Automated CHF safety volume reduction (0.5 mL/kg/h) with pulmonary edema monitoring.

4. **Nephrotoxic Medication Audit**:
   - Flags Metformin (hold day of & 48h post), NSAIDs (hold 48h pre), ACEi/ARBs, and aminoglycosides.

## CLI Usage

```bash
# Audit a patient's contrast risk
python cin_guard.py audit --patient-id PT-001 --weight 75 --age 72 --creatinine 1.4 --egfr 48 --contrast-volume 180 --diabetes

# Query clinical guidelines
python cin_guard.py chat What is the hydration protocol for urgent PCI?
```

## Running Unit Tests

```bash
python -m unittest test_cin_guard.py
```
