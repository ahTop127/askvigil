import { useNavigate, useParams } from "react-router";
import {
  Wallet,
  TrendingUp,
  Briefcase,
  Shield,
  Search,
  MessageCircle,
  AlertTriangle,
  Globe,
  Lock,
  FileWarning,
  ExternalLink,
  Key,
  Phone,
  AlertCircle,
  ShieldAlert,
  Send,
  Banknote,
  QrCode,
  Store,
  Download,
  Link,
  Keyboard,
  EyeOff,
  CreditCard,
  Mail,
  Eye,
  Ban,
  LinkIcon,
  Smartphone,
} from "lucide-react";
import { Button } from "../components/ui/button";
import { Navigation } from "../components/Navigation";
import { BackButton } from "../components/BackButton";
import phoneScamImage from "@/assets/099c23e86c408aa2b5beb8b8d410e4b0d5999520.png";
import job2 from "@/assets/jobscam2.png";
import phishing2 from "@/assets/phishing2.webp";
import otp2 from "@/assets/otpscam2.png";
import qr2 from "@/assets/qrscam2.jpg";
import suslink2 from "@/assets/suslink2.jpg";

const scamDetails: Record<string, {
  title: string;
  icon: React.ElementType;
  description: string;
  heroImage: string;
  howItHappens: {
    subtitle: string;
    steps: string[];
    exampleTitle?: string;
    exampleDescription?: string;
  };
  howToDefend: {
    subtitle: string;
    tips: Array<{
      icon: React.ElementType;
      title: string;
      description: string;
    }>;
  };
}> = {
  "job-scam": {
    title: "What are Job Scams?",
    icon: Briefcase,
    description: "Job scams happen when scammers pretend to offer attractive job opportunities in order to steal money, personal information, or bank details. They often target students, job seekers, and young adults by making the offer seem urgent, easy, and highly rewarding.",
    heroImage: job2,
    howItHappens: {
      subtitle: "Here is how Job Scams unfold.",
      steps: [
        "Scammers post job offers through social media or messaging apps.",
        "The scammer promises high salary, flexible work, or quick hiring with little effort.",
        "The victim is asked to pay an upfront fee for registration, training, processing, or equipment.",
        "In some cases, they ask for bank details, IC copies, or other sensitive information under the guise of 'verification'.",
        "Once the victim sends money or information, the scammer disappears or keeps asking for more.",
      ],
      exampleTitle: "Example of a scammer impersonating a delivery company staff personnel:",
      exampleDescription: "A scammer contacts you on Telegram offering a 'data entry work from home' job earning RM3,000/month. They ask for a RM200 registration fee to 'secure your position'. After payment, they disappear."
    },
    howToDefend: {
      subtitle: "Here is what you can do to protect yourself.",
      tips: [
        {
          icon: CreditCard,
          title: "Avoid jobs that require upfront payment",
          description: "Legitimate employers do not ask for fees before hiring."
        },
        {
          icon: TrendingUp,
          title: "Be cautious of unrealistically high salaries",
          description: "If it sounds too good to be true, it probably is."
        },
        {
          icon: Briefcase,
          title: "Ensure there is a proper hiring process",
          description: "Real jobs involve interviews and formal procedures."
        },
        {
          icon: Shield,
          title: "Do not share personal or banking details early",
          description: "Sensitive information should only be shared with verified employers."
        },
        {
          icon: Search,
          title: "Verify the company through official sources",
          description: "Check websites or trusted job platforms before proceeding."
        },
        {
          icon: MessageCircle,
          title: "Be cautious of unsolicited job messages",
          description: "Scammers often reach out via WhatsApp or Telegram."
        }
      ]
    }
  },
  "phishing": {
    title: "What are Phishing Scams?",
    icon: Mail,
    description: "Phishing scams happen when scammers pretend to be trusted organisations, such as banks, delivery services, or government agencies, to trick users into giving away sensitive information. Their goal is often to steal passwords, banking details, or personal data.",
    heroImage: phishing2,
    howItHappens: {
      subtitle: "Here is how Phishing Scams unfold.",
      steps: [
        "The victim receives an email, SMS, or message that looks official from banks, government, or services.",
        "The message creates urgency, such as warning about account suspension, refund issues, or unpaid invoices.",
        "The victim is told to click a link or open an attachment.",
        "The link leads to a fake website that looks similar to a real one.",
        "The fake site asks you to enter login details, card numbers, or personal information.",
        "Scammers use this stolen information to access your real accounts and steal money.",
      ],
      exampleTitle: "Example of a phishing message:",
      exampleDescription: "You receive an SMS claiming to be from your bank saying your account has been suspended. The message includes a link to 'verify your account'. The link leads to a fake banking website."
    },
    howToDefend: {
      subtitle: "Here is what you can do to protect yourself.",
      tips: [
        {
          icon: AlertTriangle,
          title: "Be cautious of urgent or threatening messages",
          description: "Scammers create panic to force quick actions."
        },
        {
          icon: Globe,
          title: "Check website URLs carefully",
          description: "Look for spelling mistakes or unusual domains."
        },
        {
          icon: Lock,
          title: "Never enter credentials on suspicious sites",
          description: "Fake websites are designed to steal your login details."
        },
        {
          icon: FileWarning,
          title: "Avoid opening unexpected attachments",
          description: "Attachments may contain malware or fake documents."
        },
        {
          icon: MessageCircle,
          title: "Do not trust links from unknown senders",
          description: "Messages from unfamiliar sources are high risk."
        },
        {
          icon: ExternalLink,
          title: "Access websites directly",
          description: "Type the official URL instead of clicking links."
        }
      ]
    }
  },
  "otp-scam": {
    title: "What are OTP Scams?",
    icon: Smartphone,
    description: "OTP or SMS scams happen when scammers try to obtain one-time passwords or verification codes in order to access a victim’s bank account or online services. These scams often rely on impersonation, panic, and confusion.",
    heroImage: otp2,
    howItHappens: {
      subtitle: "Here is how OTP Scams unfold.",
      steps: [
        "Scammer calls or messages while pretending to be from your bank or a trusted service provider.",
        "The victim is told there is a problem with their account, transaction, or identity.",
        "Creates urgency to make the victim act quickly without thinking.",
        "At the same time, the victim receives an OTP or TAC message.",
        "Asks the victim to share the OTP 'to verify their identity' or 'block the transaction'.",
        "Uses the victim's OTP to access their account, authorize transactions, or steal money.",
      ],
      exampleTitle: "Example of an OTP scam call:",
      exampleDescription: "Someone calls claiming to be from your bank, saying someone is trying to withdraw money. They ask you to share the OTP to 'stop the transaction'. In reality, they're using it to steal your money."
    },
    howToDefend: {
      subtitle: "Here is what you can do to protect yourself.",
      tips: [
        {
          icon: Key,
          title: "Never share OTP or TAC codes with anyone, ever.",
          description: "Real banks will never ask for your OTP or security codes."
        },
        {
          icon: Phone,
          title: "Don't respond to calls claiming to be from law enforcement agencies.",
          description: "Hang up and call the official number yourself to verify."
        },
        {
          icon: Shield,
          title: "Never approve unauthorised transactions.",
          description: "Enable additional security features like 2FA on all accounts."
        },
        {
          icon: AlertCircle,
          title: "Watch for unexpected OTP messages",
          description: "They may indicate someone is trying to access your account."
        },
        {
          icon: Banknote,
          title: "Contact your bank immediately",
          description: "Act fast if you suspect suspicious activity."
        }
      ]
    }
  },
  "qr-scam": {
    title: "What are QR Code Scams?",
    icon: QrCode,
    description: "QR code scams, also known as quishing, happen when scammers use fake or tampered QR codes to redirect victims to malicious websites, fake payment pages, or harmful downloads. Because QR codes are widely used for payments and information access, many users scan them without checking carefully.",
    heroImage: qr2,
    howItHappens: {
      subtitle: "Here is how QR Code Scams unfold.",
      steps: [
        "Scammers create or replace legitimate QR codes with malicious ones on parking meters, menus, or flyers.",
        "The victim scans the QR code, expecting to make a payment or access information.",
        "The QR code redirects the victim to a fake website, login page, or app download.",
        "The victim may enter login details, banking details, or download a malicious APK file.",
        "The scammer then uses the stolen information or malware for fraud.",
      ],
      exampleTitle: "Example of a QR code scam:",
      exampleDescription: "You park and scan a QR code on a parking meter payment sticker. Instead of the official site, it takes you to a fake page. The scammers placed their own sticker over the real one."
    },
    howToDefend: {
      subtitle: "Here is what you can do to protect yourself.",
      tips: [
        {
          icon: Eye,
          title: "Only scan QR codes from trusted sources.",
          description: "Check if QR codes look tampered with or have stickers over them."
        },
        {
          icon: Store,
          title: "Confirm merchant details before paying",
          description: "Ensure the name matches the real business."
        },
        {
          icon: AlertCircle,
          title: "Be cautious of login pages after scanning",
          description: "QR codes should not lead to suspicious login requests."
        },
        {
          icon: Download,
          title: "Avoid downloading apps via QR codes",
          description: "Only install apps from official app stores."
        },
        {
          icon: Shield,
          title: "Use trusted payment methods",
          description: "Stick to official apps and secure channels."
        }
      ]
    }
  },
  "suspicious-link": {
    title: "What are Suspicious Links?",
    icon: LinkIcon,
    description: "Suspicious URL scams involve links that are designed to look legitimate but actually lead to fake or harmful websites. These websites may steal login credentials, banking information, or install malware.",
    heroImage: suslink2,
    howItHappens: {
      subtitle: "Here is how Suspicious Link Scams unfold.",
      steps: [
        "Scammers send messages containing disguised or shortened URLs via SMS, email, or social media.",
        "Links may mimic legitimate websites with slight spelling changes (e.g., 'poslaju-my.com' vs 'poslaju.com.my').",
        "Clicking the link takes the victim to a fake login or payment page that captures their information.",
        "The victim enters personal details, login credentials, or payment information.",
        "The scammer captures the information and may use it for fraud and identity theft or even install malware.",
      ],
      exampleTitle: "Example of a suspicious link scam:",
      exampleDescription: "You receive an SMS claiming your package couldn't be delivered, with a link to 'reschedule'. After clicking and entering details, the scammers now have your personal and payment information."
    },
    howToDefend: {
      subtitle: "Here is what you can do to protect yourself.",
      tips: [
        {
          icon: AlertTriangle,
          title: "Avoid clicking unknown links",
          description: "Links from unfamiliar sources are risky."
        },
        {
          icon: Eye,
          title: "Check for misspelled or unusual URLs",
          description: "Scammers often mimic real websites with slight changes."
        },
        {
          icon: Keyboard,
          title: "Type official addresses directly.",
          description: "Go to websites by typing the URL yourself, not clicking links."
        },
        {
          icon: EyeOff,
          title: "Be cautious of shortened links",
          description: "They may hide the real destination."
        }
      ]
    }
  },
};

