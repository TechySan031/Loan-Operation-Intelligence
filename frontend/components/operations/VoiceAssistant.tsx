'use client';

import React, { useEffect, useState, useRef } from 'react';
import { Phone, PhoneCall, PhoneOff, AlertCircle, MessageSquare, Wrench } from 'lucide-react';
import { BorrowerLookupResponse } from '@/lib/api';
import { useToast } from '@/components/Toast';

interface VoiceAssistantProps {
  borrower: BorrowerLookupResponse | null;
  onLogActivity?: (activity: {
    id: string;
    type: 'voice_started';
    title: string;
    desc: string;
    timestamp: string;
  }) => void;
}

// Map borrower markets to env variables and human-friendly names
const getAssistantConfig = (market: string) => {
  const normMarket = (market || '').toLowerCase().trim();
  if (normMarket === 'india') {
    return {
      id: (process.env.NEXT_PUBLIC_VAPI_INDIA_ASSISTANT || '').trim(),
      name: 'India Assistant (Hindi/English)',
    };
  } else if (normMarket === 'philippines') {
    return {
      id: (process.env.NEXT_PUBLIC_VAPI_PH_ASSISTANT || '').trim(),
      name: 'Philippines Assistant (Taglish/English)',
    };
  } else if (normMarket === 'indonesia') {
    return {
      id: (process.env.NEXT_PUBLIC_VAPI_ID_ASSISTANT || '').trim(),
      name: 'Indonesia Assistant (Bahasa/English)',
    };
  }
  return {
    id: '',
    name: 'Not Configured',
  };
};

