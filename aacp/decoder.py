"""
AACP v1.0 Decoder
Expands pipe-delimited AACP packets to human-readable English.
Pure logic. No LLM calls. Deterministic.
"""

from .schema import DecodedPacket, FIELD_POSITIONS

TASK_EX = {
    "FETCH":"Retrieve","PROC":"Process","FLAG":"Flag for review",
    "RESOLVE":"Resolve","LOG":"Log to audit trail","SEND":"Send",
    "BUILD":"Build","MERGE":"Merge","CALC":"Calculate",
    "REPORT":"Generate report","ACK":"Acknowledge","SYNC":"Synchronise",
}
DOM_EX = {
    "HR":"Human Resources","FIN":"Finance","SALES":"Sales",
    "LEGAL":"Legal","IT":"IT & Infrastructure","CS":"Customer Services",
    "MKT":"Marketing",
}
RISK_EX = {
    "low":"low risk","medium":"medium risk",
    "high":"high risk — review required",
    "critical":"critical risk — do not proceed without approval",
}
STATUS_EX = {
    "ok":"completed successfully",
    "review_required":"completed — review required before proceeding",
    "error":"failed — error encountered",
    "blocked":"blocked — cannot proceed",
    "negotiate":"recommend negotiation",
    "approve":"approved to proceed",
}
PRI_EX = {"1":"critical priority","2":"medium priority","3":"low priority"}
TONE_EX = {
    "empathetic":"Use an empathetic, supportive tone.",
    "formal":"Use a formal, professional tone.",
    "terse":"Be concise and direct.",
}


class AACPDecoder:

    def decode(self, packet: str) -> DecodedPacket:
        fields = packet.strip().split("|")
        parsed = {}
        is_complete = True

        # Positional fields
        for i, f in enumerate(fields[:10]):
            f = f.strip()
            if not f: continue
            key = FIELD_POSITIONS.get(i, f"pos{i}")
            val = f.split(":", 1)[1].strip() if ":" in f and i >= 2 else f
            parsed[key] = val

        # Extended fields
        for f in fields[10:]:
            f = f.strip()
            if not f: continue
            if ":" in f:
                k, v = f.split(":", 1)
                parsed[k.strip().lower()] = v.strip()
            else:
                is_complete = False

        sentences = []

        task = parsed.get("TASK", "")
        dom  = parsed.get("DOM",  "")
        task_ex = TASK_EX.get(task, task)
        dom_ex  = DOM_EX.get(dom,   dom)

        if task and dom:
            sentences.append(f"{task_ex} ({dom_ex} domain).")
        elif task:
            sentences.append(f"{task_ex}.")

        if "res"      in parsed: sentences.append(f"Resource: {parsed['res'].replace('_',' ')}.")
        if "period"   in parsed: sentences.append(f"For period: {parsed['period']}.")
        if "filter"   in parsed: sentences.append(f"Filter: {parsed['filter'].replace('=',' = ')}.")
        if "fields"   in parsed: sentences.append(f"Return fields: {parsed['fields'].replace(',',' ')}.")
        if "fmt"      in parsed: sentences.append(f"Format: {parsed['fmt'].upper()}.")
        if "src"      in parsed: sentences.append(f"Source: {parsed['src']}.")
        if "src_prev" in parsed: sentences.append(f"Prior period: {parsed['src_prev']}.")
        if "rules"    in parsed: sentences.append(f"Apply rules: {parsed['rules'].replace('_',' ')}.")
        if "validate" in parsed: sentences.append(f"Validate against: {parsed['validate']}.")
        if "tmpl"     in parsed: sentences.append(f"Template: {parsed['tmpl'].replace('_',' ')}.")
        if "data_ptr" in parsed: sentences.append(f"Data reference: {parsed['data_ptr']}.")
        if "amt"      in parsed:
            ccy = parsed.get("ccy", "")
            sentences.append(f"Amount: {ccy} {parsed['amt']}.")
        if "sup"      in parsed: sentences.append(f"Supplier: {parsed['sup'].replace('-',' ')}.")
        if "match"    in parsed: sentences.append(f"Match against: {parsed['match']}.")
        if "terms"    in parsed: sentences.append(f"Terms: {parsed['terms'].replace('net','Net ')}.")
        if "party"    in parsed: sentences.append(f"Counterparty: {parsed['party'].replace('-',' ')}.")
        if "type"     in parsed: sentences.append(f"Document type: {parsed['type']}.")
        if "clause"   in parsed: sentences.append(f"Clause: {parsed['clause']}.")
        if "issue"    in parsed: sentences.append(f"Issue: {parsed['issue'].replace('_',' ')}.")
        if "risk"     in parsed:
            sentences.append(f"Risk: {RISK_EX.get(parsed['risk'], parsed['risk'])}.")
        if "block"    in parsed: sentences.append(f"Blocked pending: {parsed['block']}.")
        if "flags"    in parsed: sentences.append(f"Flags: {parsed['flags'].replace(',',' ')}.")
        if "req"      in parsed: sentences.append(f"Required actions: {parsed['req'].replace(',',' ')}.")
        if "to"       in parsed: sentences.append(f"Send to: {parsed['to'].replace(',',' and ')}.")
        if "subj"     in parsed: sentences.append(f"Subject: {parsed['subj'].replace('_',' ')}.")
        if "sentiment" in parsed: sentences.append(f"Sentiment: {parsed['sentiment']}.")
        if "tone"     in parsed:
            sentences.append(TONE_EX.get(parsed["tone"], f"Tone: {parsed['tone']}."))
        if "prog"     in parsed:
            try: sentences.append(f"Progress: {float(parsed['prog'])*100:.0f}%.")
            except ValueError: pass
        if "status"   in parsed:
            sentences.append(f"Status: {STATUS_EX.get(parsed['status'], parsed['status'])}.")
        if "actor"    in parsed: sentences.append(f"Initiated by: {parsed['actor']}.")
        if "chain"    in parsed:
            sentences.append(f"Agent chain: {parsed['chain'].replace(',',' > ')}.")
        if "p"        in parsed:
            sentences.append(f"Priority: {PRI_EX.get(parsed['p'], parsed['p'])}.")
        if "return"   in parsed: sentences.append(f"Return to: {parsed['return']}.")

        english = " ".join(sentences) if sentences else "Empty or unrecognised packet."
        return DecodedPacket(english=english, parsed=parsed, is_complete=is_complete)
