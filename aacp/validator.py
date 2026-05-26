"""
AACP v1.0 Validator
Validates pipe-delimited AACP packets against the v1.0 schema.
Pure logic. No LLM calls. Fast and free.

Usage:
    validator = AACPValidator()
    result = validator.validate("FETCH|HR|res:emp_salary|...|return:HR-Agent|p:1|aacp:1.0")
    print(result.summary())
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

        fields = packet.strip().split("|")

        # ── Positional fields ──────────────────────────────────────────────────
        if len(fields) < 10:
            errors.append(
                f"Packet has {len(fields)} fields, minimum 10 required. "
                f"Format: TASK|DOM|res:|period:|filter:|fields:|fmt:|return:|p:|aacp:"
            )
            return ValidationResult(valid=False, errors=errors)

        task   = fields[0].strip()
        dom    = fields[1].strip()
        ret    = self._val(fields[7])
        p      = self._val(fields[8])
        aacp   = self._val(fields[9])

        # Required: TASK
        if not task:
            errors.append("Field 0 (TASK) is empty. Must be one of: " + ", ".join(sorted(VALID_TASKS)))
        elif task not in VALID_TASKS:
            errors.append(f"Unknown TASK '{task}'. Valid: {', '.join(sorted(VALID_TASKS))}")

        # Required: DOM
        if not dom:
            errors.append("Field 1 (DOM) is empty. Must be one of: " + ", ".join(sorted(VALID_DOMAINS)))
        elif dom not in VALID_DOMAINS:
            errors.append(f"Unknown DOM '{dom}'. Valid: {', '.join(sorted(VALID_DOMAINS))}")

        # Required: return
        if not ret:
            errors.append("Field 7 (return:) is empty. Must specify receiving agent.")

        # Required: aacp version
        if not aacp:
            warnings.append("Field 9 (aacp:) is empty. Add aacp:1.0 for compatibility.")
        elif aacp != AACP_VERSION:
            warnings.append(f"AACP version '{aacp}' — current is {AACP_VERSION}.")

        # Optional: priority
        if p and p not in VALID_PRIORITIES:
            warnings.append(f"Priority '{p}' non-standard. Expected 1, 2, or 3.")

        # ── Extended fields ────────────────────────────────────────────────────
        for f in fields[10:]:
            f = f.strip()
            if not f: continue
            if ":" not in f:
                warnings.append(f"Extended field '{f}' has no colon — expected key:value.")
                continue
            key = f.split(":", 1)[0].lower()
            if key not in EXTENDED_FIELDS:
                warnings.append(
                    f"Unknown extended field '{key}'. "
                    f"May be valid extension — ensure receiving agent supports it."
                )

        # ── Companion rules ────────────────────────────────────────────────────
        extended_keys = set()
        for f in fields[10:]:
            if ":" in f:
                extended_keys.add(f.split(":", 1)[0].lower())

        if "sentiment" in extended_keys and "tone" not in extended_keys:
            warnings.append(
                "sentiment field present without tone. "
                "Add tone:empathetic|formal|terse for human-facing tasks."
            )
        if "ltv" in extended_keys and "ccy" not in extended_keys:
            warnings.append("ltv field present without ccy — add currency context.")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def _val(self, field: str) -> str:
        """Extract value from a named field like 'return:HR-Agent' or bare value."""
        field = field.strip()
        if ":" in field:
            return field.split(":", 1)[1].strip()
        return field
