import {
  Briefcase,
  Link as LinkIcon,
  Mail,
  QrCode,
  Smartphone,
} from "lucide-react";
import type { ScamType } from "@lib/types";
import job1 from "@assets/jobscam1.png";
import job2 from "@assets/jobscam2.png";
import phishing1 from "@assets/phishing1.webp";
import phishing2 from "@assets/phishing2.webp";
import otp1 from "@assets/otpscam1.jpg";
import otp2 from "@assets/otpscam2.png";
import qr1 from "@assets/qrscam1.jpg";
import qr2 from "@assets/qrscam2.jpg";
import suslink1 from "@assets/suslink1.jpg";
import suslink2 from "@assets/suslink2.jpg";

/**
 * Canonical scam categories for Guidance + Learning pages.
 * Each entry shares identity fields; `guidance` vs `learning` hold page-specific copy and art.
 */
export const scamTypes: ScamType[] = [
  {
    id: "job-scam",
    title: "Job Scams",
    shortTitle: "Job",
    icon: Briefcase,
    guidance: {
      description:
        "Fake job offers asking for upfront payment or personal details. Learn what to do if you've been targeted.",
      image:
        job1,
      bgColor: "from-[#EAA866] to-[#D89654]",
      imageClass: "scale-100",
    },
    learning: {
      description:
        "Calls from imposters pretending to be authorities threatening you to make payment.",
      image:
        job2,
      bgColor: "from-[#75AB93] to-[#669E84]",
    },
  },
  {
    id: "phishing",
    title: "Phishing Scams",
    shortTitle: "Phishing",
    icon: Mail,
    guidance: {
      description:
        "Fake messages pretending to be from legitimate organizations. Get immediate help to secure your accounts.",
      image:
        phishing1,
      bgColor: "from-[#D89654] to-[#C68442]",
    },
    learning: {
      description:
        "Fake messages impersonating legitimate organizations to steal your personal data.",
      image:
        phishing2,
      bgColor: "from-[#669E84] to-[#5A8B75]",
    },
  },
  {
    id: "otp-scam",
    title: "OTP Scams",
    shortTitle: "OTP",
    icon: Smartphone,
    guidance: {
      description:
        "Scammers trying to steal your one-time passwords. Take action now to protect your accounts.",
      image:
        otp1,
      bgColor: "from-[#EAA866] to-[#EAA866]",
    },
    learning: {
      description:
        "Scammers trick you into revealing your one-time passwords and verification codes.",
      image:
        otp2,
      bgColor: "from-[#669E84] to-[#669E84]",
    },
  },
  {
    id: "qr-scam",
    title: "QR Code Scams",
    shortTitle: "QR Code",
    icon: QrCode,
    guidance: {
      description:
        "Malicious QR codes leading to fake sites or installing malware. Learn how to minimize the damage.",
      image:
        qr1,
      bgColor: "from-[#EAA866] to-[#D89654]",
    },
    learning: {
      description:
        "Malicious QR codes that lead to fake websites or install harmful apps on your device.",
      image:
        qr2,
      bgColor: "from-[#75AB93] to-[#669E84]",
    },
  },
  {
    id: "suspicious-link",
    title: "Suspicious Links",
    shortTitle: "Links",
    icon: LinkIcon,
    guidance: {
      description:
        "Harmful URLs designed to steal data or spread malware. Find out what steps to take next.",
      image:
        suslink1,
      bgColor: "from-[#D89654] to-[#C68442]",
    },
    learning: {
      description:
        "Harmful URLs designed to steal your information or infect your device with malware.",
      image:
        suslink2,
      bgColor: "from-[#669E84] to-[#5A8B75]",
    },
  },
];
