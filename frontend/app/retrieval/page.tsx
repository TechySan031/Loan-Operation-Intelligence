'use client';

import React, { useState } from 'react';
import { 
  Play, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  TrendingUp, 
  RefreshCw,
  Eye,
  X,
  Sliders,
  FileCheck
} from 'lucide-react';
import { api } from '@/lib/api';
import MetricCard from '@/components/MetricCard';
import LoadingSpinner from '@/components/LoadingSpinner';
import ErrorState from '@/components/ErrorState';
import { useToast } from '@/components/Toast';

interface TestResultItem {
  test_id: string;
  query: string;
  description: string;
  expected_category: string;
  expected_keywords: string[];
  matched_keywords: string[];
  match_ratio: number;
  verdict: 'correct' | 'partially_correct' | 'incorrect' | 'error';
  top_result: {
    record_id: string | null;
    title: string | null;
    relevance_score: number | null;
    source: string | null;
    content_preview: string | null;
  } | null;
  total_results: number;
  retrieval_time_ms: number;
}

interface TestSummary {
  total_tests: number;
  verdicts: {
    correct: number;
    partially_correct: number;
    incorrect: number;
    error: number;
  };
  accuracy: number;
  partial_or_better: number;
  avg_retrieval_time_ms: number;
}

export default function RetrievalTest() {
  const { toast } = useToast();
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Response results
  const [summary, setSummary] = useState<TestSummary | null>(null);
  const [results, setResults] = useState<TestResultItem[]>([]);

  // Detailed Modal state
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<TestResultItem | null>(null);

  const runEvaluationTest = async () => {
    try {
      setRunning(true);
      setError(null);
      toast('Running retrieval evaluation suite...', 'info');

      // Trigger eval run
      const res = await api.runEval('rag_retrieval');
      
      if (res.results?.rag_retrieval) {
        const data = res.results.rag_retrieval;
        setSummary(data.summary);
        setResults(data.results || []);
        toast(`Evaluation finished. Accuracy: ${Math.round(data.summary.accuracy * 100)}%`, 'success');
      } else {
        throw new Error('Invalid response structure from evaluation runner');
      }
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to complete evaluation test.');
      toast('Evaluation run failed', 'error');
    } finally {
      setRunning(false);
    }
  };

  const getVerdictBadge = (verdict: string) => {
    switch (verdict) {
      case 'correct':
        return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'partially_correct':
        return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'error':
      case 'incorrect':
      default:
        return 'bg-rose-500/10 text-rose-600 dark:text-rose-455 border-rose-500/20';
    }
  };

  const getVerdictIcon = (verdict: string) => {
    switch (verdict) {
      case 'correct':
        return CheckCircle2;
      case 'partially_correct':
        return AlertTriangle;
      case 'error':
      case 'incorrect':
      default:
        return XCircle;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[var(--navbar-border)] pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent flex items-center gap-2">
            Retrieval Evaluation Hub
          </h1>
          <p className="text-xs text-neutral-550 dark:text-neutral-455 mt-1.5 leading-relaxed">
            Validate search quality against 7 standard golden query test sets. Computes precision and query matching accuracy.
          </p>
        </div>
        <div>
          <button
            onClick={runEvaluationTest}
            disabled={running}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white transition-all shadow-lg shadow-indigo-600/15 disabled:opacity-50 border border-indigo-400/20 cursor-pointer"
          >
            {running ? (
              <RefreshCw className="h-4 w-4 animate-spin text-white" />
            ) : (
              <Play className="h-4 w-4 text-white" />
            )}
            {running ? 'Running Pipeline...' : 'Run Retrieval Test'}
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center justify-between p-3.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl text-xs font-medium animate-pulse mb-4">
          <span>Evaluation pipeline is offline or database is degraded. Please start PostgreSQL and uvicorn.</span>
          <button 
            onClick={runEvaluationTest}
            className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-[10px] font-bold border border-red-550/20 animate-fade-in"
          >
            Retry Run
          </button>
        </div>
      )}

      {/* Loading Overlay */}
      {running && (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-8 text-center backdrop-blur-md glass-panel">
          <LoadingSpinner text="Triggering neural embedding query models, checking expected matches, scoring precision ratios..." />
        </div>
      )}

      {/* Summary Cards */}
      {summary && !running && (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          <MetricCard
            title="Test Cases Verdict"
            value={`${summary.verdicts.correct} / ${summary.total_tests} Passed`}
            icon={TrendingUp}
            change={`Accuracy: ${Math.round(summary.accuracy * 100)}%`}
          />
          <MetricCard
            title="Partial or Better Accuracy"
            value={`${Math.round(summary.partial_or_better * 100)}%`}
            icon={FileCheck}
            change="Target >= 90%"
            changeType={summary.partial_or_better >= 0.9 ? 'positive' : 'negative'}
          />
          <MetricCard
            title="Avg Retrieval Speed"
            value={`${summary.avg_retrieval_time_ms.toFixed(1)}ms`}
            icon={Clock}
            change="Target < 200ms"
            changeType={summary.avg_retrieval_time_ms < 200 ? 'positive' : 'negative'}
          />
          <MetricCard
            title="Total Test Cases Checked"
            value={summary.total_tests}
            icon={Sliders}
            change="7 scenarios total"
          />
        </div>
      )}

      {/* Progress bar indication of verdicts breakdown */}
      {summary && !running && (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 backdrop-blur-md shadow-xl glass-panel">
          <div className="flex justify-between text-xs text-neutral-500 dark:text-neutral-400 mb-2 font-bold uppercase tracking-wider">
            <span>Verdict Breakdown Progress</span>
            <span>{Math.round(summary.accuracy * 100)}% Success</span>
          </div>
          <div className="flex h-2.5 overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-900 border border-[var(--card-border)]">
            <div 
              style={{ width: `${(summary.verdicts.correct / summary.total_tests) * 100}%` }}
              className="bg-emerald-500 transition-all duration-500" 
              title="Correct"
            />
            <div 
              style={{ width: `${(summary.verdicts.partially_correct / summary.total_tests) * 100}%` }}
              className="bg-amber-500 transition-all duration-500" 
              title="Partially Correct"
            />
            <div 
              style={{ width: `${((summary.verdicts.incorrect + summary.verdicts.error) / summary.total_tests) * 100}%` }}
              className="bg-rose-500 transition-all duration-500" 
              title="Incorrect/Error"
            />
          </div>
        </div>
      )}

      {/* Main Results Table */}
      {results.length > 0 && !running && (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] overflow-hidden backdrop-blur-md shadow-2xl glass-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[var(--card-border)] bg-[var(--pill-bg)] text-neutral-550 dark:text-neutral-400 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Test ID</th>
                  <th className="py-3 px-4">Query Scenario</th>
                  <th className="py-3 px-4">Expected Category</th>
                  <th className="py-3 px-4">Retrieved ID</th>
                  <th className="py-3 px-4">Verdict</th>
                  <th className="py-3 px-4">Speed</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--card-border)]">
                {results.map((result) => {
                  const VerdictIcon = getVerdictIcon(result.verdict);
                  return (
                    <tr key={result.test_id} className="hover:bg-[var(--pill-bg)]/50 text-[var(--foreground)] opacity-95 transition-colors border-b border-[var(--card-border)]/50">
                      <td className="py-3.5 px-4 font-mono text-[10px] text-neutral-500">{result.test_id}</td>
                      <td className="py-3.5 px-4 font-bold truncate max-w-sm" title={result.query}>
                        {result.query}
                      </td>
                      <td className="py-3.5 px-4 capitalize font-semibold text-neutral-550 dark:text-neutral-400">{result.expected_category}</td>
                      <td className="py-3.5 px-4 font-mono text-[10px]">
                        {result.top_result?.record_id || 'none'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold capitalize ${getVerdictBadge(result.verdict)}`}>
                          <VerdictIcon className="h-2.5 w-2.5" />
                          {result.verdict.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-neutral-500 font-semibold">
                        {result.retrieval_time_ms.toFixed(1)}ms
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={() => {
                            setSelectedItem(result);
                            setIsDetailOpen(true);
                          }}
                          className="p-1.5 text-neutral-400 hover:text-neutral-200 rounded-lg hover:bg-neutral-900/50 transition-colors"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Initial Awaiting state */}
      {results.length === 0 && !running && (
        <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-dashed border-white/[0.03] bg-neutral-900/5 min-h-[300px] text-center">
          <FileCheck className="h-10 w-10 text-neutral-600 mb-4" />
          <h3 className="text-sm font-bold text-neutral-300">Awaiting Evaluation Test Run</h3>
          <p className="mt-2 text-xs text-neutral-500 max-w-sm leading-relaxed font-light">
            Click the &quot;Run Retrieval Test&quot; button to query all golden test cases, parse compliance metrics, and review system precision.
          </p>
        </div>
      )}

      {/* Details Dialog */}
      {isDetailOpen && selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-white/[0.04] bg-neutral-950/95 p-6 shadow-2xl animate-scale-in max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/[0.03] pb-3 mb-4">
              <h3 className="font-bold text-neutral-100 text-base">Test Case Telemetry Details</h3>
              <button onClick={() => setIsDetailOpen(false)} className="text-neutral-500 hover:text-neutral-350 transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500 block mb-0.5">Test Case ID</span>
                <p className="font-mono text-neutral-450 font-bold">{selectedItem.test_id}</p>
              </div>

              <div>
                <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500 block mb-0.5">Tested Query</span>
                <p className="text-neutral-200 font-extrabold leading-relaxed text-sm">{selectedItem.query}</p>
              </div>

              <div className="grid grid-cols-2 gap-4 bg-neutral-900/10 p-3 rounded-xl border border-white/[0.03] backdrop-blur-md">
                <div>
                  <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Expected Category</span>
                  <span className="text-neutral-300 font-bold capitalize">{selectedItem.expected_category}</span>
                </div>
                <div>
                  <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Verdict Status</span>
                  <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[9px] font-bold capitalize ${getVerdictBadge(selectedItem.verdict)}`}>
                    {selectedItem.verdict.replace('_', ' ')}
                  </span>
                </div>
              </div>

              <div>
                <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500 block mb-1">Expected Keywords Match</span>
                <div className="flex flex-wrap gap-1.5">
                  {selectedItem.expected_keywords.map((kw, i) => {
                    const isMatched = selectedItem.matched_keywords.includes(kw);
                    return (
                      <span
                        key={i}
                        className={`px-2 py-0.5 rounded-lg text-[10px] font-semibold border ${
                          isMatched
                            ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/15'
                            : 'bg-rose-500/10 text-rose-455 border-rose-500/15 line-through opacity-70'
                        }`}
                      >
                        {kw}
                      </span>
                    );
                  })}
                </div>
              </div>

              {selectedItem.top_result && (
                <div className="border-t border-white/[0.03] pt-3.5 space-y-2">
                  <span className="text-[9px] uppercase font-bold tracking-wider text-neutral-500 block">Top Retrieved Document</span>
                  <div className="p-3.5 bg-neutral-900/40 rounded-xl border border-white/[0.03] backdrop-blur-md">
                    <p className="font-bold text-neutral-200 text-xs">{selectedItem.top_result.title}</p>
                    <span className="text-[9px] font-mono text-neutral-500 mt-1 block">ID: {selectedItem.top_result.record_id} | Score: {selectedItem.top_result.relevance_score?.toFixed(4)}</span>
                    <p className="text-[11px] text-neutral-400 mt-2.5 leading-relaxed font-sans font-light">{selectedItem.top_result.content_preview}...</p>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end border-t border-white/[0.03] pt-4 mt-6">
              <button
                type="button"
                onClick={() => setIsDetailOpen(false)}
                className="rounded-xl border border-white/[0.03] bg-neutral-955 px-4 py-2 font-semibold text-neutral-450 hover:text-neutral-200 transition-colors"
              >
                Close Details
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
