Country: {{ inputs.country }}
Sector: {{ inputs.sector }}
Run date: {{ run.date }}

Below are {{ nodes.collect_articles | length }} de-duplicated news search results. Each has a `ref` number.

Identify the distinct external events that could materially affect {{ inputs.sector }} in {{ inputs.country }}.

Materiality guide:
- high: severe market moves; liquidity, funding or repo stress; rate or credit-spread shocks; major regulatory rules or enforcement (SEC, CFTC, Federal Reserve, Treasury); large fund failures, closures or redemptions; systemic-risk concerns; material changes in leverage or financing markets.
- medium: developments with a plausible but indirect or limited credit channel, or early signals of the above.
- low: generic commentary, opinion, marketing, minor personnel news, single-firm stories with no sector read-through. Return these only if nothing better exists, and mark them low.

For each event return:
- headline: one line, factual
- summary: two to four sentences, factual, drawn from the articles
- country, sector: lists
- subsectors_or_strategies: affected strategies, e.g. "Fixed Income Relative Value", "Macro", "Multi-Strategy", "Equity Long/Short"
- event_type: one of the allowed values
- materiality and materiality_rationale
- direction
- impact_channels: e.g. leverage, liquidity, repo funding, margin requirements, performance, redemptions, regulatory compliance
- keywords: terms useful for later customer-specific research
- source_refs: the `ref` numbers of every supporting article
- validation_query: one search query to corroborate this event on regulator and major-newswire sites
- confidence: 0 to 1, your confidence that the event is real and correctly described

Also return `excluded_refs` for articles you judged irrelevant or immaterial.

Articles:
{{ nodes.collect_articles | pretty }}
