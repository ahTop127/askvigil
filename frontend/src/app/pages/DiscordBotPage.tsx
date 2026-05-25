import { useCallback, useState } from "react";
import { ExternalLink } from "lucide-react";
import { Navigation } from "../components/Navigation";
import { Button } from "../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";

/** Default Discord OAuth (Add to Server / integration). */
const DEFAULT_DISCORD_INTEGRATION_URL =
  "https://discord.com/oauth2/authorize?client_id=1501471273186754640";

export default function DiscordBotPage() {
  const [open, setOpen] = useState(false);

  const onAdd = useCallback(() => {
    setOpen(true);
  }, []);
  const onSave = useCallback(() => {
    window.open(
      DEFAULT_DISCORD_INTEGRATION_URL,
      "_blank",
      "noopener,noreferrer",
    );
    setOpen(false);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navigation />
      <main className="mx-auto w-full max-w-[1180px] px-4 py-12 space-y-10">
        {/* Product header (Notion-style): Discord icon + title | Add button — above gray preview */}
        <section className="space-y-5">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="flex min-w-0 items-start gap-3 md:gap-4">
              <div
                className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#5865F2] text-white shadow-sm md:h-12 md:w-12"
                aria-hidden
              >
                <svg
                  className="h-6 w-6 md:h-7 md:w-7"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                  aria-hidden
                >
                  <path
                    fill="currentColor"
                    d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"
                  />
                </svg>
              </div>
              <h1 className="text-pretty text-2xl font-bold tracking-tight text-slate-900 md:text-[1.65rem] md:leading-snug lg:text-[1.85rem]">
                AskVigil Discord Integration
              </h1>
            </div>
            <Button
              type="button"
              onClick={onAdd}
              className="h-11 shrink-0 rounded-full px-6 font-semibold shadow-sm sm:self-start bg-primary hover:bg-secondary text-primary-foreground"
            >
              Add to AskVigil
            </Button>
          </div>

          {/* Gray shell: left = preview card, right = Discord highlight */}
          <div className="relative rounded-[28px] bg-[#ececec] p-5 md:p-7 shadow-[0_2px_24px_rgba(15,23,42,0.06)]">
            <div className="relative grid gap-10 lg:grid-cols-[minmax(0,1fr)_minmax(17rem,26%)] lg:items-center lg:gap-12">
              {/* Left: UI preview (white card) */}
              <div className="rounded-2xl bg-white px-5 py-6 md:px-8 md:py-8 shadow-sm ring-1 ring-slate-900/[0.04]">
                <h2 className="text-pretty text-2xl font-bold tracking-tight text-slate-900 md:text-[1.65rem] md:leading-snug lg:text-[1.85rem]">
                  Example: send in Discord → what you get back
                </h2>

                <div className="mt-5 rounded-xl bg-slate-50/90 p-5 md:p-6">
                  <p className="text-base leading-relaxed text-slate-800 md:text-[17px]">
                    After integration, post suspicious content in a channel or
                    DM. You only get analysis for messages{" "}
                    <span className="font-semibold text-slate-900">
                      you send
                    </span>{" "}
                    — nothing is scanned automatically across the whole server.
                  </p>

                  <div className="mt-6 rounded-xl bg-white px-4 py-4 md:px-5 md:py-5">
                    <p className="text-base font-bold text-slate-900 md:text-[17px]">
                      Sample message
                    </p>
                    <p className="mt-3 text-base leading-relaxed text-slate-800 md:text-[17px]">
                      “Suspicious login detected. Verify your account and enter
                      OTP here: http://secure-login-otp-check.com”
                    </p>
                  </div>

                  <div className="mt-6">
                    <p className="text-base font-bold text-slate-900 md:text-[17px]">
                      What the bot returns (example)
                    </p>
                    <ul className="mt-3 space-y-2 text-base leading-relaxed text-slate-800 md:text-[17px]">
                      <li>
                        <span className="font-semibold text-slate-900">
                          Risk score
                        </span>{" "}
                        — e.g.{" "}
                        <span className="font-semibold text-slate-900">
                          78 / 100
                        </span>
                      </li>
                      <li>
                        <span className="font-semibold text-slate-900">
                          Risk level
                        </span>{" "}
                        — e.g.{" "}
                        <span className="font-semibold text-slate-900">
                          High
                        </span>
                      </li>
                      <li>
                        <span className="font-semibold text-slate-900">
                          Scam type
                        </span>{" "}
                        — e.g.{" "}
                        <span className="font-semibold text-slate-900">
                          Phishing
                        </span>
                      </li>
                      <li>
                        <span className="font-semibold text-slate-900">
                          Explanation
                        </span>{" "}
                        — why it looks risky
                      </li>
                      <li>
                        <span className="font-semibold text-slate-900">
                          Safety advice
                        </span>{" "}
                        — what to do next
                      </li>
                    </ul>
                  </div>
                </div>

                <div className="mt-8">
                  <p className="text-pretty text-2xl font-bold tracking-tight text-slate-900 md:text-[1.65rem] md:leading-snug lg:text-[1.85rem]">
                    What you can send
                  </p>
                  <div className="mt-5 grid gap-6 md:grid-cols-2 md:gap-x-10 md:gap-y-5">
                    {[
                      {
                        title: "Text messages",
                        desc: "Suspicious chat lines or pasted wording.",
                      },
                      {
                        title: "URLs / links",
                        desc: "A link you want checked for phishing or scam signals.",
                      },
                      {
                        title: "QR code content",
                        desc: "Decoded QR text, or an image of the QR code.",
                      },
                      {
                        title: "Screenshots / images",
                        desc: "Screenshots of messages, ads, or payment screens.",
                      },
                    ].map((item) => (
                      <div key={item.title}>
                        <p className="text-base font-bold text-slate-900 md:text-[17px]">
                          {item.title}
                        </p>
                        <p className="mt-1 text-base leading-relaxed text-slate-800 md:text-[17px]">
                          {item.desc}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Right: large round logo + title (container’s right side) */}
              <aside className="mx-auto flex max-w-sm flex-col items-center justify-center text-center lg:mx-0 lg:max-w-none lg:py-4">
                <div
                  className="flex h-[4.5rem] w-[4.5rem] shrink-0 items-center justify-center rounded-full bg-white shadow-[0_4px_24px_rgba(15,23,42,0.08)] ring-1 ring-slate-200/90 md:h-[5.25rem] md:w-[5.25rem]"
                  aria-hidden
                >
                  <svg
                    className="h-10 w-10 text-[#5865F2] md:h-12 md:w-12"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden
                  >
                    <path
                      fill="currentColor"
                      d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0 12.64 12.64 0 0 0-.617-1.25.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057 19.9 19.9 0 0 0 5.993 3.03.078.078 0 0 0 .084-.028 14.09 14.09 0 0 0 1.226-1.994.076.076 0 0 0-.041-.106 13.107 13.107 0 0 1-1.872-.892.077.077 0 0 1-.008-.128 10.2 10.2 0 0 0 .372-.292.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127 12.299 12.299 0 0 1-1.873.892.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028 19.839 19.839 0 0 0 6.002-3.03.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.956-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419 0-1.333.955-2.419 2.157-2.419 1.21 0 2.176 1.096 2.157 2.42 0 1.333-.946 2.418-2.157 2.418z"
                    />
                  </svg>
                </div>
                <h2 className="mt-5 text-pretty text-3xl font-bold leading-[1.12] tracking-tight text-slate-900 md:mt-6 md:text-4xl">
                  Discord
                </h2>
              </aside>
            </div>
          </div>
        </section>

        {/* Bottom: flat sections — typography only, no card chrome (Notion-style) */}
        <section className="max-w-4xl space-y-14 md:space-y-16">
          <section>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
              Overview
            </h2>
            <p className="mt-5 text-base leading-relaxed text-slate-800 md:text-[17px]">
              After you connect Discord on AskVigil, you can send suspicious
              content from Discord and receive the same risk score, risk level,
              scam type, explanation, and safety advice as on this website.
            </p>
          </section>

          <section>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
              How to use
            </h2>
            <ol className="mt-6 space-y-4 text-slate-800">
              {[
                "Click Add to AskVigil, review the dialog, then click Continue to open Discord.",
                "Complete the setup so AskVigil can reach the channel you choose.",
                "In Discord, send suspicious text, URLs, decoded QR content, or screenshots when you want a check.",
                "Read the detection result (score, risk level, scam type, explanation, and advice).",
              ].map((line, idx) => (
                <li key={line} className="flex gap-3">
                  <span className="mt-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-white font-bold text-sm">
                    {idx + 1}
                  </span>
                  <span className="leading-relaxed">{line}</span>
                </li>
              ))}
            </ol>
          </section>

          <section>
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
              Privacy reminder
            </h2>
            <ul className="mt-6 space-y-3 text-base leading-relaxed text-slate-800 md:text-[17px]">
              <li className="flex gap-2">
                <span aria-hidden className="mt-0.5">
                  •
                </span>
                <span>
                  AskVigil only checks content you actively send. It does not
                  automatically monitor all Discord messages.
                </span>
              </li>
              <li className="flex gap-2">
                <span aria-hidden className="mt-0.5">
                  •
                </span>
                <span>
                  Do not send passwords, banking details, OTP/TAC codes,
                  identification numbers, or other sensitive personal
                  information.
                </span>
              </li>
              <li className="flex gap-2">
                <span aria-hidden className="mt-0.5">
                  •
                </span>
                <span>
                  AskVigil results are a support tool, not a 100% guarantee.
                  Always verify through official channels.
                </span>
              </li>
            </ul>
          </section>
        </section>
      </main>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-xl rounded-2xl p-6">
          <DialogHeader>
            <DialogTitle className="text-2xl font-black text-slate-900">
              Add AskVigil to Discord
            </DialogTitle>
            <DialogDescription>
              Review the configuration requirements before connecting Discord to
              your AskVigil account.
            </DialogDescription>
          </DialogHeader>

          <div className="mt-2 space-y-5 text-sm text-slate-800">
            <section className="rounded-xl bg-slate-50 p-4">
              <p className="text-sm font-semibold text-slate-900">
                Discord integration link
              </p>
              <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                Official AskVigil Discord install link (read-only; you can
                select and copy if needed).
              </p>
              <div
                id="discord-integration-link"
                role="textbox"
                aria-readonly="true"
                className="mt-3 w-full rounded-xl bg-slate-100/80 px-3 py-3 text-sm text-slate-800 shadow-[inset_0_0_0_1px_rgba(15,23,42,0.08)] select-text break-all"
              >
                {DEFAULT_DISCORD_INTEGRATION_URL}
              </div>
            </section>

            <section>
              <p className="font-semibold text-slate-900">Requirements</p>
              <ul className="mt-2 space-y-2">
                <li className="flex gap-2">
                  <span aria-hidden className="mt-0.5">
                    •
                  </span>
                  <span>
                    You have access to a Discord server where you can manage
                    integrations (Manage Server or Manage Webhooks permission).
                  </span>
                </li>
                <li className="flex gap-2">
                  <span aria-hidden className="mt-0.5">
                    •
                  </span>
                  <span>
                    A channel in that server is reserved for AskVigil checks.
                  </span>
                </li>
                <li className="flex gap-2">
                  <span aria-hidden className="mt-0.5">
                    •
                  </span>
                  <span>
                    Click Continue to open the official link in your browser and
                    finish authorization on Discord.
                  </span>
                </li>
              </ul>
            </section>
          </div>

          <DialogFooter className="mt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              className="h-10 border-0 bg-slate-100 hover:bg-slate-200"
            >
              Cancel
            </Button>
            <Button
              type="button"
              onClick={onSave}
              className="h-10 bg-primary hover:bg-secondary text-primary-foreground font-semibold"
            >
              Continue
              <ExternalLink className="ml-2 h-4 w-4" aria-hidden />
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
