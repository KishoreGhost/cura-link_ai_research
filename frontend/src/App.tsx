import { API_BASE_URL } from './lib/config'
import type {
  AnswerSection,
  ChatMessage,
  CitationRecord,
  ClinicalTrialRecord,
  PublicationRecord,
  ResearchRequest,
  SessionSummary,
} from './contracts/api'

const previewSession: SessionSummary = {
  session_id: 'session-lung-cancer-001',
  patient_alias: 'Case Atlas',
  disease: 'Lung cancer',
  location: 'Toronto, Canada',
  message_count: 4,
  last_activity_label: 'Updated 3 minutes ago',
}

const previewRequest: ResearchRequest = {
  session_id: previewSession.session_id,
  query: 'Latest treatment options and active clinical trials',
  candidate_target: 150,
  include_trials: true,
  context: {
    patient_alias: previewSession.patient_alias,
    disease: previewSession.disease ?? 'Lung cancer',
    intent: 'Identify recent treatment evidence and active trials',
    location: previewSession.location,
    follow_up_question: 'Would vitamin D supplementation matter for this case?',
  },
}

const answerSections: AnswerSection[] = [
  {
    heading: 'Condition Overview',
    body: 'The workbench is scoped to treat lung cancer as the active condition and frame every follow-up around current treatment evidence plus ongoing trials.',
  },
  {
    heading: 'Research Insights',
    body: 'Phase 1 stops before live retrieval, but the interface is already shaped around broad-source evidence capture, reranking, and grounded synthesis.',
  },
  {
    heading: 'Clinical Trials',
    body: 'Trial cards and filters are reserved for live ClinicalTrials.gov results once the retrieval layer is wired in Phase 2.',
  },
]

const publications: PublicationRecord[] = [
  {
    id: 'pubmed-demo-001',
    title: 'Scaffold contract for evidence-backed oncology literature review',
    authors: ['Curalink Team'],
    publication_year: 2026,
    source: 'pubmed',
    url: 'https://pubmed.ncbi.nlm.nih.gov/',
    abstract_snippet: 'Phase 1 focuses on stable contracts and workspace design before retrieval begins.',
    supporting_snippet: 'Contracts now exist for publications, trials, sessions, and grounded chat turns.',
    relevance_reason: 'Models the exact shape expected from PubMed-backed evidence cards.',
  },
  {
    id: 'openalex-demo-001',
    title: 'Research workbench architecture for retrieval and reranking systems',
    authors: ['Platform Architecture'],
    publication_year: 2026,
    source: 'openalex',
    url: 'https://api.openalex.org/',
    abstract_snippet: 'The UI reserves space for ranked literature, source credibility, and explainable snippets.',
    supporting_snippet: 'OpenAlex results will be normalized into the shared evidence schema in Phase 2.',
    relevance_reason: 'Represents how OpenAlex metadata lands in the evidence panel.',
  },
]

const trials: ClinicalTrialRecord[] = [
  {
    id: 'trial-demo-001',
    title: 'Recruiting precision oncology study placeholder',
    recruiting_status: 'Scaffolded placeholder',
    eligibility_criteria: 'Will be populated from ClinicalTrials.gov once connectors are added.',
    location: 'Toronto, Canada',
    contact_information: 'research-site@example.org',
    source: 'clinicaltrials',
    url: 'https://clinicaltrials.gov/',
    supporting_snippet: 'The trial rail is ready for recruiting status, location, and contact metadata.',
    relevance_reason: 'Ensures the layout accounts for trial-specific fields, not just paper abstracts.',
  },
]

const citations: CitationRecord[] = [
  {
    id: 'cite-001',
    source: 'pubmed',
    title: publications[0].title,
    year: publications[0].publication_year,
    authors: publications[0].authors,
    url: publications[0].url,
    snippet: publications[0].supporting_snippet ?? '',
  },
  {
    id: 'cite-002',
    source: 'clinicaltrials',
    title: trials[0].title,
    authors: ['ClinicalTrials.gov'],
    url: trials[0].url,
    snippet: trials[0].supporting_snippet ?? '',
  },
]

const conversation: ChatMessage[] = [
  {
    role: 'user',
    content: 'Latest treatment for lung cancer',
  },
  {
    role: 'assistant',
    content: 'Phase 1 has the workspace and contracts ready. Live evidence retrieval begins next.',
  },
  {
    role: 'user',
    content: previewRequest.context.follow_up_question ?? '',
  },
]

