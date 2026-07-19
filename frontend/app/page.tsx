'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ArrowRight, 
  Layers, 
  Sparkles, 
  ShieldCheck, 
  Zap, 
  Cpu, 
  Mic, 
  LineChart, 
  Database,
  ExternalLink,
  BookOpen,
  LayoutDashboard
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen text-[var(--foreground)] bg-[var(--background)] selection:bg-indigo-500/20 transition-colors duration-300">
      
      {/* Dynamic Background Effects */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(99,102,241,0.03)_1px,transparent_1px),linear-gradient(to_bottom,rgba(99,102,241,0.03)_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)]"></div>
        <div className="absolute top-[-10%] left-[10%] w-[500px] h-[500px] rounded-full bg-indigo-500/5 blur-[80px] dark:bg-indigo-500/10"></div>
        <div className="absolute top-[20%] right-[10%] w-[400px] h-[400px] rounded-full bg-purple-500/5 blur-[80px] dark:bg-purple-500/10"></div>
      </div>

      {/* Global Header */}
      <header className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-[var(--navbar-border)] bg-[var(--navbar-bg)] px-6 backdrop-blur-md transition-all duration-300">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-tr from-indigo-500 to-purple-600 shadow-[0_0_12px_rgba(99,102,241,0.25)]">
            <Layers className="h-4 w-4 text-white" />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-xs tracking-wider text-neutral-800 dark:text-neutral-200">
              LOAN OPS
            </span>
            <span className="text-[8px] uppercase font-bold text-indigo-500 dark:text-indigo-400 tracking-widest -mt-1 flex items-center gap-0.5">
              Intelligence <Sparkles className="h-1.5 w-1.5" />
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6 text-xs font-semibold text-[var(--foreground)] opacity-80">
          <a href="#features" className="hover:text-indigo-500 transition-colors">Features</a>
          <a href="#architecture" className="hover:text-indigo-500 transition-colors">Architecture</a>
          <a href="#tech-stack" className="hover:text-indigo-500 transition-colors">Tech Stack</a>
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 hover:text-indigo-500 transition-colors">
            API Docs <ExternalLink className="h-3 w-3" />
          </a>
        </nav>

        <div className="flex items-center gap-3">
          <Link 
            href="/dashboard" 
            className="inline-flex items-center gap-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-3.5 py-1.5 text-xs font-bold text-white transition-all shadow-md hover:shadow-indigo-500/10 cursor-pointer"
          >
            Launch Dashboard
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </div>
      </header>

      {/* Main content container */}
      <main className="relative z-10 max-w-7xl mx-auto px-6 py-20 md:py-28 space-y-32">
        
        {/* Hero Section */}
        <section className="text-center max-w-3xl mx-auto space-y-6 animate-fade-in">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-100 dark:border-indigo-500/20 px-3 py-1 text-[10px] font-bold text-indigo-600 dark:text-indigo-400">
            <Sparkles className="h-3 w-3" /> Outbound AI Loan Operations System
          </div>
          
          <h1 className="text-4xl md:text-6xl font-black tracking-tight leading-[1.1] bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent">
            Automate Borrower Outreach with Grounded Intelligence
          </h1>
          
          <p className="text-sm md:text-base text-neutral-550 dark:text-neutral-450 leading-relaxed font-medium">
            An end-to-end production-grade platform pairing conversational voice bots with real-time semantic knowledge lookup, outbound compliance scoring, and live supervisor telemetry.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link 
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-6 py-3.5 text-sm font-bold text-white shadow-xl hover:shadow-indigo-500/25 transition-all duration-300 transform hover:-translate-y-0.5 cursor-pointer"
            >
              <LayoutDashboard className="h-4.5 w-4.5" />
              Launch Ops Console
            </Link>
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noopener noreferrer" 
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-[var(--pill-bg)] border border-[var(--card-border)] hover:bg-[var(--card-bg)] px-6 py-3.5 text-sm font-bold text-[var(--foreground)] opacity-90 transition-all duration-300 transform hover:-translate-y-0.5"
            >
              <ExternalLink className="h-4.5 w-4.5 text-neutral-500" />
              Interactive API Specs
            </a>
          </div>
        </section>

        {/* Highlights Bar */}
        <section className="grid grid-cols-2 md:grid-cols-4 gap-6 p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md shadow-lg glass-panel max-w-4xl mx-auto">
          <div className="text-center">
            <p className="text-2xl font-black text-indigo-500 dark:text-indigo-400">98.7%</p>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mt-1">RAG Accuracy</p>
          </div>
          <div className="text-center border-l border-[var(--card-border)]">
            <p className="text-2xl font-black text-indigo-500 dark:text-indigo-400">&lt; 850ms</p>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mt-1">ASR SLA (P95)</p>
          </div>
          <div className="text-center border-l border-[var(--card-border)] md:border-l">
            <p className="text-2xl font-black text-indigo-500 dark:text-indigo-400">Zero-PII</p>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mt-1">Ingestion Shield</p>
          </div>
          <div className="text-center border-l border-[var(--card-border)]">
            <p className="text-2xl font-black text-indigo-500 dark:text-indigo-400">Live</p>
            <p className="text-[10px] font-bold text-neutral-500 uppercase tracking-wider mt-1">Supervisor Nudges</p>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-black tracking-tight text-neutral-800 dark:text-neutral-200">
              Engineered for Production AI Operations
            </h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-450 max-w-lg mx-auto leading-relaxed">
              Every system element is constructed to address actual deployment bottlenecks—from vector index drift to multilingual dialect parsing and latency SLA bounds.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            
            {/* Card 1 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <Mic className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">Knowledge-Grounded Voice Bots</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Configure outbound calling templates mapped to dynamic vector sources. Agents fetch grounded obection handlings and policy disclosures programmatically instead of hallucinating prompts.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <ShieldCheck className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">PII Filtering & Data Hygiene</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Ingested website scraping or document parsing goes through an active regex-based data compliance boundary, scrubing customer phone numbers, tax details, and emails before indexing.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <Zap className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">Real-Time Supervisor Nudges</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Process live audio packets to track agent disclosures, objection Objections, and cross-sell triggers. Generates real-time supervisor recommendations displayed within seconds.
              </p>
            </div>

            {/* Card 4 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <Cpu className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">Localized Multilingual Bots</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Dynamic configuration supporting Taglish (Philippines) and Bahasa Indonesia with regional accents. Adapts vocabulary to code-switching and local terms like `cicilan` or `denda` smoothly.
              </p>
            </div>

            {/* Card 5 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <Database className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">Traceable Semantic Search</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Inspect vector similarity outcomes, query latency metrics, category distributions, and explicit sources side-by-side using high-fidelity local retrieval tests.
              </p>
            </div>

            {/* Card 6 */}
            <div className="p-6 rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-md hover:border-indigo-500/20 hover:-translate-y-0.5 transition-all duration-300 shadow-md glass-panel relative overflow-hidden group">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-indigo-500/10 group-hover:bg-indigo-500 transition-colors" />
              <div className="rounded-xl bg-indigo-500/5 p-3 w-fit text-indigo-500 border border-indigo-500/10 mb-4">
                <LineChart className="h-5 w-5" />
              </div>
              <h3 className="font-extrabold text-sm text-neutral-800 dark:text-neutral-200">SLA Telemetry & Latency Metrics</h3>
              <p className="text-[11px] text-neutral-550 dark:text-neutral-450 mt-2 leading-relaxed">
                Breakdown of median (P50) and maximum (P95) pipeline latencies. Tracks response thresholds for speech transcribers, rule evaluations, LLM iterations, and WebSocket deliveries.
              </p>
            </div>

          </div>
        </section>

        {/* Architecture Section */}
        <section id="architecture" className="space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-black tracking-tight text-neutral-800 dark:text-neutral-200">
              Interactive System Architecture
            </h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-450 max-w-lg mx-auto leading-relaxed">
              Demonstrates the flow of unstructured documents through the ingestion pipeline, and real-time call telemetry.
            </p>
          </div>

          <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-8 backdrop-blur-md shadow-xl glass-panel max-w-4xl mx-auto overflow-x-auto">
            <div className="min-w-[700px] flex flex-col items-center gap-10 py-4 text-xs font-semibold">
              
              {/* Row 1 */}
              <div className="flex gap-16 items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-neutral-100 dark:bg-neutral-900 border border-[var(--card-border)] rounded-xl text-neutral-700 dark:text-neutral-300 w-36 text-center shadow-md">
                    Unstructured Files
                  </div>
                  <span className="text-[9px] text-neutral-450 uppercase font-bold">Scraping / PDF / Form</span>
                </div>

                <div className="text-neutral-400">➔</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 rounded-xl w-36 text-center shadow-md font-bold font-bold">
                    Ingestion Shield
                  </div>
                  <span className="text-[9px] text-indigo-500 uppercase font-bold">PII Cleaning</span>
                </div>

                <div className="text-neutral-400">➔</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-neutral-100 dark:bg-neutral-900 border border-[var(--card-border)] rounded-xl text-neutral-700 dark:text-neutral-300 w-36 text-center shadow-md">
                    BGE Embedding
                  </div>
                  <span className="text-[9px] text-neutral-450 uppercase font-bold">384-Dim Vectorizer</span>
                </div>
              </div>

              {/* Row 2 - Down arrows */}
              <div className="flex w-full justify-around px-24 text-neutral-400 -my-4 text-base">
                <div>↓</div>
                <div>↓</div>
              </div>

              {/* Row 3 */}
              <div className="flex gap-16 items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-xl w-36 text-center shadow-md font-bold">
                    PostgreSQL Cache
                  </div>
                  <span className="text-[9px] text-emerald-500 uppercase font-bold">Meta-data relational</span>
                </div>

                <div className="text-neutral-400">⟷</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 rounded-xl w-36 text-center shadow-md font-bold">
                    Pinecone Index
                  </div>
                  <span className="text-[9px] text-indigo-500 uppercase font-bold">Neural Query Search</span>
                </div>

                <div className="text-neutral-400">⟷</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-neutral-100 dark:bg-neutral-900 border border-[var(--card-border)] rounded-xl text-neutral-700 dark:text-neutral-300 w-36 text-center shadow-md">
                    Vapi Webhook
                  </div>
                  <span className="text-[9px] text-neutral-450 uppercase font-bold">Grounded RAG Bot</span>
                </div>
              </div>

              {/* Row 4 - Down arrow */}
              <div className="text-neutral-400 -my-4 text-base">↓</div>

              {/* Row 5 */}
              <div className="flex gap-16 items-center">
                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-neutral-100 dark:bg-neutral-900 border border-[var(--card-border)] rounded-xl text-neutral-700 dark:text-neutral-300 w-36 text-center shadow-md">
                    Redis Message Bus
                  </div>
                  <span className="text-[9px] text-neutral-450 uppercase font-bold">Pub/Sub Queues</span>
                </div>

                <div className="text-neutral-400">➔</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-500 rounded-xl w-36 text-center shadow-md font-bold">
                    Telemetry Stream
                  </div>
                  <span className="text-[9px] text-indigo-500 uppercase font-bold">Server-Sent Events</span>
                </div>

                <div className="text-neutral-400">➔</div>

                <div className="flex flex-col items-center gap-1.5">
                  <div className="p-3 bg-purple-500/10 border border-purple-500/20 text-purple-500 rounded-xl w-36 text-center shadow-md font-bold">
                    Ops Console Dashboard
                  </div>
                  <span className="text-[9px] text-purple-500 uppercase font-bold">Live supervisor screen</span>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* Tech Stack Grid */}
        <section id="tech-stack" className="space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-black tracking-tight text-neutral-800 dark:text-neutral-200">
              Modern Technology Stack
            </h2>
            <p className="text-xs text-neutral-500 dark:text-neutral-450 max-w-lg mx-auto leading-relaxed">
              Built on performant and scalable frameworks to satisfy standard enterprise infrastructure standards.
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            
            {/* Tech 1 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Next.js 15</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">Frontend App</span>
            </div>

            {/* Tech 2 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">FastAPI</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">Python Backend</span>
            </div>

            {/* Tech 3 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">PostgreSQL</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">Relational DB</span>
            </div>

            {/* Tech 4 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Pinecone</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">Vector Search</span>
            </div>

            {/* Tech 5 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Redis</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">Message Bus</span>
            </div>

            {/* Tech 6 */}
            <div className="flex flex-col items-center justify-center p-4 rounded-xl border border-[var(--card-border)] bg-[var(--card-bg)] backdrop-blur-sm text-center shadow-sm glass-panel">
              <span className="text-xs font-bold text-neutral-800 dark:text-neutral-200">Langfuse</span>
              <span className="text-[9px] text-neutral-500 uppercase font-bold mt-1">MLOps Tracing</span>
            </div>

          </div>
        </section>

      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--navbar-border)] bg-[var(--navbar-bg)] py-8 px-6 text-center text-xs text-neutral-500 transition-all duration-300">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1 font-semibold">
            <span>Loan Operation Intelligence System</span>
            <span className="text-[10px] text-indigo-500 dark:text-indigo-400">v1.2</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-450 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-bold text-[10px]">All Systems Operational</span>
          </div>
          <p className="font-medium text-[10px]">© 2026 Antigravity IDE system. Built for AI Engineering Portfolio.</p>
        </div>
      </footer>

    </div>
  );
}
