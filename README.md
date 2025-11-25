 # Automated MCQ Generator (LangChain + OpenAI)

A small demo project that generates multiple-choice questions (MCQs) from a block of text using LangChain and OpenAI (Chat models). This repository includes:

- An importable package: `src/mcqgenerator` with generator & helper utilities
- A demo Streamlit UI: `StreamlitAPP.py` (interactive front-end with model selector, cost estimate, preview and per-question edit/regenerate controls)
- A notebook `experiment/mcq.ipynb` showing common usage and examples
- A CLI demo: `run_example.py` to exercise the generator from the command line

---

## Quick start (Windows / conda)

Recommendation: use Python 3.8–3.11 in a named conda environment called `env`.

```bash
# create & activate the conda environment
conda create -n env python=3.8 -y
conda activate env

# change to the inner project folder (path may be nested if you downloaded a zip)
cd Automated-MCQ-Generator-Using-Langchain-OpenAI-API-main

# install dependencies and a local editable package for development
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .
```

If you see an ImportError mentioning `langchain_community` ("No module named 'langchain_community'"), install the optional community package used by LangChain:

```bash
python -m pip install langchain-community
```

## Configuration — OpenAI key

Set your OpenAI API key via a `.env` file at the project root (next to `StreamlitAPP.py`):

```text
OPENAI_API_KEY=sk-<your_openai_api_key_here>
```

Or set it in your shell:

```bash
export OPENAI_API_KEY="sk-..."   # bash / WSL
setx OPENAI_API_KEY "sk-..."     # Windows cmd / PowerShell
```

> Note: OpenAI calls consume tokens/credits — you can get a 429 (insufficient_quota) if your account has run out of quota. The app detects quota errors and falls back to a demo response so the UI remains usable.

## Run the Streamlit UI (recommended)

```bash
streamlit run StreamlitAPP.py
```

Open http://localhost:8501. Key Streamlit features:

- Upload `.txt`/`.pdf` or paste text (PDF extraction uses PyPDF2; scanned PDFs may need OCR)
- Sidebar controls to choose model (gpt-3.5-turbo / gpt-4), set temperature, number of MCQs, and enable cost estimates
- Preview parsed text and a rough token & cost estimate before generating
- After generating: review table, edit questions inline, accept questions, or regenerate an individual question
- Export the final quiz as CSV

If the model returns extra explanation or formatting around JSON, the app tries to extract the JSON automatically and provide a friendly error if parsing fails.

## CLI demo

```bash
python run_example.py
```

`run_example.py` will check for `OPENAI_API_KEY`, attempt generation, and print parsed output and a compact tabular preview when possible.

## Development notes

- You can control the model and temperature used by the generator via environment variables: `OPENAI_MODEL` and `OPENAI_TEMP`.
- The generator is implemented with LangChain chains in `src/mcqgenerator/MCQGenerator.py` and uses helper utilities in `src/mcqgenerator/utils.py` for file reading and robust JSON extraction from LLM outputs.

## Troubleshooting

- Blank Streamlit page: ensure `streamlit` is installed and `StreamlitAPP.py` contains UI code.
- Errors about `langchain_community`: run `python -m pip install langchain-community`.
- 429 / insufficient_quota: check OpenAI Billing & Usage (https://platform.openai.com/account/usage) and add/update payment method if needed.
- If PDFs do not extract correctly (scanned documents), add OCR support such as `pdfplumber` or `pytesseract`.

## Improvements you might want next

- Add OCR fallback for scanned PDFs
- Add accurate token usage/cost accounting (post-generation and pre-run estimates)
- Add undo/redo and change-history for per-question edits

---

If anything is failing locally paste the terminal output here and I will help you debug it.

Enjoy — happy quiz-making!
# Automated MCQ Generator — quick start

This repository contains a small package `src/mcqgenerator` showing how to use LangChain + OpenAI to automatically generate multiple-choice questions (MCQs) from text.

Quick steps to run the project locally

1) Create (or activate) conda environment named `env` using Python 3.8–3.11

```bash
conda create -n env python=3.8 -y
conda activate env
```

2) Install dependencies

```bash
# move into the inner project folder if necessary
cd Automated-MCQ-Generator-Using-Langchain-OpenAI-API-main

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e .

If you run into an error mentioning `No module named 'langchain_community'` or `langchain_community` when generating, install the community package used by LangChain:

```bash
python -m pip install langchain-community
```
```

3) Add your OpenAI API key

Create a `.env` file at the project root (next to `StreamlitAPP.py`) and add:

```
OPENAI_API_KEY=sk-<your_key_here>
```

4) Try a simple CLI demo

```bash
python run_example.py
```

5) Run the Streamlit demo (the UI is scaffolded and will show a sample or call the generator if you provide a key)

```bash
streamlit run StreamlitAPP.py
```

Notes
- The `experiment/mcq.ipynb` notebook contains an extended example of how the chain is built.
- The Streamlit app will run in demo mode if no OPENAI_API_KEY is found; provide a key to enable generation.

