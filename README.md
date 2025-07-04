# 🗂️ Feedback - Backend (FastAPI + MongoDB)

This is the backend server for **Feedback** – a simple, secure, and structured feedback-sharing system between managers and employees.

---

## 🚀 Features

- Role-based user system (Manager, Employee)
- Feedback submission and history tracking
- Commenting system with Markdown support
- Anonymous peer feedback
- Feedback requests
- Notifications (in-app)
- Export feedback to PDF
- Full CRUD for users and feedback
- CORS enabled for frontend connection

---

## 🛠️ Tech Stack

| Layer        | Technology           |
| ------------ | -------------------- |
| Language     | Python 3.10+         |
| Framework    | FastAPI              |
| ORM          | Beanie (MongoDB ODM) |
| Database     | MongoDB              |
| Async Driver | Motor                |
| Auth         | (Optional) JWT       |
| PDF Export   | ReportLab            |
| Markdown     | markdown2            |
| Dev Tools    | Uvicorn, .env        |

---

## 🧱 Directory Structure

```
app/
├── main.py               # App entrypoint
├── db/
│   └── mongo.py          # MongoDB setup
├── models/               # Beanie document models
├── schemas/              # Pydantic request/response schemas
├── routers/              # API routes
│   ├── user.py
│   ├── feedback.py
│   └── notification.py
└── utils/                # Utility functions (auth, email, etc.)
```

---

## ⚙️ Setup Instructions

### ✅ Prerequisites

- Python 3.10+
- MongoDB (local or Atlas)

---

### 🔧 Installation

1. **Clone the repo**

```bash
git clone https://github.com/PrashantJha183/Feedback-backend.git
cd Feedback-backend
```

2. **Create virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure environment**

Create a `.env` file in the root directory:

```env
MONGODB_URI=mongodb://localhost:27017/feedbackdb
```

---

### ▶️ Run the Server

```bash
uvicorn app.main:app --reload
```

Visit the API docs at [https://feedback-2uwd.onrender.com/docs](https://feedback-2uwd.onrender.com/docs)

---

## 📄 API Documentation

FastAPI auto-generates docs at:

- Swagger UI: `https://feedback-2uwd.onrender.com/docs`
- ReDoc: `https://feedback-2uwd.onrender.com/docs`

---

## 📌 Design Decisions

- **FastAPI** was chosen for its speed, automatic docs, and async support.
- **MongoDB** fits well with document-based structures like nested feedback/comments.
- **Beanie** provides Pydantic-based ODM, simplifying model validation and querying.
- **Role-based access** is handled using user roles (`manager`, `employee`).
- **PDF export** implemented using `reportlab`.
- **Markdown rendering** allows enhanced comment formatting.

---

## 🧪 Testing

Use Postman or Thunder Client with the `/docs` page to test endpoints. Sample payloads are provided in docs.

---
