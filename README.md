# Multi Purpose RAG Application

## Overview

The Multi-Purpose RAG Application simplifies getting answers from your information. Just pick a source - like a document, a website, or a YouTube video - and this AI system turns it into a smart knowledge base. This means you get precise answers to your questions, based directly on the content you provide.

## Steps to Run the App (Locally) :-

### 1. Clone the repository:
```
git clone https://github.com/GDGouravDey/multi-purpose-rag.git
cd multi-purpose-rag
```
### 2. Set up a virtual environment:
```
python -m venv venv
venv\Scripts\activate (On Windows)
source venv/bin/activate (On macOS/Linux)
```
OR
```
conda create -n venv_name
conda activate venv_name
```
### 3. Install the dependencies:
```
pip install -r requirements.txt
```
### 4. Configure environment variables:
```
I. Create a .env at the root of the repository
II. Set GOOGLE_API_KEY = "YOUR_GEMINI_API_KEY"
```
### 5. Run the Streamlit App
```
streamlit run app.py
```

