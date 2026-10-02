For each event below, a search was run on trusted domains ({{ inputs.trusted_domains | join(", ") }}) to corroborate it.

Decide for each event:
- validation_status:
  - corroborated: at least one trusted-domain result clearly reports the same development
  - partially_corroborated: trusted results cover part of it, or a closely related development
  - not_found: no trusted result addresses it (absence of evidence, not contradiction)
  - contradicted: a trusted result conflicts with the event as described
  - not_checked: no validation search result is available for it
- trusted_urls: URLs copied exactly from the validation results that support your decision. Never invent or edit URLs.
- note: one or two sentences explaining the decision
- adjusted_confidence: 0 to 1, the event confidence after validation

Return one assessment per event, keyed by event_id.

Events with their validation results. `validation_results: null` with no error means the event was not searched (not_checked). An empty list means the search ran and found nothing (not_found).
{{ nodes.validation_digest | pretty }}