export default function VoiceAssistant({ borrower, onLogActivity }: VoiceAssistantProps) {
  const { toast } = useToast();
  
  // Vapi Client Instance
  const vapiRef = useRef<any>(null);
  
  // Read Public Key directly from env variables (trimmed to handle leading spaces in configuration)
  const publicKey = (process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY || '').trim();

  // Connection & Calling states
  const [isVapiLoaded, setIsVapiLoaded] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'ready' | 'error' | 'not_configured'>('not_configured');
  const [callStatus, setCallStatus] = useState<'idle' | 'connecting' | 'active' | 'ended'>('idle');
  const [transcript, setTranscript] = useState<{ speaker: 'agent' | 'user'; text: string }[]>([]);
  const [toolCalls, setToolCalls] = useState<{
    id: string;
    name: string;
    params: any;
    status: 'pending' | 'completed' | 'failed';
    response?: any;
  }[]>([]);

  // Determine configuration based on current borrower context
  const market = borrower?.market || '';
  const { id: assistantId, name: assistantName } = getAssistantConfig(market);

  // Lazy-load and initialize Vapi SDK client-side
  useEffect(() => {
    const initVapi = async () => {
      try {
        if (!publicKey) {
          setConnectionStatus('not_configured');
          return;
        }
        
        const VapiModule = (await import('@vapi-ai/web')).default;
        vapiRef.current = new VapiModule(publicKey);
        setIsVapiLoaded(true);
        setConnectionStatus('ready');
      } catch (err) {
        console.error('Failed to load Vapi Web SDK:', err);
        setConnectionStatus('error');
      }
    };

    initVapi();

    return () => {
      if (vapiRef.current) {
        vapiRef.current.stop();
      }
    };
  }, [publicKey]);

  // Global unhandled promise rejection catcher for WebRTC/Daily-co ejections
  useEffect(() => {
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const errorMsg = reason?.message || String(reason || '');
      
      if (
        errorMsg.includes('ejection') || 
        errorMsg.includes('Daily') || 
        errorMsg.includes('meeting') ||
        errorMsg.includes('Meeting')
      ) {
        // Prevent default browser console noise/crash overlay
        event.preventDefault();
        console.warn('[WebRTC Ejection Caught]:', errorMsg);
        toast('Voice Session Ended: WebRTC meeting room has closed or credentials are inactive.', 'error');
        setCallStatus('idle');
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, [toast]);

  // Subscribe to Vapi WebRTC connection events
  useEffect(() => {
    if (!vapiRef.current) return;

    const vapi = vapiRef.current;

    const handleCallStart = () => {
      setCallStatus('active');
      toast('Live Vapi Outbound Connection Started', 'success');
      if (onLogActivity && borrower) {
        onLogActivity({
          id: Math.random().toString(36).substring(2, 9),
          type: 'voice_started',
          title: 'Vapi Call Initiated',
          desc: `Voice session started with borrower: ${borrower.borrower_name} (${borrower.loan_id})`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        });
      }
    };

    const handleCallEnd = () => {
      setCallStatus('ended');
      toast('Call completed successfully', 'info');
      setTimeout(() => setCallStatus('idle'), 3000);
    };

    const handleMessage = (msg: any) => {
      // Handle speech transcription updates
      if (msg.type === 'transcript' && msg.transcriptType === 'final') {
        setTranscript((prev) => [
          ...prev,
          {
            speaker: msg.role === 'assistant' ? 'agent' : 'user',
            text: msg.transcript,
          },
        ]);
      }
      
      // Handle active tool calls execution tracking
      else if (msg.type === 'tool-calls' || msg.type === 'function-call') {
        const calls = msg.toolCalls || [msg.functionCall];
        const newCalls = calls.map((c: any) => ({
          id: c.id || Math.random().toString(36).substring(2, 7),
          name: c.name || c.function?.name || 'unknown_tool',
          params: c.parameters || JSON.parse(c.function?.arguments || '{}'),
          status: 'pending' as const,
        }));
        setToolCalls((prev) => [...newCalls, ...prev]);
        toast(`Vapi Assistant executing tool: ${newCalls[0].name}`, 'info');
      }

      // Handle active tool execution results returning
      else if (msg.type === 'tool-call-result' || msg.type === 'function-call-result') {
        const result = msg.toolCallResult || msg.functionCallResult;
        setToolCalls((prev) =>
          prev.map((tc) =>
            tc.name === result.name
              ? { ...tc, status: 'completed', response: result.result }
              : tc
          )
        );
      }
    };

    const handleError = (error: any) => {
      console.error('Vapi call session error:', error);
      toast(`Vapi Error: ${error.message || String(error)}`, 'error');
      setCallStatus('idle');
    };

    vapi.on('call-start', handleCallStart);
    vapi.on('call-end', handleCallEnd);
    vapi.on('message', handleMessage);
    vapi.on('error', handleError);

    return () => {
      vapi.off('call-start', handleCallStart);
      vapi.off('call-end', handleCallEnd);
      vapi.off('message', handleMessage);
      vapi.off('error', handleError);
    };
  }, [isVapiLoaded, borrower]);

  const handleStartCall = () => {
    if (!vapiRef.current) {
      toast('Vapi SDK is not initialized. Please verify environment settings.', 'error');
      return;
    }
    if (!assistantId) {
      toast('No assistant ID is configured for this market.', 'error');
      return;
    }

    setCallStatus('connecting');
    setTranscript([]);
    setToolCalls([]);
    
    // Start microphone stream call session
    vapiRef.current.start(assistantId).catch((err: any) => {
      console.error(err);
      toast(`Failed to dial: ${err.message || String(err)}`, 'error');
      setCallStatus('idle');
    });
  };

  const handleStopCall = () => {
    if (vapiRef.current) {
      vapiRef.current.stop();
    }
  };

  // Compile warning states
  let warningMessage = '';
  if (!publicKey) {
    warningMessage = 'Voice Assistant is not configured.';
  } else if (!borrower) {
    warningMessage = 'Please select a borrower before launching the voice assistant.';
  } else if (!assistantId) {
    warningMessage = 'No assistant configured for this market.';
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold uppercase tracking-wider text-neutral-500">
          outbound voice assistant
        </h2>
      </div>

      <div className="rounded-2xl border border-white/[0.03] bg-neutral-900/10 backdrop-blur-xl p-5 shadow-2xl space-y-4">
        
        {/* Professional Status Panel Grid */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-[10px] border-b border-white/[0.03] pb-4 font-semibold text-neutral-400">
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Voice Provider</span>
            <span className="text-neutral-250 font-mono">Vapi</span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Model</span>
            <span className="text-neutral-250 font-mono">GPT-4.1</span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Speech Recognition</span>
            <span className="text-neutral-250 font-mono">Soniox RT</span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Voice</span>
            <span className="text-neutral-250 font-mono">Configured Voice</span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5 col-span-2">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Assistant</span>
            <span className="text-indigo-400 font-mono text-[9px] truncate max-w-[220px]" title={assistantName}>
              {assistantName}
            </span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Market</span>
            <span className="text-neutral-200 capitalize">{market || 'None Selected'}</span>
          </div>
          <div className="flex justify-between border-b border-white/[0.01] pb-1.5">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Status</span>
            <span className="text-emerald-400 font-bold flex items-center gap-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Ready
            </span>
          </div>
          <div className="flex justify-between col-span-2 pt-1">
            <span className="text-neutral-500 font-bold uppercase tracking-wider text-[8px]">Connection Status</span>
            <span className={`font-mono text-[9px] ${
              connectionStatus === 'ready' ? 'text-emerald-400 font-bold' : 'text-rose-450 font-bold'
            }`}>
              {connectionStatus === 'ready' ? 'Connected' : 'Not Configured'}
            </span>
          </div>
        </div>

        {/* Warning Banner Or Dial Card Widget */}
        {warningMessage ? (
          <div className="flex flex-col items-center justify-center p-5 bg-neutral-950/40 border border-amber-500/10 rounded-xl text-center min-h-[155px]">
            <AlertCircle className="h-7 w-7 text-amber-500/90 mb-2.5 animate-pulse" />
            <p className="text-[11px] font-bold text-neutral-300 px-2">{warningMessage}</p>
            {!publicKey && (
              <p className="text-[9px] text-neutral-500 mt-1.5 max-w-[230px]">
                Please add <code className="text-neutral-400 font-mono bg-neutral-900 px-1 py-0.5 rounded">NEXT_PUBLIC_VAPI_PUBLIC_KEY</code> to the frontend environment to initialize the Web SDK.
              </p>
            )}
            <div className="mt-4 w-full">
              <button
                disabled
                className="w-full py-2 bg-neutral-800 disabled:opacity-40 text-neutral-500 text-xs font-extrabold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-not-allowed"
              >
                <Phone className="h-3.5 w-3.5" />
                Launch Voice Assistant
              </button>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center p-5 bg-neutral-950/45 border border-white/[0.02] rounded-xl text-center">
            <div className="relative mb-3">
              <div className={`h-11 w-11 rounded-full flex items-center justify-center border transition-all duration-300 ${
                callStatus === 'active'
                  ? 'bg-emerald-500/10 border-emerald-500 text-emerald-450 animate-pulse'
                  : callStatus === 'connecting'
                  ? 'bg-amber-500/10 border-amber-500 text-amber-450 animate-bounce'
                  : 'bg-neutral-900 border-white/[0.03] text-neutral-500'
              }`}>
                <PhoneCall className="h-4.5 w-4.5" />
              </div>
              {callStatus === 'active' && (
                <span className="absolute top-0 right-0 block h-2.5 w-2.5 rounded-full bg-emerald-500 ring-2 ring-neutral-950 animate-ping" />
              )}
            </div>

            <h3 className="font-extrabold text-xs text-neutral-200 uppercase tracking-wider">
              {callStatus === 'idle' && 'Assistant Ready'}
              {callStatus === 'connecting' && 'Connecting WebRTC...'}
              {callStatus === 'active' && 'Active Vapi Session'}
              {callStatus === 'ended' && 'Call Concluded'}
            </h3>
            <p className="text-[10px] text-neutral-550 mt-1 font-medium">
              {callStatus === 'idle' && 'Microphone ready for client calling'}
              {callStatus === 'connecting' && 'Opening media sockets'}
              {callStatus === 'active' && 'AI Bot connected to browser mic'}
              {callStatus === 'ended' && 'Compiling logs and metrics'}
            </p>

            <div className="mt-4 w-full">
              {callStatus === 'idle' || callStatus === 'ended' ? (
                <button
                  onClick={handleStartCall}
                  className="w-full py-2 bg-emerald-650 hover:bg-emerald-600 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <Phone className="h-3.5 w-3.5" />
                  Launch Voice Assistant
                </button>
              ) : (
                <button
                  onClick={handleStopCall}
                  className="w-full py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  <PhoneOff className="h-3.5 w-3.5" />
                  Hang Up Session
                </button>
              )}
            </div>
          </div>
        )}

        {/* Live Conversation Transcript Display */}
        {callStatus === 'active' && transcript.length > 0 && (
          <div className="border border-white/[0.03] bg-neutral-950/60 p-3 rounded-xl max-h-[140px] overflow-y-auto space-y-2 text-[10px] leading-relaxed font-semibold animate-fade-in scrollbar-thin">
            <span className="block text-[8px] uppercase tracking-wider font-extrabold text-indigo-400 flex items-center gap-1">
              <MessageSquare className="h-3 w-3" />
              Live Conversation Transcript
            </span>
            {transcript.map((t, idx) => (
              <p key={idx} className={t.speaker === 'agent' ? 'text-indigo-400' : 'text-neutral-300'}>
                <span className="capitalize font-bold">{t.speaker}: </span>
                {t.text}
              </p>
            ))}
          </div>
        )}

        {/* Incoming Tool Execution Audits */}
        {toolCalls.length > 0 && (
          <div className="space-y-2 border-t border-white/[0.03] pt-3.5">
            <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500 flex items-center gap-1.5">
              <Wrench className="h-3 w-3 text-neutral-600" />
              vapi function integrations triggered
            </span>
            <div className="space-y-1.5 max-h-[150px] overflow-y-auto pr-0.5">
              {toolCalls.map((tc) => (
                <div
                  key={tc.id}
                  className="p-2.5 rounded-lg bg-neutral-950 border border-white/[0.02] text-[10px] space-y-1 animate-fade-in"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-extrabold text-indigo-400 font-mono">{tc.name}</span>
                    <span className={`text-[8px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                      tc.status === 'completed'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/10'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/10'
                    }`}>
                      {tc.status}
                    </span>
                  </div>
                  <div className="text-neutral-550 font-medium">
                    <span className="font-semibold text-neutral-500">Params: </span>
                    <span className="font-mono text-[9px] text-neutral-400">{JSON.stringify(tc.params)}</span>
                  </div>
                  {tc.response && (
                    <div className="text-neutral-550 border-t border-white/[0.01] pt-1 mt-1 font-medium">
                      <span className="font-semibold text-neutral-500">Output: </span>
                      <span className="font-mono text-[9px] text-neutral-450">{JSON.stringify(tc.response)}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

