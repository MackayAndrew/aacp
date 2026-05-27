# AACP Encoding Registry

Logs every LLM fallback call as a rule-based encoding candidate.

Run examples/demo.py --fallback to populate.

Each entry:
  id                   sha256 hash of normalised English (12 chars)
  timestamp            ISO 8601 UTC
  domain               HR FIN SALES LEGAL IT CS MKT
  english              original English instruction
  aacp_packet          the encoded packet
  compression_loss     none minor partial significant
  rule_based_written   false until a rule-based encoder exists for this pattern

When rule_based_written is set to true the pattern has a rule-based
encoder and no longer needs an LLM call.
