# Quick Start Guide

Get the Clinical FHIR Extractor running in 5 minutes!

## 1. Prerequisites

- Python 3.10+ installed
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## 2. Installation

### Windows (PowerShell)
```powershell
# Run the setup script
.\setup.ps1

# Or manual setup
uv sync  # or: python -m venv venv && .\venv\Scripts\activate && pip install -e .
```

### macOS/Linux
```bash
# Make script executable and run
chmod +x setup.sh
./setup.sh

# Or manual setup
uv sync  # or: python3 -m venv venv && source venv/bin/activate && pip install -e .
```

## 3. Configure

Set your OpenAI API key:

```powershell
# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."

# macOS/Linux Bash
export OPENAI_API_KEY="sk-..."
```

Or create a `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

## 4. Run

```bash
# Using uv
uv run python main.py

# Or using Python directly (with activated venv)
python main.py
```

The API will be available at **http://localhost:8000**

## 5. Test

Open your browser to:
- **http://localhost:8000/docs** - Interactive API documentation
- **http://localhost:8000** - API info

Or test with curl:

```bash
# Test the example clinical note
curl -X POST "http://localhost:8000/extract-fhir" \
  -F "file=@example_clinical_note.txt" \
  > output.json

# View the results
cat output.json
```

## 6. API Usage

### Python Example

```python
import requests

# Extract FHIR data from a clinical document
url = "http://localhost:8000/extract-fhir"
files = {"file": open("example_clinical_note.txt", "rb")}
response = requests.post(url, files=files)

fhir_bundle = response.json()
print(fhir_bundle)
```

### JavaScript Example

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/extract-fhir', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

## Output Format

The API returns a FHIR R4 Bundle containing:

```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "Patient",
        "id": "patient-1",
        "name": [{"text": "John Doe", "family": "Doe", "given": ["John"]}],
        "birthDate": "1980-01-01",
        "gender": "male"
      }
    },
    {
      "resource": {
        "resourceType": "Observation",
        "id": "obs-1",
        "status": "final",
        "code": {"text": "Blood Pressure"},
        "subject": {"reference": "Patient/patient-1"},
        "valueQuantity": {"value": 120, "unit": "mmHg"}
      }
    }
    // ... more resources (Condition, MedicationStatement, etc.)
  ]
}
```

## Troubleshooting

**API Key Error?**
- Ensure `OPENAI_API_KEY` is set correctly
- Check the key is valid on OpenAI platform

**Import Errors?**
- Run `uv sync` or `pip install -e .`
- Ensure virtual environment is activated

**Port 8000 in use?**
- Change port: `uvicorn app.main:app --port 8080`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check out the [example clinical note](example_clinical_note.txt)

---

**Questions?** Open an issue on GitHub or refer to the main README.

