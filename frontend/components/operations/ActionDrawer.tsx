'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, UserCheck, CreditCard, Calendar, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';
import { api, BorrowerLookupResponse } from '@/lib/api';
import { useToast } from '@/components/Toast';

interface ActionDrawerProps {
  isOpen: boolean;
  type: 'eligibility' | 'payment' | 'callback' | 'escalation' | null;
  borrower: BorrowerLookupResponse | null;
  onClose: () => void;
  onActivityLogged: (activity: {
    id: string;
    type: 'borrower_loaded' | 'eligibility_checked' | 'payment_recorded' | 'callback_scheduled' | 'escalated' | 'voice_started' | 'knowledge_retrieved';
    title: string;
    desc: string;
    timestamp: string;
  }) => void;
}

export default function ActionDrawer({ isOpen, type, borrower, onClose, onActivityLogged }: ActionDrawerProps) {
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);

  // Eligibility Check Form State
  const [selectedProgram, setSelectedProgram] = useState('');
  
  // Payment Commitment Form State
  const [commitmentDate, setCommitmentDate] = useState('');
  const [commitmentAmount, setCommitmentAmount] = useState('');
  const [paymentMethod, setPaymentMethod] = useState('UPI');

  // Callback Scheduler Form State
  const [callbackDate, setCallbackDate] = useState('');
  const [callbackTime, setCallbackTime] = useState('');
  const [callbackReason, setCallbackReason] = useState('Follow-up on payment');

  // Human Escalation Form State
  const [escalationReason, setEscalationReason] = useState('');
  const [escalationPriority, setEscalationPriority] = useState('normal');

  // Form errors
  const [errors, setErrors] = useState<Record<string, string>>({});

  // Reset fields when active action changes
  useEffect(() => {
    setErrors({});
    if (borrower) {
      setCommitmentAmount(borrower.amount_due?.toString() || '');
    }
    // Clean fields
    setSelectedProgram('');
    setCommitmentDate('');
    setCallbackDate('');
    setCallbackTime('');
    setCallbackReason('Follow-up on payment');
    setEscalationReason('');
    setEscalationPriority('normal');
  }, [type, borrower]);

  if (!isOpen || !type || !borrower) return null;

  const logActivity = (
    activityType: Parameters<ActionDrawerProps['onActivityLogged']>[0]['type'],
    title: string,
    desc: string
  ) => {
    onActivityLogged({
      id: Math.random().toString(36).substring(2, 9),
      type: activityType,
      title,
      desc,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    });
  };

  // Submit handlers
  const handleCheckEligibility = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProgram) {
      setErrors({ program: 'Please select a program type' });
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const res = await api.checkEligibility({
        loan_id: borrower.loan_id || '',
        program_type: selectedProgram,
      });

      logActivity(
        'eligibility_checked',
        'Eligibility Check Executed',
        `${borrower.borrower_name} evaluated for ${selectedProgram.replace('_', ' ')}: ${res.eligible ? 'Eligible' : 'Not Eligible'}`
      );

      if (res.eligible) {
        toast(`Eligible for ${selectedProgram.replace('_', ' ')} program!`, 'success');
      } else {
        toast(`Eligibility result: ${res.message}`, 'error');
      }
      onClose();
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'Eligibility check request failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handlePaymentCommitment = async (e: React.FormEvent) => {
    e.preventDefault();
    const formErrors: Record<string, string> = {};
    if (!commitmentDate) formErrors.date = 'Commitment date is required';
    if (!commitmentAmount || parseFloat(commitmentAmount) <= 0) formErrors.amount = 'Valid amount is required';
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const amt = parseFloat(commitmentAmount);
      const res = await api.paymentCommitment({
        commitment_date: commitmentDate,
        amount: amt,
        payment_method: paymentMethod,
      });

      logActivity(
        'payment_recorded',
        'Payment Commitment Recorded',
        `Committed to pay ${borrower.market === 'india' ? '₹' : borrower.market === 'philippines' ? '₱' : 'Rp'}${amt.toLocaleString()} on ${commitmentDate} via ${paymentMethod}`
      );

      toast(res.message || 'Payment commitment stored successfully!', 'success');
      onClose();
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'Payment commitment logging failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleCallback = async (e: React.FormEvent) => {
    e.preventDefault();
    const formErrors: Record<string, string> = {};
    if (!callbackDate) formErrors.date = 'Callback date is required';
    if (!callbackTime) formErrors.time = 'Callback time is required';
    
    if (Object.keys(formErrors).length > 0) {
      setErrors(formErrors);
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const res = await api.scheduleCallback({
        date: callbackDate,
        time: callbackTime,
        reason: callbackReason,
      });

      logActivity(
        'callback_scheduled',
        'Call Callback Scheduled',
        `Scheduled for ${callbackDate} at ${callbackTime}. Reason: ${callbackReason}`
      );

      toast(res.message || 'Callback registered successfully!', 'success');
      onClose();
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'Callback scheduling failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleEscalate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!escalationReason.trim() || escalationReason.trim().length < 5) {
      setErrors({ reason: 'Escalation reasoning is required (min 5 chars)' });
      return;
    }
    setErrors({});
    setLoading(true);

    try {
      const res = await api.escalate({
        reason: escalationReason,
        priority: escalationPriority,
      });

      logActivity(
        'escalated',
        'Human Supervisor Escalated',
        `Escalated call with priority "${escalationPriority}". Context: ${escalationReason}`
      );

      toast(res.message || 'Escalated to active supervisor queue', 'success');
      onClose();
    } catch (err: any) {
      console.error(err);
      toast(err.message || 'Escalation trigger failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const drawerTitles = {
    eligibility: { label: 'Hardship Eligibility', icon: UserCheck, color: 'text-indigo-400' },
    payment: { label: 'Payment Commitment', icon: CreditCard, color: 'text-emerald-400' },
    callback: { label: 'Callback Scheduler', icon: Calendar, color: 'text-amber-400' },
    escalation: { label: 'Supervisor Escalation', icon: ShieldAlert, color: 'text-rose-455' },
  };

  const currentType = drawerTitles[type];
  const TitleIcon = currentType.icon;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
        {/* Backdrop overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.5 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        />

        {/* Slide-out Panel */}
        <motion.div
          initial={{ translateX: '100%' }}
          animate={{ translateX: 0 }}
          exit={{ translateX: '100%' }}
          transition={{ type: 'spring', damping: 25, stiffness: 220 }}
          className="relative w-full max-w-md h-full bg-neutral-950 border-l border-white/[0.03] shadow-2xl p-6 flex flex-col justify-between"
        >
          <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/[0.03] pb-4">
              <div className="flex items-center gap-2.5">
                <TitleIcon className={`h-5 w-5 ${currentType.color}`} />
                <h3 className="font-extrabold text-sm text-neutral-100 tracking-tight">
                  {currentType.label}
                </h3>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg bg-white/[0.02] border border-white/[0.03] text-neutral-450 hover:text-neutral-200 transition-all cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Borrower Mini-Tag Context */}
            <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.01] border border-white/[0.02] text-xs">
              <div>
                <span className="block text-[8px] uppercase tracking-wider font-extrabold text-neutral-500">Active context</span>
                <span className="font-bold text-neutral-300">{borrower.borrower_name}</span>
              </div>
              <span className="font-mono text-[9px] bg-neutral-950 px-2 py-0.5 rounded border border-white/[0.03] text-neutral-400">
                {borrower.loan_id}
              </span>
            </div>

            {/* Forms Switch */}
            {type === 'eligibility' && (
              <form onSubmit={handleCheckEligibility} className="space-y-4">
                <div>
                  <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                    hardship relief program
                  </label>
                  <select
                    value={selectedProgram}
                    onChange={(e) => setSelectedProgram(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2.5 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-indigo-500 premium-input font-bold"
                  >
                    <option value="">-- Select Relief Program --</option>
                    <option value="emi_holiday">EMI Deferral Holiday</option>
                    <option value="extension">15-day Payment Extension</option>
                    <option value="restructuring">Tenure Deferral Restructuring</option>
                    <option value="grace_period">3-day Penalty Grace Period</option>
                  </select>
                  {errors.program && (
                    <span className="text-[10px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {errors.program}
                    </span>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {loading ? 'Evaluating details...' : 'Evaluate Eligibility'}
                </button>
              </form>
            )}

            {type === 'payment' && (
              <form onSubmit={handlePaymentCommitment} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                      commitment date
                    </label>
                    <input
                      type="date"
                      value={commitmentDate}
                      onChange={(e) => setCommitmentDate(e.target.value)}
                      disabled={loading}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-emerald-500 premium-input font-bold"
                    />
                    {errors.date && (
                      <span className="text-[9px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        {errors.date}
                      </span>
                    )}
                  </div>
                  <div>
                    <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                      committed amount
                    </label>
                    <input
                      type="number"
                      value={commitmentAmount}
                      onChange={(e) => setCommitmentAmount(e.target.value)}
                      disabled={loading}
                      placeholder="EMI amount"
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-emerald-500 premium-input font-bold font-mono"
                    />
                    {errors.amount && (
                      <span className="text-[9px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        {errors.amount}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                    intended payment channel
                  </label>
                  <select
                    value={paymentMethod}
                    onChange={(e) => setPaymentMethod(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2.5 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-emerald-500 premium-input font-bold"
                  >
                    <option value="UPI">UPI Transfer</option>
                    <option value="Net Banking">Net Banking</option>
                    <option value="Debit Card">Debit Card</option>
                    <option value="Credit Card">Credit Card</option>
                    <option value="Bank Transfer">Bank Wire Transfer</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {loading ? 'Recording Commitment...' : 'Record Payment Commitment'}
                </button>
              </form>
            )}

            {type === 'callback' && (
              <form onSubmit={handleScheduleCallback} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                      callback date
                    </label>
                    <input
                      type="date"
                      value={callbackDate}
                      onChange={(e) => setCallbackDate(e.target.value)}
                      disabled={loading}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-amber-500 premium-input font-bold"
                    />
                    {errors.date && (
                      <span className="text-[9px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        {errors.date}
                      </span>
                    )}
                  </div>
                  <div>
                    <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                      callback time
                    </label>
                    <input
                      type="time"
                      value={callbackTime}
                      onChange={(e) => setCallbackTime(e.target.value)}
                      disabled={loading}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-amber-500 premium-input font-bold"
                    />
                    {errors.time && (
                      <span className="text-[9px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        {errors.time}
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                    callback notes / agenda
                  </label>
                  <input
                    type="text"
                    value={callbackReason}
                    onChange={(e) => setCallbackReason(e.target.value)}
                    disabled={loading}
                    placeholder="Agenda notes..."
                    className="w-full px-3 py-2.5 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-amber-500 premium-input font-semibold"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {loading ? 'Scheduling...' : 'Schedule Outbound Callback'}
                </button>
              </form>
            )}

            {type === 'escalation' && (
              <form onSubmit={handleEscalate} className="space-y-4">
                <div>
                  <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                    escalation priority
                  </label>
                  <select
                    value={escalationPriority}
                    onChange={(e) => setEscalationPriority(e.target.value)}
                    disabled={loading}
                    className="w-full px-3 py-2.5 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-rose-500 premium-input font-bold"
                  >
                    <option value="low">Low Priority</option>
                    <option value="normal">Normal / Standard Priority</option>
                    <option value="high">High priority</option>
                    <option value="critical">Critical / Hotline Transfer</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[9px] uppercase font-extrabold text-neutral-500 mb-1.5">
                    escalation details / agent notes
                  </label>
                  <textarea
                    value={escalationReason}
                    onChange={(e) => setEscalationReason(e.target.value)}
                    disabled={loading}
                    rows={4}
                    placeholder="Provide supervisor context (disputes, hardship evidence, etc.)"
                    className="w-full px-3 py-2.5 bg-neutral-900 border border-white/[0.03] rounded-xl text-xs text-[var(--foreground)] focus:outline-none focus:border-rose-500 premium-input font-semibold"
                  />
                  {errors.reason && (
                    <span className="text-[10px] text-red-400 font-semibold mt-1 block flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0" />
                      {errors.reason}
                    </span>
                  )}
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold rounded-xl transition-all shadow-md flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {loading ? 'Escalating file...' : 'Trigger Supervisor Escalation'}
                </button>
              </form>
            )}
          </div>

          {/* Footer warning info */}
          <div className="border-t border-white/[0.03] pt-4 text-[10px] text-neutral-500 font-medium">
            Submitting this action will write audit updates to the loan ledger and triggers outbound queues.
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
