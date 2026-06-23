import { useRef, useState } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = 'http://127.0.0.1:8000/top-candidates'
const UPLOAD_JD_URL = 'http://127.0.0.1:8000/upload-jd'

const ACCEPTED_JD_TYPES = ['.pdf', '.docx', '.txt']
const ACCEPTED_MIME_TYPES = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/plain',
]
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024

const SEARCH_STEPS = [
  'Analyzing Job Description...',
  'Extracting role requirements...',
  'Searching candidate database...',
  'Ranking candidates...',
]

const GITHUB_URL = 'https://github.com/KoumudiSahasrabudhe27/TalentLens-AI'
const LINKEDIN_URL = 'https://linkedin.com/in/linkedin-placeholder'
const EMAIL_URL = 'mailto:email.placeholder@example.com'

function getScoreBadgeClass(score) {
  if (score > 75) return 'high'
  if (score > 65) return 'medium'
  return 'low'
}

function getConfidenceBadgeClass(score) {
  if (score >= 95) return 'excellent'
  if (score >= 85) return 'strong'
  if (score >= 75) return 'good'
  return 'moderate'
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString()
}

function isAcceptedJdFile(file) {
  if (!file) return false

  const fileName = file.name.toLowerCase()
  const hasValidExtension = ACCEPTED_JD_TYPES.some((ext) =>
    fileName.endsWith(ext)
  )
  const hasValidMime = ACCEPTED_MIME_TYPES.includes(file.type)

  return hasValidExtension || hasValidMime
}

