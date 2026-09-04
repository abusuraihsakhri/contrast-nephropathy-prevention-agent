# Contrast Nephropathy Prevention Agent

> **Domain:** Cardiovascular Medicine & Hemodynamic Analytics
> **Reference Guidelines & Standards:** KDIGO 2012 / ESUR 2018 / ACC/AHA 2021 CA-AKI Prevention Guidelines

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Contrast Nephropathy Prevention Agent** is a clinical decision support platform that implements:
- **Mehran Risk Score** calculation for Contrast-Induced Nephropathy (CIN / CA-AKI)
- **Maximum Contrast Dose** calculations (Cigarroa formula)
- **Contrast/eGFR Ratio** safety assessment
- **Personalized hydration protocol** generation (saline vs bicarbonate)
- **Medication adjustment** recommendations for nephrotoxic drugs

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`MehranScoreResult`**: Mehran Risk Score assessment for Contrast-Induced Nephropathy.
- **`ContrastDosingSafetyResult`**: Maximum contrast media volume and safety threshold calculations.
- **`HydrationProtocol`**: Personalized pre- and post-procedure hydration regimen.
- **`MedicationAdjustmentRecommendation`**: Recommendations for withholding nephrotoxic / renal-eliminated drugs.
- **`CINGuardReport`**: Unified Clinical Decision Support Report for Contrast-Induced Nephropathy.
- **`CINGuardEngine`**: Core computational engine for Contrast-Induced Nephropathy risk and prevention.

---

## 📐 Mathematical Formulation & Logic

### Mehran Risk Score
```
Score Points:
  - Hypotension (SBP < 80 requiring inotropes): +5
  - IABP: +5
  - CHF (Class III/IV): +5
  - Age > 75: +4
  - Anemia: +3
  - Diabetes: +3
  - Contrast Volume: +1 per 100 mL
  - Renal dysfunction (eGFR): +2 to +6 based on severity

Risk Stratification:
  - Score ≤ 5: Low risk (CIN 7.5%, Dialysis 0.04%)
  - Score 6-10: Moderate risk (CIN 14.0%, Dialysis 0.12%)
  - Score 11-15: High risk (CIN 26.1%, Dialysis 1.09%)
  - Score > 15: Very High risk (CIN 57.3%, Dialysis 12.60%)
```

### Cigarroa Maximum Contrast Dose
```
MCD = (5 mL × Weight in kg) / Serum Creatinine (mg/dL)
```

### Contrast/eGFR Ratio
```
Ratio = Contrast Volume (mL) / eGFR (mL/min)
High risk threshold: ≥ 3.7 (or ≥ 3.0 in severe CKD, eGFR < 30)
```

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/contrast-nephropathy-prevention-agent.git
cd contrast-nephropathy-prevention-agent

# Install dependencies
pip install -e .

# For development (includes test dependencies)
pip install -e ".[dev]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
# Using the main CIN-Guard engine
python cin_guard.py audit --patient-id PT-001 --weight 70 --age 68 --creatinine 1.3 --egfr 52 --contrast-volume 160

# Using the enterprise supervisor
python cli.py audit --task-id TASK-001 --target KEY-01 --primary 28.5 --secondary 14.2
```

### Parameter Reference (cin_guard.py)
- `--patient-id`: Patient identifier
- `--weight`: Weight in kg
- `--age`: Age in years
- `--creatinine`: Serum creatinine in mg/dL
- `--egfr`: eGFR in mL/min
- `--contrast-volume`: Contrast volume in mL
- `--hypotension`: Flag for hypotension
- `--iabp`: Flag for IABP support
- `--chf`: Flag for congestive heart failure
- `--anemia`: Flag for anemia
- `--diabetes`: Flag for diabetes
- `--urgent`: Flag for urgent procedure
- `--fluid`: Fluid type (SALINE or BICARBONATE)
- `--meds`: List of medications

### Input Data Schema (Batch Processing)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `case_id` | Case identifier | Required |
| `patient_synthetic_id` | Synthetic patient identifier | Required |
| `metric_primary` | Primary measurement value | Required |
| `metric_secondary` | Secondary measurement value | Required |
| `is_stat` | STAT priority flag | Required |
| `status_flag` | Status descriptor | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Input Validation:** Comprehensive validation of all clinical parameters with meaningful error messages.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

The audit trail requires a secret key to be configured via environment variable:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key-here"
```

**Note:** Never hardcode secret keys in production. Always use environment variables or a secure secrets manager.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
# Run pytest tests
pytest -v

# Run unittest tests
python -m unittest test_cin_guard -v

# Run all tests
pytest tests/ -v && python -m unittest test_cin_guard -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t contrast-nephropathy-prevention-agent .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-secret-key" contrast-nephropathy-prevention-agent
```

---

## 📁 Project Structure

```
contrast-nephropathy-prevention-agent/
├── agents/                          # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py                       # FastAPI REST server
│   ├── base.py                      # Security, PHI guard, audit trail
│   ├── learning.py                  # Bayesian calibration engine
│   ├── llm_factory.py               # LLM provider factory
│   ├── metrics.py                   # Prometheus metrics
│   ├── models.py                    # Pydantic data models
│   ├── streamer.py                  # WebSocket telemetry
│   ├── supervisor.py                # Supervisor orchestrator
│   └── workers.py                   # Specialized worker agents
├── contrast_nephropathy_prevention_agent/  # Alternative package structure
│   ├── __init__.py
│   ├── agents.py                    # Coordinator and sub-agents
│   ├── cli.py                       # CLI interface
│   ├── engine.py                    # Clinical domain engine
│   ├── models.py                    # Data models
│   └── server.py                    # FastAPI application
├── tests/                           # Pytest test suite
│   ├── test_contrast_nephropathy_prevention_agent.py
│   └── test_enrichment.py
├── cin_guard.py                     # Main CIN-Guard engine (standalone)
├── cli.py                           # Enterprise CLI
├── enrichment.py                    # Enrichment feature engines
├── simulator.py                     # High-throughput simulator
├── test_cin_guard.py                # Unittest suite for CIN-Guard
├── pyproject.toml                   # Project configuration
├── Dockerfile                       # Container definition
└── docker-compose.yml               # Multi-container orchestration
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
