# /// script
# dependencies = [
#     "discord.py",
#     "aiohttp",
#     "python-dotenv",
# ]
# ///
import discord
import os
import aiohttp
from dotenv import load_dotenv
import asyncio

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
ASKVIGIL_API_URL = https://askvigil.duckdns.org/api/v1/detection/scan


class AftercareView(discord.ui.View):
    def __init__(self, aftercare_text, learn_more_url=None):
        super().__init__(timeout=180)
        self.aftercare_text = aftercare_text

        # add a website link button only if a URL is provided
        if learn_more_url:
            self.add_item(
                discord.ui.Button(
                    label="Learn more about this scam",
                    style=discord.ButtonStyle.link,
                    url=learn_more_url,
                    emoji="📘",
                )
            )

    @discord.ui.button(
        label="I may have been scammed, what should I do?",
        style=discord.ButtonStyle.primary,
        emoji="🛡️",
    )
    async def show_aftercare(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(self.aftercare_text, ephemeral=True)


class Client(discord.Client):
    async def on_ready(self):
        print(f"Logged on as {self.user}!")  # name of the bot

    async def on_guild_join(
        self, guild
    ):  # we will introduce our bot when it is added to a new server
        intro_message = (
            "👋 **Welcome to AskVigil!**\n\n"
            "AskVigil helps you quickly check suspicious messages, links, screenshots, and QR codes "
            "for possible scam risks directly inside Discord.\n\n"
            "**What I can check:**\n"
            "- 💬 Suspicious text messages\n"
            "- 🔗 URLs and links\n"
            "- 🖼️ Screenshots containing scam messages\n"
            "- 📱 QR codes that may lead to suspicious links\n\n"
            "**How to use me:**\n"
            "- Type `!scan` followed by the message or link you want to check\n"
            "- Upload a screenshot with `!scan` to analyse the text inside it\n"
            "- Upload a QR code image with `!scan` to check where it may lead\n\n"
            "**Examples:**\n"
            "`!scan Your bank account has been blocked. Verify now at this link.`\n"
            "`!scan https://example-link.com`\n\n"
            "After scanning, I may show:\n"
            "- A risk level and score\n"
            "- The predicted scam type\n"
            "- Reasons the content may be suspicious\n"
            "- Safety advice and recovery guidance when needed\n\n"
            "🔒 **Privacy reminder:** AskVigil only analyses content that users actively submit using `!scan`. "
            "It does not automatically monitor every message in your server."
        )

        channel = guild.system_channel

        if channel and channel.permissions_for(guild.me).send_messages:
            await channel.send(intro_message)
            return

        for text_channel in guild.text_channels:
            if text_channel.permissions_for(guild.me).send_messages:
                await text_channel.send(intro_message)
                return

    async def on_message(self, message):
        if message.author == self.user:  # dont reply to the bot itself
            return

        if message.content.startswith("hello"):
            await message.channel.send(
                f"Hi there {message.author}, welcome to **AskVigil!** Type `!help` to see how I can help you stay safe from scams."
            )

        if message.content.startswith("!help"):
            help_message = (
                "👋 **AskVigil Help Guide**\n\n"
                "AskVigil helps you check suspicious messages, links, screenshots, and QR codes "
                "for possible scam risks.\n\n"
                "**How to use `!scan`:**\n"
                "💬 **Check a suspicious message**\n"
                "`!scan Your bank account has been blocked. Verify now.`\n\n"
                "🔗 **Check a suspicious link**\n"
                "`!scan https://example-link.com`\n\n"
                "🖼️ **Check a screenshot**\n"
                "Upload an image or screenshot, then type:\n"
                "`!scan`\n\n"
                "📱 **Check a QR code**\n"
                "Upload a QR code image, then type:\n"
                "`!scan`\n\n"
                "**What AskVigil may return:**\n"
                "- Risk level and score\n"
                "- Predicted scam type\n"
                "- Reasons the content may be suspicious\n"
                "- Safety advice\n"
                "- Recovery guidance and learning links when relevant\n\n"
                "🔒 **Privacy reminder:** AskVigil only analyses content that users actively submit using `!scan`. "
                "It does not automatically monitor every message in the server."
            )

            await message.channel.send(help_message)
            return

        if message.content.startswith("!scan"):  # scanning
            text_to_scan = message.content.replace("!scan", "", 1).strip()

            image_attachment = None

            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith(
                    "image/"
                ):
                    image_attachment = attachment
                    break

            if not text_to_scan and image_attachment is None:
                await message.channel.send(
                    "Please type a message or attach an image after `!scan`.\n"
                    "Example: `!scan Your Maybank account has been blocked.`\n"
                    "Or upload a screenshot with `!scan`."
                )
                return

            await message.channel.send("Scanning this message with AskVigil...")

            result = await self.scan_with_askvigil(
                text=text_to_scan, attachment=image_attachment
            )

            if result is None:
                await message.channel.send(
                    "AskVigil is temporarily unavailable. Please try again later."
                )
                return

            reply = self.format_scan_result(result)
            view = self.build_aftercare_view(result)

            if view:
                await message.channel.send(reply, view=view)
            else:
                await message.channel.send(reply)

    async def scan_with_askvigil(self, text, attachment):
        for attempt in range(3):
            try:
                timeout = aiohttp.ClientTimeout(total=60)

                async with aiohttp.ClientSession(timeout=timeout) as session:
                    form = aiohttp.FormData()

                    if text:
                        form.add_field("text", text)

                    if attachment is not None:
                        file_bytes = await attachment.read()

                        form.add_field(
                            "file",
                            file_bytes,
                            filename=attachment.filename,
                            content_type=attachment.content_type
                            or "application/octet-stream",
                        )

                    async with session.post(ASKVIGIL_API_URL, data=form) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            print("Backend error:", response.status, error_text)
                            return None

                        return await response.json()

            except aiohttp.ClientConnectorError as e:
                print(f"Connection attempt {attempt + 1} failed:", e)

                if attempt < 2:
                    await asyncio.sleep(2)

            except Exception as e:
                print("Error calling AskVigil API:", e)
                return None

        return None

    def format_scan_result(self, result):
        unified = result.get("unified_text_analysis") or {}

        # text_analysis can be None for URL-only scans
        text_analysis = unified.get("text_analysis") or {}
        url_analysis = unified.get("url_analysis") or []

        has_text_analysis = bool(text_analysis)
        has_url_analysis = bool(url_analysis)

        # CASE 1: URL ONLY
        if not has_text_analysis and has_url_analysis:
            return self.format_url_only_result(unified, url_analysis)

        # TEXT ONLY or TEXT + URL
        return self.format_text_result(
            unified=unified,
            text_analysis=text_analysis,
            url_analysis=url_analysis,
            has_url_analysis=has_url_analysis,
        )

    def format_text_result(
        self, unified, text_analysis, url_analysis, has_url_analysis
    ):
        risk_percent = text_analysis.get("risk_score_percent")

        if risk_percent is None:
            risk_score = unified.get("overall_risk_score", 0)
            risk_percent = risk_score * 100 if risk_score <= 1 else risk_score

        decision = text_analysis.get("decision", "unknown").title()

        scam_type_data = text_analysis.get("scam_type", {})
        predicted_type = scam_type_data.get("predicted_type", "Unknown")
        confidence = scam_type_data.get("confidence_level", "unknown").title()

        explainability = text_analysis.get("explainability", {})
        matched_indicators = explainability.get("matched_indicators", [])

        guidance = text_analysis.get("immediate_guidance") or {}
        guidance_title = guidance.get("title", "Safety advice")
        guidance_summary = guidance.get("summary", "")

        if risk_percent >= 69:
            emoji = "🚨"
            risk_level = "High"
        elif risk_percent >= 40:
            emoji = "⚠️"
            risk_level = "Medium"
        else:
            emoji = "✅"
            risk_level = "Low"

        # extract the reasons
        reasons = []

        for indicator in matched_indicators[:3]:
            category = indicator.get("category", "Suspicious pattern")
            terms = indicator.get("matched_terms", [])

            if terms:
                terms_text = ", ".join(terms)
                reasons.append(f"- **{category}:** `{terms_text}`")
            else:
                reasons.append(f"- **{category}**")

        if not reasons:
            reasons.append("- No strong suspicious keywords were detected.")

        # immediate guidances
        dont_do = guidance.get("dont_do", [])
        safer_action = guidance.get("safer_action", [])

        dont_do_text = "\n".join([f"- {item}" for item in dont_do[:3]])
        safer_action_text = "\n".join([f"- {item}" for item in safer_action[:3]])

        if not dont_do_text:
            dont_do_text = (
                "- Avoid sharing sensitive information or clicking unfamiliar links."
            )

        if not safer_action_text:
            safer_action_text = "- Verify important requests through official channels."

        # for text only
        reply = (
            f"{emoji} **AskVigil Scan Result**\n\n"
            f"**Risk Level:** {risk_level}\n"
            f"**Risk Score:** {risk_percent:.1f}%\n"
            f"**Decision:** {decision}\n"
            f"**Predicted Scam Type:** {predicted_type} ({confidence} confidence)\n\n"
            f"**Why it may be risky:**\n"
            f"{chr(10).join(reasons)}\n\n"
            f"**{guidance_title}**\n"
            f"{guidance_summary}\n\n"
            f"**❌  Do not:**\n"
            f"{dont_do_text}\n\n"
            f"**✅  Safer actions:**\n"
            f"{safer_action_text}"
        )

        # if if url exist in text
        if has_url_analysis:
            reply += "\n\n" + self.build_url_section(url_analysis)

        return reply

    def format_url_only_result(self, unified, url_analysis):  # only url
        return self.build_url_section(url_analysis)

    def build_url_section(self, url_analysis):  # url under the text section
        url_blocks = []

        for index, url_item in enumerate(url_analysis[:3], start=1):
            url_score = url_item.get("risk_score", 0)
            url_percent = url_score * 100 if url_score <= 1 else url_score

            url_decision = url_item.get("decision", "unknown").title()
            input_url = url_item.get("input_url", "Unknown URL")
            resolved_url = url_item.get("resolved_url", input_url)

            if url_percent >= 69:
                url_emoji = "🚨"
                url_level = "High"
                url_summary = (
                    "This URL shows strong technical signs of being suspicious."
                )
            elif url_percent >= 40:
                url_emoji = "⚠️"
                url_level = "Medium"
                url_summary = "This URL shows some suspicious signs. Check it carefully before opening."
            else:
                url_emoji = "✅"
                url_level = "Low"
                url_summary = "This link does not show strong technical signs of being suspicious."

            resolved_line = ""
            if resolved_url != input_url:
                resolved_line = f"\n**Final Destination:** {resolved_url}"

            url_blocks.append(
                f"{url_emoji} **URL {index} Risk Analysis**\n"
                f"**URL:** {input_url}\n"
                f"**Risk Level:** {url_level}\n"
                f"**Risk Score:** {url_percent:.1f}%\n"
                f"**Decision:** {url_decision}"
                f"{resolved_line}\n\n"
                f"{url_summary}"
            )

        return "🔗 **Link Analysis**\n\n" + "\n\n".join(url_blocks)

    def build_aftercare_view(self, result):
        unified = result.get("unified_text_analysis") or {}
        text_analysis = unified.get("text_analysis") or {}
        url_analysis = unified.get("url_analysis") or []

        modalities = result.get("modalities") or {}
        qr_analysis = modalities.get("qr") or {}

        post_scam_text = None
        scam_type_for_link = None

        # Text scam result
        if text_analysis:
            decision = text_analysis.get("decision", "").lower()

            scam_type_data = text_analysis.get("scam_type", {})
            predicted_type = scam_type_data.get("predicted_type", "")

            if decision in {"suspicious", "flagged"}:
                post_scam_text = self.build_post_scam_section(predicted_type)
                scam_type_for_link = predicted_type

        # QR-only result
        elif qr_analysis:
            qr_url_analysis = qr_analysis.get("url_analysis") or []

            highest_qr_risk = max(
                [item.get("risk_score", 0) for item in qr_url_analysis], default=0
            )

            if highest_qr_risk >= 0.40:
                post_scam_text = self.build_post_scam_section("QR Code Scam")
                scam_type_for_link = "QR Code Scam"

        # URL-only result
        elif url_analysis:
            highest_url_risk = max(
                [item.get("risk_score", 0) for item in url_analysis], default=0
            )

            if highest_url_risk >= 0.40:
                post_scam_text = self.build_post_scam_section("Suspicious Link")
                scam_type_for_link = "Suspicious Link"

        if not post_scam_text:
            return None

        learn_more_url = self.get_learn_more_url(scam_type_for_link)

        return AftercareView(
            aftercare_text=post_scam_text, learn_more_url=learn_more_url
        )

    def build_post_scam_section(self, scam_type):
        post_scam_map = {
            "Job Scam": (
                "🛡️ **What to do if you may have engaged with this job scam**\n\n"
                "**1. Immediate disengagement**"
                "Do not reply or send more documents, payments, or personal information.\n\n"
                "**2. Save evidence**"
                "Keep screenshots of chats, job ads, payment receipts, phone numbers, and account numbers of the scammer.\n\n"
                "**3. Contact your bank / NSRC**"
                "If you paid a processing fee, deposit, or made a transfer:\n"
                "- **Single bank transaction:** Call your bank immediately to try to block or reverse the transaction.\n"
                "- **Multiple banks involved:** Call **NSRC 997** and provide evidence for rapid multi-bank action.\n\n"
                "**4. File a police report to Polis Diraja Malaysia (PDRM)**"
                "If money was lost or sensitive data was shared with the scammer:\n"
                "- Visit **ereporting.rmp.gov.my** for online e-reporting, or\n"
                "- Visit the nearest police station to provide more detailed information.\n\n"
                "**5. Report to Cyber999 for technical reporting**"
                "Submit a report via **https://www.mycert.org.my** or call **1-300-88-2999**. "
                "This helps authorities identify and take down malicious websites, phishing pages, and scam-related links."
            ),
            "Phishing": (
                "🛡️ **What to do if you may have interacted with this phishing scam**\n\n"
                "**1. Immediate disengagement**"
                "Stop interacting with the message, website, or attachment immediately.\n\n"
                "**2. Secure your accounts**"
                "Change passwords immediately, especially email, banking, and any reused passwords. "
                "Enable two-factor authentication (2FA).\n\n"
                "**3. Check account activity**"
                "Review account activity for any suspicious logins or transactions.\n\n"
                "**4. Save evidence**"
                "Keep screenshots of chats, payment receipts, phone numbers, and account numbers of the scammer.\n\n"
                "**5. Contact your bank / NSRC**"
                "If banking credentials, card details, or payment details were entered into any phishing website:\n"
                "- **Single bank transaction:** Call your bank immediately to try to block or reverse the transaction.\n"
                "- **Multiple banks involved:** Call **NSRC 997** and provide evidence for rapid multi-bank action.\n\n"
                "**6. File a police report to Polis Diraja Malaysia (PDRM)**"
                "If the phishing caused financial loss, account takeover, or identity misuse:\n"
                "- Visit **ereporting.rmp.gov.my** for online e-reporting, or\n"
                "- Visit the nearest police station to provide more detailed information.\n\n"
                "**7. Report to Cyber999 for technical reporting**"
                "Submit a report via **https://www.mycert.org.my** or call **1-300-88-2999**. "
                "This helps authorities identify and take down scam infrastructure such as phishing websites and malicious links."
            ),
            "QR Code Scam": (
                "🛡️ **What to do if you may have scanned a suspicious QR code**\n\n"
                "**1. Immediate disengagement**"
                "Stop interacting with the QR code immediately.\n\n"
                "**2. Identify what the QR code did**"
                "Review whether the QR code opened a website, triggered a payment, or installed an app.\n\n"
                "**3. Check device for malware**"
                "Run a malware or antivirus scan to detect any harmful apps or software and remove them.\n\n"
                "**4. Save evidence**"
                "Keep screenshots of chats, payment receipts, phone numbers, and account numbers of the scammer.\n\n"
                "**5. Contact your bank / NSRC**"
                "If banking credentials, card details, or payment details were entered after scanning the QR code, "
                "or if unauthorised bank transactions were made:\n"
                "- **Single bank transaction:** Call your bank immediately to try to block or reverse the transaction.\n"
                "- **Multiple banks involved:** Call **NSRC 997** and provide evidence for rapid multi-bank action.\n\n"
                "**6. File a police report to Polis Diraja Malaysia (PDRM)**\n"
                "If the QR scam caused financial loss, account takeover, or identity misuse:\n"
                "- Visit **ereporting.rmp.gov.my** for online e-reporting, or\n"
                "- Visit the nearest police station to provide more detailed information.\n\n"
                "**7. Report to Cyber999 for technical reporting**\n"
                "Submit a report via **https://www.mycert.org.my** or call **1-300-88-2999**. "
                "This helps authorities identify and take down scam infrastructure such as phishing websites and malicious links."
            ),
            "Suspicious Link": (
                "🛡️ **What to do if you may have clicked a suspicious link**\n\n"
                "**1. Immediate disengagement**"
                "Do not click the link again, open any attachments, or continue interacting with the message sender.\n\n"
                "**2. Secure your accounts**"
                "Change passwords immediately, especially email, banking, and any reused passwords. "
                "Enable two-factor authentication (2FA).\n\n"
                "**3. Check account activity**"
                "Review account activity for any suspicious logins or transactions.\n\n"
                "**4. Check your device**"
                "Run a malware or antivirus scan if the link downloaded anything to your device, and remove anything suspicious.\n\n"
                "**5. Save evidence**"
                "Keep screenshots of the message, suspicious URL, sender details, website pages, and any transaction or login attempt related to the scam.\n\n"
                "**6. Contact your bank / NSRC**"
                "If you entered banking details, card details, or made any payment through the suspicious link:\n"
                "- **Single bank transaction:** Call your bank immediately to try to block or reverse the transaction.\n"
                "- **Multiple banks involved:** Call **NSRC 997** and provide evidence for rapid multi-bank action.\n\n"
                "**7. File a police report to Polis Diraja Malaysia (PDRM)**"
                "If money was lost or sensitive data was shared through the suspicious link:\n"
                "- Visit **ereporting.rmp.gov.my** for online e-reporting, or\n"
                "- Visit the nearest police station to provide more detailed information.\n\n"
                "**8. Report to Cyber999 for technical reporting**"
                "Submit a report via **https://www.mycert.org.my** or call **1-300-88-2999**. "
                "This helps authorities identify and take down scam infrastructure such as phishing websites and malicious links."
            ),
            "OTP Scam": (
                "🛡️ **What to do if you may have shared an OTP**\n\n"
                "**1. Treat it as urgent**"
                "The scammer might already be trying to use your accounts.\n\n"
                "**2. Secure your accounts**"
                "Change your passwords immediately, prioritising banking, email, and any linked accounts. "
                "Enable two-factor authentication (2FA) and log out all active sessions if possible.\n\n"
                "**3. Check account activity**"
                "Review account activity for any suspicious logins or transactions.\n\n"
                "**4. Save evidence**"
                "Keep screenshots of chats, payment receipts, phone numbers, and account numbers of the scammer.\n\n"
                "**5. Contact your bank / NSRC**"
                "If you gave away your OTP for your bank account:\n"
                "- **Single bank transaction:** Call your bank immediately to block cards, freeze suspicious access, or secure online banking.\n"
                "- **Multiple banks involved:** Call **NSRC 997** and provide evidence for rapid multi-bank action.\n\n"
                "**6. File a police report to Polis Diraja Malaysia (PDRM)**"
                "If the OTP scam caused financial loss, account takeover, or identity misuse:\n"
                "- Visit **ereporting.rmp.gov.my** for online e-reporting, or\n"
                "- Visit the nearest police station to provide more detailed information.\n\n"
                "**7. Report to Cyber999 for technical reporting**"
                "Submit a report via **https://www.mycert.org.my** or call **1-300-88-2999**. "
                "This helps authorities identify and take down scam infrastructure such as phishing websites and malicious links."
            ),
        }

        return post_scam_map.get(scam_type, "")

    def get_learn_more_url(self, scam_type):
        learn_more_links = {
            "Phishing": "https://askvigil.duckdns.org/learning/phishing",
            "OTP Scam": "https://askvigil.duckdns.org/learning/otp-scam",
            "Job Scam": "https://askvigil.duckdns.org/learning/job-scam",
            "QR Code Scam": "https://askvigil.duckdns.org/learning/qr-scam",
            "Suspicious Link": "https://askvigil.duckdns.org/learning/suspicious-link",
        }

        return learn_more_links.get(scam_type)


intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_BOT_TOKEN)
