import asyncio
import json

from tortoise import Tortoise
from transformers import AutoTokenizer

from app.core.database import TORTOISE_ORM
from app.core.lifespan import sync_assets, load_onnx_session
from app.core.config import settings
from app.core.registry import MODEL_REGISTRY
from app.services import nlp_service


print("DEBUG: testing_mlp.py loaded")


async def setup_models():
    await sync_assets()

    MODEL_REGISTRY["text"] = {
        "session": load_onnx_session(str(settings.TEXT_MODEL_PATH)),
        "tokenizer": AutoTokenizer.from_pretrained(
            str(settings.TEXT_MODEL_PATH),
            local_files_only=True,
        ),
    }

    MODEL_REGISTRY["text_classifier"] = {
        "session": load_onnx_session(str(settings.TEXT_CLASSIFIER_PATH)),
    }


def print_guidance(guidance):
    print("IMMEDIATE GUIDANCE:")

    if guidance is None:
        print("- None")
        return

    print("Title:", guidance.get("title"))
    print("Summary:", guidance.get("summary"))

    print("Don't do:")
    for item in guidance.get("dont_do", []):
        print(f"- {item}")

    print("Safer action:")
    for item in guidance.get("safer_action", []):
        print(f"- {item}")


def print_explanations(result):
    print("EXPLANATIONS:")

    indicators = result.get("explainability", {}).get("matched_indicators", [])

    if not indicators:
        print("- No risky indicators detected.")
        return

    for item in indicators:
        print(f"- {item.get('category')}")
        print(f"  Severity: {item.get('severity')}")
        print(f"  Matched terms: {item.get('matched_terms')}")
        print(f"  Reason: {item.get('reason')}")
        print(f"  Boost: {item.get('boost')}")


async def main():
    await Tortoise.init(config=TORTOISE_ORM)

    try:
        await setup_models()

        test_texts = [
            "Your Maybank account has been blocked. Click here to verify immediately.",
            "Congratulations! You won RM10000. Send your IC number to claim now.",
            "Part time job RM500 per day. Register now using this link.",
            "URGENT: Your bank account will be suspended unless you confirm your details now.",
            "Please send me the OTP code you received to verify your account.",
            "Can you please send me your verification code?",
            "Let's meet at the library tomorrow for our group assignment.",
            "Hi mom, I will be home late today.",
            "Can you send me the notes from yesterday's lecture?",
            "Reminder: team meeting tomorrow at 10am.",
        ]

        for text in test_texts:
            print("=" * 90)
            print("TEXT:", text)

            clean_text, urls = nlp_service.standardize_text(text)
            print("CLEAN TEXT:", clean_text)
            print("URLS:", urls)

            result = await nlp_service.scan_text(clean_text)

            print("RISK SCORE:", result["risk_score"])
            print("RISK SCORE PERCENT:", result["risk_score_percent"])
            print("DECISION:", result["decision"])

            print("MODEL OUTPUT:")
            print("Spam score:", result["model_output"]["spam_score"])
            print("Ham score:", result["model_output"]["ham_score"])

            print("SCAM TYPE:")
            print(result.get("scam type"))

            print("RULE BOOST:", result["explainability"]["rule_boost"])

            print_explanations(result)
            print_guidance(result.get("immediate_guidance"))

            print("FULL JSON RESULT:")
            print(json.dumps(result, indent=2, ensure_ascii=False))

    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    print("DEBUG: running main")
    asyncio.run(main())
