import type { DoppelgangerPaper } from "../types";

interface DoppelgangerCardProps {
  doppelganger: DoppelgangerPaper;
  isTop3?: boolean;
}

export default function DoppelgangerCard({
  doppelganger,
  isTop3 = false,
}: DoppelgangerCardProps) {
  if (isTop3) {
    // Top 3 cards - more prominent styling
    const displayPlace = doppelganger.place ?? doppelganger.id;
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-sm font-bold">
            #{displayPlace}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-base font-semibold text-slate-800 mb-2">
              {doppelganger.title}
            </h4>
            <p className="text-xs text-slate-600 mb-2">
              <span className="font-medium">Domain:</span> {doppelganger.domain}
            </p>
            <p className="text-sm text-slate-700 mb-3 leading-relaxed">
              {doppelganger.reason}
            </p>
            {doppelganger.url && (
              <a
                href={doppelganger.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-700 text-sm font-medium underline inline-flex items-center gap-1"
              >
                View paper →
              </a>
            )}
          </div>
        </div>
      </div>
    );
  }

  // All doppelgangers - more compact styling
  return (
    <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-4">
      <div className="flex items-start gap-4">
        <div className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center text-xs font-semibold">
          {doppelganger.id}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-slate-800 mb-1">
            {doppelganger.title}
          </h4>
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-600 mb-2">
            <span className="font-medium">{doppelganger.domain}</span>
          </div>
          <p className="text-xs text-slate-700 mb-2 leading-relaxed">
            {doppelganger.reason}
          </p>
          {doppelganger.url && (
            <a
              href={doppelganger.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-700 text-xs font-medium underline"
            >
              View paper →
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

