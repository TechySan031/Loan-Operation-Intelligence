'use client';

import React, { useEffect, useState } from 'react';
import { ShieldCheck, ShieldAlert, RefreshCw, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

interface ConnectionStatusProps {
  onStatusChange?: (connected: boolean) => void;
}

export default function ConnectionStatus({ onStatusChange }: ConnectionStatusProps) {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [dbStatus, setDbStatus] = useState<{ postgres: string; redis: string; pinecone: string } | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);

  const checkConnection = async () => {
    try {
      const res = await api.getReadiness();
      setStatus(res.status === 'ready' || res.status === 'degraded' ? 'connected' : 'disconnected');
      setDbStatus(res.checks);
      if (onStatusChange) {
        onStatusChange(true);
      }
    } catch (err) {
      console.warn('Backend connection check failed:', err);
      setStatus('disconnected');
      setDbStatus(null);
      if (onStatusChange) {
        onStatusChange(false);
      }
    }
  };

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleRetry = async () => {
    setIsRetrying(true);
    await checkConnection();
    setTimeout(() => setIsRetrying(false), 500);
  };

  return (
    <div className="space-y-4">
      {/* Top Banner Alert when Disconnected */}
      {status === 'disconnected' && (
        <div className="flex items-center justify-between gap-3 p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-xl text-xs font-medium animate-pulse">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>FastAPI Server is offline. The dashboard is running in simulated resilience mode.</span>
          </div>
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-200 border border-red-500/30 rounded-lg transition-all text-[11px] font-bold cursor-pointer disabled:opacity-50"
          >
            <RefreshCw className={`h-3 w-3 ${isRetrying ? 'animate-spin' : ''}`} />
            Reconnect
          </button>
        </div>
      )}

      {/* Main Connection Status Bar widget */}
      <div className="flex items-center justify-between p-3.5 bg-neutral-900/40 border border-white/[0.03] rounded-xl backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="relative flex h-2.5 w-2.5">
            {status === 'connected' && (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-450 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-500"></span>
              </>
            )}
            {status === 'checking' && (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-450 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
              </>
            )}
            {status === 'disconnected' && (
              <>
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-450 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500"></span>
              </>
            )}
          </div>
          <div className="text-xs">
            <p className="font-bold text-neutral-200">
              {status === 'connected' && 'API Endpoint Live'}
              {status === 'checking' && 'Verifying API Endpoint...'}
              {status === 'disconnected' && 'Platform Offline'}
            </p>
            <p className="text-[10px] text-neutral-500">
              {status === 'connected' && 'Connected to http://localhost:8000'}
              {status === 'checking' && 'Connecting to API port...'}
              {status === 'disconnected' && 'CORS / Server link failure'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-[10px] font-mono font-bold text-neutral-450">
          {status === 'connected' && dbStatus && (
            <div className="hidden sm:flex gap-3">
              <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
                dbStatus.postgres === 'ok' ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : 'bg-red-500/5 border-red-500/10 text-red-400'
              }`}>
                POSTGRES: {dbStatus.postgres === 'ok' ? 'OK' : 'FAIL'}
              </span>
              <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
                dbStatus.redis === 'ok' ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : 'bg-red-500/5 border-red-500/10 text-red-400'
              }`}>
                REDIS: {dbStatus.redis === 'ok' ? 'OK' : 'FAIL'}
              </span>
              <span className={`flex items-center gap-1.5 px-2 py-0.5 rounded border ${
                dbStatus.pinecone.includes('ok') ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' : 'bg-red-500/5 border-red-500/10 text-red-400'
              }`}>
                PINECONE: {dbStatus.pinecone.includes('ok') ? 'OK' : 'FAIL'}
              </span>
            </div>
          )}
          <button
            onClick={handleRetry}
            disabled={isRetrying}
            className="p-1.5 bg-white/[0.02] border border-white/[0.03] hover:bg-white/[0.05] rounded-lg transition-all text-neutral-400 hover:text-neutral-200 cursor-pointer disabled:opacity-50"
            title="Refresh Connection"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRetrying ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>
    </div>
  );
}
