import re


def strip_code_fences(*, text: str) -> str:
    clean = text.strip()
    if clean.startswith("```"):
        clean = clean.split("```", 1)[1].strip()
        if clean.startswith("json"):
            clean = clean[len("json"):].strip()
        if "```" in clean:
            clean = clean.split("```")[0].strip()
    return clean


def extract_json_block(*, text: str) -> str | None:
    start_idx = None
    stack = []
    in_string = False
    escape = False

    for idx, char in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "\"":
                in_string = False
            continue

        if char == "\"":
            in_string = True
            continue

        if char in ("{", "["):
            if start_idx is None:
                start_idx = idx
            stack.append(char)
            continue

        if char in ("}", "]") and stack:
            opening = stack.pop()
            if (opening == "{" and char != "}") or (opening == "[" and char != "]"):
                return None
            if not stack and start_idx is not None:
                return text[start_idx:idx + 1]

    return None


def escape_control_chars(*, text: str) -> str:
    escaped = []
    in_string = False
    escape = False

    for char in text:
        if in_string:
            if escape:
                escape = False
                escaped.append(char)
                continue
            if char == "\\":
                escape = True
                escaped.append(char)
                continue
            if char == "\"":
                in_string = False
                escaped.append(char)
                continue
            if char == "\n":
                escaped.append("\\n")
                continue
            if char == "\r":
                escaped.append("\\r")
                continue
            if char == "\t":
                escaped.append("\\t")
                continue
            escaped.append(char)
            continue

        if char == "\"":
            in_string = True
        escaped.append(char)

    return "".join(escaped)


def remove_trailing_commas(*, text: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", text)


def close_unterminated_json(*, text: str) -> str | None:
    stack = []
    in_string = False
    escape = False
    for char in text:
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == "\"":
                in_string = False
            continue
        if char == "\"":
            in_string = True
        elif char in ("{", "["):
            stack.append(char)
        elif char in ("}", "]") and stack:
            opening = stack.pop()
            if (opening == "{" and char != "}") or (opening == "[" and char != "]"):
                return None
    if not stack and not in_string:
        return None
    suffix = ""
    if in_string:
        if escape:
            suffix += "\\\\"
        suffix += "\""
    if stack:
        suffix += "".join("}" if item == "{" else "]" for item in reversed(stack))
    return text + suffix
