import type { AnalyzeQueryInfo } from "../types";

interface QuerySummaryCardProps {
  query: AnalyzeQueryInfo;
}

export default function QuerySummaryCard({ query }: QuerySummaryCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h3 className="text-xl font-semibold text-slate-800 mb-4">
        Query Summary
      </h3>
      <div className="space-y-3">
        {query.normalized_title && (
          <div>
            <p className="text-sm font-medium text-slate-600">Title</p>
            <p className="text-slate-800">{query.normalized_title}</p>
          </div>
        )}
        {query.field && (
          <div>
            <p className="text-sm font-medium text-slate-600">Field</p>
            <p className="text-slate-800">{query.field}</p>
          </div>
        )}
        {query.summary && (
          <div>
            <p className="text-sm font-medium text-slate-600">Summary</p>
            <p className="text-slate-800">{query.summary}</p>
          </div>
        )}
      </div>
    </div>
  );
}

