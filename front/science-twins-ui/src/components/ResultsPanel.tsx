import type { AnalyzeResponse } from "../types";
import DoppelgangerCard from "./DoppelgangerCard";

interface ResultsPanelProps {
  response: AnalyzeResponse | null;
  isLoading: boolean;
  error: string | null;
}

export default function ResultsPanel({
  response,
  isLoading,
  error,
}: ResultsPanelProps) {
  //
  // ⛔ ERROR
  //
  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6">
        <h3 className="text-lg font-semibold text-red-800 mb-2">
          Something went wrong
        </h3>
        <p className="text-sm text-red-600">
          We couldn't reach the analysis service. Please try again in a moment.
        </p>
      </div>
    );
  }

  //
  // ⏳ LOADING
  //
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
        <p className="text-slate-600">Analyzing your text…</p>
      </div>
    );
  }

  //
  // ⬜ NO DATA YET
  //
  if (!response) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
        <p className="text-slate-600">
          Paste a text or upload a PDF, then run the analysis.
        </p>
      </div>
    );
  }

  //
  // 🟥 PLAIGARISM MODE
  //
  if (response.mode === "plagiarism") {
    const { result } = response as any;

    if (result.type === "plagiarism") {
      return (
        <div className="bg-red-50 rounded-xl shadow-sm border border-red-300 p-6">
          <h3 className="text-xl font-semibold text-red-800 mb-4">
            ⚠️ Plagiarism Detected
          </h3>

          {result.title && (
            <div className="mb-3">
              <p className="text-sm font-medium text-red-700 mb-1">Title:</p>
              <p className="text-base text-red-800">{result.title}</p>
            </div>
          )}

          {result.reason && (
            <div className="mb-3">
              <p className="text-sm font-medium text-red-700 mb-1">Reason:</p>
              <p className="text-base text-red-800">{result.reason}</p>
            </div>
          )}

          {result.url && (
            <div className="mt-4">
              <a
                href={result.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-red-700 hover:text-red-800 text-sm font-medium underline"
              >
                View original article →
              </a>
            </div>
          )}
        </div>
      );
    }

    // 🟢 No plagiarism
    return (
      <div className="bg-emerald-50 rounded-xl shadow-sm border border-emerald-300 p-6 text-center">
        <p className="text-lg font-semibold text-emerald-700">
          No plagiarism detected 🎉
        </p>
      </div>
    );
  }

  //
  // 🧠 CONCEPTUAL DOPPELGANGERS MODE
  //
  if (response.mode === "doppelganger") {
    const { result } = response;

    if (!result || result.type !== "doppelganger") {
      return (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
          <p className="text-slate-600">
            No conceptual twins data available yet.
          </p>
        </div>
      );
    }

    const { top_3, all_doppelgangers_with_reasons, count } = result;

    return (
      <div className="space-y-12">
        {/* 🌟 Section A: Top 3 conceptual twins */}
        <section>
          <h3 className="text-xl font-semibold text-slate-800 mb-3 text-center">
            Top 3 conceptual twins
          </h3>

          {top_3.justification && (
            <p className="text-sm text-slate-600 mb-8 max-w-3xl mx-auto text-center leading-relaxed">
              {top_3.justification}
            </p>
          )}

          {top_3.papers.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <p className="text-slate-600">No top matches found.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {top_3.papers.map((paper) => (
                <DoppelgangerCard
                  key={paper.id}
                  doppelganger={paper}
                  isTop3={true}
                />
              ))}
            </div>
          )}
        </section>

        {/* 📚 Section B: All doppelgängers */}
        <section>
          <h3 className="text-xl font-semibold text-slate-800 mb-4">
            All doppelgängers {count > 0 && `(${count})`}
          </h3>

          {all_doppelgangers_with_reasons.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 text-center">
              <p className="text-slate-600">No doppelgängers found.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {all_doppelgangers_with_reasons.map((doppelganger) => (
                <DoppelgangerCard
                  key={doppelganger.id}
                  doppelganger={doppelganger}
                  isTop3={false}
                />
              ))}
            </div>
          )}
        </section>
      </div>
    );
  }

  //
  // 🟦 FALLBACK (if unknown mode)
  //
  return null;
}