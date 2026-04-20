# Eka AI Debugger

> 🚀 AI-powered debugging platform for developers and teams
> Analyze code, logs and stack traces using multiple AI providers and turn solutions into a reusable knowledge base

Eka AI Debugger is a production-grade, multi-tenant debugging and analysis platform designed for real-world development teams, SaaS companies and technical support environments.

It allows you to analyze errors using both cloud and local AI models, detect recurring issues and build a persistent internal knowledge base.

---

## ⚡ Core Features

* Multi AI Provider Support (OpenAI, Anthropic, OpenRouter, NVIDIA, HuggingFace)
* Local Model Integration (LM Studio, Ollama)
* Debug Sessions with code, logs and stack traces
* Similar Error Detection (historical matching)
* Knowledge Base from resolved issues
* Token & Cost Tracking Dashboard
* Multi-tenant workspace system
* Premium SaaS dashboard interface

---

## 🧠 Why this project?

Most AI debugging tools are either limited, expensive or not self-hostable.

Eka AI Debugger provides:

* Full control over your AI providers
* Local model support (no API cost required)
* Reusable internal knowledge base
* Multi-tenant architecture for real SaaS usage

---

## 📸 Screenshots

| Login                             | Debug Session                     |
| --------------------------------- | --------------------------------- |
| ![](/screenshot/Screenshot_1.png) | ![](/screenshot/Screenshot_2.png) |

| Settings                          | Knowledge Base                    |
| --------------------------------- | --------------------------------- |
| ![](/screenshot/Screenshot_3.png) | ![](/screenshot/Screenshot_4.png) |

---

## 🧪 Example Analysis Output

```json
{
  "root_cause": "Null reference in database connection",
  "severity": "high",
  "suggested_fix": "Check database connection before query execution",
  "optimization": "Use connection pooling",
  "security_note": "Avoid exposing database errors in production"
}
```

---

## 🏗️ Architecture Overview

### Multi-Tenant System

The platform uses a workspace-based architecture where all debug sessions, logs and knowledge entries are isolated per tenant.

### AI Provider Layer

The system supports both cloud and local providers:

* OpenAI
* Anthropic (Claude)
* OpenRouter
* NVIDIA AI
* HuggingFace
* LM Studio (local)
* Ollama (local)

Provider-based architecture allows flexible switching and scaling.

### Debug Engine

* Accepts code, logs, stack traces and notes
* Performs structured AI analysis
* Stores results for future reuse
* Detects similar historical issues

---

## 🛠️ Tech Stack

* Backend: Python (FastAPI)
* Frontend: Tailwind CSS (premium SaaS UI)
* Database: MySQL / SQLite
* AI Integration: OpenAI, Anthropic, HTTPX

---

## ⚙️ Installation

### Requirements

* Python 3.10+
* MySQL or SQLite

---

### Setup

```bash
cd eka-ai-debugger
pip install -r requirements.txt
```

Create `.env` file:

```env
DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/eka_ai_debugger
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

Run server:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## 🔐 Demo Access

Admin
[info@ekayazilim.com.tr](mailto:info@ekayazilim.com.tr) / ekasunucu

---

## 💼 Use Cases

* Debug production errors quickly
* Analyze logs with AI assistance
* Build internal debugging knowledge base
* Reduce repeated debugging effort
* Improve developer productivity

---

## 🛣️ Roadmap

* Advanced AI error clustering
* Team collaboration tools
* Export reports (PDF / JSON)
* Webhook & alert system
* CI/CD integration

---

## ⭐ Support

If you find this project useful, consider giving it a ⭐ on GitHub.

---

## 💼 Commercial Use

Custom SaaS development, AI integrations and enterprise solutions available.

📧 [info@ekayazilim.com.tr](mailto:info@ekayazilim.com.tr)

---

