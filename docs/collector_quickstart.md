# Collector Quick Start

## Prerequisites
- Python 3.11+
- `requests` library (install via `pip install -r backend/requirements.txt` if requirements file exists)

## Steps
1. (Optional) Copy `.env.example` to `.env` and set `CIVITAI_API_KEY` if you have one.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install requests
   ```
4. Run the collector:
   ```bash
   python backend/src/collector/collector.py
   ```
5. Inspect outputs:
   - Raw data: `data/raw/*.json`
   - State file: `data/state/collector_state.json`
   - Logs: `logs/collector/run.log`

## Next Improvements (Roadmap)
- Add retry/backoff for 429 & 5xx
- Implement legacy adapter logic in `adapter_v8.py`
- Introduce duplicate detection & normalization
- Switch endpoint to actual desired CivitAI resource
- Add unit tests for schema & state