from __future__ import annotations

import asyncio
import os
import sys
from dotenv import load_dotenv
from tortoise import Tortoise
import logging
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
    logger.warning(
        f" Warning: The environment variable file {env_path} cannot be found. The system will attempt to rely on the existing system environment variables."
    )

from app.core.database import TORTOISE_ORM
from datetime import date
from app.models.scam_case import ScamCase

STATIC_SCAM_CASES = [
    # --- Suspicious Link ---
    {
        "title": "Fake Maybank Website Scam",
        "content": "A Malaysian user, Azizul Osman, became a victim of a phishing scam after accidentally visiting a fake Maybank website through a Google search result. The website closely resembled the official Maybank login page, including identical design elements such as the logo, fonts, and login interface. Believing the website was legitimate, he entered his banking username and password, followed by a TAC received via SMS. Shortly afterwards, an unauthorised transaction of RM3,600 was made from his account to a third-party online shopping platform.",
        "scam_type": "suspicious_link",
        "platform": "facebook",
        "news_date": date(2021, 2, 5),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/man-warns-of-fake-maybank2u-website-after-getting-scammed-rm3600",
    },
    {
        "title": "Fake Maybank2u Email Scam",
        "content": "Victims received fraudulent emails claiming that their Maybank accounts had been compromised. The emails instructed users to click on a hyperlink to resolve the supposed security issue. After clicking the link, victims were redirected to a fake website designed to closely resemble the official Maybank2u portal. Users were then asked to enter sensitive information including their username, password, and phone number.",
        "scam_type": "suspicious_link",
        "platform": "email",
        "news_date": date(2021, 4, 15),
        "source": "The Sun",
        "url_link": "https://thesun.my/news/malaysia-news/scammers-target-bank-customers-with-fake-websites-if7755864/",
    },
    {
        "title": "Fake Tax Refund Scam",
        "content": 'Many Malaysians have reportedly received phishing emails claiming to offer income tax refunds from trusted institutions such as banks and government-related organisations. The scam emails instructed recipients to submit their personal information in order to process the supposed tax refund. Victims were asked to complete a "security verification" step by downloading an attachment or clicking a provided link.',
        "scam_type": "suspicious_link",
        "platform": "email",
        "news_date": date(2016, 10, 19),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/bank-negara-tax-refund-email-lhdn",
    },
    {
        "title": "Fake AirAsia Free Ticket Scam",
        "content": "A scam involving fake free AirAsia ticket promotions recently circulated widely on Facebook and other social media platforms. The scam claimed that users could receive free flight tickets or vouchers by clicking on promotional links and completing online forms. The scam was designed to collect users' personal information by promising rewards such as free flights or vouchers. Victims were often redirected to suspicious websites or forms requesting personal details in exchange for the fake promotion.",
        "scam_type": "suspicious_link",
        "platform": "facebook",
        "news_date": date(2016, 7, 27),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/free-tesco-vouchers-gsc-tickets-7eleven-coupons-airasia-flights-hoax",
    },
    # --- Phishing Scams ---
    {
        "title": "Fake LHDN Phone Scam",
        "content": "A Malaysian victim lost RM15,000 after falling for a phone scam involving individuals impersonating officers from the Inland Revenue Board of Malaysia (LHDN). The victim received an automated call claiming it was a final warning regarding unpaid income tax. Throughout the scam, the victim was transferred between different callers, each playing specific roles to create fear and pressure. Eventually, the victim discovered that RM15,000 had been transferred from her account through five unauthorised transactions to the same bank account.",
        "scam_type": "phishing",
        "platform": "phone_call",
        "news_date": date(2021, 1, 21),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/victim-shares-experience-getting-caught-in-emotional-manipulation-of-scam-call",
    },
    {
        "title": "Fake Bank Officer & Identity Fraud Scam",
        "content": "A Malaysian victim received a phone call from individuals pretending to be AmBank representatives, claiming that suspicious transactions had been made using his card on Lazada. The call was then transferred multiple times to different scammers posing as representatives from Bank Negara Malaysia and police inspectors. During the call, the victim suddenly received SMS notifications indicating that his e-banking credentials had been changed and money was being transferred out of his Maybank and OCBC accounts.",
        "scam_type": "phishing",
        "platform": "phone_call",
        "news_date": date(2020, 11, 20),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/malaysian-loses-rm-30000-over-bank-fraud-security",
    },
    # --- OTP Scams ---
    {
        "title": "WhatsApp Verification Code Scam",
        "content": "The victim received a message asking him to provide a six-digit verification code from someone pretending to be his university friend. Shortly afterwards, he was logged out of his WhatsApp account and prompted to verify his phone number again. The victim later received verification messages in Spanish and discovered that he would need to wait 12 hours before attempting to recover his account.",
        "scam_type": "otp_scam",
        "platform": "whatsapp",
        "news_date": date(2020, 11, 20),
        "source": "SAYS",
        "url_link": "https://says.com/my/tech/twitter-user-warns-open-whatsapp-text-from-loses-account-scam",
    },
    {
        "title": "Fake BigPay Customer Service Scam",
        "content": "One victim shared that the scammers instructed her not to log into her BigPay account during the call. After ending the conversation and checking the application, she discovered that her account had already been compromised. Because her RHB bank card was linked to the BigPay account, approximately RM900 was transferred without her permission.",
        "scam_type": "otp_scam",
        "platform": "phone_call",
        "news_date": date(2020, 7, 10),
        "source": "SAYS",
        "url_link": "https://says.com/my/news/m-sians-are-losing-money-on-bigpay-in-new-online-scam-here-s-their-crafty-modus-operandi",
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
