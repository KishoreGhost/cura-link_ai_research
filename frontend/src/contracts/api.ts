export type ResearchStatus = 'foundation_only' | 'retrieving' | 'ready' | 'error'
export type ChatStatus = 'foundation_only' | 'streaming' | 'completed' | 'error'
export type SourcePlatform = 'pubmed' | 'openalex' | 'clinicaltrials'
export type ConversationRole = 'system' | 'user' | 'assistant'

export interface QueryContext {
  patient_alias?: string
  disease: string
  intent?: string
  location?: string
  follow_up_question?: string
}

export interface QueryContextUpdate {
  patient_alias?: string
  disease?: string
  location?: string
}

export interface PublicationRecord {
  id: string
  title: string
  authors: string[]
  publication_year?: number
  source: 'pubmed' | 'openalex'
  url: string
  abstract_snippet?: string
  supporting_snippet?: string
  relevance_reason?: string
}

export interface ClinicalTrialRecord {
  id: string
  title: string
  recruiting_status: string
  eligibility_criteria?: string
  location?: string
  contact_information?: string
  source: 'clinicaltrials'
  url: string
  supporting_snippet?: string
  relevance_reason?: string
}

export interface CitationRecord {
  id: string
  source: SourcePlatform
  title: string
  year?: number
  authors: string[]
  url: string
  snippet: string
}

export interface ResearchRequest {
  session_id?: string
  query: string
  candidate_target?: number
  include_trials?: boolean
  context: QueryContext
}

export interface ResearchResponse {
  session_id: string
  status: ResearchStatus
  note: string
  expanded_queries: string[]
  publications: PublicationRecord[]
  clinical_trials: ClinicalTrialRecord[]
  evidence_count: number
}

export interface ChatMessage {
  role: ConversationRole
  content: string
}

export interface AnswerSection {
  heading: string
  body: string
}

export interface ChatTurnRequest {
  session_id?: string
  context_update?: QueryContextUpdate
  messages: ChatMessage[]
}

export interface ChatTurnResponse {
  session_id: string
  status: ChatStatus
  message: ChatMessage
  answer_sections: AnswerSection[]
  citations: CitationRecord[]
}

export interface SessionCreateRequest {
  patient_alias?: string
  disease?: string
  location?: string
}

export interface SessionSummary {
  session_id: string
  patient_alias?: string
  disease?: string
  location?: string
  message_count: number
  last_activity_label: string
}
