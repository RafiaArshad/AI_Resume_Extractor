# 🧠 AI Resume Extractor

An AI-powered full-stack web application that extracts, analyzes, and structures data from resumes (PDF/DOCX).  
It uses a **FastAPI backend** for processing and a **React frontend** for an interactive user interface.

---

## 🚀 Features

- 📄 Upload resumes (PDF / DOCX)
- 🧠 Extract text using AI-based parsing
- 🧾 Structured candidate information extraction
- 🔍 Intelligent resume analysis
- 🌐 Modern and responsive UI
- ⚡ Fast API-based backend processing

---

## 🏗️ Tech Stack

### 💻 Frontend
- React (Vite)
- TypeScript
- Tailwind CSS

### ⚙️ Backend
- FastAPI (Python)
- Uvicorn
- PyMuPDF (fitz)
- aiosqlite (async database support)
- Python-dotenv

---

## 📁 Project Structure

```bash
AI_Resume_Extractor/
│
├── frontend/              # React frontend (UI)
│   ├── src/
│   ├── public/
│   └── package.json
│
├── backend/               # FastAPI backend (API server)
│   ├── app/
│   ├── myvenv/            # (NOT pushed to GitHub)
│   ├── requirements.txt
│   └── main.py
│
├── .gitignore
└── README.md
