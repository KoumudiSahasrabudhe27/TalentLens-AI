# TalentLens AI

### Explainable Talent Intelligence Platform

TalentLens AI is an intelligent candidate discovery and ranking engine developed for the **Redrob x Hack2Skill India.Runs Challenge**.

Traditional recruitment systems rely heavily on keyword matching, causing organizations to overlook highly capable candidates with transferable skills, strong career trajectories, and proven real-world experience.

TalentLens AI addresses this problem through a hybrid ranking architecture that combines:

* Semantic candidate-job matching
* Behavioral hiring signals
* Recruiter engagement indicators
* Candidate availability analysis
* Explainable AI reasoning

---

## Problem Statement

Given:

* A Job Description (JD)
* A dataset of 100,000 candidate profiles

Identify and rank the top 100 candidates most likely to succeed in the target role.

The system goes beyond keyword matching by understanding:

* Career history
* Skill relevance
* Product vs service experience
* Retrieval and ranking expertise
* Behavioral engagement signals
* Hiring readiness

---

## Key Features

### Semantic Candidate Matching

Uses transformer embeddings to understand candidate relevance beyond exact keyword overlap.

### Hybrid Ranking Engine

Combines technical fit, behavioral signals, recruiter engagement, and candidate availability into a unified ranking score.

### Explainable AI

Generates recruiter-friendly reasoning for every ranked candidate, highlighting strengths, concerns, and alignment with job requirements.

### Hidden Talent Discovery

Identifies high-potential candidates who may not explicitly match all keywords but demonstrate strong adjacent experience and career signals.

### Honeypot Detection

Detects inconsistent or unrealistic candidate profiles using credibility and profile-quality checks.

---

## Architecture

Job Description
↓
Feature Extraction
↓
Semantic Retrieval
↓
Behavioral Signal Analysis
↓
Hybrid Ranking Engine
↓
Explainability Layer
↓
Top-100 Candidate Recommendations

---

## Technology Stack

### Backend

* Python
* FastAPI

### AI / ML

* Sentence Transformers
* FAISS
* Scikit-learn

### Data Processing

* Pandas
* NumPy

### Frontend

* React
* TypeScript
* Tailwind CSS

---

## Repository Structure

See project folders for ingestion, feature engineering, retrieval, ranking, reasoning, and evaluation pipelines.

---

## Challenge

Redrob x Hack2Skill — India.Runs Datathon Arena

Focus:
Building an Explainable Intelligent Candidate Discovery & Ranking Engine capable of ranking large-scale candidate datasets under strict CPU-only constraints.

---

## Authors

Koumudi Sahasrabudhe
