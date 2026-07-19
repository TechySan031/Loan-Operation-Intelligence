// Types for Loan Operation Intelligence API

export interface HealthCheck {
  status: string;
  service: string;
}

export interface ReadinessCheck {
  status: string;
  checks: {
    postgres: string;
    redis: string;
    pinecone: string;
  };
}

export interface KBRecord {
  id: string;
  record_id: string;
  title: string;
  content: string;
  content_clean: string | null;
  category: string;
  subcategory: string | null;
  source: string;
  source_url: string | null;
  version: string;
  contains_pii: boolean;
  metadata: Record<string, any> | null;
  chunk_id: string | null;
  parent_doc_id: string | null;
  token_count: number | null;
  language: string;
  created_at: string;
  updated_at: string;
}

export interface KBRecordCreate {
  record_id: string;
  title: string;
  content: string;
  category: string;
  subcategory?: string;
  source: string;
  source_url?: string;
  version?: string;
  metadata?: Record<string, any>;
  language?: string;
}

export interface KBStats {
  total_records: number;
  categories: Record<string, number>;
}

export interface KBSearchResult {
  record_id: string;
  title: string;
  content: string;
  category: string;
  source: string;
  source_url: string | null;
  relevance_score: number;
  metadata: Record<string, any> | null;
}

export interface KBSearchResponse {
  query: string;
  results: KBSearchResult[];
  total: number;
  retrieval_time_ms: number;
}

export interface RetrievalTestItem {
  test_id: string;
  query: string;
  retrieved_record: KBSearchResult | null;
  source_reference: string;
  relevance_explanation: string;
  verdict: 'correct' | 'partially_correct' | 'incorrect' | 'error';
  retrieval_time_ms: number;
}

export interface Call {
  id: string;
  external_call_id: string | null;
  borrower_name: string | null;
  loan_id: string | null;
  loan_type: string | null;
  language: string;
  status: string;
  outcome: string | null;
  payment_due_date: string | null;
  amount_due: number | null;
  commitment_date: string | null;
  callback_scheduled: string | null;
  summary: string | null;
  sentiment_score: number | null;
  market: string;
  created_at: string;
  updated_at: string;
  event_count?: number;
  nudge_count?: number;
}

export interface CallEvent {
  id: string;
  event_type: string;
  from_state: string | null;
  to_state: string | null;
  payload: Record<string, any> | null;
  created_at: string;
}

export interface CallAnalyticsSummary {
  total_calls: number;
  outcomes: Record<string, number>;
}

export interface Nudge {
  id: string;
  call_id: string;
  signal_type: string;
  signal_text: string;
  nudge_text: string;
  confidence: number;
  priority: string;
  latency_ms: {
    asr: number;
    signal: number;
    llm: number;
    delivery: number;
    total: number;
  } | null;
  created_at: string;
}

export interface NudgeAnalysis {
  call_id: string;
  total_nudges: number;
  delivered_nudges: number;
  suppressed_nudges: number;
  suppression_breakdown: Record<string, number>;
  avg_confidence: number;
  avg_latency_ms: Record<string, number>;
  p50_latency_ms: number;
  p95_latency_ms: number;
  signal_type_breakdown: Record<string, number>;
  false_positive_estimate: number;
}

export interface LatencyReport {
  total_calls_analyzed: number;
  total_nudges_generated: number;
  total_nudges_delivered: number;
  total_nudges_suppressed: number;
  component_latency: Record<string, { p50: number; p95: number }>;
  end_to_end_latency: { p50: number; p95: number };
  signal_type_accuracy: Record<string, number>;
}

export interface BorrowerLookupResponse {
  found: boolean;
  borrower_name?: string;
  loan_id?: string;
  loan_type?: string;
  amount_due?: number;
  due_date?: string;
  days_until_due?: number;
  payment_history?: string;
  eligible_programs?: string[];
  market?: string;
  language?: string;
  message: string;
}

export interface ToolSearchResponse {
  found: boolean;
  answer: string;
  sources: {
    record_id: string;
    title: string;
    source: string;
  }[];
  confidence: number;
}

export interface EligibilityResponse {
  eligible: boolean;
  program_type: string;
  message: string;
}

export interface CallbackResponse {
  scheduled: boolean;
  callback_date: string;
  callback_time: string;
  reason: string;
  message: string;
}

export interface PaymentCommitmentResponse {
  recorded: boolean;
  commitment_date: string;
  amount: number;
  payment_method: string;
  message: string;
}

export interface EscalationResponse {
  escalated: boolean;
  reason: string;
  priority: string;
  message: string;
}

// API CLIENT CONFIG
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

