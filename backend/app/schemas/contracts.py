from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


ResearchStatus = Literal['foundation_only', 'retrieving', 'ready', 'error']
ChatStatus = Literal['foundation_only', 'streaming', 'completed', 'error']
SourcePlatform = Literal['pubmed', 'openalex', 'clinicaltrials']
ConversationRole = Literal['system', 'user', 'assistant']


class QueryContext(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    patient_alias: str | None = None
    disease: str = Field(..., min_length=2)
    intent: str | None = None
    location: str | None = None
    follow_up_question: str | None = None


class QueryContextUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')

    patient_alias: str | None = None
    disease: str | None = Field(default=None, min_length=2)
    location: str | None = None


class PublicationRecord(BaseModel):
    id: str
    title: str
    authors: list[str] = Field(default_factory=list)
    publication_year: int | None = None
    source: Literal['pubmed', 'openalex']
    url: str
    abstract_snippet: str | None = None
    supporting_snippet: str | None = None
    relevance_reason: str | None = None


class ClinicalTrialRecord(BaseModel):
    id: str
    title: str
    recruiting_status: str
    eligibility_criteria: str | None = None
    location: str | None = None
    contact_information: str | None = None
    source: Literal['clinicaltrials'] = 'clinicaltrials'
    url: str
    supporting_snippet: str | None = None
    relevance_reason: str | None = None


class CitationRecord(BaseModel):
    id: str
    source: SourcePlatform
    title: str
    year: int | None = None
    authors: list[str] = Field(default_factory=list)
    url: str
    snippet: str


class ResearchRequest(BaseModel):
    session_id: str | None = None
    query: str = Field(..., min_length=3)
    candidate_target: int = Field(default=150, ge=25, le=300)
    include_trials: bool = True
    context: QueryContext


class ResearchResponse(BaseModel):
    session_id: str
    status: ResearchStatus
    note: str
    expanded_queries: list[str] = Field(default_factory=list)
    publications: list[PublicationRecord] = Field(default_factory=list)
    clinical_trials: list[ClinicalTrialRecord] = Field(default_factory=list)
    evidence_count: int = 0


class ChatMessage(BaseModel):
    role: ConversationRole
    content: str = Field(..., min_length=1)


class AnswerSection(BaseModel):
    heading: str
    body: str


class ChatTurnRequest(BaseModel):
    session_id: str | None = None
    context_update: QueryContextUpdate | None = None
    messages: list[ChatMessage] = Field(default_factory=list, min_length=1)

    @model_validator(mode='after')
    def validate_turn_shape(self) -> Self:
        if self.session_id is None:
            if self.context_update is None or self.context_update.disease is None:
                raise ValueError(
                    'New chat session requires context_update.disease to establish disease-aware context.'
                )
        return self


class ChatTurnResponse(BaseModel):
    session_id: str
    status: ChatStatus
    message: ChatMessage
    answer_sections: list[AnswerSection] = Field(default_factory=list)
    citations: list[CitationRecord] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    patient_alias: str | None = None
    disease: str | None = None
    location: str | None = None


class SessionSummary(BaseModel):
    session_id: str
    patient_alias: str | None = None
    disease: str | None = None
    location: str | None = None
    message_count: int = 0
    last_activity_label: str = 'just now'


class ReadyResponse(BaseModel):
    status: Literal['ready'] = 'ready'
    environment: str
    api_prefix: str
    ollama_model: str
