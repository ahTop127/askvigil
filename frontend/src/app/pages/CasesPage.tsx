import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import {
  FolderOpen,
  TriangleAlert,
  Briefcase,
  ShieldAlert,
  Smartphone,
  QrCode,
  Link as LinkIcon,
} from "lucide-react";
import { Navigation } from "@components/Navigation";
import { Badge } from "@components/ui/badge";
import { Button } from "@components/ui/button";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@components/ui/pagination";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@components/ui/select";
import { fetchScamCases } from "@lib/api/cases";
import type { ScamCase } from "@lib/types";

const PAGE_SIZE = 9;

function getScamVisuals(type: string) {
  switch (type) {
    case "job-scam":
      return {
        icon: Briefcase,
        chip: "bg-[#FFF4E8] text-[#B8681B] border-[#F2C28E]",
        banner: "from-[#FFE7CC] to-[#FFF6EA]",
      };
    case "phishing":
      return {
        icon: ShieldAlert,
        chip: "bg-[#FFECEE] text-[#B63A47] border-[#F4B5BC]",
        banner: "from-[#FFD8DE] to-[#FFF1F3]",
      };
    case "otp-scam":
      return {
        icon: Smartphone,
        chip: "bg-[#FFF2E8] text-[#B65E24] border-[#F4C59F]",
        banner: "from-[#FFE1CC] to-[#FFF3E8]",
      };
    case "qr-scam":
      return {
        icon: QrCode,
        chip: "bg-[#EEF3FF] text-[#365FB6] border-[#BDD0F6]",
        banner: "from-[#DCE8FF] to-[#F1F6FF]",
      };
    default:
      return {
        icon: LinkIcon,
        chip: "bg-[#FFF6E8] text-[#9A6A1A] border-[#EFCF94]",
        banner: "from-[#FFECCC] to-[#FFF8EA]",
      };
  }
}

