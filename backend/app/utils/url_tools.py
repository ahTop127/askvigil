import vt
import asyncio
import whois
from datetime import datetime

# It is recommended to obtain the API Key here through environment variables to protect privacy
VT_API_KEY = "1b6d1ec3926f80084ce0546ea7cad8ed5744cbf681ba1f23cc9be80cf9e41175"


async def get_url_report(target_url: str):
    """
    Core detection logic: Combining VirusTotal and WHOIS information
    """
    # 1. Initialize the VT client asynchronously
    async with vt.Client(VT_API_KEY) as client:
        try:
            # Convert the URL to a VT-specific ID format
            url_id = vt.url_id(target_url)

            # Obtain the URL report object
            # Note: The Public API is limited to 4 requests per minute
            report = await client.get_object_async(f"/urls/{url_id}")

            # Extract detection statistics (e.g., 0/90)
            stats = report.last_analysis_stats
            malicious = stats.get("malicious", 0)
            total = sum(stats.values())

            # 2. Obtain the domain name registration information (WHOIS usually does not support asynchronous processing, here it is simply handled)
            domain = target_url.split("//")[-1].split("/")[0]
            try:
                w = whois.whois(domain)
                reg_date = w.creation_date
                # Handle the situation where some domain names return lists
                if isinstance(reg_date, list):
                    reg_date = reg_date[0]
            except Exception:
                reg_date = "Unknown"

            # 3. Assemble a data structure similar to the one in your picture
            return {
                "Website Address": target_url,
                "Detections Counts": f"{malicious}/{total}",
                "Domain Registration": reg_date.strftime("%Y-%m-%d")
                if isinstance(reg_date, datetime)
                else reg_date,
                "Status": "Safe" if malicious == 0 else "Malicious",
                "Last Analysis": report.last_analysis_date.strftime("%Y-%m-%d %H:%M"),
            }

        except vt.APIError as e:
            if e.code == "NotFoundError":
                return {
                    "Error": "This URL has not been scanned by VT yet. Please submit the scan first."
                }
            return {"Error": f"VT API error: {str(e)}"}
        except Exception as e:
            return {"Error": f"Program exception: {str(e)}"}


# --- Main Test method ---
if __name__ == "__main__":
    # Test objective
    test_url = "https://www.bilibili.com"

    print(f"Under detection: {test_url} ...")

    # Run asynchronous tasks
    try:
        result = asyncio.run(get_url_report(test_url))

        print("\n--- Summary of the Test Report ---")
        for key, value in result.items():
            print(f"{key}: {value}")

    except KeyboardInterrupt:
        print("\nThe test has been stopped.")
