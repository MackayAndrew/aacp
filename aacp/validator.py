"""
AACP v1.0 Validator — accepts both full and compact pipe-delimited packets.
Compact packets omit empty optional positional fields.
Required: TASK (pos 0), DOM (pos 1), return:, aacp:
"""

from .schema import (
    VALID_TASKS, VALID_DOMAINS, VALID_PRIORITIES,
    EXTENDED_FIELDS, ValidationResult, AACP_VERSION,
)


class AACPValidator:

    def validate(self, packet: str) -> ValidationResult:
        errors = []
        warnings = []

        if not packet or not packet.strip():
            return ValidationResult(valid=False, errors=["Empty packet."])

        fields = [f.strip() for f in packet.strip().split("|")]

        if len(fields) < 3:
            errors.append("Packet too short — minimum: TASK|DOM|...|return:AGENT|p:N|aacp:1.0")
            return ValidationResult(valid=False, errors=errors)

        # Field 0 — TASK (always positional)
        task = fields[0]
        if not task:
            errors.append("Field 0 (TASK) is empty.")
        elif task not in VALID_TASKS:
            errors.append(f"Unknown TASK '{task}'. Valid: {', '.join(sorted(VALID_TASKS))}")

        # Field 1 — DOM (always positional)
        dom = fields[1] if len(fields) > 1 else ""
        if not dom:
            errors.append("Field 1 (DOM) is empty.")
        elif dom not in VALID_DOMAINS:
            errors.append(f"Unknown DOM '{dom}'. Valid: {', '.join(sorted(VALID_DOMAINS))}")

        # Parse all remaining fields — mix of positional and key:value
        all_keys = {}
        for f in fields[2:]:
            if ":" in f:
                k, v = f.split(":", 1)
                all_keys[k.strip().lower()] = v.strip()

        # Required: return
        if "return" not in all_keys:
            errors.append("Missing return: field. Must specify receiving agent.")

        # Required: aacp version
        if "aacp" not in all_keys:
            warnings.append("Missing aacp: version tag. Add aacp:1.0 for compatibility.")
        elif all_keys["aacp"] != AACP_VERSION:
            warnings.append(f"AACP version '{all_keys['aacp']}' — current is {AACP_VERSION}.")

        # Optional: priority
        if "p" in all_keys and all_keys["p"] not in VALID_PRIORITIES:
            warnings.append(f"Priority '{all_keys['p']}' non-standard. Expected 1, 2, or 3.")

        # Unknown extended keys
        CORE_KEYS = {"return","p","aacp","res","period","filter","fields","fmt"}
        for k in all_keys:
            if k not in CORE_KEYS and k not in EXTENDED_FIELDS:
                warnings.append(f"Unknown field '{k}'. May be valid extension.")

        # Companion rules
        if "sentiment" in all_keys and "tone" not in all_keys:
            warnings.append(
                "sentiment field present without tone. "
                "Add tone:empathetic|formal|terse for human-facing tasks."
            )
        if "ltv" in all_keys and "ccy" not in all_keys:
            warnings.append("ltv field present without ccy — add currency context.")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
