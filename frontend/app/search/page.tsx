'use client';

import React, { useState } from 'react';
import { 
  Search, 
  Sparkles, 
  HelpCircle, 
  ExternalLink,
  Tag,
  Clock,
  Compass,
  Database
} from 'lucide-react';
import { api, KBSearchResponse } from '@/lib/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';
import ErrorState from '@/components/ErrorState';
import { useToast } from '@/components/Toast';

export default function SemanticSearch() {
  const { toast } = useToast();
  
  // Search state
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [language, setLanguage] = useState('');
  const [market, setMarket] = useState('');
  
  // Response states
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchResponse, setSearchResponse] = useState<KBSearchResponse | null>(null);

  const handleSearch = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!query.trim()) {
      toast('Please enter a search query', 'info');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const res = await api.searchKB({
        query: query.trim(),
        category: category || undefined,
        language: language || undefined,
        market: market || undefined,
        top_k: 5,
      });

      setSearchResponse(res);
      
      if (res.results.length === 0) {
        toast('No matching documents found', 'info');
      } else {
        toast(`Found ${res.results.length} matches in ${res.retrieval_time_ms}ms`, 'success');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Semantic search pipeline failed');
      toast('Failed to search knowledge base', 'error');
    } finally {
      setLoading(false);
    }
  };

  const formatScore = (score: number) => {
    return `${Math.round(score * 100)}% Relevance`;
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.75) return 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
    if (score >= 0.6) return 'text-indigo-600 dark:text-indigo-400 bg-indigo-500/10 border-indigo-500/20';
    return 'text-neutral-500 dark:text-neutral-450 bg-neutral-100 dark:bg-neutral-900 border border-[var(--card-border)]';
  };

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Page Header */}
      <div className="border-b border-[var(--navbar-border)] pb-5">
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent flex items-center gap-2">
          Semantic Search Engine
        </h1>
        <p className="text-xs text-neutral-550 dark:text-neutral-455 mt-1.5 leading-relaxed">
          Query the loan operations vector index using neural embeddings powered by BAAI/bge-small-en-v1.5.
        </p>
      </div>

      {/* Offline Status Warning Alert */}
      {error && (
        <div className="flex items-center justify-between p-3.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl text-xs font-medium animate-pulse mb-4">
          <span>Failed to connect to Pinecone Vector Index. Query will fail until service is restored.</span>
          <button 
            onClick={() => handleSearch()}
            className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-[10px] font-bold border border-red-550/20"
          >
            Retry Call
          </button>
        </div>
      )}

      {/* Large AI Search Box Card */}
      <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 backdrop-blur-md shadow-2xl glow-card-indigo glass-panel">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-neutral-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything (e.g. 'What is the penalty for personal loan late EMI?')"
              className="w-full pl-12 pr-32 py-4 bg-neutral-100 dark:bg-neutral-955 border border-[var(--card-border)] rounded-xl text-[var(--foreground)] focus:outline-none focus:border-indigo-500 placeholder-neutral-500 dark:placeholder-neutral-650 shadow-inner text-sm leading-relaxed premium-input"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-3 top-1/2 -translate-y-1/2 inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2 text-xs font-semibold text-white transition-all shadow-lg disabled:opacity-50 border border-indigo-400/25 cursor-pointer"
            >
              <Sparkles className="h-3.5 w-3.5" />
              Query
            </button>
          </div>

          {/* Search filters row */}
          <div className="grid gap-3 sm:grid-cols-3 pt-2 text-xs">
            <div>
              <label className="block text-[9px] uppercase font-bold text-neutral-500 mb-1">
                Limit Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-100 dark:bg-neutral-950 border border-[var(--card-border)] rounded-xl text-neutral-650 dark:text-neutral-350 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
              >
                <option value="">All Categories</option>
                <option value="policy">Policy</option>
                <option value="product">Product</option>
                <option value="faq">FAQ</option>
                <option value="objection">Objection</option>
                <option value="compliance">Compliance</option>
                <option value="payment">Payment</option>
                <option value="escalation">Escalation</option>
              </select>
            </div>
            <div>
              <label className="block text-[9px] uppercase font-bold text-neutral-500 mb-1">
                Market Location
              </label>
              <select
                value={market}
                onChange={(e) => setMarket(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-100 dark:bg-neutral-950 border border-[var(--card-border)] rounded-xl text-neutral-650 dark:text-neutral-350 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
              >
                <option value="">All Markets</option>
                <option value="india">India</option>
                <option value="philippines">Philippines</option>
                <option value="indonesia">Indonesia</option>
              </select>
            </div>
            <div>
              <label className="block text-[9px] uppercase font-bold text-neutral-500 mb-1">
                Language Model
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 bg-neutral-100 dark:bg-neutral-950 border border-[var(--card-border)] rounded-xl text-neutral-650 dark:text-neutral-350 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
              >
                <option value="">All Languages</option>
                <option value="en">English (IN)</option>
                <option value="ph">Taglish (PH)</option>
                <option value="id">Indo-English (ID)</option>
              </select>
            </div>
          </div>
        </form>
      </div>

      {/* Search results telemetry & listing */}
      {loading ? (
        <LoadingSpinner text="Computing neural search embeddings and querying vector index..." />
      ) : error ? (
        <EmptyState
          title="Vector Database Offline"
          description="We are unable to query the Pinecone neural search cluster. Verify that your API keys are correct and the FastAPI vector pipeline is active."
          icon={Compass}
          actionButton={
            <button
              onClick={() => handleSearch()}
              className="px-4 py-2 bg-indigo-650 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all"
            >
              Retry Query
            </button>
          }
        />
      ) : searchResponse ? (
        <div className="space-y-6">
          {/* Metadata/telemetry banner */}
          <div className="flex items-center justify-between text-xs text-neutral-600 dark:text-neutral-400 border border-[var(--card-border)] bg-[var(--card-bg)] px-4 py-3.5 rounded-xl backdrop-blur-md glass-panel">
            <span className="flex items-center gap-1.5 font-semibold">
              <Database className="h-4 w-4 text-indigo-500 dark:text-indigo-400" />
              Retrieved <span className="text-[var(--foreground)] opacity-90">{searchResponse.results.length}</span> documents
            </span>
            <span className="flex items-center gap-1.5 font-semibold">
              <Clock className="h-4 w-4 text-indigo-500 dark:text-indigo-400" />
              Query Latency: <span className="text-[var(--foreground)] opacity-90">{searchResponse.retrieval_time_ms} ms</span>
            </span>
          </div>

          {searchResponse.results.length === 0 ? (
            <EmptyState
              title="No semantic matches"
              description="No vectors found above the minimum confidence threshold. Try softening your query keywords or changing the filters."
              icon={Compass}
            />
          ) : (
            <div className="space-y-5">
              {searchResponse.results.map((result, idx) => (
                <div 
                  key={idx} 
                  className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] hover:bg-[var(--card-bg)]/80 p-6 transition-all duration-300 hover:-translate-y-0.5 shadow-2xl relative overflow-hidden group hover:border-indigo-500/25 glass-panel"
                >
                  <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />

                  {/* Top card metadata */}
                  <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pl-1">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-bold ${getScoreColor(result.relevance_score)}`}>
                        {formatScore(result.relevance_score)}
                      </span>
                      <span className="text-[9px] font-mono font-bold text-neutral-500">ID: {result.record_id}</span>
                    </div>

                    <div className="flex items-center gap-2 text-[10px] font-bold text-neutral-500">
                      <span className="capitalize bg-neutral-100 dark:bg-neutral-900/60 text-neutral-600 dark:text-neutral-300 px-2.5 py-1 rounded-lg border border-[var(--card-border)]">
                        {result.category}
                      </span>
                      {result.source && (
                        <span className="bg-neutral-100 dark:bg-neutral-900/60 text-neutral-600 dark:text-neutral-300 px-2.5 py-1 rounded-lg border border-[var(--card-border)] flex items-center gap-1">
                          Source: {result.source}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Document Title & Content */}
                  <div className="space-y-2 mb-4 pl-1">
                    <h3 className="text-sm font-extrabold text-neutral-200 group-hover:text-indigo-400 transition-colors">
                      {result.title}
                    </h3>
                    <p className="text-xs text-neutral-350 leading-relaxed font-sans font-light">
                      {result.content}
                    </p>
                  </div>

                  {/* Card bottom metadata details */}
                  {result.metadata && (
                    <div className="border-t border-white/[0.02] pt-3.5 flex flex-wrap gap-2 pl-1 text-[9px] font-bold">
                      {result.metadata.product_type && (
                        <span className="inline-flex items-center gap-1 rounded bg-neutral-900/40 px-2 py-1 text-neutral-500 border border-white/[0.03]">
                          <Tag className="h-2.5 w-2.5 text-indigo-400" />
                          Type: {Array.isArray(result.metadata.product_type) ? result.metadata.product_type.join(', ') : result.metadata.product_type}
                        </span>
                      )}
                      {result.metadata.applicable_market && (
                        <span className="inline-flex items-center gap-1 rounded bg-neutral-900/40 px-2 py-1 text-neutral-500 border border-white/[0.03]">
                          Market: {result.metadata.applicable_market}
                        </span>
                      )}
                      {result.source_url && (
                        <a 
                          href={result.source_url} 
                          target="_blank" 
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 rounded bg-indigo-500/5 hover:bg-indigo-500/10 px-2 py-1 text-indigo-400 border border-indigo-500/10 transition-colors ml-auto"
                        >
                          Citation Link
                          <ExternalLink className="h-2.5 w-2.5" />
                        </a>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        // Initial state explanation card
        <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-dashed border-white/[0.03] bg-neutral-900/5 min-h-[300px] text-center">
          <HelpCircle className="h-10 w-10 text-neutral-600 mb-4" />
          <h3 className="text-sm font-bold text-neutral-300 font-sans">Awaiting Search Query</h3>
          <p className="mt-2 text-xs text-neutral-500 max-w-sm leading-relaxed font-light">
            Enter an operational policy question above. The engine will embed the query using the transformer model and search matching vector configurations.
          </p>
        </div>
      )}
    </div>
  );
}
