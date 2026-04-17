/**
 * Typed API client for Curalink backend.
 */

import { API_BASE_URL } from './config'
import type {
  ChatTurnRequest,
  ChatTurnResponse,
  ResearchRequest,
  ResearchResponse,
} from '../contracts/api'

async function apiPost<TReq, TRes>(path: string, body: TReq): Promise<TRes> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!response.ok) {
    let detail = `HTTP ${response.status}`
    try {
      const err = await response.json()
      detail = err.detail ?? detail
    } catch {
      // ignore
    }
    throw new Error(detail)
  }
  return response.json() as Promise<TRes>
}

export function fetchResearch(request: ResearchRequest): Promise<ResearchResponse> {
  return apiPost<ResearchRequest, ResearchResponse>('/research/query', request)
}

export function sendChatTurn(request: ChatTurnRequest): Promise<ChatTurnResponse> {
  return apiPost<ChatTurnRequest, ChatTurnResponse>('/chat/turn', request)
}
