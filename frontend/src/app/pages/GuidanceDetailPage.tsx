import { useNavigate, useParams } from "react-router";
import { ArrowLeft, CheckCircle, Briefcase, Mail, Smartphone } from "lucide-react";
import { Button } from "../components/ui/button";
import { Navigation } from "../components/Navigation";
import { BackButton } from "../components/BackButton";



function renderTextWithLinks(text: string) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;

  const parts = text.split(urlRegex);

  return parts.map((part, index) => {
    if (urlRegex.test(part)) {
      // remove trailing punctuation like ., ) , !
      const cleanUrl = part.replace(/[.,!?)]*$/, "");

      // get the trailing punctuation (if any)
      const trailing = part.slice(cleanUrl.length);

      return (
        <span key={index}>
          <a
            href={cleanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="underline text-blue-600 hover:text-blue-800"
          >
            {cleanUrl}
          </a>
          {trailing}
        </span>
      );
    }
    return <span key={index}>{part}</span>;
  });
}

const scamData: Record<string, {
  title: string;
  icon: React.ElementType;
  steps: {
  title: string;
  description: string;
  bullets?: { label?: string; text: string }[];
  }[]
}> = {
  "job-scam": {
    title: "Job Scam",
    icon: Briefcase,
    steps: [
      {
        title: "Immediate disengagement",
        description: "Do not reply or send more documents, payments, or personal info.",
      },
      {
        title: "Save Evidence",
        description: "Keep screenshots of chats, job ads, payment receipts, phone numbers, and account numbers of the scammer.",
      },
      {
        title: "Contact your bank / NSRC",
        description: "If you paid a processing fee, deposit, or transfer:",
        bullets: [
          {
            label: "Single Bank Transaction",
            text: "Call your bank immediately to try to block or reverse the transaction."
          },
          {
            label: "Multiple Banks Involved",
            text: "Call NSRC at 997 and provide evidence for rapid multi-bank action."
          }
        ]
      },
      {
        title: "File a police report to Polis Diraja Malaysia (PDRM)",
        description: "If money was lost or sensitive data was shared with the scammer:",
        bullets: [
          {
            text: "Submit an online report via https://ereporting.rmp.gov.my.",
          },
          {
            text: "Visit the nearest police station with your evidence."
          }
        ]
      },
      {
        title: "Report to Cyber999 for Technical Reporting",
        description: "Submit a report via https://www.mycert.org.my or call 1-300-88-2999. This helps authorities identify and take down malicious websites, phishing pages, and scam-related links.",
      },
    ],
  },
  "phishing": {
    title: "Phishing",
    icon: Mail,
    steps: [
      {
        title: "Immediate disengagement",
        description: "Stop interacting with the message, website, or attachment immediately.",
      },
      {
        title: "Secure your accounts",
        description: "Change passwords immediately, especially email, banking, and any reused passwords and enable two-factor authentication (2FA).",
      },
      {
        title: "Check Account Activity",
        description: "Review account activity for any suspicious logins or transactions.",
      },
      {
        title: "Save Evidence",
        description: "Keep screenshots of chats, payment receipts, phone numbers, and account numbers of the scammer.",
      },
      {
        title: "Contact your bank / NSRC",
        description: "If banking credentials, card details, or payment details were entered to any phishing websites:",
        bullets: [
          {
            label: "Single Bank Transaction",
            text: "Call your bank immediately to try to block or reverse the transaction."
          },
          {
            label: "Multiple Banks Involved",
            text: "Call NSRC at 997 and provide evidence for rapid multi-bank action."
          }
        ]
      },
      {
        title: "File a police report to Polis Diraja Malaysia (PDRM)",
        description: "If the phishing caused financial loss, account takeover or identity misuse:",
        bullets: [
          {
            text: "Submit an online report via https://ereporting.rmp.gov.my.",
          },
          {
            text: "Visit the nearest police station with your evidence."
          }
        ]
      },
      {
        title: "Report to Cyber999 for Technical Reporting",
        description: "Submit a report via https://www.mycert.org.my or call 1-300-88-2999. This helps authorities identify and take down malicious websites, phishing pages, and scam-related links.",
      },
    ],
  },
  "otp-scam": {
    title: "One Time Password (OTP) Scams",
    icon: Smartphone,
    steps: [
      {
        title: "Treat it as Urgent",
        description: "The scammer might already be trying to use your accounts.",
      },
      {
        title: "Secure your accounts",
        description: "",
        bullets: [
          {
            text: "Change your passwords immediately, prioritise banking, email and any linked accounts and enable two-factor authentication (2FA).",
          },
          {
            text: "Try to log out all active sessions.(if possible)"
          }
        ]
      },
      {
        title: "Check Account Activity",
        description: "Review account activity for any suspicious logins or transactions.",
      },
      {
        title: "Save Evidence",
        description: "Keep screenshots of chats, payment receipts, phone numbers, and account numbers of the scammer.",
      },
      {
        title: "Contact your bank / NSRC",
        description: "If you gave away your OTP for your bank account:",
        bullets: [
          {
            label: "Single Bank Transaction",
            text: "Call your bank immediately to try to block or reverse the transaction."
          },
          {
            label: "Multiple Banks Involved",
            text: "Call NSRC at 997 and provide evidence for rapid multi-bank action."
          }
        ]
      },
      {
        title: "File a police report to Polis Diraja Malaysia (PDRM)",
        description: "If the OTP scam caused financial loss, account takeover or identity misuse:",
        bullets: [
          {
            text: "Submit an online report via https://ereporting.rmp.gov.my.",
          },
          {
            text: "Visit the nearest police station with your evidence."
          }
        ]
      },      
      {
        title: "Report to Cyber999 for Technical Reporting",
        description: "Submit a report via https://www.mycert.org.my or call 1-300-88-2999. This helps authorities identify and take down malicious websites, phishing pages, and scam-related links.",
      },
    ],
  },
  "qr-scam": {
    title: "QR Scam",
    icon: Mail,
    steps: [
      {
        title: "Immediate disengagement",
        description: "Stop interacting with the QR code immediately.",
      },
      {
        title: "Identify what the QR code did",
        description: "Review whether the QR code opened a website, triggered a payment, or installed an app.",
      },
      {
        title: "Check device for malware",
        description: "Run a malware or antivirus scan to detect any harmful apps or software and remove it immediately.",
      },
      {
        title: "Save evidence",
        description: "Keep screenshots of chats, the QR code, payment receipts, phone numbers, and account numbers of the scammer.",
      },
      {
        title: "Contact your bank / NSRC",
        description: "If banking credentials, card details, or payment details were entered after scanning the QR or unauthorised bank transactions were made:",
        bullets: [
          {
            label: "Single Bank Transaction",
            text: "Call your bank immediately to try to block or reverse the transaction."
          },
          {
            label: "Multiple Banks Involved",
            text: "Call NSRC at 997 and provide evidence for rapid multi-bank action."
          }
        ]
      },
      {
        title: "File a police report to Polis Diraja Malaysia (PDRM)",
        description: "If the OTP scam caused financial loss, account takeover or identity misuse:",
        bullets: [
          {
            text: "Submit an online report via https://ereporting.rmp.gov.my.",
          },
          {
            text: "Visit the nearest police station with your evidence."
          }
        ]
      },
      {
        title: "Report to Cyber999 for Technical Reporting",
        description: "Submit a report via https://www.mycert.org.my or call 1-300-88-2999. This helps authorities identify and take down malicious websites, phishing pages, and scam-related links.",
      },  
    ],
  },
  "suspicious-link": {
    title: "Suspicious Link",
    icon: Mail,
    steps: [
      {
        title: "Immediate disengagement",
        description: "Do not click the link again, open any attachments, or continue interacting with the message sender.",
      },
      {
        title: "Secure your accounts",
        description: "Change passwords immediately, especially email, banking, and any reused passwords and enable two-factor authentication (2FA).",
      },
      {
        title: "Check account activity",
        description: "Review account activity for any suspicious logins or transactions.",
      },
      {
        title: "Check your device",
        description: "Run a malware or antivirus to scan if the link downloaded anything to your device and remove it.",
      },
      {
        title: "Save evidence",
        description: "Keep screenshots of the message, the suspicious URL, sender details, website pages, and any transaction or login attempt related to the scam.",
      },
            {
        title: "Contact your bank / NSRC",
        description: "If money was lost or sensitive data was shared in the suspicious link:",
        bullets: [
          {
            label: "Single Bank Transaction",
            text: "Call your bank immediately to try to block or reverse the transaction."
          },
          {
            label: "Multiple Banks Involved",
            text: "Call NSRC at 997 and provide evidence for rapid multi-bank action."
          }
        ]
      },
      {
        title: "File a police report to Polis Diraja Malaysia (PDRM)",
        description: "If the OTP scam caused financial loss, account takeover or identity misuse:",
        bullets: [
          {
            text: "Submit an online report via https://ereporting.rmp.gov.my.",
          },
          {
            text: "Visit the nearest police station with your evidence."
          }
        ]
      },
      {
        title: "Report to Cyber999 for Technical Reporting",
        description: "Submit a report via https://www.mycert.org.my or call 1-300-88-2999. This helps authorities identify and take down malicious websites, phishing pages, and scam-related links.",
      }, 
    ],
  },
};

