import { useState, useRef, useEffect, useCallback, type KeyboardEvent } from 'react'
import {
  Globe,
  Paperclip,
  Microscope,
  Plus,
  ArrowUp,
  ChevronDown,
  FlaskConical,
  BookOpen,
  Stethoscope,
  Clock,
  Sparkles,
  X,
  ExternalLink,
  ChevronRight,
} from 'lucide-react'
import { cn } from './lib/utils'
import { fetchResearch, sendChatTurn } from './lib/api'
import { DNABuddy } from './components/DNABuddy'
import type {
  AnswerSection,
  CitationRecord,
  ClinicalTrialRecord,
  PublicationRecord,
} from './contracts/api'

// ─── Types ────────────────────────────────────────────────────────────────────

type Mode = 'structured' | 'quick'
type ToolId = 'sources' | 'trials' | 'deep' | 'web'

interface ActiveTool {
  id: ToolId
  label: string
}

interface FeedEntry {
  kind: 'query' | 'thinking' | 'answer' | 'pubs' | 'trials' | 'cites'
  query?: string
  sections?: AnswerSection[]
  pubs?: PublicationRecord[]
  trials?: ClinicalTrialRecord[]
  cites?: CitationRecord[]
}

interface SessionEntry {
  id: string
  title: string
  ts: string
}

// ─── Conversational detection (mirrors backend logic) ───────────────────────

const CONVERSATIONAL_PATTERNS = [
  'hello', 'hi', 'hey', 'howdy', 'hiya', 'sup', "what's up", 'whats up',
  'who are you', 'what are you', 'what can you do', 'what do you do',
  'tell me about yourself', 'introduce yourself', 'your name',
  'how are you', "how's it going", 'good morning', 'good afternoon',
  'good evening', 'good night', 'thanks', 'thank you', 'thx', 'ty',
  'cheers', 'cool', 'awesome', 'great', 'nice',
  'help', 'what should i ask', 'how does this work', 'get started',
  'can you help', 'how do i use',
]

const MEDICAL_KEYWORDS = [
  'disease', 'cancer', 'diabetes', 'treatment', 'symptoms', 'diagnosis',
  'trial', 'medication', 'drug', 'study', 'research', 'clinical', 'therapy',
  'patient', 'cure', 'syndrome', 'disorder', 'condition', 'infection',
  'surgery', 'hospital', 'doctor', 'physician', 'oncology', 'neurology',
  'cardiovascular', 'parkinson', 'alzheimer', 'covid', 'vaccine', 'gene',
]

function isConversational(message: string): boolean {
  const msg = message.toLowerCase().trim().replace(/[!?.]+$/, '')
  // Short messages with no medical keywords are conversational
  if (msg.split(' ').length <= 3 && !MEDICAL_KEYWORDS.some(kw => msg.includes(kw))) {
    return true
  }
  return CONVERSATIONAL_PATTERNS.some(pattern => msg.includes(pattern))
}

// ─── Constants ────────────────────────────────────────────────────────────────

const SUGGESTIONS = [
  { icon: Stethoscope, label: 'Latest lung cancer treatment options' },
  { icon: FlaskConical, label: 'Clinical trials for Type 2 Diabetes' },
  { icon: BookOpen, label: 'Top Alzheimer\'s disease researchers' },
  { icon: Globe, label: 'Recent heart disease intervention studies' },
]

const INPUT_TOOLS: { id: ToolId; icon: React.ElementType; label: string; desc: string }[] = [
  { id: 'sources', icon: BookOpen, label: 'Include PubMed', desc: 'Pull from PubMed & OpenAlex' },
  { id: 'trials', icon: FlaskConical, label: 'Clinical Trials', desc: 'Include ClinicalTrials.gov' },
  { id: 'deep', icon: Microscope, label: 'Deep Search', desc: 'Broader candidate pool (300)' },
  { id: 'web', icon: Globe, label: 'Location', desc: 'Match trials by location' },
]

// ─── Skeleton ─────────────────────────────────────────────────────────────────

function Skeleton({ className }: { className?: string }) {
  return <div className={cn('shimmer rounded-md bg-white/[0.04]', className)} />
}

