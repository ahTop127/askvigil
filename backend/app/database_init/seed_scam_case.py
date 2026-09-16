from __future__ import annotations

import asyncio
import logging
import os
import sys

from dotenv import load_dotenv
from tortoise import Tortoise

logger = logging.getLogger(__name__)

current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.append(project_root)

# 2. Dynamically load environment variables (must be loaded before importing core.database!)
# Read the system environment variable APP_ENV. If it is not set, it defaults to fallback to 'dev'.
app_env = os.getenv("ENVIRONMENT", "dev")
env_filename = f".env.{app_env}"
env_path = os.path.join(project_root, env_filename)

if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    logger.exception(
        f" Warning: The environment variable file {env_path} cannot be found. The system will attempt to rely on the existing system environment variables."
    )

from datetime import date

from app.core.database import TORTOISE_ORM
from app.models.scam_case import ScamCase

STATIC_SCAM_CASES = [
    # --- Job Scams ---
    {
        "title": "Elderly Woman Falls Victim To Online Part-time Job Offer, Loses Over RM500,000",
        "content": 'A 71-year-old woman in Kuching lost RM527,130 after falling for a fraudulent part-time job offer sent by an unknown individual on TikTok. Lured by the promise of lucrative commissions, she completed "tasks" that required her to make 23 separate transactions to 16 different bank accounts. She only realized it was a scam when the promised returns never materialized. Kuching police revealed that 49 similar cases have been investigated since the start of the year, with total losses reaching RM2.26 million.',
        "scam_type": "JOB_SCAM",
        "platform": "tiktok",
        "news_date": date(2025, 12, 19),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2496938",
    },
    {
        "title": "Trader Loses Over RM500,000 To Online Job Scam",
        "content": 'A 38-year-old trader in Kuala Terengganu lost over RM500,000 after being contacted by a Facebook user named "Nabila Puteri." He was lured by a part-time job offering high commissions. To "earn," he was instructed to buy items through a suspicious app. After an initial small commission was paid to gain his trust, he performed 38 more transactions to 22 different bank accounts using his life savings and credit cards.',
        "scam_type": "JOB_SCAM",
        "platform": "facebook",
        "news_date": date(2025, 5, 14),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php/sports/world/news.php?id=2443416",
    },
    {
        "title": "Retired Engineer Loses Over RM100,000 In Scam Recovery Ruse",
        "content": 'In a double-blow case, a retired engineer who had previously lost money to a scam fell for a second scam on Facebook. He clicked an ad promising to "recover lost scam money." The "recovery agents" on WhatsApp convinced him to pay "file opening fees" and "processing charges," leading to an additional loss of RM108,001 via 8 online transfers.',
        "scam_type": "JOB_SCAM",
        "platform": "facebook",
        "news_date": date(2026, 1, 14),
        "source": "The Star",
        "url_link": "https://www.thestar.com.my/news/nation/2026/01/14/retired-engineer-loses-over-rm100000-in-scam-recovery-ruse",
    },
    {
        "title": "Malaysian victim speaks of scam by 'friend', torture in Cambodia",
        "content": 'A 40-year-old businessman who escaped a job syndicate in Cambodia shared his ordeal. He was lured by a "friend" to Bangkok but was instead taken to a guarded hostel in Cambodia. He was forced to work for a scam center, calling people in Singapore and Malaysia to steal their IC numbers under the guise of being "cybersecurity officers."',
        "scam_type": "JOB_SCAM",
        "platform": "facebook",
        "news_date": date(2025, 12, 4),
        "source": "The Straits Times",
        "url_link": "https://www.straitstimes.com/asia/se-asia/malaysian-victim-speaks-of-scam-by-friend-torture-in-cambodia",
    },
    {
        "title": "Housewife Loses RM223,000 To Investment Scam",
        "content": 'A 51-year-old housewife in Bentong was lured into a "non-existent investment scheme" that functioned like a part-time job. She made 12 transactions from her personal savings (including money left by her late husband) to seven different bank accounts before the bank alerted her that the recipients were flagged for fraud.',
        "scam_type": "JOB_SCAM",
        "platform": "phone_call",
        "news_date": date(2025, 9, 30),
        "source": "Bernama",
        "url_link": "https://bernama.com/en/news.php?id=2472976",
    },
    # --- Phishing Scams ---
    {
        "title": "Singapore Travellers To Malaysia Lose S$24,000 In Phishing Scams",
        "content": "Scammers sent SMS alerts to Malaysian and Singaporean travelers claiming unpaid road tolls. Victims clicked a link to a fake portal, entered their bank details, and lost a combined $24,000 (approx. RM80,000).",
        "scam_type": "phishing",
        "platform": "whatsapp",
        "news_date": date(2026, 2, 11),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2522632",
    },
    {
        "title": "Phishing Scams Impersonating RMP",
        "content": 'A widespread phishing campaign targeted Malaysian drivers by sending SMS alerts impersonating the Royal Malaysia Police (PDRM). The message claimed the recipient had "unpaid traffic summons" that would lead to legal action if not settled immediately.',
        "scam_type": "phishing",
        "platform": "whatsapp",
        "news_date": date(2026, 1, 10),
        "source": "Bernama / Singapore Police Force (Regional Alert)",
        "url_link": "https://www.police.gov.sg/Media-Hub/News/2026/02/20260210_phishing_scams_involving_smses_that_impersonate_royal_malaysia_police",
    },
    {
        "title": "Malaysia scam losses rise to RM2.7bil in 2025, spike during festive seasons",
        "content": "During the 2026 Ramadan and Aidilfitri season, phishing activity spiked by 76%. Scammers distributed links via social media and WhatsApp promising “Government E-Duit Raya” subsidies or festive bonuses.",
        "scam_type": "phishing",
        "platform": "whatsapp",
        "news_date": date(2026, 3, 24),
        "source": "The Star",
        "url_link": "https://www.thestar.com.my/business/business-news/2026/03/24/malaysia-scam-losses-rise-to-rm27bil-in-2025-spike-during-festive-seasons",
    },
    {
        "title": "Beware! Impersonation Of The CEO Of EPF (Feb 12, 2026)",
        "content": 'Scammers impersonated high-ranking Employees Provident Fund (EPF/KWSP) officials, including the CEO, by sending fraudulent emails and SMS claiming that a "security audit" or "identity synchronization" was mandatory to prevent i-Akaun suspension. Victims were lured into clicking a link to a fake EPF portal, where they unknowingly handed over their passwords and OTPs, allowing scammers to take control of their retirement savings data to change beneficiary details or attempt unauthorized withdrawals.',
        "scam_type": "phishing",
        "platform": "whatsapp",
        "news_date": date(2025, 2, 24),
        "source": "KWSP Official",
        "url_link": "https://www.kwsp.gov.my/en/corporate/news-highlights/scam-alerts",
    },
    {
        "title": "Be cautious of SCAMS involving Pos Malaysia!",
        "content": "Exploiting the high volume of online shopping, scammers sent SMS alerts claiming to be from Pos Malaysia. The message stated that a parcel could not be delivered due to an “incomplete address” or “missing house number”.",
        "scam_type": "phishing",
        "platform": "whatsapp",
        "news_date": date(2025, 1, 9),
        "source": "https://www.pos.com.my/scam-update",
        "url_link": "",
    },
    # --- QR Code Scams ---
    {
        "title": "QR Code Manipulation: Scammers' New Tactic To Steal Users' Data",
        "content": "Scammers targeted local food stalls and night markets by pasting their own fraudulent DuitNow QR stickers over the merchants' original payment codes. Customers who scanned these manipulated codes to pay for their meals unknowingly transferred their money directly into the scammers' bank accounts rather than to the vendors. PDRM issued a nationwide alert after dozens of merchants in Kuala Lumpur reported a sudden loss of daily earnings due to these physical QR overlays.",
        "scam_type": "qr_code_scam",
        "platform": "phone_message",
        "news_date": date(2025, 1, 9),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2456453",
    },
    {
        "title": "Manipulasi Kod QR Taktik Scammer Perangkap Pengguna",
        "content": 'Exploiting the digital "Duit Raya" trend, scammers shared QR codes on WhatsApp promising a government-funded Aidilfitri subsidy of RM500. The scan led to a site that requested a "face scan" or biometric verification to unlock the funds, which was actually a tactic to steal the victim\'s facial data and bypass banking security features. This case highlighted a new level of "Quishing" where scammers use QR codes to harvest biometric data for identity theft.',
        "scam_type": "qr_code_scam",
        "platform": "whatsapp",
        "news_date": date(2025, 8, 14),
        "source": "Bernama",
        "url_link": "https://bernama.com/bm/news.php?id=2456454",
    },
    {
        "title": "Careless QR Scanning Leads to Data Leaks and Financial Loss",
        "content": 'At several Malaysian airports and malls, scammers placed QR code stickers on public charging stations promising "Free High-Speed Wi-Fi" for users who scanned them. Instead of providing internet access, the QR code redirected the browser to a page that forced the installation of a hidden "tracking profile" or spyware on the device. This allowed scammers to monitor the victim\'s keystrokes and steal login credentials for social media and banking apps in real-time.',
        "scam_type": "qr_code_scam",
        "platform": "whatsapp",
        "news_date": date(2025, 8, 14),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2456453",
    },
    {
        "title": "Online scammer uses fake ID, QR code to take RM9,000",
        "content": "An insurance salesperson in Sibu lost nearly RM9,000 after being lured by a scammer offering a fake installment plan for a prize purchase. To gain her trust, the suspect used a fake employee ID card. The victim was then deceived into scanning a QR code that allowed the suspect to gain illegal access to her accounts. Once scanned, her savings were quickly drained through a series of rapid unauthorized transactions.",
        "scam_type": "qr_code_scam",
        "platform": "whatsapp",
        "news_date": date(2026, 2, 20),
        "source": "The Star",
        "url_link": "https://www.thestar.com.my/metro/metro-news/2026/02/20/online-scammer-uses-fake-id-qr-code-to-take-rm9000",
    },
    {
        "title": "New Scam Alert: Physical Red Packets with Fraudulent QR Codes",
        "content": 'During the 2026 festive season, Maybank issued an emergency alert regarding physical "Lucky Packets" (Angpao) being distributed in public areas and mailboxes. These packets contained cards with QR codes promising "free lucky money" or "festive rewards." Scanning the code directed victims to a fake website that harvested banking credentials or prompted the download of malicious files, resulting in account takeovers.',
        "scam_type": "qr_code_scam",
        "platform": "phone_message",
        "news_date": date(2026, 2, 20),
        "source": "Maybank2u",
        "url_link": "https://www.maybank2u.com.my/maybank2u/malaysia/en/personal/security_alert/new-scam-alert.page",
    },
    # --- OTP / SMS Scams ---
    {
        "title": "Two Company Directors In Penang Lose Nearly RM900,000 To Phone Scams",
        "content": 'A 69-year-old retired clerk in Penang lost RM457,607 after receiving a call from a scammer impersonating an officer from the Malaysian Communications and Multimedia Commission (MCMC). The victim was told her phone number was involved in illegal activities and was coerced into "registering" her bank account for an audit by providing her online banking credentials and multiple OTP/TAC codes. These codes allowed the scammers to gain full control of her account and perform 11 unauthorized transfers within a single afternoon.',
        "scam_type": "otp_scam",
        "platform": "whatsapp",
        "news_date": date(2026, 3, 27),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2538131",
    },
    {
        "title": "Medical Specialist Loses RM529,200 To Non-Existent Investment Scam",
        "content": 'A medical specialist in his 50s lost RM529,200 after being contacted by a scammer posing as a "legal assistant" from a reputable bank. The scammer claimed to be helping the specialist recover funds lost in a previous failed investment. To "verify the refund process," the victim was asked to provide his banking username and the OTP codes that arrived on his phone; instead of receiving a refund, his remaining life savings were systematically drained.',
        "scam_type": "otp_scam",
        "platform": "tiktok",
        "news_date": date(2026, 1, 3),
        "source": "Bernama",
        "url_link": "https://bernama.com/en/news.php?id=2508564",
    },
    {
        "title": "Three Malaysians Detained In Online Scam, 46 Sim Cards Seized",
        "content": 'PDRM arrested three individuals for a "SIM Swap" syndicate that targeted users of major Malaysian telcos like Maxis and Celcom. Scammers called victims pretending to be technical support, claiming their 4G SIM cards needed a "5G upgrade" to avoid service disruption. They asked the victims to read out a verification code sent via SMS; this code was actually the authorization to port the phone number to a new SIM card, allowing the scammers to intercept all future banking OTPs.',
        "scam_type": "otp_scam",
        "platform": "whatsapp",
        "news_date": date(2026, 1, 27),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/news.php?id=2517308",
    },
    {
        "title": "Selangor Police Deny Raya Fundraising Event, Confirm Scam Attempt",
        "content": 'Selangor police warned the public about a viral SMS soliciting donations for a fake "PDRM Hari Raya Event." The message asked people to click a link to donate and then enter their OTP to "verify the charity contribution." Police confirmed that this was a phishing attempt where scammers harvested OTPs to gain access to the victims\' online banking portals under the guise of a charitable act.',
        "scam_type": "otp_scam",
        "platform": "whatsapp",
        "news_date": date(2026, 3, 25),
        "source": "Bernama",
        "url_link": "https://www.bernama.com/en/region/news.php/business/news.php?id=2537634",
    },
]