export default function CasesPage() {
  const navigate = useNavigate();
  const [params, setParams] = useSearchParams();
  const [cases, setCases] = useState<ScamCase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const scamType = params.get("scamType") ?? "all";
  const platform = params.get("platform") ?? "all";
  const date = params.get("date") ?? "all";
  const page = Math.max(1, Number(params.get("page") ?? "1"));

  useEffect(() => {
    let cancelled = false;
    setIsLoading(true);
    setLoadError(null);
    fetchScamCases({ scamType, platform, date })
      .then((items) => {
        if (cancelled) return;
        setCases(items);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadError(
          err instanceof Error ? err.message : "Failed to load cases.",
        );
        setCases([]);
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [date, platform, scamType]);

  const filtered = useMemo(() => cases, [cases]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const currentPage = Math.min(page, totalPages);
  const paged = filtered.slice(
    (currentPage - 1) * PAGE_SIZE,
    currentPage * PAGE_SIZE,
  );

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    next.set(key, value);
    next.set("page", "1");
    setParams(next);
  };

  const setPage = (nextPage: number) => {
    const next = new URLSearchParams(params);
    next.set("page", String(nextPage));
    setParams(next);
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <main className="max-w-6xl mx-auto px-4 py-10">
        <h1 className="text-6xl md:text-7xl font-semibold text-black leading-tight tracking-tight">
          Real Scam Cases.
        </h1>
        <p className="text-2xl text-gray-700 mt-4 mb-8 max-w-3xl">
          Learn from real examples to recognise scam patterns and protect
          yourself.
        </p>
        <section className="p-1 md:p-1.5 mb-4">
          <div className="flex flex-wrap items-end gap-2">
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-0.5">
                Scam Type
              </p>
              <Select
                value={scamType}
                onValueChange={(v) => setFilter("scamType", v)}
              >
                <SelectTrigger className="h-9 w-[200px] rounded-md border-gray-200 bg-white">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="job-scam">Job Scams</SelectItem>
                  <SelectItem value="phishing">Phishing Scams</SelectItem>
                  <SelectItem value="otp-scam">OTP Scams</SelectItem>
                  <SelectItem value="qr-scam">QR Code Scams</SelectItem>
                  <SelectItem value="suspicious-link">
                    Suspicious Links
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-0.5">
                Platform
              </p>
              <Select
                value={platform}
                onValueChange={(v) => setFilter("platform", v)}
              >
                <SelectTrigger className="h-9 w-[200px] rounded-md border-gray-200 bg-white">
                  <SelectValue placeholder="All Platforms" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Platforms</SelectItem>
                  <SelectItem value="WhatsApp">WhatsApp</SelectItem>
                  <SelectItem value="Telegram">Telegram</SelectItem>
                  <SelectItem value="SMS">SMS</SelectItem>
                  <SelectItem value="Email">Email</SelectItem>
                  <SelectItem value="Social Media">Social Media</SelectItem>
                  <SelectItem value="Phone Call">Phone Call</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-0.5">Date</p>
              <Select value={date} onValueChange={(v) => setFilter("date", v)}>
                <SelectTrigger className="h-9 w-[200px] rounded-md border-gray-200 bg-white">
                  <SelectValue placeholder="All Time" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="3m">Last 3 Months</SelectItem>
                  <SelectItem value="6m">Last 6 Months</SelectItem>
                  <SelectItem value="1y">Last Year</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </section>

        <section>
          {isLoading ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center text-gray-600">
              Loading scam cases...
            </div>
          ) : loadError ? (
            <div className="bg-white rounded-2xl border border-red-200 p-10 text-center">
              <p className="font-semibold text-red-700">
                Failed to load scam cases.
              </p>
              <p className="text-sm text-red-600 mt-1">{loadError}</p>
              <Button
                className="mt-4"
                variant="outline"
                onClick={() => {
                  setIsLoading(true);
                  setLoadError(null);
                  fetchScamCases({ scamType, platform, date })
                    .then((items) => setCases(items))
                    .catch((err: unknown) => {
                      setLoadError(
                        err instanceof Error
                          ? err.message
                          : "Failed to load cases.",
                      );
                      setCases([]);
                    })
                    .finally(() => setIsLoading(false));
                }}
              >
                Retry
              </Button>
            </div>
          ) : filtered.length === 0 ? (
            <div className="bg-white rounded-2xl border border-gray-200 p-10 text-center">
              <FolderOpen className="w-8 h-8 mx-auto text-gray-400 mb-3" />
              <p className="font-semibold text-gray-900">
                No scam cases available yet.
              </p>
              <p className="text-sm text-gray-600 mt-1">
                We&apos;re collecting real cases to help you stay safe. Check
                back soon.
              </p>
            </div>
          ) : (
            <>
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {paged.map((item) => (
                  <article
                    key={item.id}
                    className="bg-white rounded-3xl border border-gray-200 min-h-[320px] shadow-sm hover:-translate-y-0.5 hover:shadow-md transition flex flex-col overflow-hidden"
                  >
                    {(() => {
                      const visuals = getScamVisuals(item.scamType);
                      const ScamIcon = visuals.icon;
                      return (
                        <>
                          <div
                            className={`bg-gradient-to-r ${visuals.banner} px-6 py-4 border-b border-gray-100`}
                          >
                            <div className="flex items-center justify-between gap-3">
                              <div className="inline-flex items-center gap-2 text-sm font-semibold text-gray-800">
                                <TriangleAlert className="w-4 h-4 text-red-500" />
                                Scam Alert Case
                              </div>
                              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-white/80 border border-white">
                                <ScamIcon className="w-4 h-4 text-gray-700" />
                              </span>
                            </div>
                          </div>

                          <div className="p-6 flex-1 flex flex-col">
                            <div className="flex flex-wrap gap-2 mb-4">
                              <Badge
                                variant="outline"
                                className={`text-xs px-2.5 py-1 border ${visuals.chip}`}
                              >
                                {item.scamType}
                              </Badge>
                              <Badge
                                variant="outline"
                                className="text-xs px-2.5 py-1"
                              >
                                {item.platform}
                              </Badge>
                            </div>
                            <h3 className="text-2xl font-semibold text-gray-900 line-clamp-2 leading-snug">
                              {item.title}
                            </h3>
                            <p className="text-lg text-gray-700 line-clamp-4 mt-3 leading-relaxed">
                              {item.summary}
                            </p>
                            <div className="mt-auto pt-6 flex justify-end">
                              <button
                                className="inline-flex items-center justify-center gap-2 rounded-full bg-primary hover:bg-secondary text-primary-foreground text-sm font-semibold px-5 py-2.5 shadow-sm transition-all"
                                onClick={() => {
                                  window.open(
                                    item.sourceUrl,
                                    "_blank",
                                    "noopener,noreferrer",
                                  );
                                }}
                              >
                                View Details
                                <span aria-hidden>→</span>
                              </button>
                            </div>
                          </div>
                        </>
                      );
                    })()}
                  </article>
                ))}
              </div>
              {totalPages > 1 && (
                <Pagination className="mt-6">
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          if (currentPage > 1) setPage(currentPage - 1);
                        }}
                      />
                    </PaginationItem>
                    {Array.from({ length: totalPages }).map((_, idx) => (
                      <PaginationItem key={idx + 1}>
                        <PaginationLink
                          href="#"
                          isActive={idx + 1 === currentPage}
                          onClick={(e) => {
                            e.preventDefault();
                            setPage(idx + 1);
                          }}
                        >
                          {idx + 1}
                        </PaginationLink>
                      </PaginationItem>
                    ))}
                    <PaginationItem>
                      <PaginationNext
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          if (currentPage < totalPages) {
                            setPage(currentPage + 1);
                          }
                        }}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
