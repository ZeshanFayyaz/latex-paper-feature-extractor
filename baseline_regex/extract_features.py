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
    match = re.search(r'\\title\{(.+?)\}', text, re.DOTALL) #Searches for \title{...}. DOTALL allows to match newlines, so the abstract can span multiple lines
    return match.group(1).strip() if match else "N/A"

def extract_abstract(text):
    match = re.search(r'\\begin\{abstract\}(.+?)\\end\{abstract\}', text, re.DOTALL)
    return re.sub(r'\s+', ' ', match.group(1).strip()) if match else "N/A"

def extract_year(text):
    # Try common patterns like 20xx or 19xx
    match = re.search(r'(19|20)\d{2}', text) #Could be easily wrong -> grabs the first instance of the year it sees
    return match.group(0) if match else "N/A" #re.search stops at the first match

def extract_citations(text):
    # Capture all \cite{} and \citep{} style citations
    citations = re.findall(r'\\cite[tp]?\{(.+?)\}', text) #Can either be citet or citep or cite (optional addition of t or p)
    return list(set(citations)) if citations else [] #removes duplicates

def extract_equations(text, max_equations=5):
    # Match equations inside equation environments or \[ \]
    eqs = re.findall(r'\\begin\{equation\}(.+?)\\end\{equation\}', text, re.DOTALL) #Find equations inside \begin{equation} ... \end(equation)
    eqs += re.findall(r'\\\[(.+?)\\\]', text, re.DOTALL) #Find equations written as \[ ... \]
    return [e.strip() for e in eqs[:max_equations]] #remove extra whitespace and newlines around each equation string

def extract_table(text):
    match = re.search(r'\\begin\{table\}(.+?)\\end\{table\}', text, re.DOTALL) #Return the entire first table block
    return match.group(0).strip() if match else "N/A" #Group 0 returns the entire match

def clean_main_text(text):
    # Remove environments like figure, table, equation to get main body only
    text = re.sub(r'\\begin\{figure\}.*?\\end\{figure\}', '', text, flags=re.DOTALL) #Remove figures
    text = re.sub(r'\\begin\{table\}.*?\\end\{table\}', '', text, flags=re.DOTALL) #Removes tables
    text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', '', text, flags=re.DOTALL) #Remove display math
    text = re.sub(r'\\\[.*?\\\]', '', text, flags=re.DOTALL) #Removes equations
    return text

def extract_main_text_sample(text, sample_len=500):
    clean_text = clean_main_text(text)
    return {
        "start": clean_text[:sample_len].strip(), #Return first 500 chars
        "end": clean_text[-sample_len:].strip() #Return last 500 chars
    }

# ---------- Core parser ----------

def process_tex_file(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read() #Open a .tex file and read its content

    # Go through each of the extraction functions and store its result in dictionary (data)
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

    tex_files = [f for f in os.listdir(input_dir) if f.endswith(".tex")] #Gather all .tex files
    
    # If none exist, print warning and exit
    if not tex_files:
        print("No .tex files found in 'input/' folder.")
        sys.exit(1)

    # For each file -> first process
    for filename in tex_files:
        path = os.path.join(input_dir, filename)
        print(f"Processing: {filename}")

        result = process_tex_file(path)
        out_path = os.path.join(output_dir, filename.replace(".tex", ".json"))

        with open(out_path, "w", encoding="utf-8") as out_f:
            json.dump(result, out_f, indent=2, ensure_ascii=False)

        print(f"Saved extracted features → {out_path}")

if __name__ == "__main__":
    main()
