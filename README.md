# Contrast-Associated AKI Risk Calculator

### [Open the Live Application →](https://abusuraihsakhri.github.io/contrast-nephropathy-prevention-agent/)

A small research and educational tool for calculating the original Mehran PCI contrast-nephropathy risk score, empirical contrast-dose limits, contrast/eGFR ratio, and protocol-planning outputs.

> **Clinical scope:** This repository is not a prescribing system and is not a substitute for clinical judgment or local policy. The original Mehran score was derived and validated in patients undergoing percutaneous coronary intervention (PCI); its absolute risk estimates should not be generalized to routine intravenous contrast-enhanced CT.

## Features

- Original Mehran risk score with historical PCI-cohort risk bands
- Empirical maximum contrast dose: `5 × weight (kg) / serum creatinine (mg/dL)`
- Contrast-volume/eGFR ratio
- Hydration schedule calculator retained for protocol comparison
- Medication-review prompts rather than automatic stop orders
- Single-case CLI and CSV batch processing
- FastAPI endpoint for local/server use
- Static browser calculator for GitHub Pages
- Light and dark themes; browser calculations run locally

## Browser application

The GitHub Pages application performs its calculations in the browser. No patient data is sent to this repository or to an application backend.

The web interface intentionally focuses on the risk score and contrast-dose calculations. For intravenous iodinated contrast, current ACR–NKF guidance emphasizes AKI/eGFR, volume-overload risk, clinical urgency, route of administration, and local protocol when deciding whether prophylactic IV saline is appropriate.

## Install

```bash
git clone https://github.com/abusuraihsakhri/contrast-nephropathy-prevention-agent.git
cd contrast-nephropathy-prevention-agent

python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

For the API server:

```bash
python -m pip install -e ".[server]"
contrast-nephropathy-prevention-agent serve --host 127.0.0.1 --port 8000
```

## CLI

Single case:

```bash
contrast-nephropathy-prevention-agent audit \
  --patient-id PT-001 \
  --weight 70 \
  --age 68 \
  --creatinine 1.3 \
  --egfr 52 \
  --contrast-volume 160 \
  --diabetes
```

Batch CSV:

```bash
contrast-nephropathy-prevention-agent batch -i sample.csv -o cin_results.csv
```

The batch input columns are demonstrated in `sample.csv`.

## API

Start the server, then send a `POST` request to `/api/evaluate` using the structure in `sample_payload.json`. A health endpoint is available at `/health`.

The checked-in `openapi_spec.json` documents the stable request shape. FastAPI also exposes its generated interactive documentation when running locally.

## Testing

```bash
python -m pip install -e ".[server,dev]"
python -m pip check
python -m compileall -q cin_guard.py contrast_nephropathy_prevention_agent
pytest -q
python -m unittest test_cin_guard -v
```

CI runs the test suite on Python 3.10, 3.11, and 3.12.

## Evidence and limitations

The repository retains the original Mehran score for compatibility and research use. That model was developed for CIN after PCI, not for general IV contrast exposure. Modern literature also distinguishes contrast-associated AKI from AKI causally attributable to contrast.

For IV iodinated contrast, the ACR–NKF consensus recommends IV normal saline prophylaxis primarily for patients with AKI or eGFR <30 mL/min/1.73 m² when not contraindicated, with individualized consideration for selected higher-risk patients with eGFR 30–44 mL/min/1.73 m². Exact hydration rate and duration are not universal.

References:

- Mehran R, et al. *J Am Coll Cardiol.* 2004;44(7):1393-1399. PMID: 15464318.
- Davenport MS, et al. ACR–NKF consensus on intravenous iodinated contrast media in kidney disease. *Radiology.* 2020;294(3):660-668. DOI: 10.1148/radiol.2019192094.
- American College of Radiology. *Manual on Contrast Media*.

## Technology

Python 3.9+, standard-library clinical engine, optional FastAPI/Uvicorn server, and a dependency-free static web application.

## License

MIT. See [LICENSE](LICENSE).
