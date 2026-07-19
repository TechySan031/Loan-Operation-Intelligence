'use client';

import React, { useState } from 'react';
import { Search, Sparkles, Copy, Check, FileText, AlertCircle } from 'lucide-react';
import { api, ToolSearchResponse } from '@/lib/api';
import { useToast } from '@/components/Toast';

interface KnowledgePanelProps {
  onLogActivity?: (activity: {
    id: string;
    type: 'knowledge_retrieved';
    title: string;
    desc: string;
    timestamp: string;
  }) => void;
}

export default function KnowledgePanel({ onLogActivity }: KnowledgePanelProps) {
  const { toast } = useToast();
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ToolSearchResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await api.searchTools({
        query: query.trim(),
        category: category || null,
      });

      // Parse JSON response safely if needed
      let parsedResult: ToolSearchResponse;
      try {
        if (typeof res === 'string') {
          parsedResult = JSON.parse(res);
        } else if ((res as any).result) {
          parsedResult = JSON.parse((res as any).result);
        } else {
          parsedResult = res as unknown as ToolSearchResponse;
        }
      } catch (pErr) {
        parsedResult = res as unknown as ToolSearchResponse;
      }

      setResult(parsedResult);

      if (onLogActivity) {
        onLogActivity({
          id: Math.random().toString(36).substring(2, 9),
          type: 'knowledge_retrieved',
          title: 'Knowledge Base Queried',
          desc: `Searched RAG database for: "${query.trim().substring(0, 40)}${query.trim().length > 40 ? '...' : ''}" (Confidence: ${Math.round((parsedResult.confidence ?? 0) * 100)}%)`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        });
      }

      if (parsedResult.found) {
        toast('Grounding content loaded successfully', 'success');
      } else {
        toast('No matching articles found in index', 'info');
      }
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'RAG Search query failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result?.answer) return;
    navigator.clipboard.writeText(result.answer);
    setCopied(true);
    toast('Answer copied to clipboard', 'success');
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-4">
      <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
        grounded RAG search
      </h2>

      <div className="rounded-2xl border border-white/[0.03] bg-neutral-900/10 backdrop-blur-xl p-5 shadow-2xl space-y-4">
        {/* ChatGPT Style input bar */}
        <form onSubmit={handleSearch} className="space-y-3">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask RAG (e.g., 'What is the late EMI penalty?')"
              disabled={loading}
              className="w-full pl-3.5 pr-28 py-3.5 bg-neutral-950 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-indigo-500 placeholder-neutral-600 premium-input font-medium shadow-inner"
            />
            <div className="absolute right-2.5 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={loading}
                className="px-2.5 py-1.5 bg-neutral-900 border border-white/[0.03] rounded-lg text-[9px] font-bold text-neutral-450 uppercase focus:outline-none focus:border-indigo-500"
              >
                <option value="">ALL</option>
                <option value="policy">POLICY</option>
                <option value="product">PRODUCT</option>
                <option value="faq">FAQ</option>
                <option value="objection">OBJECTION</option>
              </select>
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="p-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-lg transition-all cursor-pointer"
              >
                <Search className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </form>

        {/* ChatGPT Style Thread Response Area */}
        <div className="min-h-[140px] flex flex-col justify-center">
          {loading ? (
            /* Shimmer Skeleton */
            <div className="space-y-3.5 animate-pulse w-full">
              <div className="h-2 w-1/3 bg-neutral-800 rounded" />
              <div className="space-y-2">
                <div className="h-2.5 w-full bg-neutral-900 rounded" />
                <div className="h-2.5 w-full bg-neutral-900 rounded" />
                <div className="h-2.5 w-4/5 bg-neutral-900 rounded" />
              </div>
              <div className="h-2 w-1/4 bg-neutral-800 rounded pt-1" />
            </div>
          ) : result ? (
            <div className="space-y-4 animate-fade-in text-xs">
              {/* Score header */}
              <div className="flex items-center justify-between border-b border-white/[0.02] pb-3">
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider ${
                    result.found
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/15'
                      : 'bg-rose-500/10 text-rose-400 border-rose-500/15'
                  }`}>
                    {result.found ? 'Grounded Match' : 'No Grounding'}
                  </span>
                  {result.found && (
                    <span className="text-[10px] text-neutral-500 font-mono font-bold">
                      relevance: {Math.round(result.confidence * 100)}%
                    </span>
                  )}
                </div>
                
                {result.found && (
                  <button
                    onClick={handleCopy}
                    className="flex items-center gap-1 px-2.5 py-1 bg-white/[0.02] hover:bg-white/[0.06] border border-white/[0.03] text-neutral-450 hover:text-neutral-200 rounded-lg text-[10px] font-bold transition-all cursor-pointer"
                  >
                    {copied ? <Check className="h-3 w-3 text-emerald-450" /> : <Copy className="h-3 w-3" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                )}
              </div>

              {/* Response Answer */}
              <div className="bg-neutral-950/45 p-3.5 rounded-xl border border-white/[0.02] leading-relaxed text-neutral-300 font-medium">
                {result.answer}
              </div>

              {/* Citations */}
              {result.found && result.sources && result.sources.length > 0 && (
                <div className="space-y-2">
                  <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500 flex items-center gap-1.5">
                    <FileText className="h-3 w-3 text-neutral-600" />
                    grounded sources & citations
                  </span>
                  <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-3">
                    {result.sources.map((src, i) => (
                      <div
                        key={i}
                        className="flex flex-col justify-between p-2.5 rounded-xl bg-white/[0.01] border border-white/[0.03] hover:bg-white/[0.02] transition-colors"
                      >
                        <span className="font-extrabold text-[9px] text-indigo-400 font-mono">
                          {src.record_id}
                        </span>
                        <span className="text-[10px] font-medium text-neutral-450 truncate mt-1">
                          {src.title}
                        </span>
                        <span className="text-[8px] font-bold uppercase tracking-wider text-neutral-500 mt-2 text-right">
                          {src.source}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-neutral-500 text-xs font-medium flex flex-col items-center gap-2">
              <Sparkles className="h-6 w-6 text-neutral-600 animate-pulse" />
              <span>Ask a query above to run neural semantic search check on policies.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
