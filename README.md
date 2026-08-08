# NidaanPath AI
## Diagnostic Journey Stagnation and Escalation Agent

> **It does not diagnose the disease. It detects when the process of finding the cause has stopped progressing.**

---

## 🎯 Competition Overview

NidaanPath AI is a national-competition MVP demonstrating **diagnostic process continuity** — reconstructing fragmented patient medical records into a live Diagnostic Journey Twin, detecting when progress has stalled, and preparing safe clinician escalation packets.

## ❗ Problem Statement

Patients with persistent symptoms consult multiple providers across clinics, labs and hospitals. Their journey becomes fragmented across prescriptions, lab reports, referrals, and consultation notes. Existing platforms **store and share** records — they do not reveal whether the **diagnostic process is actually progressing**.

Critical gaps remain hidden:
- A test completed but never reviewed
- A specialist referral issued but no consultation found
- The same symptom across multiple visits without resolution
- Treatment changed with no response documented
- A follow-up advised but not completed

## 💡 Core Innovation — Diagnostic Journey Twin

NidaanPath converts fragmented records into a **live, evidence-linked journey**:

```
Patient Concern → Consultation → Test Ordered → Test Completed
→ Result Review → Follow-Up → Referral → Specialist Consultation
→ Remaining Uncertainty → Clinician Escalation
```

## 🤖 One-Agent Architecture

**One NidaanPath Coordinator Agent** + **Six Controlled Tools** + **Three Safety Gates**

### Six Tools
| # | Tool | Purpose |
|---|------|---------|
| 1 | `extract_medical_document()` | Structured extraction from medical documents |
| 2 | `build_diagnostic_journey()` | Chronological journey construction |
| 3 | `detect_process_gaps()` | Deterministic stagnation detection |
| 4 | `match_new_evidence()` | Match new documents to open gaps |
| 5 | `select_next_evidence_question()` | Single best question to ask |
| 6 | `generate_clinician_packet()` | Evidence-grounded escalation packet |

### Three Safety Gates
1. **Patient Confirmation** — No AI-extracted data enters the journey without user confirmation
2. **Deterministic Stagnation Rules** — Gemini cannot independently classify a journey as stagnant
3. **Clinician Escalation** — Any clinical uncertainty is escalated, never auto-resolved

## 🛠 Technology Stack

- **Backend**: Python 3.11+, Flask, Flask-SQLAlchemy, Pydantic
- **AI**: Google Gemini API (`google-genai`) + Mock AI fallback
- **Frontend**: HTML5, CSS3 (custom design system), Vanilla JS, Jinja2
- **Processing**: NetworkX, RapidFuzz, Pandas, PyPDF, Pillow
- **Reports**: ReportLab (PDF generation)
- **Tests**: Pytest

## 📁 Project Structure

```
nidaanpath-ai/
├── run.py                  # Entry point
├── requirements.txt
├── .env.example
├── pytest.ini
├── app/
│   ├── __init__.py         # App factory
│   ├── config.py           # Environment configuration
│   ├── routes/             # Flask blueprints
│   ├── models/             # SQLAlchemy + Pydantic schemas
│   ├── services/           # AI, journey, stagnation, matching
│   ├── templates/          # Jinja2 HTML templates
│   ├── static/             # CSS, JavaScript
│   └── translations/       # en.json, ta.json
├── demo_reports/           # Auto-extracted synthetic dataset
├── uploads/                # User uploads (temporary)
├── generated_reports/      # Generated PDFs
└── tests/                  # Pytest test suite
```

## 🚀 Installation

### 1. Create virtual environment

```bash
python -m venv .venv
```

### 2. Activate (Windows)

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

### 5. Run

```bash
python run.py
```

Open: http://localhost:5000

## 🎯 Judge Demo Mode (No API Key Required)

The full demo works without any API key using Mock AI Mode:

1. Open http://localhost:5000/demo/
2. **Step 1**: Click "Load Reports 01–08" → See **Possible Stagnation** state
3. **Step 2**: Observe agent question: *"Did you complete the ENT consultation?"*
4. **Step 3**: Click "Add Specialist Evidence (Report 09)" → State changes to **Active Progress**
5. **Step 4**: Click "Add Result Review Evidence (Report 10)" → Lab review documented

## 🔑 Gemini API Setup (Optional)

```env
# .env
GEMINI_API_KEY=your_actual_key_here
GEMINI_MODEL=gemini-1.5-flash
USE_MOCK_LLM=false
```

**Security**: The API key is server-side only. It is never exposed in JavaScript, HTML, logs, or screenshots.

## 🧪 Testing

```bash
pytest
```

## 🛡 Responsible AI

NidaanPath **does NOT**:
- Diagnose any disease
- Predict medical outcomes
- Prescribe medication
- Recommend tests
- Replace healthcare professionals
- Identify medical negligence

NidaanPath **ONLY**:
- Reconstructs the diagnostic process timeline
- Detects process gaps using transparent Python rules
- Asks clarifying questions about process (not disease)
- Prepares evidence for safe clinician review

## ⚠ Limitations

- Prototype MVP — not a regulated medical device
- All demo data is synthetic only
- Extraction accuracy depends on document legibility
- Mock mode uses deterministic responses only

## 🔮 Future Work

- Multimodal document scanning with Gemini Vision
- ABHA (Ayushman Bharat Health Account) integration
- Regional language support (Hindi, Telugu, Kannada)
- FHIR R4 structured data export
- Differential privacy for patient data

---

*NidaanPath AI — Prototype Diagnostic Process Continuity System*
*Not a medical device. Not for clinical use.*
