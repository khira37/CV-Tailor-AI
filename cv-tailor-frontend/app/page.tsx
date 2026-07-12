'use client';

import React from 'react';
import { useCVStore } from '@/store/useCVStore';

export default function CVTailingDashboard() {
  const {
    documentId,
    jobDescription,
    tailoredBullets,
    isLoading,
    error,
    setDocumentId,
    setJobDescription,
    processCV
  } = useCVStore();

  return (
    <main className="min-h-screen bg-slate-50 text-slate-900 p-8 font-sans">
      <header className="max-w-7xl mx-auto mb-8 border-b border-slate-200 pb-4">
        <h1 className="text-3xl font-extrabold tracking-tight text-indigo-600">
          CV Tailor AI 
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Extract Google Docs context and optimize application structures via LLM.
        </p>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* LEFT COLUMN: Input Configuration Control Panel */}
        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col gap-6">
          <h2 className="text-xl font-bold border-b border-slate-100 pb-2">Configuration</h2>
          
          <div>
            <label className="block text-sm font-semibold mb-2 text-slate-700">Google Document ID</label>
            <input
              type="text"
              className="w-full p-3 rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm transition"
              placeholder="e.g., 1u87Yd...your-long-doc-id"
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
            />
          </div>

          <div className="flex-1 flex flex-col">
            <label className="block text-sm font-semibold mb-2 text-slate-700">Target Job Description</label>
            <textarea
              className="w-full flex-1 min-h-[300px] p-3 rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm transition resize-none"
              placeholder="Paste the raw text block gathered from the target career portal..."
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
            />
          </div>

          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 text-rose-600 rounded-lg text-sm font-medium">
              ⚠️ {error}
            </div>
          )}

          <button
            onClick={processCV}
            disabled={isLoading}
            className={`w-full py-3.5 px-4 font-bold rounded-lg text-white shadow-md transition ${
              isLoading 
                ? 'bg-slate-400 cursor-not-allowed' 
                : 'bg-indigo-600 hover:bg-indigo-700 active:scale-[0.99]'
            }`}
          >
            {isLoading ? 'Processing Pipeline...' : 'Generate Optimized Content'}
          </button>
        </section>

        {/* RIGHT COLUMN: AI Live Output Output Viewport */}
        <section className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col">
          <h2 className="text-xl font-bold border-b border-slate-100 pb-2 mb-4">Optimized Core Output</h2>
          
          {isLoading && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 gap-3">
              <div className="w-8 h-8 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm font-medium animate-pulse">Running architectural remapping...</p>
            </div>
          )}

          {!isLoading && tailoredBullets.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-400 p-8 border-2 border-dashed border-slate-200 rounded-lg">
              <p className="text-sm text-center">
                Configure input parameters and initialize pipeline to view structured metrics.
              </p>
            </div>
          )}

          {!isLoading && tailoredBullets.length > 0 && (
            <div className="flex-1 flex flex-col gap-4">
              <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg text-xs font-semibold tracking-wide uppercase">
                ✓ Optimization Matrix Complete
              </div>
              <div className="flex-1 overflow-y-auto max-h-[500px] pr-2 flex flex-col gap-3">
                {tailoredBullets.map((bullet, idx) => (
                  <div 
                    key={idx} 
                    className="p-4 rounded-lg bg-slate-50 border border-slate-150 hover:border-indigo-200 transition relative pl-8 group"
                  >
                    <span className="absolute left-3 top-4 text-indigo-500 font-bold text-sm select-none">•</span>
                    <p className="text-sm leading-relaxed text-slate-800 font-medium">{bullet}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}