# utils.py
from django.utils import timezone
import requests
from django.conf import settings
from django.utils.dateparse import parse_datetime

def is_result_accessible(schedule_time):
    """
    Safely checks if the scheduled result time has passed (WAT timezone).
    Handles both string and datetime formats.
    Returns: (is_accessible: bool, readable_time: str)
    """
    if not schedule_time:
        return True, None  # Always accessible if no time is set

    # Convert string to datetime if necessary
    if isinstance(schedule_time, str):
        schedule_time = parse_datetime(schedule_time)

    if schedule_time is None:
        return True, None  # if parsing failed, assume accessible

    # Make timezone-aware if naive
    if timezone.is_naive(schedule_time):
        schedule_time = timezone.make_aware(schedule_time)

    # Convert both to local WAT time
    now_wat = timezone.localtime(timezone.now())
    schedule_time = timezone.localtime(schedule_time)

    # Compare
    is_open = now_wat >= schedule_time
    readable_time = schedule_time.strftime("%B %d, %Y %I:%M %p WAT")
    return is_open, readable_time


TERMII_API_KEY = settings.TERMIL_API_KEY
SENDER_ID = "SchoolDevs"

def normalize_phone(number):
    """
    Convert phone number to correct international format (Nigeria example)
    Removes duplicates, invalid numbers, and extra characters.
    """
    number = str(number).strip().replace("`", "").replace(" ", "")  # remove spaces/backticks

    # Remove leading +
    if number.startswith("+"):
        number = number[1:]

    # Convert local 0-prefixed number to international
    if number.startswith("0"):
        number = "234" + number[1:]

    # Validate length (Nigeria numbers should be 13 digits including 234)
    if len(number) != 13 or not number.isdigit():
        return None  # invalid number

    return number

def clean_phone_numbers(numbers):
    """
    Normalize and deduplicate a list of phone numbers
    """
    cleaned = set()
    for num in numbers:
        normalized = normalize_phone(num)
        if normalized:
            cleaned.add(normalized)
    return list(cleaned)

def send_bulk_sms(phone_numbers, message_text):
    results = {"success": [], "failed": []}

    # Normalize (keep duplicates if needed)
    phone_numbers = [normalize_phone(n) for n in phone_numbers if normalize_phone(n)]
    print("Sending SMS to:", phone_numbers)

    for num in phone_numbers:
        url = "https://api.ng.termii.com/api/sms/send"
        payload = {
            "to": [num],
            "from": SENDER_ID,
            "sms": message_text,
            "type": "plain",
            "channel": "generic",
            "api_key": TERMII_API_KEY
        }
        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            res_json = response.json()
            if res_json.get("code") == "ok":
                results["success"].append(num)
                print('sent')
            else:
                results["failed"].append({"number": num, "error": res_json.get("message", "Unknown error")})
        except Exception as e:
            results["failed"].append({"number": num, "error": str(e)})

    return results



#result