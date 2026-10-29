# AI TestPilot — QA Test Case Generator & Analyzer

A Streamlit hackathon prototype for generating test cases from requirements and analyzing basic coverage gaps and duplicate titles.

## Features
- Paste requirements or upload TXT, Markdown, PDF, DOCX, CSV, or XLSX
- Generate structured positive, negative, boundary, functional, security, usability, and regression cases
- Edit test cases in the UI
- Export to CSV and Excel
- View a keyword-based coverage estimate, potential gaps, and similar test titles
- Demo mode works without a Gemini API key

## Setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

## Configure Gemini
1. Create a Google AI Studio API key, if your organization's policy permits it.
2. Paste the key in the sidebar, or set it in PowerShell for the current terminal:

```powershell
$env:GOOGLE_API_KEY="YOUR_API_KEY"
streamlit run app.py
```

For a corporate hackathon, check TCS policy before sending any internal requirements or documents to an external AI service. Use synthetic or anonymized examples for demos.

## Demo requirements
Paste the following into the Requirements tab:

> As a registered customer, I want to log in using my email and password. The email is mandatory and must have a valid email format. The password is mandatory and must be at least 8 characters long. After 5 consecutive failed login attempts, the account must be temporarily locked. Successful login redirects the customer to the dashboard. Error messages must not reveal whether an email address is registered.

Generate 15 cases, review the Test Cases tab, then open Coverage Analysis. Download the CSV or Excel output.

## Important limitations
- The built-in coverage score is a heuristic based on keyword overlap, not a formal requirement-to-test traceability engine.
- Demo mode uses templates to demonstrate the UI; it is not a substitute for model-generated requirement-specific cases.
- AI outputs can be incorrect or incomplete. QA review and execution are required.
- Do not upload secrets, production customer data, credentials, or confidential documents unless explicitly approved.

## Suggested hackathon enhancements
1. Add explicit requirement IDs and a traceability matrix.
2. Use embeddings to match test cases to requirements semantically.
3. Add risk scoring based on business impact and likelihood.
4. Add a reviewer approval step and audit trail.
5. Integrate with Jira/Azure DevOps only after approval and with least-privilege access.


## Docker setup

Requirements: Docker Desktop installed and running.

Build the image:

```powershell
docker build -t ai-testpilot:1.0 .
```

Run the container:

```powershell
docker run -d --name ai-testpilot -p 8501:8501 ai-testpilot:1.0
```

Open http://localhost:8501.

View logs and stop the container:

```powershell
docker logs ai-testpilot
docker stop ai-testpilot
docker rm ai-testpilot
```

Alternatively, use Docker Compose:

```powershell
docker compose up --build -d
docker compose logs -f
docker compose down
```

The application can run in demo mode without a Gemini API key. For Gemini generation, enter your key in the Streamlit sidebar or set `GOOGLE_API_KEY` in your local environment. Never commit a real API key or `.env` file.

## Push this project to GitHub

Create an empty repository on GitHub, then run these commands in PowerShell from this directory. Replace `YOUR_USERNAME` with your GitHub username.

```powershell
git init
git add .
git status
git commit -m "Add AI TestPilot with Docker support"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ai-testpilot.git
git push -u origin main
```

If `origin` already exists, use `git remote set-url origin https://github.com/YOUR_USERNAME/ai-testpilot.git` instead of `git remote add origin ...`. Check `git status` before committing and ensure secrets are not staged.