function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Curalink Research Workbench</p>
          <h1>Evidence-first medical research assistant</h1>
        </div>
        <div className="status-cluster">
          <span className="status-pill">Phase 1 scaffold</span>
          <span className="status-pill">Model: gemma4:e4b</span>
          <span className="status-pill">API: {API_BASE_URL}</span>
        </div>
      </header>

      <main className="workspace-grid">
        <aside className="panel context-panel">
          <section>
            <p className="section-label">Session</p>
            <h2>{previewSession.session_id}</h2>
            <dl className="definition-list">
              <div>
                <dt>Patient alias</dt>
                <dd>{previewSession.patient_alias}</dd>
              </div>
              <div>
                <dt>Disease</dt>
                <dd>{previewSession.disease}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{previewSession.location}</dd>
              </div>
              <div>
                <dt>Messages</dt>
                <dd>{previewSession.message_count}</dd>
              </div>
            </dl>
          </section>

          <section>
            <p className="section-label">Structured query</p>
            <div className="stack-card">
              <strong>{previewRequest.query}</strong>
              <p>{previewRequest.context.intent}</p>
              <ul className="token-list">
                <li>Disease-linked query expansion</li>
                <li>Candidate pool target: {previewRequest.candidate_target}</li>
                <li>Trials included: yes</li>
              </ul>
            </div>
          </section>

          <section>
            <p className="section-label">Conversation preview</p>
            <div className="conversation-list">
              {conversation.map((message) => (
                <article key={`${message.role}-${message.content}`} className={`bubble bubble-${message.role}`}>
                  <span>{message.role}</span>
                  <p>{message.content}</p>
                </article>
              ))}
            </div>
          </section>
        </aside>

        <section className="panel answer-panel">
          <div className="panel-header">
            <div>
              <p className="section-label">Answer assembly</p>
              <h2>Structured response skeleton</h2>
            </div>
            <div className="pipeline-state">
              <span>expand</span>
              <span>retrieve</span>
              <span>rerank</span>
              <span>ground</span>
            </div>
          </div>

          <div className="answer-sections">
            {answerSections.map((section) => (
              <article key={section.heading} className="answer-card">
                <h3>{section.heading}</h3>
                <p>{section.body}</p>
              </article>
            ))}
          </div>

          <section className="contract-strip">
            <p className="section-label">Phase 1 deliverables</p>
            <ul className="token-list compact">
              <li>React workspace shell</li>
              <li>Typed API contracts</li>
              <li>FastAPI route scaffold</li>
              <li>CI and env templates</li>
            </ul>
          </section>
        </section>

        <aside className="panel evidence-panel">
          <section>
            <div className="panel-header minor">
              <div>
                <p className="section-label">Publications</p>
                <h2>{publications.length} preview cards</h2>
              </div>
            </div>
            <div className="evidence-list">
              {publications.map((publication) => (
                <article key={publication.id} className="evidence-card">
                  <span className="source-tag">{publication.source}</span>
                  <h3>{publication.title}</h3>
                  <p>{publication.abstract_snippet}</p>
                  <small>{publication.relevance_reason}</small>
                </article>
              ))}
            </div>
          </section>

          <section>
            <div className="panel-header minor">
              <div>
                <p className="section-label">Clinical trials</p>
                <h2>{trials.length} preview card</h2>
              </div>
            </div>
            <div className="evidence-list">
              {trials.map((trial) => (
                <article key={trial.id} className="evidence-card trial-card">
                  <span className="source-tag">{trial.recruiting_status}</span>
                  <h3>{trial.title}</h3>
                  <p>{trial.eligibility_criteria}</p>
                  <small>{trial.contact_information}</small>
                </article>
              ))}
            </div>
          </section>

          <section>
            <p className="section-label">Citation rail</p>
            <div className="citation-list">
              {citations.map((citation) => (
                <article key={citation.id} className="citation-card">
                  <strong>{citation.title}</strong>
                  <p>{citation.snippet}</p>
                  <a href={citation.url} target="_blank" rel="noreferrer">
                    Open source
                  </a>
                </article>
              ))}
            </div>
          </section>
        </aside>
      </main>

      <footer className="footer-bar">
        <span>Pipeline plan: query expansion / live source retrieval / evidence normalization / reranking / grounded synthesis</span>
        <span>{previewSession.last_activity_label}</span>
      </footer>
    </div>
  )
}

export default App


