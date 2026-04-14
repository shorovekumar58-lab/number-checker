import re


def normalize_number(raw: str):
    if not raw:
        return None

    num = raw.strip()

    # remove spaces and unwanted chars
    num = re.sub(r"[^\d+]", "", num)

    # 👉 international format check
    # must start with + and length 10-15 digits
    if num.startswith("+"):
        digits = num[1:]
        if digits.isdigit() and 10 <= len(digits) <= 15:
            return num

    # 👉 fallback: plain digits (without +)
    if num.isdigit() and 10 <= len(num) <= 15:
        return "+" + num

    return None


def process_numbers(raw_text: str):
    lines = raw_text.splitlines()

    cleaned = []
    seen = set()

    for line in lines:
        normalized = normalize_number(line)
        if normalized and normalized not in seen:
            seen.add(normalized)
            cleaned.append(normalized)

    return cleaned