async def seed() -> None:
    # Perfectly reuse the ORM configuration of the main application
    await Tortoise.init(config=TORTOISE_ORM)
    try:
        created_n = 0
        updated_n = 0

        for data in STATIC_SCAM_CASES:
            # Use "title" as the matching key. If it doesn't exist, create it
            # obj: The record object in the database (whether newly created or existing)
            obj, created = await ScamCase.get_or_create(
                title=data["title"],
                # Found → Directly return to this record
                # Not found → Create a new record using the fields in defaults
                defaults={
                    "content": data["content"],
                    "scam_type": data["scam_type"],
                    "platform": data["platform"],
                    "news_date": data["news_date"],
                    "source": data["source"],
                    "url_link": data["url_link"],
                },
            )

            if created:
                created_n += 1
                logger.info(f"  + created: {data['title'][:30]}...")
            else:
                # 幂等性校验：如果发现现有数据与静态数据不一致，则进行更新
                needs_update = False
                # 需要对比的字段
                for field in [
                    "content",
                    "scam_type",
                    "platform",
                    "news_date",
                    "source",
                    "url_link",
                ]:
                    # getattr(obj, field)  → 数据库里当前存的值
                    # data[field]          → 静态数据里的新值
                    if getattr(obj, field) != data[field]:
                        # 不一致 → 把内存对象更新为新值
                        setattr(obj, field, data[field])
                        needs_update = True

                # 如果有任何字段变了，才真正写回数据库
                if needs_update:
                    await obj.save()
                    updated_n += 1
                    logger.info(f"  ~ updated fields for: {data['title'][:30]}...")
                else:
                    logger.info(f"  = unchanged: {data['title'][:30]}...")

        logger.info(
            f"Done. created={created_n}, fields_updated={updated_n}, "
            f"total_defined={len(STATIC_SCAM_CASES)}"
        )
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(seed())