export default function GuidanceDetailPage() {
  const navigate = useNavigate();
  const { scamType } = useParams<{ scamType: string }>();

  const data = scamType ? scamData[scamType] : null;

  if (!data) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-4xl mx-auto px-4 py-12">
          <p className="text-center text-gray-600">Scam type not found</p>
        </main>
      </div>
    );
  }

  const Icon = data.icon;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <Navigation />
      
      {/* Back Button */}
      <BackButton />

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 py-12">
        {/* Title Section */}
        <div className="text-center mb-12">
          <div className="w-20 h-20 bg-gradient-to-br from-[#FFA00E] to-[#E0AB71] rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-lg">
            <Icon className="w-10 h-10 text-white" />
          </div>
          <h1 className="text-4xl font-bold text-[#213034] mb-3">
            {data.title}
          </h1>
          <p className="text-lg text-gray-600">
            Follow these steps to protect yourself
          </p>
        </div>

        {/* Steps */}
        <div className="bg-white rounded-2xl shadow-sm border-2 border-gray-200 p-8 mb-8">
          <div className="space-y-8">
            {data.steps.map((step, index) => (
              <div key={index} className="flex gap-4">
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-[#FFA00E] text-white rounded-full flex items-center justify-center font-semibold shadow-md">
                    {index + 1}
                  </div>
                </div>
                <div className="flex-1 pt-1">
                  <h3 className="font-semibold text-[#213034] mb-2 text-lg">
                    {step.title}
                  </h3>
                  <div className="text-gray-600 leading-relaxed">
                    <p>{renderTextWithLinks(step.description)}</p>
                    {step.bullets && (
                      <ul className="mt-3 list-disc pl-5 space-y-2">
                        {step.bullets.map((item, i) => (
                          <li key={i}>
                            {item.label && (
                              <span className="font-semibold text-[#213034]">
                                {item.label}:
                              </span>
                            )}{" "}                  
                            {renderTextWithLinks(item.text)}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Emergency Contact */}
        <div className="bg-red-50 border-2 border-red-200 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-[#213034] mb-1">
                Need Immediate Help?
              </h3>
              <p className="text-sm text-gray-600 mb-3">
                Contact the National Scam Response Centre (NSRC) at 997 or your bank's hotline immediately.
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="grid md:grid-cols-2 gap-4">
          <Button 
            onClick={() => navigate("/learning")} 
            variant="outline" 
            className="h-12 border-2 border-[#54A388] text-[#54A388] hover:bg-[#54A388] hover:text-white"
          >
            Learn More About Scams
          </Button>
          <Button 
            onClick={() => navigate("/")} 
            className="h-12 bg-[#FFA00E] hover:bg-[#E09A0D] text-white border-0"
          >
            Check Another Message
          </Button>
        </div>
      </main>
    </div>
  );
}