import type { ScamCase } from "@lib/types";

export const mockCases: ScamCase[] = [
  {
    id: "case-1",
    title: "71-year-old victim lost RM527,130 in TikTok part-time job scam",
    summary:
      "A woman in Kuching completed 23 transactions to 16 bank accounts after being promised high commissions from a fake part-time job.",
    scamType: "job-scam",
    platform: "Social Media",
    date: "2025-11-29",
    whatHappened:
      "A 71-year-old woman in Kuching received a fraudulent part-time job offer from an unknown individual via TikTok. She was lured by promises of lucrative commissions and instructed to complete tasks that required bank transfers. She made 23 transactions totalling RM527,130 to 16 different bank accounts, then discovered it was a scam when no promised returns were paid.",
    warningSigns: [
      "Promise of unusually high commission for simple tasks",
      "Repeated transfer requests to multiple personal bank accounts",
      "No verifiable employer identity or official hiring process",
    ],
    lesson:
      "Be cautious of online part-time job offers that promise easy and high returns. Verify job legitimacy through official channels and never transfer money to unknown accounts to unlock commissions.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2496938",
  },
  {
    id: "case-2",
    title: "Trader lost over RM500,000 to fake online job commission tasks",
    summary:
      "A victim was lured by a Facebook contact and pushed to complete app-based buying tasks through 38 transactions.",
    scamType: "job-scam",
    platform: "Social Media",
    date: "2024-12-12",
    whatHappened:
      "A 38-year-old trader in Kuala Terengganu was contacted by a Facebook user and offered a high-commission part-time job. After receiving a small initial payout, he made 38 transactions to 22 bank accounts using savings and credit cards, eventually losing over RM500,000.",
    warningSigns: [
      "Promise of easy commissions with repeated top-ups",
      "Payments sent to many unrelated bank accounts",
      "Task platform not linked to any legitimate employer",
    ],
    lesson:
      "Scam syndicates often pay a small early return to build trust before demanding larger transfers.",
    sourceUrl: "https://www.bernama.com/en/news.php/sports/world/news.php?id=2443416",
  },
  {
    id: "case-3",
    title: "Retired engineer lost RM108,001 in fake scam-recovery offer",
    summary:
      "After already losing money once, the victim was tricked again by a Facebook ad promising fund recovery.",
    scamType: "job-scam",
    platform: "Social Media",
    date: "2026-01-14",
    whatHappened:
      "The victim clicked a Facebook ad and was connected to fake 'recovery agents' via WhatsApp. He paid file-opening and processing charges through 8 online transfers, resulting in an additional loss of RM108,001.",
    warningSigns: [
      "Claims of guaranteed scam recovery",
      "Upfront administrative fees requested",
      "Pressure to pay quickly through personal channels",
    ],
    lesson:
      "Legitimate recovery support does not guarantee returns or demand repeated transfer fees to private accounts.",
    sourceUrl:
      "https://www.thestar.com.my/news/nation/2026/01/14/retired-engineer-loses-over-rm100000-in-scam-recovery-ruse",
  },
  {
    id: "case-4",
    title: "Victim trafficked to Cambodian scam center by trusted contact",
    summary:
      "A businessman was lured abroad by a 'friend' and forced to work in a call-scam operation.",
    scamType: "job-scam",
    platform: "Phone Call",
    date: "2026-01-22",
    whatHappened:
      "A 40-year-old Malaysian businessman accepted an overseas opportunity and was taken to a guarded hostel in Cambodia. He was forced to impersonate officers and collect sensitive personal data from victims in Singapore and Malaysia.",
    warningSigns: [
      "Vague overseas job arrangement without verification",
      "Travel instructions changed at the last minute",
      "No formal employment documentation",
    ],
    lesson:
      "Verify overseas opportunities through official channels and never rely solely on personal referrals for cross-border jobs.",
    sourceUrl:
      "https://www.straitstimes.com/asia/se-asia/malaysian-victim-speaks-of-scam-by-friend-torture-in-cambodia",
  },
  {
    id: "case-5",
    title: "Housewife lost RM223,000 in fake investment-task scheme",
    summary:
      "A non-existent investment model required repeated transfers until bank alerts flagged fraudulent recipient accounts.",
    scamType: "job-scam",
    platform: "Social Media",
    date: "2025-08-22",
    whatHappened:
      "A 51-year-old housewife in Bentong joined what appeared to be an investment and task-earning scheme. She made 12 transfers from her savings, including inherited funds, before the bank warned that recipient accounts were linked to fraud.",
    warningSigns: [
      "Investment and task income model with no licensed entity",
      "Repeated manual transfers to different accounts",
      "No transparent withdrawal process",
    ],
    lesson:
      "Always verify investment licenses and avoid any programme that combines commission tasks with repeated personal-bank transfers.",
    sourceUrl: "https://bernama.com/en/news.php?id=2472976",
  },
  {
    id: "case-6",
    title: "Travellers lost S$24,000 in fake road toll phishing alerts",
    summary:
      "SMS messages about unpaid tolls redirected users to a fake payment portal that harvested bank information.",
    scamType: "phishing",
    platform: "SMS",
    date: "2026-02-20",
    whatHappened:
      "Travellers to Malaysia received SMS toll notices and clicked links to fraudulent portals. Victims entered payment and banking details, leading to total losses of S$24,000.",
    warningSigns: [
      "Urgent unpaid toll notice with embedded link",
      "Unverified payment domain",
      "Request for full banking credentials",
    ],
    lesson:
      "Use only official transport and toll channels; never pay through links received by unsolicited SMS.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2522632",
  },
  {
    id: "case-7",
    title: "PDRM summons phishing campaign targeted Malaysian drivers",
    summary:
      "Scammers impersonated police and threatened legal action unless recipients paid summons via fake websites.",
    scamType: "phishing",
    platform: "SMS",
    date: "2026-02-10",
    whatHappened:
      "Victims received SMS messages impersonating the Royal Malaysia Police, warning of unpaid summonses. Links redirected to fake portals where personal and payment data were stolen.",
    warningSigns: [
      "Threat-based law-enforcement message",
      "Short deadline for payment",
      "Non-official portal URL",
    ],
    lesson:
      "Always verify summonses through official police channels and apps, not third-party links in text messages.",
    sourceUrl:
      "https://www.police.gov.sg/Media-Hub/News/2026/02/20260210_phishing_scams_involving_smses_that_impersonate_royal_malaysia_police",
  },
  {
    id: "case-8",
    title: "Festive season phishing surged with fake E-Duit Raya offers",
    summary:
      "Scammers exploited Ramadan and Aidilfitri by spreading subsidy links through social and messaging platforms.",
    scamType: "phishing",
    platform: "Social Media",
    date: "2026-03-24",
    whatHappened:
      "A 76% spike in phishing activity was recorded during festive periods. Fake subsidy and bonus links were distributed through WhatsApp and social platforms to steal credentials and payment information.",
    warningSigns: [
      "Government aid claims without official channel",
      "Bonus links forwarded in group chats",
      "Form requests for account access data",
    ],
    lesson:
      "Treat festive financial announcements as suspicious unless confirmed on official government or bank websites.",
    sourceUrl:
      "https://www.thestar.com.my/business/business-news/2026/03/24/malaysia-scam-losses-rise-to-rm27bil-in-2025-spike-during-festive-seasons",
  },
  {
    id: "case-9",
    title: "EPF impersonation campaign used fake security audit notices",
    summary:
      "Fraud emails and SMS impersonated EPF officials and pushed users to fake i-Akaun portals.",
    scamType: "phishing",
    platform: "Email",
    date: "2026-02-12",
    whatHappened:
      "Scammers posed as EPF leadership and sent messages claiming identity synchronization was mandatory. Victims entered passwords and OTPs on fake portals, exposing account access and beneficiary settings.",
    warningSigns: [
      "Executive impersonation with urgent compliance request",
      "Link to look-alike EPF login page",
      "Request for password and OTP in one flow",
    ],
    lesson:
      "Public agencies do not request credentials via message links; use official portals directly from bookmarked URLs.",
    sourceUrl: "https://www.kwsp.gov.my/en/corporate/news-highlights/scam-alerts",
  },
  {
    id: "case-10",
    title: "Parcel delivery phishing used fake Pos Malaysia failure notices",
    summary:
      "Victims received messages claiming incomplete addresses and were tricked into entering sensitive payment details.",
    scamType: "phishing",
    platform: "SMS",
    date: "2026-02-02",
    whatHappened:
      "High-volume delivery periods were abused through fake parcel alerts. Users were redirected to counterfeit forms that captured card and account data under delivery-reschedule pretexts.",
    warningSigns: [
      "Unexpected delivery issue notices",
      "Payment request to update address",
      "Unofficial courier web domain",
    ],
    lesson:
      "Track shipments only from official courier apps and never submit financial details through message links.",
    sourceUrl: "https://www.pos.com.my/scam-update",
  },
  {
    id: "case-11",
    title: "DuitNow QR sticker overlays redirected customer payments",
    summary:
      "Scammers replaced merchant QR codes at food stalls and night markets, diverting payments to fraud accounts.",
    scamType: "qr-scam",
    platform: "Social Media",
    date: "2025-01-14",
    whatHappened:
      "Merchants reported lost daily income after customers unknowingly scanned tampered payment QR codes. Funds were transferred into scammer-controlled accounts instead of business wallets.",
    warningSigns: [
      "Physical QR stickers layered over original code",
      "Merchant did not receive payment confirmation",
      "Altered sticker quality and alignment",
    ],
    lesson:
      "Before paying, confirm merchant name in your banking app and check whether QR stickers look replaced or tampered.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2456453",
  },
  {
    id: "case-12",
    title: "Fake Duit Raya QR campaign stole facial biometric data",
    summary:
      "WhatsApp QR links promised subsidy cashouts but redirected victims to pages requesting face scans.",
    scamType: "qr-scam",
    platform: "WhatsApp",
    date: "2025-01-14",
    whatHappened:
      "Users were lured by festive subsidy claims and asked to complete 'verification' by scanning their faces. The flow harvested biometric data for potential account takeover and identity abuse.",
    warningSigns: [
      "Unexpected QR subsidy campaign in chat groups",
      "Face-scan requirement for cash reward",
      "No official government authentication flow",
    ],
    lesson:
      "Never submit biometric verification for rewards from unofficial campaigns shared through messaging apps.",
    sourceUrl: "https://bernama.com/bm/news.php?id=2456454",
  },
  {
    id: "case-13",
    title: "Public charging station QR codes delivered spyware profiles",
    summary:
      "Airport and mall QR stickers promised free Wi-Fi but pushed hidden tracking payloads.",
    scamType: "qr-scam",
    platform: "Social Media",
    date: "2025-01-14",
    whatHappened:
      "Users scanning public QR prompts were redirected to malicious pages that installed tracking profiles. Attackers monitored activity and attempted credential theft for banking and social accounts.",
    warningSigns: [
      "QR prompts at unrelated physical spots",
      "Forced profile or configuration install",
      "Unexpected permission requests",
    ],
    lesson:
      "Do not install profiles or unknown files after scanning QR codes in public areas.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2456453",
  },
  {
    id: "case-14",
    title: "Fake staff ID and QR payment trick caused RM9,000 loss",
    summary:
      "A victim in Sibu was deceived into scanning a QR code that granted fraudulent access to her accounts.",
    scamType: "qr-scam",
    platform: "Phone Call",
    date: "2026-02-20",
    whatHappened:
      "An insurance salesperson accepted an installment offer from a scammer showing a fake staff ID. After scanning the provided QR code, unauthorized transactions rapidly drained her account.",
    warningSigns: [
      "Unverified salesperson identity",
      "QR code used for account authorization",
      "Immediate burst of unauthorized transactions",
    ],
    lesson:
      "Always verify seller identity independently and never scan QR codes for account access or verification.",
    sourceUrl:
      "https://www.thestar.com.my/metro/metro-news/2026/02/20/online-scammer-uses-fake-id-qr-code-to-take-rm9000",
  },
  {
    id: "case-15",
    title: "Physical red packet QR scam led to account takeover attempts",
    summary:
      "Fraudulent festive packets containing QR reward cards redirected users to credential-theft pages.",
    scamType: "qr-scam",
    platform: "Social Media",
    date: "2026-01-28",
    whatHappened:
      "Maybank warned of physical angpao packets distributed in public spaces containing scam QR codes. Scans redirected to fake pages or malicious downloads that exposed account credentials.",
    warningSigns: [
      "Unexpected QR reward cards in public distribution",
      "Prompt to download unknown file",
      "Login request on non-official banking domain",
    ],
    lesson:
      "Treat physical QR reward campaigns as high-risk unless validated through official bank channels.",
    sourceUrl:
      "https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/security_alert/new-scam-alert.page",
  },
  {
    id: "case-16",
    title: "Retired clerk lost RM457,607 after fake MCMC audit call",
    summary:
      "A scam caller coerced the victim to share banking login and OTP/TAC details under a legal-threat narrative.",
    scamType: "otp-scam",
    platform: "Phone Call",
    date: "2026-03-15",
    whatHappened:
      "A 69-year-old victim in Penang was told her number was linked to crimes and that account registration was required for an audit. She shared credentials and OTPs, enabling 11 unauthorized transfers in one afternoon.",
    warningSigns: [
      "Official-impersonation call with legal intimidation",
      "Request for banking credentials and OTP",
      "Urgent instruction to keep call secret",
    ],
    lesson:
      "No regulator or police officer will request your OTP/TAC; end the call and verify through official hotlines.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2538131",
  },
  {
    id: "case-17",
    title: "Medical specialist lost RM529,200 in fake refund verification",
    summary:
      "A scammer posing as bank legal staff asked for OTPs to process a refund and drained the victim account.",
    scamType: "otp-scam",
    platform: "Phone Call",
    date: "2025-12-18",
    whatHappened:
      "The victim was told a previous failed investment could be recovered. During the 'refund verification' process, he provided online banking details and OTP codes, leading to systematic account depletion.",
    warningSigns: [
      "Unexpected refund recovery call",
      "OTP requested for verification",
      "No formal case reference or bank branch process",
    ],
    lesson:
      "Refund processing does not require sharing OTP with callers; verify through official branch or app channels.",
    sourceUrl: "https://bernama.com/en/news.php?id=2508564",
  },
  {
    id: "case-18",
    title: "Fake Aidilfitri bonus SMS used OTP to bypass 2FA",
    summary:
      "Victims entered OTP on fake portals and attackers registered wallets on new devices.",
    scamType: "otp-scam",
    platform: "SMS",
    date: "2026-03-28",
    whatHappened:
      "Scam messages promised government festive bonus and linked to fake portals requesting OTP confirmation. Attackers used OTP to bypass 2FA and steal funds from linked cards and accounts.",
    warningSigns: [
      "Bonus claim via unsolicited SMS",
      "OTP required to unlock aid payment",
      "Unknown domain with government branding",
    ],
    lesson:
      "Do not enter OTP on links from SMS promotions; official aid disbursement channels are publicly verifiable.",
    sourceUrl: "https://bernama.com/en/region/news.php?id=2536979",
  },
  {
    id: "case-19",
    title: "SIM swap syndicate hijacked OTP by fake 5G upgrade calls",
    summary:
      "Victims read out SMS verification codes, unknowingly approving number porting to scammer SIM cards.",
    scamType: "otp-scam",
    platform: "Phone Call",
    date: "2026-02-26",
    whatHappened:
      "Scammers posing as telco support asked users to authorize SIM upgrades. The code shared by victims enabled SIM swap operations, allowing criminals to intercept all future banking OTPs.",
    warningSigns: [
      "Unexpected telco upgrade call",
      "Request to read SMS verification code aloud",
      "Sudden signal loss after code sharing",
    ],
    lesson:
      "Never share telco verification codes over calls; contact your provider through official channels for SIM services.",
    sourceUrl: "https://www.bernama.com/en/news.php?id=2517308",
  },
  {
    id: "case-20",
    title: "Fake PDRM donation SMS harvested OTP through charity pretext",
    summary:
      "A viral fundraising message linked to fake donation pages and captured OTP for banking account takeover.",
    scamType: "otp-scam",
    platform: "SMS",
    date: "2026-03-30",
    whatHappened:
      "Victims received donation requests for a fake police festive event and were asked to verify contribution by OTP. The OTP was used to access banking services fraudulently.",
    warningSigns: [
      "Unofficial charity drive using authority branding",
      "Donation link outside trusted channels",
      "OTP requested for simple donation action",
    ],
    lesson:
      "Confirm charity campaigns directly with official organizations; OTP should never be required to make basic donations.",
    sourceUrl:
      "https://www.bernama.com/en/region/news.php/business/news.php?id=2537634",
  },
];