export default function LearningDetailPage() {
  const navigate = useNavigate();
  const { scamType } = useParams<{ scamType: string }>();

  const data = scamType ? scamDetails[scamType] : null;

  if (!data) {
    return (
      <div className="min-h-screen bg-[#FFFEFB]">
        <Navigation />
        <main className="max-w-4xl mx-auto px-4 py-12">
          <p className="text-center text-gray-600">Scam type not found</p>
        </main>
      </div>
    );
  }

  const Icon = data.icon;

  return (
    <div className="min-h-screen bg-[#FFFEFB]">
      {/* Navigation */}
      <Navigation />
      
      {/* Back Button */}
      <BackButton />

      {/* Hero Section */}
      <section className="bg-[#669E84]/15 py-16 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            {/* Left: Icon/Image */}
            <div className="flex justify-center">
              <div className="w-full h-full flex items-center justify-center">
                <img 
                  src={data.heroImage}
                  alt={data.title}
                  className="w-full h-full object-cover drop-shadow-2xl"
                />
              </div>
            </div>

            {/* Right: Title and Description */}
            <div>
              <h1 className="text-5xl md:text-6xl font-bold text-[#669E84] mb-6 leading-tight">
                {data.title}
              </h1>
              <p className="text-xl text-gray-700 leading-relaxed">
                {data.description}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How Does It Happen Section */}
      <section className="py-20 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          {/* Section Title */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-[#669E84] mb-4">
              How Does It Happen?
            </h2>
            <p className="text-lg text-gray-600">
              {data.howItHappens.subtitle}
            </p>
          </div>

          {/* Content Grid */}
          <div className="grid md:grid-cols-2 gap-8">
            {/* Left: Example Card */}
            <div className="bg-[#669E84]/10 rounded-3xl p-8 border-2 border-[#669E84]/20 shadow-lg">
              <div className="mb-4">
                <p className="text-sm font-semibold text-[#669E84] mb-6">
                  {data.howItHappens.exampleTitle || "Example scenario:"}
                </p>
                <p className="text-gray-700 leading-relaxed">
                  {data.howItHappens.exampleDescription}
                </p>
              </div>
              
              {/* Decorative phone/device illustration placeholder */}
              <div className="mt-8 bg-[#669E84]/20 rounded-2xl p-6 text-center">
                <Icon className="w-16 h-16 text-[#669E84] mx-auto mb-3" />
                <p className="text-sm text-gray-600 italic">
                  Be vigilant and verify before taking action
                </p>
              </div>
            </div>

            {/* Right: Steps List */}
            <div className="space-y-4">
              {data.howItHappens.steps.map((step, index) => (
                <div 
                  key={index}
                  className="bg-[#669E84]/10 rounded-2xl p-6 border border-[#669E84]/20 flex gap-4 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-[#669E84] text-white rounded-full flex items-center justify-center font-bold text-lg shadow-md">
                      {index + 1}
                    </div>
                  </div>
                  <p className="text-gray-800 leading-relaxed pt-1">
                    {step}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* How to Defend Section */}
      <section className="py-20 px-4 bg-[#FFFEFB]">
        <div className="max-w-6xl mx-auto">
          {/* Section Title */}
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold text-[#669E84] mb-4">
              How to Defend
            </h2>
            <p className="text-lg text-gray-600">
              {data.howToDefend.subtitle}
            </p>
          </div>

          {/* Tips Grid */}
          <div className="grid md:grid-cols-2 gap-6">
            {data.howToDefend.tips.map((tip, index) => {
              const TipIcon = tip.icon;
              return (
                <div 
                  key={index}
                  className="bg-[#669E84]/10 rounded-2xl p-8 border border-[#669E84]/20 shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-12 h-12 bg-[#669E84] rounded-full flex items-center justify-center shadow-md">
                        <TipIcon className="w-6 h-6 text-white" />
                      </div>
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-900 mb-2 text-lg">
                        {tip.title}
                      </h3>
                      <p className="text-gray-700 leading-relaxed">
                        {tip.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Bottom CTA Section */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-4xl mx-auto">
          <div className="bg-[#669E84]/15 rounded-3xl p-12 text-center border-2 border-[#669E84]/30 shadow-xl">
            <Shield className="w-16 h-16 text-[#669E84] mx-auto mb-6" />
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Stay Protected
            </h2>
            <p className="text-lg text-gray-700 mb-8 max-w-2xl mx-auto">
              Practice your scam detection skills or get immediate guidance if you've been targeted.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                onClick={() => navigate("/practice")} 
                className="bg-[#669E84] hover:bg-[#54A388] text-white border-0 h-14 px-8 text-lg font-semibold shadow-lg"
              >
                Practice Detection
              </Button>
              <Button 
                onClick={() => navigate("/guidance")} 
                className="bg-white hover:bg-gray-50 text-[#669E84] border-2 border-[#669E84] h-14 px-8 text-lg font-semibold"
              >
                Get Guidance
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}