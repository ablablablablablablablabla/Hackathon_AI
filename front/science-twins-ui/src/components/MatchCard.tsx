import type { AnalyzeMatch } from "../types";

interface MatchCardProps {
  match: AnalyzeMatch;
}

export default function MatchCard({ match }: MatchCardProps) {
  const similarityPercentage = Math.round(match.similarity * 100);

  const getBadgeColor = (type: string) => {
    switch (type) {
      case "textual":
        return "bg-blue-100 text-blue-800";
      case "conceptual":
        return "bg-purple-100 text-purple-800";
      case "mixed":
        return "bg-indigo-100 text-indigo-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <h4 className="text-lg font-semibold text-slate-800 mb-2">
            {match.title}
          </h4>
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-sm text-slate-600">{match.field}</span>
            <span
              className={`px-2.5 py-1 rounded-full text-xs font-medium ${getBadgeColor(
                match.type
              )}`}
            >
              {match.type}
            </span>
            <span className="text-sm font-semibold text-indigo-700">
              {similarityPercentage}% similar
            </span>
          </div>
        </div>
      </div>

      {match.url && (
        <div className="mb-4">
          <a
            href={match.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-700 text-sm font-medium underline"
          >
            View paper →
          </a>
        </div>
      )}

      <div className="mb-4">
        <p className="text-sm text-slate-700 leading-relaxed">
          {match.explanation}
        </p>
      </div>

      {match.type === "textual" && match.overlap_fragments && match.overlap_fragments.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <h5 className="text-sm font-semibold text-slate-700 mb-3">
            Overlapping Fragments
          </h5>
          <div className="space-y-3">
            {match.overlap_fragments.map((fragment, idx) => (
              <div
                key={idx}
                className="bg-slate-50 rounded-lg p-3 border border-slate-200"
              >
                <div className="mb-2">
                  <p className="text-xs font-medium text-slate-600 mb-1">
                    Query fragment:
                  </p>
                  <p className="text-sm text-slate-800 italic">
                    "{fragment.query_fragment}"
                  </p>
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-600 mb-1">
                    Match fragment:
                  </p>
                  <p className="text-sm text-slate-800 italic">
                    "{fragment.match_fragment}"
                  </p>
                </div>
                {fragment.score !== undefined && (
                  <p className="text-xs text-slate-500 mt-2">
                    Score: {Math.round(fragment.score * 100)}%
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {match.type === "conceptual" && match.conceptual_links && match.conceptual_links.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-200">
          <h5 className="text-sm font-semibold text-slate-700 mb-3">
            Conceptual Links
          </h5>
          <ul className="space-y-2">
            {match.conceptual_links.map((link, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-indigo-600 mt-1">•</span>
                <p className="text-sm text-slate-700 flex-1">{link}</p>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

