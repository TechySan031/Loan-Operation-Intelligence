'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Plus, 
  Search, 
  Trash2, 
  Edit3, 
  Eye, 
  UploadCloud, 
  ArrowLeft, 
  ArrowRight,
  BookOpen,
  X,
  Sparkles
} from 'lucide-react';
import { api, KBRecord, KBRecordCreate } from '@/lib/api';
import LoadingSpinner from '@/components/LoadingSpinner';
import EmptyState from '@/components/EmptyState';
import ErrorState from '@/components/ErrorState';
import { useToast } from '@/components/Toast';

export default function KnowledgeBase() {
  const { toast } = useToast();
  
  // Loading & error states
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data lists & pagination
  const [records, setRecords] = useState<KBRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  
  // Filters & search query
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');

  // UI Dialog/Modal visibility
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<KBRecord | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // New/Edit Record Form State
  const [formRecord, setFormRecord] = useState<KBRecordCreate>({
    record_id: '',
    title: '',
    content: '',
    category: 'policy',
    subcategory: '',
    source: 'manual',
    source_url: '',
    language: 'en',
    version: '1.0',
    metadata: {
      product_type: ['personal_loan'],
      applicable_market: 'india'
    }
  });

  // Bulk Upload state
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const res = await api.getKBRecords(
        page, 
        pageSize, 
        categoryFilter || undefined, 
        languageFilter || undefined
      );
      
      let filteredRecords = res.records || [];
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        filteredRecords = filteredRecords.filter(
          r => 
            r.title.toLowerCase().includes(query) || 
            r.content.toLowerCase().includes(query) ||
            r.record_id.toLowerCase().includes(query)
        );
      }
      
      setRecords(filteredRecords);
      setTotal(res.total || 0);
    } catch (err: any) {
      console.error(err);
      setError(err.message || 'Failed to load knowledge records');
      toast('Failed to load knowledge base records', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecords();
  }, [page, categoryFilter, languageFilter]);

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      fetchRecords();
    }
  };

  // Create new record
  const handleCreateRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formRecord.record_id || !formRecord.title || !formRecord.content) {
      toast('Please enter record ID, title, and content', 'error');
      return;
    }
    
    try {
      setLoading(true);
      await api.ingestKB([formRecord], true, true);
      toast('Knowledge record created & embedded successfully', 'success');
      setIsAddOpen(false);
      
      setFormRecord({
        record_id: '',
        title: '',
        content: '',
        category: 'policy',
        subcategory: '',
        source: 'manual',
        source_url: '',
        language: 'en',
        version: '1.0',
        metadata: {
          product_type: ['personal_loan'],
          applicable_market: 'india'
        }
      });
      
      fetchRecords();
    } catch (err: any) {
      toast(`Failed to create record: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Update existing record
  const handleUpdateRecord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedRecord) return;
    
    try {
      setLoading(true);
      const updateData = {
        title: formRecord.title,
        content: formRecord.content,
        category: formRecord.category,
        subcategory: formRecord.subcategory,
      };
      
      await api.updateKBRecord(selectedRecord.record_id, updateData);
      toast('Record updated and re-indexed', 'success');
      setIsViewOpen(false);
      setSelectedRecord(null);
      setIsEditing(false);
      fetchRecords();
    } catch (err: any) {
      toast(`Failed to update record: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  // Delete record
  const handleDeleteRecord = async (recordId: string) => {
    if (!confirm('Are you sure you want to delete this record? This will delete its Pinecone vector.')) {
      return;
    }
    
    try {
      setLoading(true);
      await api.deleteKBRecord(recordId);
      toast('Record deleted and removed from vector index', 'success');
      setIsViewOpen(false);
      setSelectedRecord(null);
      fetchRecords();
    } catch (err: any) {
      toast(`Failed to delete record: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setUploading(true);
    toast('Parsing JSON and detecting PII...', 'info');
    
    try {
      const text = await file.text();
      const recordsToIngest = JSON.parse(text);
      
      if (!Array.isArray(recordsToIngest)) {
        throw new Error('JSON format must be a list of records');
      }
      
      const res = await api.ingestKB(recordsToIngest, true, true);
      toast(`Successfully bulk ingested ${res.ingested} records (${res.vectors_upserted} vector chunks)`, 'success');
      fetchRecords();
    } catch (err: any) {
      toast(`Failed to bulk ingest: ${err.message}`, 'error');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const getCategoryBadge = (cat: string) => {
    const colors: Record<string, string> = {
      product: 'bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 border-indigo-500/15',
      policy: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/15',
      faq: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/15',
      objection: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/15',
      compliance: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/15',
      payment: 'bg-pink-500/10 text-pink-600 dark:text-pink-400 border-pink-500/15',
      escalation: 'bg-rose-500/10 text-rose-600 dark:text-rose-455 border-rose-500/15',
    };
    return colors[cat] || 'bg-neutral-100 dark:bg-neutral-900 text-neutral-500 dark:text-neutral-400 border-[var(--card-border)]';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-[var(--navbar-border)] pb-5">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-neutral-900 via-neutral-800 to-neutral-600 dark:from-white dark:via-neutral-200 dark:to-neutral-500 bg-clip-text text-transparent">
            Knowledge Repository
          </h1>
          <p className="text-xs text-neutral-555 dark:text-neutral-450 mt-1.5 leading-relaxed">
            Manage clean, compliant information templates used by voice agents to address client queries.
          </p>
        </div>
        <div className="flex gap-3 shrink-0">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".json"
            className="hidden"
          />
          <button
            onClick={handleUploadClick}
            disabled={uploading}
            className="inline-flex items-center gap-2 rounded-xl bg-neutral-900/30 border border-white/[0.03] hover:border-indigo-500/30 hover:bg-neutral-900/50 px-4 py-2.5 text-xs font-semibold text-neutral-200 transition-all duration-300"
          >
            <UploadCloud className="h-4 w-4 text-indigo-400" />
            {uploading ? 'Ingesting...' : 'Bulk Ingest JSON'}
          </button>
          
          <button
            onClick={() => {
              setIsAddOpen(true);
              setIsEditing(false);
            }}
            className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white transition-all duration-300 shadow-lg shadow-indigo-600/15 border border-indigo-400/20"
          >
            <Plus className="h-4 w-4" />
            Add Record
          </button>
        </div>
      </div>

      {/* Offline Status Warning Alert */}
      {error && (
        <div className="flex items-center justify-between p-3.5 bg-red-500/10 border border-red-500/20 text-red-400 rounded-2xl text-xs font-medium animate-pulse mb-4">
          <span>Failed to connect to PostgreSQL Knowledge Repository. Running in offline view.</span>
          <button 
            onClick={fetchRecords}
            className="px-2.5 py-1 bg-red-500/20 hover:bg-red-500/30 rounded-lg text-[10px] font-bold border border-red-550/20"
          >
            Reconnect Database
          </button>
        </div>
      )}

      {/* Filters Toolbar */}
      <div className="grid gap-3 sm:grid-cols-4 bg-[var(--card-bg)] p-3 rounded-2xl border border-[var(--card-border)] backdrop-blur-md glass-panel">
        <div className="relative sm:col-span-2">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-neutral-505" />
          <input
            type="text"
            placeholder="Search records by title, content, or record ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={handleSearchKeyPress}
            className="w-full pl-9 pr-4 py-2 text-xs bg-neutral-100 dark:bg-neutral-950/80 border border-[var(--card-border)] rounded-xl text-[var(--foreground)] focus:outline-none focus:border-indigo-500/50 placeholder-neutral-500 dark:placeholder-neutral-600 premium-input"
          />
        </div>
        <div>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-neutral-100 dark:bg-neutral-955 border border-[var(--card-border)] rounded-xl text-neutral-650 dark:text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
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
          <select
            value={languageFilter}
            onChange={(e) => setLanguageFilter(e.target.value)}
            className="w-full px-3 py-2 text-xs bg-neutral-100 dark:bg-neutral-955 border border-[var(--card-border)] rounded-xl text-neutral-650 dark:text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
          >
            <option value="">All Languages</option>
            <option value="en">English (India)</option>
            <option value="ph">Taglish (Philippines)</option>
            <option value="id">Indo-English (Indonesia)</option>
          </select>
        </div>
      </div>

      {/* Main Content Table / List */}
      {loading ? (
        <LoadingSpinner text="Searching knowledge items..." />
      ) : error ? (
        <EmptyState
          title="Repository Service Offline"
          description="We are unable to reach the knowledge base service. Ensure the PostgreSQL container and FastAPI server are running, then retry."
          icon={BookOpen}
          actionButton={
            <button
              onClick={fetchRecords}
              className="px-4 py-2 bg-indigo-650 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all"
            >
              Retry Reconnect
            </button>
          }
        />
      ) : records.length === 0 ? (
        <EmptyState
          title="No knowledge records found"
          description="Try modifying your search queries or category filters. You can also bulk upload a new loan policy JSON file."
          icon={BookOpen}
        />
      ) : (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card-bg)] overflow-hidden backdrop-blur-md shadow-2xl glass-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[var(--card-border)] bg-[var(--pill-bg)] text-neutral-550 dark:text-neutral-400 font-bold uppercase tracking-wider">
                  <th className="py-3.5 px-5">Record ID</th>
                  <th className="py-3.5 px-5">Title</th>
                  <th className="py-3.5 px-5">Category</th>
                  <th className="py-3.5 px-5">Language</th>
                  <th className="py-3.5 px-5">PII Shield</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--card-border)]">
                {records.map((record) => (
                  <tr key={record.id} className="hover:bg-[var(--pill-bg)]/50 text-[var(--foreground)] opacity-95 transition-colors border-b border-[var(--card-border)]/50">
                    <td className="py-3 px-5 font-mono text-[10px] text-neutral-500">{record.record_id}</td>
                    <td className="py-3 px-5 font-bold">{record.title}</td>
                    <td className="py-3 px-5">
                      <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-bold capitalize ${getCategoryBadge(record.category)}`}>
                        {record.category}
                      </span>
                    </td>
                    <td className="py-3 px-5 uppercase font-bold text-neutral-500 dark:text-neutral-400">{record.language}</td>
                    <td className="py-3 px-5">
                      {record.contains_pii ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-[9px] font-bold text-amber-600 dark:text-amber-400 border border-amber-500/10">
                          Redacted
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-[9px] font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-500/10">
                          Clean
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-5 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          onClick={() => {
                            setSelectedRecord(record);
                            setFormRecord({
                              record_id: record.record_id,
                              title: record.title,
                              content: record.content,
                              category: record.category,
                              subcategory: record.subcategory || '',
                              source: record.source,
                              source_url: record.source_url || '',
                              language: record.language,
                              version: record.version,
                            });
                            setIsViewOpen(true);
                            setIsEditing(false);
                          }}
                          className="p-1.5 text-neutral-400 hover:text-neutral-200 rounded-lg hover:bg-neutral-900/50 transition-colors"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedRecord(record);
                            setFormRecord({
                              record_id: record.record_id,
                              title: record.title,
                              content: record.content,
                              category: record.category,
                              subcategory: record.subcategory || '',
                              source: record.source,
                              source_url: record.source_url || '',
                              language: record.language,
                              version: record.version,
                            });
                            setIsViewOpen(true);
                            setIsEditing(true);
                          }}
                          className="p-1.5 text-neutral-400 hover:text-indigo-400 rounded-lg hover:bg-neutral-900/50 transition-colors"
                        >
                          <Edit3 className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteRecord(record.record_id)}
                          className="p-1.5 text-neutral-400 hover:text-rose-455 rounded-lg hover:bg-neutral-900/50 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {total > pageSize && (
            <div className="flex items-center justify-between border-t border-white/[0.03] p-4 bg-black/10">
              <span className="text-[11px] text-neutral-500 font-semibold">
                Showing {records.length} of {total} records
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(p - 1, 1))}
                  disabled={page === 1}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.03] bg-neutral-950 px-3 py-1.5 text-xs font-semibold text-neutral-450 hover:text-neutral-200 transition-colors disabled:opacity-30"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => (records.length === pageSize ? p + 1 : p))}
                  disabled={records.length < pageSize}
                  className="inline-flex items-center gap-1.5 rounded-lg border border-white/[0.03] bg-neutral-950 px-3 py-1.5 text-xs font-semibold text-neutral-450 hover:text-neutral-200 transition-colors disabled:opacity-30"
                >
                  Next
                  <ArrowRight className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add New Record Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-white/[0.04] bg-neutral-950/95 p-6 shadow-2xl animate-scale-in max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/[0.03] pb-3 mb-4">
              <h3 className="font-extrabold text-neutral-100 text-base flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-indigo-400" />
                Ingest New Document
              </h3>
              <button onClick={() => setIsAddOpen(false)} className="text-neutral-500 hover:text-neutral-350 transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>
            <form onSubmit={handleCreateRecord} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-neutral-550 font-bold mb-1">Record ID *</label>
                  <input
                    type="text"
                    required
                    placeholder="kb_policy_001"
                    value={formRecord.record_id}
                    onChange={(e) => setFormRecord({ ...formRecord, record_id: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-250 focus:outline-none focus:border-indigo-500/50 premium-input"
                  />
                </div>
                <div>
                  <label className="block text-neutral-555 font-bold mb-1">Topic Category</label>
                  <select
                    value={formRecord.category}
                    onChange={(e) => setFormRecord({ ...formRecord, category: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input"
                  >
                    <option value="policy">Policy</option>
                    <option value="product">Product</option>
                    <option value="faq">FAQ</option>
                    <option value="objection">Objection</option>
                    <option value="compliance">Compliance</option>
                    <option value="payment">Payment</option>
                    <option value="escalation">Escalation</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-neutral-500 font-bold mb-1">Document Title *</label>
                <input
                  type="text"
                  required
                  placeholder="Personal Loan Prepayment Guidelines"
                  value={formRecord.title}
                  onChange={(e) => setFormRecord({ ...formRecord, title: e.target.value })}
                  className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-250 focus:outline-none focus:border-indigo-500/50 premium-input"
                />
              </div>

              <div>
                <label className="block text-neutral-500 font-bold mb-1">Document Content *</label>
                <textarea
                  required
                  rows={5}
                  placeholder="Enter the complete text content here..."
                  value={formRecord.content}
                  onChange={(e) => setFormRecord({ ...formRecord, content: e.target.value })}
                  className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-250 focus:outline-none focus:border-indigo-500/50 premium-input leading-relaxed font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-neutral-500 font-bold mb-1">Language</label>
                  <select
                    value={formRecord.language}
                    onChange={(e) => setFormRecord({ ...formRecord, language: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
                  >
                    <option value="en">English (India)</option>
                    <option value="ph">Taglish (Philippines)</option>
                    <option value="id">Indo-English (Indonesia)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-neutral-500 font-bold mb-1">Source Medium</label>
                  <select
                    value={formRecord.source}
                    onChange={(e) => setFormRecord({ ...formRecord, source: e.target.value })}
                    className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input font-semibold"
                  >
                    <option value="manual">Manual Ingest</option>
                    <option value="website">Website Crawl</option>
                    <option value="pdf">PDF Upload</option>
                    <option value="csv">CSV Import</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 border-t border-white/[0.03] pt-4 mt-5">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="rounded-xl border border-white/[0.03] bg-neutral-950 px-4 py-2 font-semibold text-neutral-450 hover:text-neutral-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2 font-semibold text-white transition-all shadow-lg border border-indigo-400/25"
                >
                  Ingest & Index
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View/Edit Modal */}
      {isViewOpen && selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
          <div className="w-full max-w-lg rounded-2xl border border-white/[0.04] bg-neutral-950/95 p-6 shadow-2xl animate-scale-in max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-white/[0.03] pb-3 mb-4">
              <h3 className="font-extrabold text-neutral-100 text-base">
                {isEditing ? 'Edit Knowledge Record' : 'Knowledge Item Details'}
              </h3>
              <button onClick={() => setIsViewOpen(false)} className="text-neutral-500 hover:text-neutral-350 transition-colors">
                <X className="h-5 w-5" />
              </button>
            </div>
            
            <form onSubmit={isEditing ? handleUpdateRecord : undefined} className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-neutral-500 block mb-1">
                  Unique Identifier
                </span>
                <span className="font-mono text-neutral-300 text-xs bg-neutral-900 px-2.5 py-1.5 rounded-xl border border-white/[0.03] inline-block font-semibold">
                  {selectedRecord.record_id}
                </span>
              </div>

              {isEditing ? (
                <>
                  <div>
                    <label className="block text-neutral-500 font-bold mb-1">Title</label>
                    <input
                      type="text"
                      required
                      value={formRecord.title}
                      onChange={(e) => setFormRecord({ ...formRecord, title: e.target.value })}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-250 focus:outline-none focus:border-indigo-500/50 premium-input"
                    />
                  </div>
                  <div>
                    <label className="block text-neutral-500 font-bold mb-1">Content</label>
                    <textarea
                      required
                      rows={6}
                      value={formRecord.content}
                      onChange={(e) => setFormRecord({ ...formRecord, content: e.target.value })}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-250 focus:outline-none focus:border-indigo-500/50 premium-input leading-relaxed font-sans"
                    />
                  </div>
                  <div>
                    <label className="block text-neutral-500 font-bold mb-1">Topic Category</label>
                    <select
                      value={formRecord.category}
                      onChange={(e) => setFormRecord({ ...formRecord, category: e.target.value })}
                      className="w-full px-3 py-2 bg-neutral-900 border border-white/[0.03] rounded-xl text-neutral-400 focus:outline-none focus:border-indigo-500/50 premium-input"
                    >
                      <option value="policy">Policy</option>
                      <option value="product">Product</option>
                      <option value="faq">FAQ</option>
                      <option value="objection">Objection</option>
                      <option value="compliance">Compliance</option>
                      <option value="payment">Payment</option>
                      <option value="escalation">Escalation</option>
                    </select>
                  </div>
                </>
              ) : (
                <>
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider text-neutral-500 block mb-1">
                      Title
                    </span>
                    <p className="text-sm font-bold text-neutral-200">{selectedRecord.title}</p>
                  </div>
                  
                  <div>
                    <span className="text-[10px] uppercase font-bold tracking-wider text-neutral-500 block mb-1">
                      Original Content {selectedRecord.contains_pii && '(Compliance Shield Active)'}
                    </span>
                    <div className="bg-neutral-900/40 p-4 rounded-xl border border-white/[0.03] leading-relaxed text-neutral-350 font-sans max-h-[250px] overflow-y-auto whitespace-pre-wrap font-light">
                      {selectedRecord.contains_pii ? selectedRecord.content_clean : selectedRecord.content}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 bg-neutral-900/10 p-3 rounded-xl border border-white/[0.03] backdrop-blur-md">
                    <div>
                      <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Category</span>
                      <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[9px] font-bold capitalize ${getCategoryBadge(selectedRecord.category)}`}>
                        {selectedRecord.category}
                      </span>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Language</span>
                      <span className="text-xs font-bold text-neutral-300 uppercase">{selectedRecord.language}</span>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Index Source</span>
                      <span className="text-xs font-bold text-neutral-400 capitalize">{selectedRecord.source}</span>
                    </div>
                    <div>
                      <span className="text-[9px] uppercase font-bold text-neutral-500 block mb-0.5">Indexed Date</span>
                      <span className="text-xs text-neutral-400 font-semibold">{new Date(selectedRecord.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </>
              )}

              <div className="flex justify-between items-center border-t border-white/[0.03] pt-4 mt-6">
                <div>
                  {!isEditing && (
                    <button
                      type="button"
                      onClick={() => handleDeleteRecord(selectedRecord.record_id)}
                      className="inline-flex items-center gap-1.5 text-xs text-rose-500 hover:text-rose-455 font-bold transition-colors"
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      if (isEditing) {
                        setIsEditing(false);
                      } else {
                        setIsViewOpen(false);
                      }
                    }}
                    className="rounded-xl border border-white/[0.03] bg-neutral-950 px-4 py-2 font-semibold text-neutral-450 hover:text-neutral-200 transition-colors"
                  >
                    Close
                  </button>
                  {isEditing ? (
                    <button
                      type="submit"
                      className="rounded-xl bg-indigo-600 hover:bg-indigo-500 px-4 py-2 font-semibold text-white transition-all shadow-lg border border-indigo-400/25"
                    >
                      Save Changes
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setIsEditing(true)}
                      className="inline-flex items-center gap-1.5 rounded-xl bg-neutral-900 border border-white/[0.03] hover:border-indigo-500/20 px-4 py-2 font-bold text-neutral-250 transition-all"
                    >
                      <Edit3 className="h-4 w-4 text-indigo-400" />
                      Edit Record
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