function ThinkingDots() {
  return (
    <div className="flex items-center gap-3 py-2">
      <div className="size-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0">
        <Sparkles size={13} className="text-white/40" />
      </div>
      <div className="flex gap-1.5 items-center h-5">
        <span className="dot-1 size-1.5 rounded-full bg-white/40 inline-block" />
        <span className="dot-2 size-1.5 rounded-full bg-white/40 inline-block" />
        <span className="dot-3 size-1.5 rounded-full bg-white/40 inline-block" />
      </div>
    </div>
  )
}

// ─── Publication Card ─────────────────────────────────────────────────────────

function PubCard({ pub, index }: { pub: PublicationRecord; index: number }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="group border border-white/[0.07] rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors overflow-hidden">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 text-xs font-mono text-white/20 w-5 flex-shrink-0 select-none">{index + 1}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <h4 className="text-sm font-semibold text-white/90 leading-snug">{pub.title}</h4>
              <a
                href={pub.url}
                target="_blank"
                rel="noreferrer"
                className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-white/30 hover:text-white/70"
              >
                <ExternalLink size={13} />
              </a>
            </div>
            <div className="mt-1.5 flex items-center gap-2 flex-wrap">
              <span className={cn(
                'text-[11px] font-semibold px-2 py-0.5 rounded-full border',
                pub.source === 'pubmed'
                  ? 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                  : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
              )}>
                {pub.source === 'pubmed' ? 'PubMed' : 'OpenAlex'}
              </span>
              {pub.publication_year && (
                <span className="text-[11px] text-white/30">{pub.publication_year}</span>
              )}
              {pub.authors.length > 0 && (
                <span className="text-[11px] text-white/30">
                  {pub.authors.slice(0, 2).join(', ')}{pub.authors.length > 2 ? ' et al.' : ''}
                </span>
              )}
            </div>
            {pub.abstract_snippet && (
              <div className="mt-2.5">
                <p className={cn('text-[13px] text-white/50 leading-relaxed transition-all', !open && 'line-clamp-2')}>
                  {pub.abstract_snippet}
                </p>
                {pub.abstract_snippet.length > 160 && (
                  <button
                    onClick={() => setOpen(o => !o)}
                    className="mt-1 text-[11px] text-white/30 hover:text-white/60 transition-colors flex items-center gap-0.5"
                  >
                    {open ? 'Show less' : 'Show more'}
                    <ChevronDown size={11} className={cn('transition-transform', open && 'rotate-180')} />
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Trial Card ───────────────────────────────────────────────────────────────

function TrialCard({ trial, index }: { trial: ClinicalTrialRecord; index: number }) {
  const recruiting = trial.recruiting_status.toLowerCase().includes('recruiting')
  return (
    <div className="group border border-white/[0.07] rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors overflow-hidden">
      <div className="p-4">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 text-xs font-mono text-white/20 w-5 flex-shrink-0 select-none">{index + 1}</span>
          <div className="min-w-0 flex-1">
            <div className="flex items-start justify-between gap-3">
              <h4 className="text-sm font-semibold text-white/90 leading-snug">{trial.title}</h4>
              <a href={trial.url} target="_blank" rel="noreferrer"
                className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-white/30 hover:text-white/70">
                <ExternalLink size={13} />
              </a>
            </div>
            <div className="mt-1.5 flex items-center gap-2 flex-wrap">
              <span className={cn(
                'inline-flex items-center gap-1.5 text-[11px] font-semibold px-2 py-0.5 rounded-full border',
                recruiting
                  ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
                  : 'bg-violet-500/10 border-violet-500/20 text-violet-400'
              )}>
                <span className={cn('size-1.5 rounded-full', recruiting ? 'bg-emerald-400' : 'bg-violet-400')} />
                {trial.recruiting_status}
              </span>
              {trial.location && (
                <span className="text-[11px] text-white/30">📍 {trial.location}</span>
              )}
            </div>
            {trial.eligibility_criteria && (
              <p className="mt-2.5 text-[13px] text-white/50 leading-relaxed line-clamp-2 border-l-2 border-white/10 pl-3">
                {trial.eligibility_criteria}
              </p>
            )}
            {trial.contact_information && (
              <p className="mt-1.5 text-[12px] text-amber-400/70">✉ {trial.contact_information}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Answer Block ─────────────────────────────────────────────────────────────

const SECTION_META: Record<string, { icon: React.ElementType; color: string }> = {
  'Condition Overview': { icon: Stethoscope, color: 'text-blue-400' },
  'Research Insights': { icon: BookOpen, color: 'text-violet-400' },
  'Clinical Trials': { icon: FlaskConical, color: 'text-emerald-400' },
  'Personalized Insight': { icon: Sparkles, color: 'text-amber-400' },
  'Research Summary': { icon: Microscope, color: 'text-white/60' },
}

function AnswerBlock({ sections }: { sections: AnswerSection[] }) {
  return (
    <div className="space-y-3">
      {sections.map(s => {
        const meta = SECTION_META[s.heading] ?? { icon: Sparkles, color: 'text-white/50' }
        const Icon = meta.icon
        return (
          <div key={s.heading} className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4">
            <div className="flex items-center gap-2 mb-2.5">
              <Icon size={14} className={cn(meta.color)} />
              <h3 className="text-[13px] font-semibold text-white/80 tracking-tight">{s.heading}</h3>
            </div>
            <p className="text-[14px] text-white/60 leading-relaxed">{s.body}</p>
          </div>
        )
      })}
    </div>
  )
}

// ─── Section label ────────────────────────────────────────────────────────────

function SectionLabel({ label, count }: { label: string; count: number }) {
  return (
    <div className="flex items-center gap-3 mt-6 mb-3">
      <span className="text-[11px] font-semibold uppercase tracking-[0.12em] text-white/30">{label}</span>
      <span className="text-[11px] text-white/20 font-mono">{count}</span>
      <div className="flex-1 h-px bg-white/[0.05]" />
    </div>
  )
}

// ─── Citations ────────────────────────────────────────────────────────────────

function CitationsRow({ cites }: { cites: CitationRecord[] }) {
  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {cites.slice(0, 8).map((c, i) => (
        <a
          key={c.id}
          href={c.url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border border-white/[0.08] bg-white/[0.03] text-[12px] text-white/40 hover:text-white/70 hover:border-white/15 transition-all group"
        >
          <span className="text-white/20 font-mono text-[10px]">{i + 1}</span>
          <span className="max-w-[160px] truncate">{c.title}</span>
          <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
        </a>
      ))}
    </div>
  )
}

// ─── Main App ─────────────────────────────────────────────────────────────────

export default function App() {
  // Input state
  const [mode, setMode] = useState<Mode>('quick')
  const [input, setInput] = useState('')
  const [disease, setDisease] = useState('')
  const [patientName, setPatientName] = useState('')
  const [location, setLocation] = useState('')
  const [activeTools, setActiveTools] = useState<Set<ToolId>>(new Set(['sources', 'trials']))
  const [toolPickerOpen, setToolPickerOpen] = useState(false)

  // Session / feed state
  const [sessions, setSessions] = useState<SessionEntry[]>([])
  const [activeSession, setActiveSession] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [feed, setFeed] = useState<FeedEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [hasResults, setHasResults] = useState(false)

  const feedEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const toolPickerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [feed])

  // Close tool picker on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (toolPickerRef.current && !toolPickerRef.current.contains(e.target as Node)) {
        setToolPickerOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const toggleTool = (id: ToolId) => {
    setActiveTools(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })
  }

  const registerSession = useCallback((sid: string, title: string) => {
    const entry: SessionEntry = { id: sid, title: title.slice(0, 30), ts: 'Just now' }
    setSessions(p => [entry, ...p])
    setActiveSession(sid)
  }, [])

  const newSession = () => {
    setFeed([])
    setSessionId(null)
    setActiveSession(null)
    setHasResults(false)
    setError(null)
    setInput('')
    setDisease('')
    setPatientName('')
    setLocation('')
    setTimeout(() => textareaRef.current?.focus(), 50)
  }

  // ── Core submit logic ───────────────────────────────────────────────────────

  const submit = useCallback(async (queryText: string, diseaseCtx: string) => {
    if (!queryText.trim() || loading) return
    setLoading(true)
    setError(null)
    setHasResults(true)

    setFeed(f => [...f,
    { kind: 'query', query: queryText },
    { kind: 'thinking' },
    ])

    const includeTrials = activeTools.has('trials')
    const candidateTarget = activeTools.has('deep') ? 300 : 150
    const loc = activeTools.has('web') && location.trim() ? location.trim() : undefined

    const conversational = isConversational(queryText)

    try {
      if (conversational) {
        // ── Greeting / off-topic — skip research retrieval entirely ──
        const chat = await sendChatTurn({
          session_id: sessionId ?? undefined,
          context_update: sessionId ? undefined : {
            disease: diseaseCtx || queryText,
            location: loc,
            patient_alias: patientName.trim() || undefined,
          },
          messages: [{ role: 'user', content: queryText }],
        })

        const sid = chat.session_id
        if (!sessionId) {
          setSessionId(sid)
          registerSession(sid, queryText)
        }

        setFeed(f => {
          const base = f.filter(x => x.kind !== 'thinking')
          const additions: FeedEntry[] = []
          if (chat.answer_sections.length) additions.push({ kind: 'answer', sections: chat.answer_sections })
          return [...base, ...additions]
        })
      } else {
        // ── Research query — run full retrieval + chat in parallel ──
        const [res, chat] = await Promise.all([
          fetchResearch({
            query: queryText,
            candidate_target: candidateTarget,
            include_trials: includeTrials,
            context: {
              disease: diseaseCtx || queryText,
              intent: queryText,
              location: loc,
              patient_alias: patientName.trim() || undefined,
            },
            session_id: sessionId ?? undefined,
          }),
          sendChatTurn({
            session_id: sessionId ?? undefined,
            context_update: sessionId ? undefined : {
              disease: diseaseCtx || queryText,
              location: loc,
              patient_alias: patientName.trim() || undefined,
            },
            messages: [{ role: 'user', content: queryText }],
          }),
        ])

        const sid = chat.session_id
        if (!sessionId) {
          setSessionId(sid)
          registerSession(sid, queryText)
        }

        setFeed(f => {
          const base = f.filter(x => x.kind !== 'thinking')
          const additions: FeedEntry[] = []
          if (chat.answer_sections.length) additions.push({ kind: 'answer', sections: chat.answer_sections })
          if (res.publications.length) additions.push({ kind: 'pubs', pubs: res.publications })
          if (res.clinical_trials.length) additions.push({ kind: 'trials', trials: res.clinical_trials })
          if (chat.citations.length) additions.push({ kind: 'cites', cites: chat.citations })
          return [...base, ...additions]
        })
      }
    } catch (e) {
      setFeed(f => f.filter(x => x.kind !== 'thinking'))
      setError(e instanceof Error ? e.message : 'Request failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [activeTools, loading, location, patientName, sessionId, registerSession])

  const handleQuickSend = async () => {
    const q = input.trim()
    if (!q) return
    setInput('')
    await submit(q, q)
  }

  const handleStructuredSend = async (e: React.FormEvent) => {
    e.preventDefault()
    const q = input.trim() || `Latest research on ${disease}`
    if (!q && !disease.trim()) return
    setInput('')
    await submit(q, disease || q)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (mode === 'quick') handleQuickSend()
    }
  }

  const loadSuggestion = (text: string) => {
    setInput(text)
    setMode('quick')
    textareaRef.current?.focus()
  }

  // ── Feed renderer ───────────────────────────────────────────────────────────

  const renderEntry = (entry: FeedEntry, i: number) => {
    switch (entry.kind) {
      case 'query':
        return (
          <div key={i} className="flex justify-end">
            <div className="max-w-[75%] bg-[#1e1e1e] border border-white/[0.08] rounded-2xl rounded-br-sm px-4 py-2.5 text-[14px] text-white/90 leading-relaxed">
              {entry.query}
            </div>
          </div>
        )
      case 'thinking':
        return <ThinkingDots key={i} />
      case 'answer':
        return (
          <div key={i} className="flex gap-3">
            <div className="size-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
              <Sparkles size={13} className="text-white/50" />
            </div>
            <div className="flex-1 min-w-0">
              <AnswerBlock sections={entry.sections!} />
            </div>
          </div>
        )
      case 'pubs':
        return (
          <div key={i} className="flex gap-3">
            <div className="size-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
              <BookOpen size={13} className="text-white/50" />
            </div>
            <div className="flex-1 min-w-0">
              <SectionLabel label="Publications" count={entry.pubs!.length} />
              <div className="space-y-2">
                {entry.pubs!.map((p, idx) => <PubCard key={p.id} pub={p} index={idx} />)}
              </div>
            </div>
          </div>
        )
      case 'trials':
        return (
          <div key={i} className="flex gap-3">
            <div className="size-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
              <FlaskConical size={13} className="text-white/50" />
            </div>
            <div className="flex-1 min-w-0">
              <SectionLabel label="Clinical Trials" count={entry.trials!.length} />
              <div className="space-y-2">
                {entry.trials!.map((t, idx) => <TrialCard key={t.id} trial={t} index={idx} />)}
              </div>
            </div>
          </div>
        )
      case 'cites':
        return (
          <div key={i} className="flex gap-3">
            <div className="size-7 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0 mt-0.5">
              <Paperclip size={13} className="text-white/50" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-[11px] uppercase tracking-widest text-white/25 font-semibold mt-6 mb-2">Sources</p>
              <CitationsRow cites={entry.cites!} />
            </div>
          </div>
        )
      default:
        return null
    }
  }

  // ── Active tools badges ─────────────────────────────────────────────────────

  const activeToolBadges = INPUT_TOOLS.filter(t => activeTools.has(t.id))

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex h-screen bg-[#0a0a0a] text-white overflow-hidden">

      {/* ── Sidebar ── */}
      <aside className="w-[240px] flex-shrink-0 flex flex-col border-r border-white/[0.06] bg-[#0a0a0a]">
        {/* logo */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-white/[0.05]">
          <DNABuddy isLoading={loading} hasResults={hasResults} compact />
          <div>
            <p className="text-[13px] font-semibold text-white/90 leading-none">Curalink</p>
            <p className="text-[10px] text-white/30 mt-0.5">AI Research</p>
          </div>
        </div>

        {/* New session */}
        <button
          onClick={newSession}
          className="cursor-pointer mx-3 mt-3 flex items-center gap-2 px-3 py-2 rounded-lg border border-white/[0.07] text-[13px] text-white/50 hover:text-white/80 hover:bg-white/[0.04] transition-all group"
          id="new-session-btn"
        >
          <Plus size={14} className="group-hover:rotate-90 transition-transform duration-200" />
          New session
        </button>

        {/* Session list */}
        {sessions.length > 0 && (
          <div className="mt-4 flex-1 overflow-y-auto px-2 pb-4">
            <p className="px-2 mb-2 text-[10px] uppercase tracking-widest text-white/20 font-semibold">Recent</p>
            {sessions.map(s => (
              <button
                key={s.id}
                onClick={() => setActiveSession(s.id)}
                className={cn(
                  'cursor-pointer w-full text-left px-3 py-2 rounded-lg text-[13px] transition-colors flex items-start gap-2',
                  activeSession === s.id
                    ? 'bg-white/[0.07] text-white/90'
                    : 'text-white/40 hover:text-white/70 hover:bg-white/[0.03]'
                )}
              >
                <Clock size={12} className="flex-shrink-0 mt-0.5 opacity-50" />
                <div className="min-w-0">
                  <p className="truncate">{s.title}</p>
                  <p className="text-[11px] opacity-50">{s.ts}</p>
                </div>
              </button>
            ))}
          </div>
        )}
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

        {/* Topbar */}
        <header className="flex items-center justify-between px-5 h-12 border-b border-white/[0.05] flex-shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-[13px] text-white/50">Curalink</span>
            <ChevronRight size={12} className="text-white/20" />
            <span className="text-[13px] text-white/80">
              {activeSession ? sessions.find(s => s.id === activeSession)?.title ?? 'Session' : 'Medical Research Assistant'}
            </span>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {!hasResults ? (
            /* ── Hero ── */
            <div className="flex flex-col items-center justify-center h-full px-6 text-center pb-8">
              <h1 className="text-2xl font-semibold text-white/90 tracking-tight mb-2">
                Medical Research, <span className="text-white/40">Powered by AI</span>
              </h1>
              <p className="text-[14px] text-white/35 max-w-md leading-relaxed mb-8">
                Retrieves from PubMed, OpenAlex & ClinicalTrials.gov — ranked, synthesized, and grounded by Gemma.
              </p>
              {/* Suggestion cards */}
              <div className="grid grid-cols-2 gap-2 max-w-xl w-full">
                {SUGGESTIONS.map(s => {
                  const Icon = s.icon
                  return (
                    <button
                      key={s.label}
                      onClick={() => loadSuggestion(s.label)}
                      className="cursor-pointer group text-left p-3.5 rounded-xl border border-white/[0.07] bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/[0.12] transition-all"
                    >
                      <Icon size={14} className="text-white/30 mb-2 group-hover:text-white/50 transition-colors" />
                      <p className="text-[13px] text-white/55 group-hover:text-white/80 transition-colors leading-snug">{s.label}</p>
                    </button>
                  )
                })}
              </div>
            </div>
          ) : (
            /* ── Feed ── */
            <div className="max-w-3xl mx-auto px-6 py-6 space-y-6">
              {feed.map((entry, i) => renderEntry(entry, i))}
              {error && (
                <div className="flex items-center gap-2 text-[13px] text-red-400/80 bg-red-500/[0.08] border border-red-500/15 rounded-xl px-4 py-3">
                  <X size={13} />
                  {error}
                </div>
              )}
              <div ref={feedEndRef} />
            </div>
          )}
        </div>

        {/* ── Input dock ── (Claude-style) */}
        <div className="flex-shrink-0 max-w-3xl w-full mx-auto">
          {/* Mascot floating above the input box */}
          <DNABuddy isLoading={loading} hasResults={hasResults} />

          <div className="px-4 sm:px-6 pb-5 pt-0">

            {/* Mode toggle */}
            <div className="flex items-center gap-1 mb-2.5">
              {(['quick', 'structured'] as Mode[]).map(m => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    'text-[12px] px-3 py-1 rounded-lg transition-colors font-medium',
                    mode === m
                      ? 'bg-white/[0.08] text-white/80'
                      : 'text-white/30 hover:text-white/60 hover:bg-white/[0.04]'
                  )}
                  id={`mode-${m}`}
                >
                  {m === 'quick' ? 'Quick Chat' : 'Structured'}
                </button>
              ))}
            </div>

            {/* Structured fields (only when mode = structured) */}
            {mode === 'structured' && (
              <div className="grid grid-cols-3 gap-2 mb-2">
                <input
                  type="text"
                  placeholder="Patient name"
                  value={patientName}
                  onChange={e => setPatientName(e.target.value)}
                  className="bg-[#111] border border-white/[0.08] rounded-lg px-3 py-2 text-[13px] text-white/80 placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                />
                <input
                  type="text"
                  placeholder="Disease / condition *"
                  value={disease}
                  onChange={e => setDisease(e.target.value)}
                  className="bg-[#111] border border-white/[0.08] rounded-lg px-3 py-2 text-[13px] text-white/80 placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                />
                <input
                  type="text"
                  placeholder="Location (trials)"
                  value={location}
                  onChange={e => setLocation(e.target.value)}
                  className="bg-[#111] border border-white/[0.08] rounded-lg px-3 py-2 text-[13px] text-white/80 placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
                />
              </div>
            )}

            {/* Main input box */}
            <div className="input-glow relative rounded-2xl border border-white/[0.10] bg-[#111111] transition-all">

              {/* Active tool chips inside box */}
              {activeToolBadges.length > 0 && (
                <div className="flex items-center gap-1.5 px-4 pt-3 flex-wrap">
                  {activeToolBadges.map(t => {
                    const Icon = t.icon
                    return (
                      <span key={t.id} className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-white/[0.06] text-[11px] text-white/50 border border-white/[0.07]">
                        <Icon size={10} />
                        {t.label}
                        <button onClick={() => toggleTool(t.id)} className="hover:text-white/80 transition-colors ml-0.5">
                          <X size={9} />
                        </button>
                      </span>
                    )
                  })}
                </div>
              )}

              {/* Textarea */}
              <textarea
                ref={textareaRef}
                id="main-input"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={mode === 'quick' ? 'Ask anything about medical research…' : 'Describe your research query…'}
                className="chat-textarea w-full bg-transparent px-4 pt-3 pb-2 text-[14px] text-white/85 placeholder:text-white/20 focus:outline-none leading-relaxed resize-none"
                disabled={loading}
                rows={1}
              />

              {/* Bottom toolbar — the "toys" */}
              <div className="flex items-center justify-between px-3 pb-3 pt-1">
                <div className="flex items-center gap-1">

                  {/* Tool picker */}
                  <div className="relative" ref={toolPickerRef}>
                    <button
                      onClick={() => setToolPickerOpen(o => !o)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-white/35 hover:text-white/70 hover:bg-white/[0.06] transition-all text-[12px]"
                      title="Add tools"
                      id="tool-picker-btn"
                    >
                      <Plus size={13} />
                      <span className="hidden sm:inline">Add</span>
                    </button>

                    {toolPickerOpen && (
                      <div className="absolute bottom-full left-0 mb-2 w-56 bg-[#161616] border border-white/[0.10] rounded-xl shadow-2xl overflow-hidden z-50">
                        <div className="px-3 py-2 border-b border-white/[0.06]">
                          <p className="text-[11px] uppercase tracking-widest text-white/25 font-semibold">Research Tools</p>
                        </div>
                        {INPUT_TOOLS.map(t => {
                          const Icon = t.icon
                          const on = activeTools.has(t.id)
                          return (
                            <button
                              key={t.id}
                              onClick={() => { toggleTool(t.id) }}
                              className={cn(
                                'w-full text-left flex items-center gap-3 px-3 py-2.5 transition-colors text-[13px]',
                                on ? 'bg-white/[0.05] text-white/80' : 'text-white/40 hover:bg-white/[0.03] hover:text-white/70'
                              )}
                            >
                              <Icon size={13} className={on ? 'text-white/70' : 'text-white/25'} />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium leading-none mb-0.5">{t.label}</p>
                                <p className="text-[11px] opacity-50 leading-tight">{t.desc}</p>
                              </div>
                              {on && <div className="size-1.5 rounded-full bg-emerald-400 flex-shrink-0" />}
                            </button>
                          )
                        })}
                      </div>
                    )}
                  </div>

                  {/* Individual quick-access toys */}
                  <button
                    onClick={() => toggleTool('sources')}
                    className={cn(
                      'p-1.5 rounded-lg transition-all',
                      activeTools.has('sources')
                        ? 'text-white/70 bg-white/[0.08]'
                        : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]'
                    )}
                    title="PubMed + OpenAlex"
                    id="toy-sources"
                  >
                    <BookOpen size={14} />
                  </button>

                  <button
                    onClick={() => toggleTool('trials')}
                    className={cn(
                      'p-1.5 rounded-lg transition-all',
                      activeTools.has('trials')
                        ? 'text-white/70 bg-white/[0.08]'
                        : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]'
                    )}
                    title="Clinical Trials"
                    id="toy-trials"
                  >
                    <FlaskConical size={14} />
                  </button>

                  <button
                    onClick={() => toggleTool('deep')}
                    className={cn(
                      'p-1.5 rounded-lg transition-all',
                      activeTools.has('deep')
                        ? 'text-white/70 bg-white/[0.08]'
                        : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]'
                    )}
                    title="Deep Search (300 results)"
                    id="toy-deep"
                  >
                    <Microscope size={14} />
                  </button>

                  <button
                    onClick={() => toggleTool('web')}
                    className={cn(
                      'p-1.5 rounded-lg transition-all',
                      activeTools.has('web')
                        ? 'text-white/70 bg-white/[0.08]'
                        : 'text-white/25 hover:text-white/55 hover:bg-white/[0.05]'
                    )}
                    title="Location-based trial matching"
                    id="toy-location"
                  >
                    <Globe size={14} />
                  </button>

                  <div className="w-px h-4 bg-white/[0.08] mx-1" />

                  <button
                    className="p-1.5 rounded-lg text-white/25 hover:text-white/55 hover:bg-white/[0.05] transition-all"
                    title="Attach file"
                    id="toy-attach"
                  >
                    <Paperclip size={14} />
                  </button>

                </div>

                {/* Send button */}
                <button
                  onClick={mode === 'quick' ? handleQuickSend : (e) => handleStructuredSend(e as unknown as React.FormEvent)}
                  disabled={loading || (!input.trim() && !disease.trim())}
                  className={cn(
                    'size-8 rounded-lg flex items-center justify-center transition-all flex-shrink-0',
                    (input.trim() || disease.trim()) && !loading
                      ? 'bg-white text-black hover:bg-white/90 shadow-sm'
                      : 'bg-white/[0.08] text-white/25 cursor-not-allowed'
                  )}
                  id="send-btn"
                >
                  {loading ? (
                    <div className="size-3.5 rounded-full border-2 border-black/20 border-t-black/70 animate-spin" />
                  ) : (
                    <ArrowUp size={15} strokeWidth={2.5} />
                  )}
                </button>
              </div>
            </div>

            {/* Footer note */}
            <p className="text-center text-[11px] text-white/15 mt-2">
              Curalink can make mistakes. Verify sources for medical decisions.
            </p>
          </div>{/* close inner padding div */}
        </div>
      </div>
    </div>
  )
}
