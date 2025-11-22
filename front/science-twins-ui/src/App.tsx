import { useState } from "react";
import Header from "./components/Header";
import QueryForm from "./components/QueryForm";
import ResultsPanel from "./components/ResultsPanel";
import { analyze } from "./api";
import type { AnalyzeResponse } from "./types";

function App() {
  const [response, setResponse] = useState<AnalyzeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [mode, setMode] = useState<"plagiarism" | "doppelganger">("plagiarism");

  const handleAnalyze = async () => {
    setIsLoading(true);
    setError(null);
    setResponse(null);

    try {
      const result = await analyze(text, mode, file);
      console.log("🔍 API RESPONSE:", result); // 👈 ДОБАВИЛИ!
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50 pt-0 pb-10 sm:pb-16">
      <div className="mx-auto w-full max-w-5xl px-4 sm:px-6 lg:px-8">
        <Header />
        <div className="mt-8 space-y-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <QueryForm
              text={text}
              mode={mode}
              loading={isLoading}
              file={file}
              onTextChange={setText}
              onModeChange={setMode}
              onFileChange={setFile}
              onAnalyze={handleAnalyze}
            />
          </div>
          <ResultsPanel
            response={response}
            isLoading={isLoading}
            error={error}
          />
        </div>
      </div>
    </main>
  );
}

export default App;
