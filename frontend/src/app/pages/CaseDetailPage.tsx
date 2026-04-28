import { useMemo } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router";
import { Navigation } from "@components/Navigation";
import { Badge } from "@components/ui/badge";
import { Button } from "@components/ui/button";
import { mockCases } from "@lib/constants/cases";

export default function CaseDetailPage() {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const item = useMemo(() => mockCases.find((c) => c.id === caseId), [caseId]);

  if (!item) {
    return (
      <div className="min-h-screen bg-[#F7F8FA]">
        <Navigation />
        <main className="max-w-4xl mx-auto px-4 py-10">
          <p className="text-gray-600">Case not found.</p>
          <Button className="mt-4" onClick={() => navigate("/cases")}>
            Back to Cases
          </Button>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      <Navigation />
      <main className="max-w-4xl mx-auto px-4 py-10">
        <Button
          variant="ghost"
          className="mb-4 px-0 text-primary"
          onClick={() => navigate(`/cases?${params.toString()}`)}
        >
          ← Back
        </Button>
        <article className="bg-white rounded-3xl border border-gray-200 p-6 space-y-6">
          <h1 className="text-3xl font-bold text-gray-900">{item.title}</h1>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="border-primary/40 text-primary">
              {item.scamType}
            </Badge>
            <Badge variant="outline">{item.platform}</Badge>
            <span className="text-sm text-gray-500">{item.date}</span>
          </div>
          <section>
            <h2 className="font-semibold text-gray-900 mb-2">What Happened</h2>
            <p className="text-gray-700 leading-7">{item.whatHappened}</p>
          </section>
          <section>
            <h2 className="font-semibold text-gray-900 mb-2">Warning Signs</h2>
            <ul className="space-y-1 text-gray-700">
              {item.warningSigns.map((sign) => (
                <li key={sign}>❌ {sign}</li>
              ))}
            </ul>
          </section>
          <section>
            <h2 className="font-semibold text-gray-900 mb-2">Lesson</h2>
            <p className="text-gray-700 leading-7">{item.lesson}</p>
          </section>
          <section>
            <h2 className="font-semibold text-gray-900 mb-2">Source</h2>
            <a
              href={item.sourceUrl}
              target="_blank"
              rel="noreferrer"
              className="text-primary hover:underline break-all"
            >
              {item.sourceUrl}
            </a>
          </section>
        </article>
        <div className="mt-6 flex gap-3">
          <Button variant="outline" onClick={() => navigate(`/cases?${params.toString()}`)}>
            Back to Cases
          </Button>
          <Button className="bg-primary hover:bg-secondary text-primary-foreground" onClick={() => navigate("/")}>
            Check Another Message
          </Button>
        </div>
      </main>
    </div>
  );
}