async function fetchJson<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;
  
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });
  } catch (err: any) {
    // Gracefully handle complete network disconnect/offline backend
    console.warn(`[Network Offline] Failed to reach API at ${url}:`, err);
    throw new Error(`The backend server at ${API_BASE_URL} is currently unreachable. Please make sure the service is online.`);
  }

  if (!response.ok) {
    let errorMsg = `API Error: ${response.status} ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson?.detail) {
        errorMsg = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
      }
    } catch (_) {}
    throw new Error(errorMsg);
  }

  return response.json() as Promise<T>;
}

export const api = {
  // Liveness & Readiness Checks
  getLiveness: () => fetchJson<HealthCheck>('/health'),
  getReadiness: () => fetchJson<ReadinessCheck>('/health/ready'),

  // Knowledge Base APIs
  getKBStats: () => fetchJson<KBStats>('/knowledge/stats'),
  getKBRecords: (page = 1, pageSize = 20, category?: string, language?: string) => {
    let query = `?page=${page}&page_size=${pageSize}`;
    if (category) query += `&category=${encodeURIComponent(category)}`;
    if (language) query += `&language=${encodeURIComponent(language)}`;
    return fetchJson<{ records: KBRecord[]; total: number; page: number; page_size: number }>(
      `/knowledge/records${query}`
    );
  },
  getKBRecord: (id: string) => fetchJson<KBRecord>(`/knowledge/records/${id}`),
  createKBRecord: (record: KBRecordCreate) =>
    fetchJson<KBRecord>('/knowledge/records', {
      method: 'POST',
      body: JSON.stringify(record),
    }),
  updateKBRecord: (id: string, record: Partial<KBRecordCreate>) =>
    fetchJson<KBRecord>(`/knowledge/records/${id}`, {
      method: 'PUT',
      body: JSON.stringify(record),
    }),
  deleteKBRecord: (id: string) =>
    fetchJson<{ status: string; record_id: string }>(`/knowledge/records/${id}`, {
      method: 'DELETE',
    }),
  searchKB: (params: {
    query: string;
    category?: string;
    product_type?: string;
    language?: string;
    market?: string;
    top_k?: number;
  }) =>
    fetchJson<KBSearchResponse>('/knowledge/search', {
      method: 'POST',
      body: JSON.stringify({
        query: params.query,
        category: params.category || null,
        product_type: params.product_type || null,
        language: params.language || null,
        market: params.market || null,
        top_k: params.top_k || 5,
      }),
    }),
  ingestKB: (records: KBRecordCreate[], embed = true, detectPii = true) =>
    fetchJson<{
      ingested: number;
      chunks_created: number;
      pii_flagged: number;
      vectors_upserted: number;
      errors: any[];
    }>('/knowledge/ingest', {
      method: 'POST',
      body: JSON.stringify({
        records,
        embed,
        detect_pii: detectPii,
      }),
    }),
  getRetrievalTest: () => fetchJson<RetrievalTestItem[]>('/knowledge/retrieval-test'),

  // Call & Nudge APIs
  getCalls: (params: {
    status?: string;
    outcome?: string;
    market?: string;
    page?: number;
    page_size?: number;
  }) => {
    let query = `?page=${params.page || 1}&page_size=${params.page_size || 20}`;
    if (params.status) query += `&status=${encodeURIComponent(params.status)}`;
    if (params.outcome) query += `&outcome=${encodeURIComponent(params.outcome)}`;
    if (params.market) query += `&market=${encodeURIComponent(params.market)}`;
    return fetchJson<{ calls: Call[]; total: number; page: number; page_size: number }>(`/calls/${query}`);
  },
  getCall: (id: string) => fetchJson<Call>(`/calls/${id}`),
  getCallTranscript: (id: string) => fetchJson<{ call_id: string; transcript: any }>(`/calls/${id}/transcript`),
  getCallEvents: (id: string) => fetchJson<{ call_id: string; events: CallEvent[] }>(`/calls/${id}/events`),
  getCallAnalytics: (market?: string) => {
    const query = market ? `?market=${encodeURIComponent(market)}` : '';
    return fetchJson<CallAnalyticsSummary>(`/calls/analytics/summary${query}`);
  },

  // Nudge Endpoints
  startNudgeSession: (callId: string, audioSource: string, chunkMs = 250) =>
    fetchJson<{ session_id: string; call_id: string; status: string }>('/nudges/session/start', {
      method: 'POST',
      body: JSON.stringify({ call_id: callId, audio_source: audioSource, chunk_ms: chunkMs }),
    }),
  stopNudgeSession: (callId: string) =>
    fetchJson<{ call_id: string; status: string }>(`/nudges/session/stop?call_id=${encodeURIComponent(callId)}`, {
      method: 'POST',
    }),
  getNudgeAnalysis: (callId: string) => fetchJson<NudgeAnalysis>(`/nudges/analysis/${callId}`),
  getLatencyReport: () => fetchJson<LatencyReport>('/nudges/latency-report'),

  // Evaluation Run
  runEval: (evalType = 'all') =>
    fetchJson<{ eval_type: string; results: any }>(`/eval/run?eval_type=${encodeURIComponent(evalType)}`, {
      method: 'POST',
    }),
  getEvalResults: () => fetchJson<{ available_results: string[]; total: number }>('/eval/results'),
  getEvalResultsByType: (evalType: string) => fetchJson<any>(`/eval/results/${evalType}`),

  // REST tools endpoints
  lookupBorrower: (params: { borrower_name?: string | null; loan_id?: string | null }) =>
    fetchJson<BorrowerLookupResponse>('/tools/lookup-borrower', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  searchTools: (params: { query: string; category?: string | null }) =>
    fetchJson<ToolSearchResponse>('/tools/search', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  checkEligibility: (params: { loan_id: string; program_type: string }) =>
    fetchJson<EligibilityResponse>('/tools/check-eligibility', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  scheduleCallback: (params: { date: string; time: string; reason?: string }) =>
    fetchJson<CallbackResponse>('/tools/schedule-callback', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  paymentCommitment: (params: { commitment_date: string; amount: number; payment_method: string }) =>
    fetchJson<PaymentCommitmentResponse>('/tools/payment-commitment', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
  escalate: (params: { reason: string; priority?: string }) =>
    fetchJson<EscalationResponse>('/tools/escalate', {
      method: 'POST',
      body: JSON.stringify(params),
    }),
};
