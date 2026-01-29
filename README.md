# 🏛️ Xaana.AI: Government Intelligence Platform

### *Hybrid Intelligence for High-Stakes Policy Audit*

---

## 🧐 The Problem
Standard LLMs are powerful but dangerous for government work. In policy auditing, **99% accuracy is a failure.** A single "hallucinated" budget figure or regulation can cause legal disaster.

## 💡 The Solution: Hybrid Intelligence
Xaana.AI is not just a wrapper around ChatGPT. It utilizes a **Hybrid Architecture** that separates **Reasoning** from **Fact Extraction**:

1.  **Deterministic Layer (The Guardrail):** Uses rigid Regex & NLP pipelines to extract hard data (Dollar amounts, Dates, Legislation IDs) with 100% mathematical certainty.
2.  **Probabilistic Layer (The Brain):** Uses **Google Gemini 2.5** via a RAG (Retrieval-Augmented Generation) pipeline to synthesize context, summarize policy, and detect sentiment.

**Result:** The reasoning power of AI with the audit safety of traditional software.

---

## 🛠 Tech Stack
* **Core Engine:** Python 3.11, FastAPI
* **AI Model:** Google Gemini 2.5 Pro (via Google Generative AI SDK)
* **Architecture:** RAG (Retrieval-Augmented Generation) + Deterministic Regex Layer
* **Deployment:** Docker (Containerized for consistency)
* **Frontend:** HTML5, TailwindCSS, Chart.js (Real-time analytics)

---

## 🚀 How to Run Locally

This project is containerized for easy testing. You will need your own free **Google Gemini API Key** to run the inference engine.

### Prerequisites
* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.
* A [Google AI Studio API Key](https://aistudio.google.com/app/apikey).

### Step 1: Clone the Repo
```bash
git clone [https://github.com/YOUR_USERNAME/government-intelligence-platform.git](https://github.com/YOUR_USERNAME/government-intelligence-platform.git)
cd government-intelligence-platform