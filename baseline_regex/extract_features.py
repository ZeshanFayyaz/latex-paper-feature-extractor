#!/usr/bin/env python3
"""
extract_features.py

A simple regex-based parser to extract structured metadata from LaTeX scientific papers.
This script scans a .tex file (or multiple files) and extracts:

- Title
- Abstract
- Year of publication
- Main text sample (first + last 500 chars)
- Citations
- Equations (first 5)
- First table

Output: JSON (saved in `output/` folder)
"""

import re
import os
import json
import sys

# ---------- Helper functions ----------

def extract_title(text):
    match = re.search(r'\\title\{(.+?)\}', text, re.DOTALL)
    return match.group(1).strip() if match else "N/A"

def extract_abstract(text):
    match = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', text, re.DOTALL)
    return re.sub(r'\s+', ' ', match.group(1).strip()) if match else "N/A"

def extract_year(text):
    # Try common patterns like 20xx or 19xx
    match = re.search(r'(19|20)\d{2}', text)
    return match.group(0) if match else "N/A"

def extract_citations(text):
    # Capture all \cite{} and \citep{} style citations
    citations = re.findall(r'\\cite[tp]?\{(.+?)\}', text)
    return list(set(citations)) if citations else []

def extract_equations(text, max_equations=5):
    # Match equations inside equation environments or \[ \]
    eqs = re.findall(r'\\begin\{equation\}(.+?)\\end\{equation\}', text, re.DOTALL)
    eqs += re.findall(r'\\\[(.+?)\\\]', text, re.DOTALL)
    return [e.strip() for e in eqs[:max_equations]]

def extract_table(text):
    match = re.search(r'\\begin\{table\}(.+?)\\end\{table\}', text, re.DOTALL)
    return match.group(0).strip() if match else "N/A"

def clean_main_text(text):
    # Remove environments like figure, table, equation to get main body
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL)
    return text

def extract_main_text_sample(text, sample_len=500):
    clean_text = clean_main_text(text)
    return {
        "start": clean_text[:sample_len].strip(),
        "end": clean_text[-sample_len:].strip()
    }

# ---------- Core parser ----------

def process_tex_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    data = {
        "title": extract_title(content),
        "abstract": extract_abstract(content),
        "year": extract_year(content),
        "main_text_sample": extract_main_text_sample(content),
        "citations": extract_citations(content),
        "equations": extract_equations(content),
        "first_table": extract_table(content),
    }
    return data

# ---------- Entry point ----------

def main():
    input_dir = "../input"
    output_dir = "../output"

    os.makedirs(output_dir, exist_ok=True)

    tex_files = [f for f in os.listdir(input_dir) if f.endswith(".tex")]
    if not tex_files:
        print("⚠️ No .tex files found in 'input/' folder.")
        sys.exit(1)

    for filename in tex_files:
        path = os.path.join(input_dir, filename)
        print(f"📄 Processing: {filename}")

        result = process_tex_file(path)
        out_path = os.path.join(output_dir, filename.replace(".tex", ".json"))

        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(result, out_f, indent=2, ensure_ascii=False)

        print(f"✅ Saved extracted features → {out_path}")

if __name__ == "__main__":
    main()
