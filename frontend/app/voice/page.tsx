'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import { 
  Phone, 
  PhoneOff, 
  Database, 
  MessageSquareCode,
  ShieldAlert,
  Radio,
  Volume2
} from 'lucide-react';
import { api } from '@/lib/api';
import { useToast } from '@/components/Toast';

interface DialogTurn {
  speaker: 'agent' | 'borrower';
  text: string;
  timeOffset: number;
  ragResult?: {
    title: string;
    content: string;
    score: number;
    recordId: string;
    source: string;
  };
  nudge?: {
    type: string;
    nudge_text: string;
    priority: 'high' | 'medium' | 'low';
  };
}

export default function VoiceAgent() {
  const { toast } = useToast();
  
  // Call configuration
  const [selectedLoanId, setSelectedLoanId] = useState('LN001');
  const [callStatus, setCallStatus] = useState<'idle' | 'dialing' | 'active' | 'completed'>('idle');
  const [callId, setCallId] = useState<string | null>(null);
  
  // Live conversation details
  const [transcript, setTranscript] = useState<{ speaker: string; text: string }[]>([]);
  const [retrievedContext, setRetrievedContext] = useState<NonNullable<DialogTurn['ragResult']>[]>([]);
  const [liveNudges, setLiveNudges] = useState<{
    id: string;
    type: string;
    nudge_text: string;
    priority: 'high' | 'medium' | 'low';
    timestamp: string;
  }[]>([]);
  
  const [sentiment, setSentiment] = useState<'neutral' | 'positive' | 'negative'>('neutral');
  const [timeElapsed, setTimeElapsed] = useState(0);
  const timeElapsedRef = useRef(0);

  // Available mock borrowers for dial list
  const borrowers = [
    { name: 'Rajesh Kumar', loanId: 'LN001', market: 'India', amount: '₹15,000' },
    { name: 'Priya Sharma', loanId: 'LN002', market: 'India', amount: '₹45,000' },
    { name: 'Amit Patel', loanId: 'LN003', market: 'India', amount: '₹22,000' },
  ];

  // Pre-configured simulated dialog turns for LN001 Rajesh Kumar
  const simulatedConversation: DialogTurn[] = useMemo(() => [
    {
      speaker: 'agent',
      text: "Hello, am I speaking with Rajesh Kumar? This is Rajesh calling from LOI Finance regarding your personal loan account.",
      timeOffset: 2,
      nudge: {
        type: 'compliance_gap',
        nudge_text: "Ensure mandatory identity verification and call recording disclosure are stated immediately.",
        priority: 'high'
      }
    },
    {
      speaker: 'borrower',
      text: "Yes, this is Rajesh. What is this about?",
      timeOffset: 6
    },
    {
      speaker: 'agent',
      text: "Thank you for confirming, Rajesh. I am calling to remind you that your EMI of ₹15,000 is due on February 15th, which is in 5 days. This call is recorded for quality purposes.",
      timeOffset: 10
    },
    {
      speaker: 'borrower',
      text: "Ah, yes. I received the SMS. But this month is difficult. My salary is delayed. What happens if I make the payment late?",
      timeOffset: 15
    },
    {
      speaker: 'agent',
      text: "I understand that can be stressful. If the EMI is overdue past the grace period, a late payment fee is charged.",
      timeOffset: 22,
      ragResult: {
        title: "Late Payment Penalty Policy",
        content: "A late payment fee of 2% of the overdue EMI amount or ₹500 (whichever is higher) is charged. The penalty is applied after a 3-day grace period from the due date.",
        score: 0.89,
        recordId: "kb_policy_late_payment_001",
        source: "loan_agreement_v2"
      },
      nudge: {
        type: 'objection_handling',
        nudge_text: "Borrower expresses financial difficulty. Empathize and state grace period details (3 days). Do not mention collections.",
        priority: 'medium'
      }
    },
    {
      speaker: 'borrower',
      text: "Is there any way I can extend the payment date or request restructuring?",
      timeOffset: 30
    },
    {
      speaker: 'agent',
      text: "Yes, we have options. For temporary difficulties, we offer restructuring or a payment extension of up to 15 days without penalty.",
      timeOffset: 36,
      ragResult: {
        title: "Hardship & Restructuring Programs",
        content: "Eligible borrowers may request a Tenure Extension of up to 24 months, or a Payment Extension of up to 15 days without late fees. Supporting document submission is required.",
        score: 0.94,
        recordId: "kb_payment_restructuring_001",
        source: "operations_manual_2025"
      },
      nudge: {
        type: 'program_offer',
        nudge_text: "Borrower is eligible for Restructuring and Payment Extension. Propose documentation submission process.",
        priority: 'high'
      }
    },
    {
      speaker: 'borrower',
      text: "Great. I will submit the request on the portal. Thank you.",
      timeOffset: 44
    },
    {
      speaker: 'agent',
      text: "You're welcome, Rajesh. I have recorded your commitment to pay. Have a great day.",
      timeOffset: 50
    }
  ], []);

  // Run simulated loop
  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (callStatus === 'active') {
      timer = setInterval(() => {
        timeElapsedRef.current += 1;
        const nextTime = timeElapsedRef.current;
        setTimeElapsed(nextTime);
        
        const turn = simulatedConversation.find(t => t.timeOffset === nextTime);
        if (turn) {
          setTranscript(t => [...t, { speaker: turn.speaker, text: turn.text }]);
          
          if (turn.ragResult) {
            setRetrievedContext(c => [turn.ragResult!, ...c]);
            toast(`Grounded KB context retrieved (Score: ${Math.round(turn.ragResult.score * 100)}%)`, 'info');
          }

          if (turn.nudge) {
            setLiveNudges(n => [{
              ...turn.nudge!,
              id: Math.random().toString(36).substring(2, 7),
              timestamp: new Date().toLocaleTimeString()
            }, ...n]);
            toast(`New AI Agent Nudge generated: ${turn.nudge.type.replace('_', ' ')}`, 'success');
          }
        }

        const maxTime = Math.max(...simulatedConversation.map(t => t.timeOffset));
        if (nextTime >= maxTime + 4) {
          setCallStatus('completed');
          toast('Voice call completed. Summary generated.', 'success');
          clearInterval(timer);
        }
      }, 1000);
    }

    return () => {
      if (timer) clearInterval(timer);
    };
  }, [callStatus, simulatedConversation, toast]);

  const handleStartCall = async () => {
    try {
      setCallStatus('dialing');
      setTranscript([]);
      setRetrievedContext([]);
      setLiveNudges([]);
      setTimeElapsed(0);
      timeElapsedRef.current = 0;
      setSentiment('neutral');
      
      const newCallId = 'vapi_call_' + Math.random().toString(36).substring(2, 9);
      setCallId(newCallId);

      await api.startNudgeSession(newCallId, 'live');

      setTimeout(() => {
        setCallStatus('active');
        setSentiment('positive');
        toast('Call connected with outbound borrower Rajesh Kumar', 'success');
      }, 1500);

    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      toast(`Failed to dial outbound: ${errorMsg}`, 'error');
      setCallStatus('idle');
    }
  };

  const handleHangUp = async () => {
    if (callId) {
      await api.stopNudgeSession(callId);
    }
    setCallStatus('completed');
    toast('Call terminated by supervisor', 'info');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header section */}
      <div className="border-b border-[var(--navbar-border)] pb-5">
        <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent">
          Voice Agent Simulation Center
        </h1>
        <p className="text-xs text-neutral-550 dark:text-neutral-455 mt-1.5 leading-relaxed">
          Monitor active outbound agent calls, compliance logs, live transcripts, and agent real-time decision support nudges.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Side: Call controls */}
        <div className="space-y-6 lg:col-span-1">
          {/* Dialer Panel */}
          <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 backdrop-blur-md relative overflow-hidden shadow-2xl glow-card-indigo glass-panel">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
              <Volume2 className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400" />
              Dialer Control Panel
            </h3>

            {/* Borrower Selection */}
            <div className="space-y-4">
              <div>
                <label className="block text-[9px] uppercase font-bold text-neutral-500 mb-1">
                  Select Borrower Profile
                </label>
                <select
                  disabled={callStatus !== 'idle' && callStatus !== 'completed'}
                  value={selectedLoanId}
                  onChange={(e) => setSelectedLoanId(e.target.value)}
                  className="w-full px-3 py-2 text-xs bg-neutral-100 dark:bg-neutral-950 border border-[var(--card-border)] rounded-xl text-neutral-600 dark:text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
                >
                  {borrowers.map((b) => (
                    <option key={b.loanId} value={b.loanId}>
                      {b.name} ({b.loanId}) — {b.amount} Due
                    </option>
                  ))}
                </select>
                        {/* Call status display */}
              <div className="rounded-xl border border-[var(--card-border)] bg-[var(--pill-bg)] dark:bg-neutral-950/80 p-4 flex flex-col items-center justify-center min-h-[160px] backdrop-blur-md">
                {callStatus === 'idle' && (
                  <div className="text-center text-xs text-neutral-500">
                    <Phone className="h-8 w-8 mx-auto mb-2 text-neutral-400 dark:text-neutral-700" />
                    System Idle
                  </div>
                )}
                {callStatus === 'dialing' && (
                  <div className="text-center text-xs text-neutral-550 dark:text-neutral-450">
                    <Radio className="h-8 w-8 mx-auto mb-2 text-indigo-500 dark:text-indigo-400 animate-pulse" />
                    Dialing...
                  </div>
                )}
                {callStatus === 'active' && (
                  <div className="text-center text-xs text-neutral-600 dark:text-neutral-300 w-full space-y-2">
                    <div className="relative inline-block">
                      <span className="relative flex h-3.5 w-3.5 mx-auto">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-450 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-emerald-500"></span>
                      </span>
                    </div>
                    <p className="font-bold text-neutral-800 dark:text-neutral-200 text-sm">Live Call Connected</p>
                    <p className="font-mono text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Duration: {timeElapsed}s</p>
                    <div className="mt-2.5 inline-flex items-center gap-1.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 border border-emerald-500/10 text-[9px] font-bold">
                      Sentiment: {sentiment.toUpperCase()}
                    </div>
                  </div>
                )}
                {callStatus === 'completed' && (
                  <div className="text-center text-xs text-neutral-550 dark:text-neutral-450">
                    <PhoneOff className="h-8 w-8 mx-auto mb-2 text-neutral-400 dark:text-neutral-700" />
                    Call Completed
                  </div>
                )}
              </div>      </div>

              {/* Trigger Button */}
              {callStatus === 'idle' || callStatus === 'completed' ? (
                <button
                  onClick={handleStartCall}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 py-3 text-xs font-semibold text-white transition-all shadow-lg shadow-indigo-600/15 border border-indigo-400/20 cursor-pointer"
                >
                  <Phone className="h-4 w-4 text-white" />
                  Initiate Outbound Call
                </button>
              ) : (
                <button
                  onClick={handleHangUp}
                  className="w-full flex items-center justify-center gap-2 rounded-xl bg-rose-600 hover:bg-rose-500 py-3 text-xs font-semibold text-white transition-all shadow-lg shadow-rose-600/15 border border-rose-455/20 cursor-pointer"
                >
                  <PhoneOff className="h-4 w-4 text-white" />
                  Disconnect Call
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right Side: Telemetry dashboard */}
        <div className="space-y-6 lg:col-span-2">
          <div className="grid gap-6 md:grid-cols-2">
             {/* Live Transcript Stream */}
            <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 backdrop-blur-md flex flex-col h-[400px] shadow-2xl glass-panel">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2 border-b border-[var(--card-border)]/50 pb-2">
                <MessageSquareCode className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400" />
                Live Conversation Log
              </h3>
              
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 text-xs leading-relaxed font-sans">
                {transcript.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-center text-neutral-600 font-light">
                    No active call transcript.
                  </div>
                ) : (
                  transcript.map((t, idx) => (
                    <div
                      key={idx}
                      className={`flex flex-col max-w-[85%] rounded-2xl p-3.5 border ${
                        t.speaker === 'agent'
                          ? 'bg-indigo-505/10 dark:bg-indigo-600/10 border border-indigo-500/20 text-neutral-800 dark:text-neutral-250 self-start'
                          : 'bg-neutral-200/50 dark:bg-neutral-900/40 border border-[var(--card-border)] text-neutral-800 dark:text-neutral-200 self-end ml-auto'
                      }`}
                    >
                      <span className="text-[9px] uppercase font-bold text-neutral-550 dark:text-neutral-500 mb-1">
                        {t.speaker === 'agent' ? 'AI Voice Agent' : 'Borrower (ASR)'}
                      </span>
                      <p className="font-sans font-medium dark:font-light leading-relaxed">{t.text}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Retrieved grounding knowledge RAG */}
            <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-5 backdrop-blur-md flex flex-col h-[400px] shadow-2xl glass-panel">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2 border-b border-[var(--card-border)]/50 pb-2">
                <Database className="h-4.5 w-4.5 text-indigo-500 dark:text-indigo-400" />
                Real-Time Grounding Context
              </h3>

              <div className="flex-1 overflow-y-auto space-y-3.5 pr-1 text-[11px] leading-relaxed">
                {retrievedContext.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-center text-neutral-500 dark:text-neutral-600 font-light">
                    Awaiting retrieval triggers...
                  </div>
                ) : (
                  retrievedContext.map((c, idx) => (
                    <div key={idx} className="rounded-xl border border-[var(--card-border)] bg-neutral-100 dark:bg-neutral-950/60 p-4 space-y-2 animate-scale-in">
                      <div className="flex items-center justify-between border-b border-[var(--card-border)]/30 pb-1.5">
                        <span className="font-bold text-neutral-800 dark:text-neutral-200">{c.title}</span>
                        <span className="rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 px-2 py-0.5 text-[9px] font-bold border border-emerald-500/10">
                          {Math.round(c.score * 100)}% Match
                        </span>
                      </div>
                      <p className="text-neutral-600 dark:text-neutral-400 text-xs font-sans font-light leading-relaxed">{c.content}</p>
                      <div className="flex justify-between text-[8px] font-bold text-neutral-500 dark:text-neutral-455 pt-1.5 uppercase tracking-wider">
                        <span>Citation: {c.recordId}</span>
                        <span>Doc: {c.source}</span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>      </div>

          {/* SSE real-time nudges */}
          <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] p-6 backdrop-blur-md shadow-2xl glass-panel">
            <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-4 flex items-center gap-2">
              <ShieldAlert className="h-4.5 w-4.5 text-indigo-550 dark:text-indigo-400" />
              Real-Time Supervisor Nudge Stream
            </h3>

            <div className="space-y-3.5 max-h-[250px] overflow-y-auto pr-1">
              {liveNudges.length === 0 ? (
                <div className="text-center py-6 text-neutral-500 dark:text-neutral-600 text-xs">
                  Awaiting nudges from compliance models...
                </div>
              ) : (
                liveNudges.map((n) => (
                  <div 
                    key={n.id} 
                    className={`rounded-xl border p-4 flex gap-3 text-xs leading-relaxed animate-slide-in ${
                      n.priority === 'high' 
                        ? 'bg-rose-500/5 dark:bg-rose-500/5 border-rose-500/15 text-rose-700 dark:text-rose-350 shadow-[0_0_15px_rgba(239,68,68,0.02)]' 
                        : 'bg-indigo-500/5 dark:bg-indigo-500/5 border-indigo-500/10 text-indigo-700 dark:text-indigo-350 shadow-[0_0_15px_rgba(99,102,241,0.02)]'
                    }`}
                  >
                    <div className="shrink-0 mt-0.5">
                      <span className={`inline-flex h-2.5 w-2.5 rounded-full ${
                        n.priority === 'high' ? 'bg-rose-500 animate-pulse' : 'bg-indigo-500'
                      }`} />
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between font-bold border-b border-[var(--card-border)]/50 pb-1 mb-1">
                        <span className="uppercase text-[9px] tracking-wider">{n.type.replace('_', ' ')}</span>
                        <span className="text-[8px] text-neutral-500 dark:text-neutral-450 font-semibold">{n.timestamp}</span>
                      </div>
                      <p className="text-neutral-700 dark:text-neutral-300 font-sans font-light">{n.nudge_text}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
