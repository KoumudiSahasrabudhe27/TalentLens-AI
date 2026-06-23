# TalentLens-AI

## Explainable Talent Intelligence Platform for Semantic Candidate Discovery

TalentLens-AI is an end-to-end AI-powered candidate discovery and ranking platform developed for the **Redrob × Hack2Skill India.Runs Datathon Arena**.

Traditional Applicant Tracking Systems (ATS) rely heavily on keyword matching, often overlooking highly qualified candidates whose experience, skills, and career trajectories indicate strong potential despite limited keyword overlap.

TalentLens-AI addresses this challenge through a hybrid AI ranking architecture that combines semantic search, behavioral hiring signals, candidate availability indicators, and explainable AI reasoning to identify the strongest candidates from large-scale talent datasets.

---

## Problem Statement

Given:

* A Job Description (JD)
* A dataset containing 100,000 candidate profiles

Build an intelligent ranking system capable of identifying and recommending the most relevant candidates while providing transparent explanations for every recommendation.

The system should go beyond traditional keyword matching and understand:

* Career progression
* Skill relevance
* Semantic similarity
* Retrieval and ranking expertise
* Recruiter engagement signals
* Hiring readiness
* Candidate availability

---

## Solution Overview

TalentLens-AI processes candidate profiles through a multi-stage retrieval and ranking pipeline:

```text
100,000 Candidate Profiles
            ↓
     Feature Extraction
            ↓
  Talent & Domain Scoring
            ↓
    Top 5,000 Candidates
            ↓
   Embedding Generation
            ↓
      FAISS Retrieval
            ↓
    Semantic Candidate Search
            ↓
      Hybrid Ranking
            ↓
   Explainable AI Layer
            ↓
 Top Candidate Recommendations
```

This architecture dramatically reduces the search space while maintaining candidate quality and ranking accuracy.

---

## Key Features

### Semantic Candidate Matching

Uses transformer-based embeddings and vector similarity search to identify relevant candidates beyond exact keyword overlap.

### Hybrid Ranking Engine

Combines:

* Domain Fit Score
* Talent Score
* Availability Score
* Semantic Similarity

to generate a unified candidate ranking score.

### Explainable AI

Every recommendation includes recruiter-friendly explanations highlighting:

* Skill alignment
* Relevant experience
* Hiring readiness
* Potential risks
* Match confidence

### Recruiter Dashboard

Interactive React dashboard featuring:

* Job Description upload
* Candidate discovery
* Confidence scoring
* Hiring risk indicators
* AI recruiter insights
* Candidate profile drawer
* Architecture visualization

### Hidden Talent Discovery

Identifies candidates with adjacent skills and transferable experience who may be overlooked by traditional ATS systems.

### Hiring Risk Analysis

Flags potential concerns such as:

* Long notice periods
* Low recruiter response rates
* Low interview completion rates
* Availability issues

---

## Technology Stack

### Backend

* Python
* FastAPI

### Machine Learning & Retrieval

* Sentence Transformers (all-MiniLM-L6-v2)
* FAISS Vector Search
* Scikit-learn

### Data Processing

* Pandas
* NumPy

### Frontend

* React
* Vite
* JavaScript
* CSS

### AI Techniques

* Semantic Search
* Embedding Generation
* Vector Retrieval
* Hybrid Ranking
* Explainable AI

---

## Dataset Statistics

| Metric                       | Value   |
| ---------------------------- | ------- |
| Total Candidates             | 100,000 |
| Candidates After Pre-Ranking | 5,000   |
| Semantic Matches Retrieved   | 100     |
| Final Ranked Candidates      | 20      |
| Embedding Dimension          | 384     |
| Vector Database              | FAISS   |

---

## Candidate Ranking Formula

### Talent Score

Combines:

* Recruiter response rate
* Interview completion rate
* Open-to-work signals
* Notice period
* GitHub activity

### Domain Fit Score

Evaluates:

* Job title relevance
* Technical skills
* Career history
* Experience alignment

### Final Hybrid Score

```text
Final Score =
(0.40 × Semantic Similarity)
+
(0.35 × Domain Fit Score)
+
(0.25 × Talent Score)
```

---

## Project Structure

```text
TalentLens-AI
│
├── backend/
├── frontend/
├── src/
│   ├── ingestion/
│   ├── features/
│   ├── embeddings/
│   ├── ranking/
│   ├── reasoning/
│   └── utils/
│
├── docs/
├── data/
├── outputs/
├── requirements.txt
└── README.md
```

---

## Future Enhancements

* Real-time Job Description parsing
* LLM-based reranking
* Recruiter feedback learning loop
* Multi-role search optimization
* Resume upload and parsing
* Advanced hiring analytics
* Cloud deployment

---

## Challenge

**Redrob × Hack2Skill — India.Runs Datathon Arena**

Objective:

Build an Explainable Intelligent Candidate Discovery and Ranking Engine capable of identifying the strongest candidates from large-scale datasets under practical resource constraints.

---

## Author

**Koumudi Sahasrabudhe**

Electronics & Telecommunication Engineering
Mastercard SDE Intern → PPO

GitHub: https://github.com/KoumudiSahasrabudhe27

---

## License

This project was developed for the Redrob × Hack2Skill India.Runs Challenge and is intended for educational and demonstration purposes.