function delay(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function App() {
  const fileInputRef = useRef(null)

  const [candidates, setCandidates] = useState([])
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState('')
  const [showResults, setShowResults] = useState(false)

  const [uploadedFile, setUploadedFile] = useState(null)
  const [jdText, setJdText] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [searchError, setSearchError] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [loadingStep, setLoadingStep] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState(null)

  const hasJdInput = Boolean(uploadedFile) || jdText.trim().length > 0
  const jdSourceLabel = uploadedFile
    ? uploadedFile.name
    : jdText.trim()
      ? 'Pasted job description'
      : ''

  const handleFileSelection = (file) => {
    if (!file) return

    if (!isAcceptedJdFile(file)) {
      setSearchError('Please upload a PDF, DOCX, or TXT job description file.')
      setUploadedFile(null)
      return
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setSearchError('File exceeds 5 MB upload limit.')
      setUploadedFile(null)
      return
    }

    setSearchError('')
    setUploadedFile(file)
  }

  const handleFileInputChange = (event) => {
    handleFileSelection(event.target.files?.[0])
  }

  const handleDragOver = (event) => {
    event.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (event) => {
    event.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    handleFileSelection(event.dataTransfer.files?.[0])
  }

  const openFilePicker = () => {
    fileInputRef.current?.click()
  }

  const fetchCandidateResults = async () => {
    const response = await axios.get(API_URL)
    setCandidates(response.data.candidates || [])
    setSummary(response.data.summary || null)
    setError('')
  }

  const handleSearch = async () => {
    setSearchError('')
    setError('')

    const hasUploadedFile = Boolean(uploadedFile)
    const hasPastedText = jdText.trim().length > 0

    if (!hasUploadedFile && !hasPastedText) {
      setSearchError('Please upload a JD file or paste JD text before searching.')
      return
    }

    setIsSearching(true)
    setShowResults(false)

    try {
      if (hasUploadedFile) {
        // TODO: Connect to backend JD upload + parsing endpoint.
        // const formData = new FormData()
        // formData.append('file', uploadedFile)
        // await axios.post(UPLOAD_JD_URL, formData, {
        //   headers: { 'Content-Type': 'multipart/form-data' },
        // })
      } else {
        // TODO: Send pasted JD text to backend once search endpoint is available.
        // await axios.post('http://127.0.0.1:8000/search-jd', {
        //   job_description_text: jdText.trim(),
        // })
      }

      for (const step of SEARCH_STEPS) {
        setLoadingStep(step)
        await delay(450)
      }

      await fetchCandidateResults()
      setShowResults(true)
    } catch (requestError) {
      setError(
        'Failed to load candidates. Make sure the FastAPI server is running at http://127.0.0.1:8000'
      )
      console.error(requestError)
    } finally {
      setIsSearching(false)
      setLoadingStep('')
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>TalentLens-AI</h1>
        <p>AI-Powered Candidate Discovery &amp; Ranking Engine</p>
      </header>

      <section className="search-section">
        <h2 className="search-section-title">Search Candidates</h2>
        <p className="search-helper-text">
          TalentLens AI will automatically extract skills, experience requirements,
          and role signals from the uploaded JD.
        </p>

        <div className="search-layout">
          <div className="search-column">
            <h3 className="search-column-title">Upload JD File</h3>
            <p className="search-supported-types">Supported: PDF, DOCX, TXT · Max 5 MB</p>

            <div
              className={`upload-dropzone ${isDragging ? 'dragging' : ''}`}
              onClick={openFilePicker}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  openFilePicker()
                }
              }}
              role="button"
              tabIndex={0}
              aria-label="Upload job description file"
            >
              <p className="upload-dropzone-text">Drop JD here or click to upload</p>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              className="file-input-hidden"
              onChange={handleFileInputChange}
            />
          </div>

          <div className="search-divider">
            <span>OR</span>
          </div>

          <div className="search-column">
            <h3 className="search-column-title">Paste JD Text</h3>
            <textarea
              className="jd-textarea"
              value={jdText}
              onChange={(event) => setJdText(event.target.value)}
              placeholder="Paste the full job description here..."
              rows={5}
            />
          </div>
        </div>

        {hasJdInput && !searchError && (
          <div className="jd-ready-card">
            <p className="jd-ready-title">Job Description Ready</p>
            <p className="jd-ready-filename">Uploaded: {jdSourceLabel}</p>
            <p className="jd-ready-formats">Supported formats: PDF • DOCX • TXT</p>
          </div>
        )}

        <div className="search-actions">
          <button
            type="button"
            className="search-button"
            onClick={handleSearch}
            disabled={isSearching}
          >
            {isSearching ? 'Searching...' : 'Search Candidates'}
          </button>
        </div>

        <p className="recruiter-note">
          TalentLens AI combines semantic retrieval, candidate intelligence signals,
          and explainable ranking to identify the strongest matches.
        </p>

        {searchError && <p className="search-message error">{searchError}</p>}

        {isSearching && (
          <div className="search-loading-panel">
            <div className="loading-spinner" aria-hidden="true" />
            <p className="loading-step-text">{loadingStep}</p>
          </div>
        )}
      </section>

      {showResults && summary && (
        <section className="stats-grid">
          <article className="stat-card">
            <p className="stat-label">Total Candidates Analyzed</p>
            <p className="stat-value">
              {formatNumber(summary.total_candidates_analyzed)}
            </p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Retrieved Candidates</p>
            <p className="stat-value">
              {formatNumber(summary.retrieved_candidates)}
            </p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Final Ranked Candidates</p>
            <p className="stat-value">
              {formatNumber(summary.final_ranked_candidates)}
            </p>
          </article>
          <article className="stat-card">
            <p className="stat-label">Top Match Score</p>
            <p className="stat-value">
              {Number(summary.top_match_score).toFixed(2)}
            </p>
          </article>
        </section>
      )}

      {showResults && error && <p className="status-message error">{error}</p>}

      {showResults && !error && (
        <section className="candidate-results-section">
          <h2 className="results-section-title">Candidate Results</h2>
          <div className="candidate-list">
            {candidates.map((candidate) => (
              <article key={candidate.candidate_id} className="candidate-card">
                <div className="card-section card-header-row">
                  <div>
                    <p className="rank-label">Rank #{candidate.rank}</p>
                    <h2 className="candidate-title">{candidate.title}</h2>
                    <p className="candidate-meta">
                      {candidate.candidate_id}
                      {candidate.current_company &&
                        candidate.current_company !== 'N/A' &&
                        ` · ${candidate.current_company}`}
                    </p>
                  </div>
                  <div className="badge-group">
                    <span
                      className={`score-badge ${getScoreBadgeClass(
                        Number(candidate.final_score)
                      )}`}
                    >
                      Final {Number(candidate.final_score).toFixed(2)}
                    </span>
                  </div>
                </div>

                <div className="candidate-summary">
                  <p>
                    <strong>Experience:</strong>{' '}
                    {candidate.years_of_experience
                      ? `${Number(candidate.years_of_experience).toFixed(1)} years`
                      : 'N/A'}
                  </p>
                  <p>
                    <strong>Domain Fit:</strong>{' '}
                    {Number(candidate.domain_fit_score).toFixed(0)}/100
                  </p>
                  <p>
                    <strong>Talent Score:</strong>{' '}
                    {Number(candidate.talent_score).toFixed(0)}/100
                  </p>
                  <p>
                    <strong>Semantic Match:</strong>{' '}
                    {(Number(candidate.semantic_similarity) * 100).toFixed(1)}%
                  </p>
                </div>

                <div className="card-section confidence-section">
                  <h3>Recruiter Confidence</h3>
                  <div className="confidence-row">
                    <span
                      className={`confidence-badge ${getConfidenceBadgeClass(
                        Number(candidate.confidence_score)
                      )}`}
                    >
                      Confidence: {Math.round(Number(candidate.confidence_score))}%
                    </span>
                    <span className="confidence-label">
                      {candidate.confidence_label}
                    </span>
                  </div>
                </div>

                <div className="card-section">
                  <h3>Hiring Risks</h3>
                  <div className="risk-badges">
                    {candidate.hiring_risks &&
                    candidate.hiring_risks.length > 0 ? (
                      candidate.hiring_risks.map((risk) => (
                        <span key={risk} className="risk-badge warning">
                          ⚠ {risk}
                        </span>
                      ))
                    ) : (
                      <span className="risk-badge safe">
                        ✓ No significant hiring risks detected
                      </span>
                    )}
                  </div>
                </div>

                <div className="card-section insight-section">
                  <h3>AI Recruiter Insight</h3>
                  <p className="insight-text">{candidate.recruiter_insight}</p>
                </div>



                <div className="card-section">
  <button
    className="view-profile-btn"
    onClick={() => setSelectedCandidate(candidate)}
  >
    View Full Profile
  </button>
</div>
                <div className="card-section why-matched">
                  <h3>Why Matched</h3>
                  <ul>
                    {(candidate.explanations || []).map((bullet, index) => (
                      <li key={`${candidate.candidate_id}-${index}`}>{bullet}</li>
                    ))}
                  </ul>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

      <section className="info-panel limitations-panel">
        <h2>System Limitations</h2>
        <ul>
          <li>Synthetic dataset used for evaluation</li>
          <li>No historical hiring outcome labels available</li>
          <li>Scoring weights are currently heuristic</li>
          <li>LLM-based reranking not implemented</li>
          <li>Real-world recruiter feedback not yet integrated</li>
        </ul>
      </section>

      {selectedCandidate && (
  <>
    <div
      className="drawer-overlay"
      onClick={() => setSelectedCandidate(null)}
    />

    <div className="candidate-drawer">

      <div className="drawer-header">
        <h2>Candidate Profile</h2>

        <button
          className="drawer-close"
          onClick={() => setSelectedCandidate(null)}
        >
          ×
        </button>
      </div>

      <div className="drawer-content">

        <p><strong>ID:</strong> {selectedCandidate.candidate_id}</p>

        <p><strong>Title:</strong> {selectedCandidate.title}</p>

        <p>
          <strong>Experience:</strong>{" "}
          {selectedCandidate.years_of_experience} years
        </p>

        <p>
          <strong>Domain Fit:</strong>{" "}
          {selectedCandidate.domain_fit_score}
        </p>

        <p>
          <strong>Talent Score:</strong>{" "}
          {selectedCandidate.talent_score}
        </p>

        <p>
          <strong>Semantic Match:</strong>{" "}
          {(selectedCandidate.semantic_similarity * 100).toFixed(1)}%
        </p>

        <p>
          <strong>Confidence:</strong>{" "}
          {selectedCandidate.confidence_score}%
        </p>

        <hr />

        <h3>AI Recruiter Insight</h3>

        <p>
          {selectedCandidate.recruiter_insight}
        </p>

        <h3>Why Matched</h3>

        <ul>
          {(selectedCandidate.explanations || []).map(
            (item, index) => (
              <li key={index}>{item}</li>
            )
          )}
        </ul>

      </div>
    </div>
  </>
)}
      <section className="architecture-section">

<h2>How TalentLens-AI Works</h2>

<div className="architecture-flow">

  <div className="arch-card">
    100,000 Candidate Profiles
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Feature Extraction
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Talent Score + Domain Fit
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Top 5,000 Candidates
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Embeddings Generation
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    FAISS Semantic Search
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Hybrid Ranking
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Explainable AI Insights
  </div>

  <div className="arrow">↓</div>

  <div className="arch-card">
    Top Candidate Recommendations
  </div>

</div>

<p className="architecture-description">
  TalentLens-AI combines structured
  candidate signals, semantic search,
  vector retrieval, and explainable
  ranking to identify high-potential
  candidates beyond traditional
  keyword matching.
</p>

</section>
      <footer className="contact-section">
        <p className="contact-title">Built for Redrob × Hack2Skill India.Runs</p>
        <div className="contact-links">
          <a href={GITHUB_URL} target="_blank" rel="noreferrer">
            GitHub Repository
          </a>
          <a href={LINKEDIN_URL} target="_blank" rel="noreferrer">
            LinkedIn Placeholder
          </a>
          <a href={EMAIL_URL}>Email Placeholder</a>
        </div>
      </footer>
    </div>
  )
}

export default App
