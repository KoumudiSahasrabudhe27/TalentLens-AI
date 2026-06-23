# TalentLens-AI Project Cleanup Report

This report classifies repository files to help maintain a clean production codebase.
**No files were deleted as part of this review.**

---

## 1. Files Actively Used by Production Pipeline

These files are part of the end-to-end ranking and dashboard flow.

### Data inputs
| File | Role |
|------|------|
| `data/raw/candidates.jsonl` | Full candidate dataset (100,000 records) |
| `data/raw/candidate_schema.json` | Schema reference for candidate records |
| `data/raw/job_description.txt` | Job description text for parsing and search |
| `data/raw/job_description.docx` | Original JD document (source reference) |

### Pipeline scripts (root)
| File | Role |
|------|------|
| `explore_dataset.py` | Initial dataset exploration |
| `dataset_analysis.py` | Full dataset statistics |
| `generate_all_summaries.py` | Builds candidate summary JSONL |
| `pre_rank_candidates.py` | Pre-ranks top 5,000 candidates |
| `generate_embeddings.py` | Creates embeddings for top 5,000 |
| `build_faiss_index.py` | Builds FAISS semantic search index |
| `jd_parser.py` | Extracts structured JD signals |
| `query_builder.py` | Builds semantic search query |
| `search_candidates.py` | Semantic search v1 (full JD) |
| `search_candidates_v2.py` | Semantic search v2 (focused query) |
| `hybrid_search.py` | Hybrid ranking experiment |
| `final_ranker.py` | Final recruiter ranking |
| `explain_candidate.py` | Initial explanation generator |
| `improve_explanations.py` | Recruiter-quality explanations |

### Source modules
| File | Role |
|------|------|
| `src/features/feature_extractor.py` | Feature extraction |
| `src/ranking/talent_score.py` | Talent intelligence score |
| `src/ranking/domain_fit_score.py` | Domain fit scoring |
| `src/ranking/hireability_score.py` | Hireability component |
| `src/ranking/availability_score.py` | Availability component |
| `src/reasoning/candidate_summary.py` | Summary text generation |

### Generated outputs (runtime artifacts)
| File | Role |
|------|------|
| `data/processed/candidate_summaries.jsonl` | Semantic summaries for all candidates |
| `data/embeddings/candidate_embeddings.pkl` | Embedding vectors |
| `data/embeddings/candidate_faiss.index` | FAISS index |
| `data/embeddings/candidate_ids.pkl` | FAISS ID mapping |
| `outputs/top_5000_candidates.csv` | Pre-ranked pool |
| `outputs/parsed_jd.json` | Parsed JD structure |
| `outputs/search_query.txt` | Semantic query string |
| `outputs/top_100_semantic_v2.csv` | Semantic search results |
| `outputs/final_ranked_candidates.json` | Final ranked list with scores |
| `outputs/final_ranked_candidates_explained.json` | Final list with explanations |

### API and frontend
| File | Role |
|------|------|
| `backend/app.py` | FastAPI production API |
| `backend/__init__.py` | Python package marker |
| `frontend/src/App.jsx` | Recruiter dashboard UI |
| `frontend/src/App.css` | Dashboard styles |
| `frontend/src/main.jsx` | React entry point |
| `frontend/index.html` | Frontend shell |
| `frontend/vite.config.js` | Vite build config |
| `frontend/package.json` | Frontend dependencies |
| `requirements.txt` | Python dependencies |

### Documentation
| File | Role |
|------|------|
| `README.md` | Project overview |

---

## 2. Files Used Only for Experimentation

These support exploration, intermediate outputs, or earlier pipeline versions.

| File | Notes |
|------|-------|
| `outputs/top_20_semantic_matches.csv` | v1 semantic search output (superseded by v2) |
| `outputs/top_20_hybrid_ranked.csv` | Hybrid ranking experiment on v1 matches |
| `outputs/top_20_explanations.json` | Explanations for v1 top-20 semantic set |
| `outputs/top_500_candidates.csv` | Earlier pre-rank output (500 vs 5,000) |
| `outputs/dataset_analysis.txt` | Exploratory dataset report |
| `outputs/sample_candidate_summary.txt` | Single-candidate summary test |
| `search_candidates.py` | Full-JD semantic search (less accurate than v2) |
| `hybrid_search.py` | Hybrid score experiment |
| `explain_candidate.py` | First-pass explanations (superseded by improve_explanations.py) |
| `explore_dataset.py` | One-record dataset peek |
| `data/raw/sample_candidates.json` | Small sample subset for testing |

---

## 3. Files That Can Probably Be Archived

Move to an `archive/` or `docs/legacy/` folder if the repo should stay lean.

| File | Reason |
|------|--------|
| `outputs/top_20_semantic_matches.csv` | Superseded by `top_100_semantic_v2.csv` |
| `outputs/top_20_hybrid_ranked.csv` | Experimental output, not used by final API |
| `outputs/top_20_explanations.json` | Tied to old semantic v1 top 20 |
| `outputs/top_500_candidates.csv` | Superseded by `top_5000_candidates.csv` |
| `outputs/sample_candidate_summary.txt` | Dev/test artifact |
| `frontend/src/assets/hero.png` | Default Vite template asset, unused |
| `frontend/src/assets/react.svg` | Default Vite template asset, unused |
| `frontend/src/assets/vite.svg` | Default Vite template asset, unused |
| `frontend/public/icons.svg` | Default Vite template asset, unused |
| `data/raw/redrob_signals_doc.docx` | Reference doc, not read by pipeline |
| `data/raw/submission_spec.docx` | Challenge spec reference only |

---

## 4. Files That Should Never Be Committed

Ensure these stay in `.gitignore` or are never added to version control.

| Pattern / File | Reason |
|----------------|--------|
| `.env` | Secrets and local environment variables |
| `venv/`, `.venv/` | Local Python virtual environments |
| `__pycache__/`, `*.pyc` | Python bytecode |
| `data/embeddings/*` | Large generated embedding artifacts (per `.gitignore`) |
| `outputs/*` | Generated pipeline outputs (per `.gitignore`) |
| `*.faiss`, `*.pkl` | Large binary model/index files |
| `frontend/node_modules/` | Node dependencies (reinstall via `npm install`) |
| `frontend/dist/` | Production build output |
| API keys, tokens, credentials | Any hardcoded secrets in config files |
| `data/raw/candidates.jsonl` | **Optional:** very large; some teams store externally (currently in repo) |

---

## Recommended Next Steps

1. Keep `improve_explanations.py` and `final_ranker.py` as the canonical explanation + ranking steps.
2. Use `search_candidates_v2.py` (not v1) for semantic retrieval.
3. Archive experimental CSV/JSON outputs under `archive/outputs/` if git history is noisy.
4. Replace LinkedIn and email placeholders in `frontend/src/App.jsx` before demo submission.
5. Re-run the full pipeline after any scoring formula change, then restart the FastAPI server.

---

*Generated as part of the TalentLens-AI recruiter dashboard upgrade. No files were deleted.*
