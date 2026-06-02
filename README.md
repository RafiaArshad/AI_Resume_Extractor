# 🧠 AI Resume Extractor

An AI-powered full-stack web application that extracts, analyzes, and structures data from resumes (PDF/DOCX).  
It uses a **FastAPI backend** for processing and a **React frontend** for an interactive user interface.

---

## 🚀 Features

- 📄 Resume Upload (PDF / DOCX)
- 🧠 AI-based Resume Parsing
- 📊 Structured Data Extraction
- 🔍 Skill Detection & Classification
- 🗂️ Experience & Education Parsing
- ⚡ Fast API Response
- 🌐 Full-stack deployment
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

## 🌐 Live Demo

👉 Frontend (Vercel):   https://ai-resume-extractor.vercel.app/

---

## 📌 Project Overview

This project automatically:
- Uploads resumes (PDF/DOCX)
- Extracts text using OCR & parsing tools
- Applies NLP-based processing
- Extracts:
  - Name
  - Email / Phone
  - Skills
  - Experience
  - Education
  - Projects
- Stores structured data in database
- Provides API for frontend integration

---
### Deployment
- Frontend: Vercel
- Backend: Render

