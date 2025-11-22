import { useRef } from "react";

type Mode = "plagiarism" | "doppelganger";

interface QueryFormProps {
  text: string;
  mode: "plagiarism" | "doppelganger";
  loading: boolean;
  file: File | null;
  onTextChange: (value: string) => void;
  onModeChange: (mode: "plagiarism" | "doppelganger") => void;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
}

export default function QueryForm({
  text,
  mode,
  loading,
  file,
  onTextChange,
  onModeChange,
  onFileChange,
  onAnalyze,
}: QueryFormProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if ((text.trim() || file) && !loading) {
      onAnalyze();
    }
  };

  const handleModeChange = (newMode: Mode) => {
    onModeChange(newMode);
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile && droppedFile.type === "application/pdf") {
      onFileChange(droppedFile);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    if (selectedFile && selectedFile.type === "application/pdf") {
      onFileChange(selectedFile);
    }
  };

  const clearFile = () => {
    onFileChange(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const isDisabled = (!text.trim() && !file) || loading;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Mode Selector - First */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-slate-800">
          What do you want to find?
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <button
            type="button"
            onClick={() => handleModeChange("plagiarism")}
            disabled={loading}
            className={`p-4 rounded-2xl border text-left transition ${
              mode === "plagiarism"
                ? "border-indigo-500 bg-indigo-50 text-indigo-900 shadow-sm"
                : "border-slate-200 bg-white/80 shadow-sm hover:border-slate-300"
            } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            <h4 className="text-sm font-semibold mb-1">
              Near-duplicate texts
            </h4>
            <p className="text-xs text-slate-600 mt-1">
              Check for highly similar wording and overlapping passages.
            </p>
          </button>

          <button
            type="button"
            onClick={() => handleModeChange("doppelganger")}
            disabled={loading}
            className={`p-4 rounded-2xl border text-left transition ${
              mode === "doppelganger"
                ? "border-indigo-500 bg-indigo-50 text-indigo-900 shadow-sm"
                : "border-slate-200 bg-white/80 shadow-sm hover:border-slate-300"
            } ${loading ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            <h4 className="text-sm font-semibold mb-1">
              Conceptual twins
            </h4>
            <p className="text-xs text-slate-600 mt-1">
              Find papers that share the same core idea, even if the wording is
              different.
            </p>
          </button>
        </div>
        <p className="text-sm text-slate-500">
          You can switch modes at any time — we'll re-analyze your text.
        </p>
      </div>

      {/* 2-Column Layout: Textarea + PDF Upload */}
      <div className="mt-6 grid gap-4 md:grid-cols-[2fr_1fr]">
        {/* Left Column: Textarea */}
        <div>
          <label htmlFor="text" className="block text-sm font-medium text-slate-700 mb-2">
            Paste your abstract or paper fragment
          </label>
          <textarea
            id="text"
            value={text}
            onChange={(e) => onTextChange(e.target.value)}
            placeholder="Paste your abstract or paper fragment here…"
            className="w-full min-h-[200px] rounded-2xl border border-indigo-300 bg-indigo-50/40 px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-200 resize-y"
            disabled={loading}
          />
          <p className="mt-2 text-xs text-slate-500">
            Add some text first — we'll do the rest.
          </p>
        </div>

        {/* Right Column: PDF Upload Card */}
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Upload PDF (optional)
          </label>
          <div
            className={`flex min-h-[200px] items-center justify-center rounded-2xl border-2 border-dashed border-indigo-300 bg-indigo-50/30 px-3 py-4 text-center transition cursor-pointer ${
              loading ? "opacity-50 cursor-not-allowed" : "hover:border-indigo-400 hover:bg-indigo-50/50"
            }`}
            onClick={loading ? undefined : handleClick}
            onDrop={loading ? undefined : handleDrop}
            onDragOver={loading ? undefined : handleDragOver}
          >
            <div>
              <p className="text-xs font-medium text-slate-700">
                Drop a file here, or click to browse.
              </p>
            </div>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            className="hidden"
            onChange={handleFileChange}
            disabled={loading}
          />
          {file && (
            <p className="mt-2 text-xs text-slate-500">
              Selected: <span className="font-medium text-slate-700">{file.name}</span>
              <button
                type="button"
                onClick={clearFile}
                disabled={loading}
                className="ml-2 text-indigo-600 hover:text-indigo-700 underline disabled:opacity-50"
              >
                Clear
              </button>
            </p>
          )}
        </div>
      </div>

      {/* Primary Button - Last */}
      <button
        type="submit"
        disabled={isDisabled}
        className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-300 disabled:cursor-not-allowed disabled:bg-slate-300 gap-2"
      >
        {loading && (
          <svg
            className="animate-spin h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            ></circle>
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
        )}
        {mode === "plagiarism"
          ? loading
            ? "Scanning for near-duplicates…"
            : "Scan for near-duplicates"
          : loading
          ? "Searching for conceptual twins…"
          : "Discover conceptual twins"}
      </button>
    </form>
  );
}
