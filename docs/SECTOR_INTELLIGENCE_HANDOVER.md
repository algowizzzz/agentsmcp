# Sector-to-Customer News Intelligence

## Comprehensive Handover for Work Mode

---

## 1. Objective

Build a prototype intelligence workflow that identifies significant external events affecting a specific country + sector, maps those events to customers in our internal book belonging to that same country and sector, researches which customers are actually relevant to each event, and produces an analyst-ready report with supporting evidence.

The first prototype should be:

- **Country:** USA
- **Sector:** Hedge Funds

This is a controlled test. Do not build the full 20-sector scheduler yet.

The broader portfolio contains approximately:

- 20 sectors
- ~5,000 customers
- Customers across 3 continents and many countries

For each customer, we currently know at minimum:

- Customer name / identifier
- Country
- Sector

Additional internal attributes may include:

- Approved limits
- Risk appetite context
- Risk rating
- Other internal credit/risk information

The system should eventually support all country-sector combinations, but the MVP runs one sector-country pair per invocation.

---

## 2. Core Business Problem

Today, external news is difficult to translate into portfolio-level credit intelligence.

The desired workflow is:

1. What important events are happening in a sector and country?
2. Which customers do we have in that sector/country?
3. Which of those customers are actually relevant to the event?
4. Is there evidence that the event has affected the customer?
5. How important is this customer for us when considering approved limits, risk appetite and other internal risk information?

The solution should reduce manual news scanning while avoiding false conclusions based solely on sector membership.

---

## 3. Fundamental Design Principle

Do not equate:

> Country + sector match

with:

> Customer impacted

Instead use three levels:

### Level 1 — Potentially Relevant

Customer belongs to the country and sector associated with the external event.

Example:

```
USA + Hedge Funds + Treasury market stress
```

All U.S. hedge-fund customers become candidates.

### Level 2 — Customer Relevance Confirmed

External evidence indicates the customer participates in, is exposed to, or operates in the part of the market affected by the event.

Examples:

- Fixed-income relative-value strategy
- Treasury basis trading
- Macro rates exposure
- Repo financing
- Relevant geography/business activity
- Relevant assets or strategy

### Level 3 — Observed Impact

There is external evidence that the event has actually affected the customer.

Examples:

- Losses
- Margin pressure
- Liquidity issues
- Redemptions
- NAV movement
- Increased funding costs
- Operational disruption
- Regulatory impact
- Positive benefit
- Mixed outcome

The system must distinguish relevance from observed impact.

---

## 4. Important Credit-Risk Principle

Customer prioritization is not based primarily on current exposure.

The relevant internal measure is the approved limit / risk appetite relationship.

The intended ordering is:

```
External event
      ↓
Customer-event relevance
      ↓
Evidence of actual or potential impact
      ↓
Overlay internal risk information
      ↓
Approved limits
Risk appetite
Risk rating
Other indicators
      ↓
Analyst prioritization
```

Do not use approved limits to decide whether an event applies to the customer.

Limits should help determine review priority after relevance has been established.

---

## 5. External Search Constraints

Available external-search capability is limited to a Tavily MCP.

The MCP currently has approximately four Tavily tools including:

- News search
- Domain search
- General web search
- One additional Tavily tool — exact capability/name must be confirmed during implementation

No Bloomberg, FactSet, Refinitiv or other premium data source should be assumed.

Potential free Google search capability may exist but Tavily should be the primary search layer for the MVP.

---

## 6. Search Strategy

Use different Tavily capabilities for different purposes.

### A. News Search — Discovery

Use news search to discover recent sector developments.

Example query:

```
USA hedge funds major developments leverage liquidity regulation rates
```

Possible additional discovery queries:

```
US hedge funds major market risks latest
US hedge funds regulation latest
US hedge funds liquidity leverage latest
US hedge funds fixed income rates latest
```

Use relatively recent date windows.

Prototype recommendation: **3–7 days** initially. Optionally expand to **30 days** for lower-frequency sectors.

### B. Domain Search — Validation

Use trusted-domain searching after an event appears material.

Examples of useful domains for U.S. hedge funds:

```
reuters.com
sec.gov
federalreserve.gov
treasury.gov
cftc.gov
finra.org
```

Do not restrict initial discovery entirely to these domains because doing so may miss material stories.

Principle:

> Broad search discovers the signal. Trusted-domain search establishes stronger evidence.

### C. Web Search — Background / Customer Enrichment

Use general web search to learn relatively persistent characteristics of a customer.

Examples:

```
"Fund ABC" investment strategy
"Fund ABC" fixed income
"Fund ABC" Treasury
"Fund ABC" macro
```

This is especially useful when the system does not yet know the customer's strategy or business characteristics.

---

## 7. Recommended Architecture

Use a fixed LangGraph orchestrator.

Do not build one fully autonomous agent with unrestricted control of the workflow.

The overall business workflow should be deterministic and auditable.

Agentic behavior should exist only inside bounded research nodes.

High-level architecture:

```
START
  ↓
Input country + sector
  ↓
Discover sector news
  ↓
Extract structured events
  ↓
Deduplicate events
  ↓
Assess materiality
  ↓
Validate important events
  ↓
Fetch internal customers
  ↓
Customer relevance assessment
  ↓
Customer research where needed
  ↓
Observed-impact assessment
  ↓
Overlay internal risk data
  ↓
Prioritize analyst review
  ↓
Generate report
  ↓
Persist evidence + learned customer attributes
  ↓
END
```

---

## 8. LangGraph vs Agentic Components

Fixed orchestration should control:

- Workflow sequence
- State transitions
- Number of searches
- Search budgets
- Customer iteration
- Stopping conditions
- Data persistence
- Output schemas
- Human-review requirements

Agentic decisions may control:

- Which Tavily tool to use for a particular research question
- How to formulate a customer-specific query
- Whether another search is needed
- Whether a source supports, contradicts or does not address the hypothesis

The preferred pattern is:

> Workflow controls the agent. Agent does not control the workflow.

---

## 9. Proposed LangGraph Nodes

Prototype nodes:

1. `initialize_run`
2. `discover_news`
3. `extract_events`
4. `deduplicate_events`
5. `assess_event_materiality`
6. `validate_event`
7. `fetch_customers`
8. `load_customer_memory`
9. `research_customer`
10. `assess_customer_relevance`
11. `assess_observed_impact`
12. `overlay_internal_risk`
13. `prioritize_customers`
14. `generate_report`
15. `persist_results`

Some nodes may later be combined if unnecessary.

---

## 10. Graph Input

The MVP should take explicit inputs.

Example:

```json
{
  "country": "USA",
  "sector": "Hedge Funds"
}
```

Possible future parameters:

```json
{
  "country": "USA",
  "sector": "Hedge Funds",
  "lookback_days": 7,
  "max_events": 5,
  "max_customer_searches": 2
}
```

No scheduler is needed initially.

The user should be able to invoke:

```python
run_sector_intelligence(
    country="USA",
    sector="Hedge Funds"
)
```

---

## 11. Suggested Graph State

Example:

```python
class IntelligenceState(TypedDict):
    run_id: str
    country: str
    sector: str
    discovery_queries: list[str]
    raw_news_results: list[dict]
    extracted_events: list[dict]
    validated_events: list[dict]
    current_event: dict | None
    candidate_customers: list[dict]
    current_customer: dict | None
    customer_memory: dict | None
    customer_search_results: list[dict]
    customer_event_assessments: list[dict]
    prioritized_customers: list[dict]
    final_report: dict | None
```

Keep the state explicit and serializable.

---

## 12. Event Schema

Every external event should become structured data.

Suggested schema:

```json
{
  "event_id": "HF_US_20261001_001",
  "headline": "Treasury market volatility pressures leveraged hedge-fund strategies",
  "summary": "Short factual description of the event.",
  "country": ["USA"],
  "sector": ["Hedge Funds"],
  "subsectors_or_strategies": [
    "Fixed Income Relative Value",
    "Macro",
    "Multi-Strategy"
  ],
  "event_type": "Market Risk",
  "materiality": "high",
  "direction": "negative",
  "impact_channels": [
    "leverage",
    "liquidity",
    "repo funding",
    "margin requirements"
  ],
  "keywords": [
    "Treasury",
    "basis trade",
    "repo",
    "rates",
    "fixed income",
    "leverage"
  ],
  "sources": [
    {
      "title": "...",
      "url": "...",
      "publisher": "...",
      "published_at": "...",
      "source_type": "news"
    }
  ],
  "confidence": 0.91
}
```

Do not force the event direction to negative.

Possible values:

```
positive
negative
mixed
neutral
unknown
```

---

## 13. Event Materiality Assessment

The LLM should distinguish important credit/risk events from generic industry news.

Material events could include:

**Market events**

- Severe market moves
- Liquidity stress
- Funding stress
- Rate shocks
- Credit-spread changes
- Commodity shocks
- FX shocks

**Regulatory events**

- SEC/CFTC rules
- Reporting changes
- Capital/liquidity requirements
- Enforcement actions

**Business events**

- Major bankruptcies
- Industry consolidation
- Large redemptions
- Fund closures
- Operational events

**Structural events**

- Changes in leverage
- Changes in financing markets
- Changes in investor flows
- Systemic-risk concerns

Do not treat the following as high-materiality events:

- Minor executive announcements
- Generic commentary
- Marketing stories
- Unsubstantiated opinion

---

## 14. Event Deduplication

Multiple articles often describe the same underlying event.

Do not surface each article separately.

Example:

```
Article 1 → Treasury sell-off
Article 2 → Basis trade unwinding
Article 3 → Hedge fund deleveraging
Article 4 → Repo volatility
```

These may belong to one larger event.

Cluster them into:

> **Event:** Treasury market volatility / basis-trade deleveraging

Preserve all supporting sources underneath the event.

---

## 15. Internal Customer Matching

Once an event is associated with `country = USA` and `sector = Hedge Funds`, query the internal book.

Example SQL:

```sql
SELECT *
FROM customer_book
WHERE country = 'USA'
AND sector = 'Hedge Funds';
```

All returned customers are initially **Potentially relevant**, not **Impacted**.

---

## 16. Customer Research

For each customer, determine whether there is enough existing knowledge to assess relevance.

If customer strategy is known, reuse it.

If not, perform external research.

Example event: Treasury basis-trade stress

Useful queries could be:

```
"<customer>" Treasury basis trade
"<customer>" fixed income repo leverage
"<customer>" Treasury relative value
"<customer>" rates strategy
```

Prefer one consolidated query where possible.

Example:

```
"<customer>" (Treasury OR repo OR fixed income OR basis trade OR rates OR leverage)
```

---

## 17. Customer Relevance Schema

Suggested output:

```json
{
  "customer_id": "12345",
  "customer_name": "Example Capital",
  "event_id": "HF_US_20261001_001",
  "event_relevance": "confirmed",
  "relevance_reason": "The firm operates a fixed-income relative-value strategy with documented Treasury-market activity.",
  "matched_attributes": [
    "Fixed Income Relative Value",
    "US Treasuries",
    "Repo"
  ],
  "evidence": [
    {
      "claim": "The firm participates in Treasury relative-value strategies.",
      "source_url": "...",
      "publisher": "...",
      "published_at": "..."
    }
  ],
  "confidence": 0.86
}
```

Allowed relevance values:

```
confirmed
probable
possible
none
insufficient_evidence
```

---

## 18. Observed Impact Schema

Separately assess whether the event has actually affected the customer.

```json
{
  "customer_id": "12345",
  "event_id": "HF_US_20261001_001",
  "observed_impact": "negative",
  "impact_evidence": [
    {
      "claim": "The fund reported losses in its fixed-income strategies.",
      "source_url": "..."
    }
  ],
  "impact_channels": [
    "performance",
    "funding cost"
  ],
  "confidence": 0.81
}
```

Possible values:

```
negative
positive
mixed
operational
unknown
no_observed_impact
```

**Important:** Do not infer impact solely because a customer operates in the affected strategy.

---

## 19. Contradictory Evidence

The workflow must actively allow evidence that contradicts the original concern.

Example:

- External event suggests tariff risk.
- Customer-specific research finds: company has no relevant imports.

Result:

```
Event relevance = possible
Observed impact = no observed impact
```

or:

```
Event relevance = none
```

This avoids confirmation bias.

---

## 20. Customer Intelligence Memory

Over time the system should build reusable customer profiles.

Example:

```json
{
  "customer_id": "12345",
  "customer_name": "Example Capital",
  "country": "USA",
  "sector": "Hedge Funds",
  "learned_attributes": {
    "strategy": [
      "Fixed Income Relative Value",
      "Macro"
    ],
    "markets": [
      "US Treasuries",
      "Interest Rate Derivatives"
    ],
    "funding": [
      "Repo"
    ],
    "geographies": [
      "USA"
    ]
  },
  "evidence": [
    {
      "attribute": "strategy",
      "source_url": "...",
      "retrieved_at": "..."
    }
  ],
  "last_updated": "2026-10-01"
}
```

Future event runs should reuse this knowledge.

This reduces Tavily usage dramatically.

---

## 21. Search-Budget Controls

For the MVP, impose strict budgets.

Recommended starting limits:

| Item | Limit |
|---|---|
| Sector discovery results | 10–15 |
| Unique events retained | 3–5 |
| Events deep-dived | 2–3 |
| Validation searches/event | 1 |
| Searches/customer/event | maximum 2 |

Do not automatically perform searches for every customer if existing memory already answers the relevance question.

---

## 22. Research Decision Logic

Suggested logic:

```
IF customer memory establishes strategy/exposure
    assess relevance using existing evidence
ELSE
    run Tavily customer research
```

Then:

```
IF relevance = none
    stop customer/event research
IF relevance = possible/probable/confirmed
    search for recent customer-specific impact evidence
```

Then:

```
IF important adverse claim is found
    validate using higher-quality / trusted-domain source when possible
```

---

## 23. Tavily Tool-Selection Guidance

The research agent should receive explicit rules.

| Research need | Tool |
|---|---|
| Recent sector development | News Search |
| Recent customer development | News Search |
| Persistent company/fund information | Web Search |
| Critical claim requiring trusted evidence | Domain Search |
| Detailed content retrieval | Fourth Tavily MCP tool, if it is an extraction/content tool |

Confirm the exact fourth MCP capability before implementation.

---

## 24. Internal Risk Overlay

After relevance and observed impact are determined, bring in internal risk information.

Possible fields:

- Approved limit
- Current risk rating
- Sector risk appetite
- Country risk appetite
- Customer risk appetite classification
- Existing watchlist indicators
- Other internal warning signals

Example prioritization approach:

```
Review Priority =
    Event Materiality
  × Customer Relevance
  × Observed Impact Strength
  × Limit Significance
  × Risk Appetite Sensitivity
  × Existing Risk Rating
```

This does not need to become a formal regulatory credit score.

It can initially be an analyst-prioritization heuristic.

---

## 25. Important Distinction: Limit vs Exposure

Do not prioritize primarily on outstanding exposure.

The business requirement discussed is centered on limits and risk appetite.

A customer can matter because:

- Approved limits are significant
- Sector-country appetite is constrained
- Customer has high-risk characteristics
- External event changes the risk outlook

even if current utilization/exposure is lower.

---

## 26. Analyst Output

The final output should contain two levels.

### A. Sector Event Summary

Example:

```
USA — Hedge Funds
Major Event:
  Treasury volatility and leveraged basis-trade retrenchment
Materiality:
  High
Why It Matters:
  Potential pressure on leveraged fixed-income relative-value strategies
  through funding, repo, margin and mark-to-market channels.
Potential Customer Population:
  167 U.S. hedge-fund customers
Customer Research Completed:
  25
Confirmed Relevant:
  8
Probable:
  6
Possible:
  4
No Evidence:
  7
```

### B. Customer Detail

Example:

```
Customer: Example Capital
Event:
  Treasury basis-trade volatility
Event Relevance:
  CONFIRMED
Why:
  Documented fixed-income relative-value strategy with Treasury-market activity.
Observed Impact:
  UNKNOWN
Evidence:
  • Source 1
  • Source 2
Internal Information:
  Approved Limit: $XXM
  Risk Rating: X
  Risk Appetite Context: Elevated
Analyst Priority:
  High
Suggested Review:
  Review current leverage, liquidity, financing and latest performance information.
```

---

## 27. Recommended Final Table

The analyst-facing table should resemble:

| Customer | Event | Relevance | Observed Impact | Approved Limit | Risk Context | Confidence |
|---|---|---|---|---|---|---|
| Customer A | Treasury volatility | Confirmed | Negative | $20M | Elevated | 88% |
| Customer B | Treasury volatility | Probable | Unknown | $35M | Near appetite | 72% |
| Customer C | SEC reporting change | Confirmed | Operational | $10M | Normal | 91% |

Do not treat confidence as probability of default.

It represents confidence in the research conclusion.

---

## 28. Source Quality

Store source-level metadata.

Example:

```json
{
  "url": "...",
  "publisher": "Reuters",
  "title": "...",
  "published_at": "...",
  "retrieved_at": "...",
  "source_type": "news",
  "trust_level": "high"
}
```

Suggested quality hierarchy:

1. Regulators / government
2. Company filings / official company statements
3. Reuters / major financial journalism
4. Established industry publications
5. General web sources

This hierarchy should influence evidence quality, not determine truth automatically.

---

## 29. Auditability Requirements

Every conclusion should be traceable.

Persist:

- Run ID
- Timestamp
- Country
- Sector
- Search query
- Tavily tool used
- Raw result metadata
- Event extracted
- LLM output
- Supporting evidence
- Customer assessed
- Customer relevance
- Observed impact
- Internal risk overlay
- Final prioritization
- Model/version if available

The analyst should be able to answer **"Why was this customer flagged?"** without reconstructing the run manually.

---

## 30. Human-in-the-Loop

The system should generate **research intelligence**, not autonomous credit decisions.

The final decision remains analyst-reviewed.

Suggested states:

```
AI-generated
Analyst reviewed
Accepted
Rejected
Needs additional research
```

---

## 31. No Autonomous Credit Downgrade

The tool must not automatically change:

- Credit rating
- Limits
- Watchlist status
- Customer classification

unless such actions are explicitly implemented later with proper approval.

For MVP: **AI recommends review only.**

---

## 32. Prototype Test Case

Use:

- Country = USA
- Sector = Hedge Funds

Example types of current events worth testing:

- Treasury market volatility
- Basis-trade leverage
- Funding/repo stress
- Large hedge-fund performance events
- Major regulatory changes
- SEC/CFTC developments
- Investor redemptions
- Market liquidity concerns

Do not hardcode these as the only valid event types. They are test examples.

---

## 33. MVP Execution Flow

Recommended exact test flow:

```
INPUT:
  USA + Hedge Funds
↓
NEWS DISCOVERY
  Run 2–4 Tavily news queries
↓
EVENT EXTRACTION
  Convert all results to structured events
↓
EVENT CLUSTERING
  Merge duplicate stories
↓
MATERIALITY FILTER
  Keep top 3–5 events
↓
EVENT VALIDATION
  Use trusted-domain search for high-materiality events
↓
CUSTOMER QUERY
  Load all USA + Hedge Funds customers
↓
CUSTOMER RESEARCH
  Use memory first
  Use Tavily only where needed
↓
CUSTOMER RELEVANCE
  Confirmed / probable / possible / none
↓
IMPACT RESEARCH
  Only for relevant customers
↓
INTERNAL OVERLAY
  Limits + appetite + rating
↓
PRIORITIZATION
↓
ANALYST REPORT
```

---

## 34. What Not to Build Yet

Do not build these during the first test unless required:

- Scheduler
- All 20 sectors
- All countries
- Streaming UI
- Complex dashboards
- Automated email alerts
- Automated credit actions
- Vector database unless clearly needed
- Knowledge graph infrastructure
- Large multi-agent swarm
- Advanced ML ranking model

First prove:

> News event → correct customer → useful evidence → analyst agrees

---

## 35. MVP Success Criteria

The prototype is successful if analysts agree that:

1. The top sector events are genuinely material.
2. Duplicate articles are consolidated properly.
3. Customers surfaced by the system are logically connected to the event.
4. Supporting evidence is credible.
5. The system distinguishes relevance, observed impact and uncertainty.
6. The system does not create obvious false positives from simple sector matching.
7. Search volume remains reasonable.
8. An analyst can understand exactly why a customer was surfaced.
9. The report is materially faster than manually researching the sector.
10. Customer intelligence learned during one run can be reused in future runs.

---

## 36. Suggested Evaluation Dataset

For the USA Hedge Funds pilot, manually select approximately **10–20 known customers**.

Include:

- Known fixed-income hedge funds
- Known equity hedge funds
- Known macro funds
- Known multi-strategy funds
- Customers with little public information

Run the same external event against these and manually assess whether the system correctly distinguishes relevance.

This creates a small gold dataset for testing.

---

## 37. Evaluation Metrics

Useful MVP measurements:

| Metric | Definition |
|---|---|
| Event precision | % surfaced events judged material by analyst |
| Customer relevance precision | % flagged customers genuinely relevant |
| False-positive rate | Customers incorrectly connected to an event |
| Evidence coverage | % conclusions supported by external evidence |
| Source quality | % evidence from trusted sources |
| Search efficiency | Tavily calls per useful customer finding |
| Analyst acceptance | % system conclusions accepted without major correction |

Do not optimize purely for recall initially.

For credit-risk intelligence, high-quality evidence and lower false positives are especially important.

---

## 38. Suggested File Structure

One possible repository structure:

```
sector_intelligence/
│
├── app/
│   ├── graph/
│   │   ├── state.py
│   │   ├── workflow.py
│   │   └── routing.py
│   │
│   ├── nodes/
│   │   ├── discover_news.py
│   │   ├── extract_events.py
│   │   ├── deduplicate_events.py
│   │   ├── validate_event.py
│   │   ├── fetch_customers.py
│   │   ├── research_customer.py
│   │   ├── assess_relevance.py
│   │   ├── assess_impact.py
│   │   ├── overlay_risk.py
│   │   └── generate_report.py
│   │
│   ├── tools/
│   │   ├── tavily_mcp.py
│   │   └── customer_repository.py
│   │
│   ├── schemas/
│   │   ├── event.py
│   │   ├── customer.py
│   │   ├── evidence.py
│   │   └── assessment.py
│   │
│   ├── prompts/
│   │   ├── extract_event.md
│   │   ├── materiality.md
│   │   ├── customer_relevance.md
│   │   └── customer_impact.md
│   │
│   └── persistence/
│       ├── runs.py
│       ├── evidence.py
│       └── customer_memory.py
│
├── tests/
│   ├── test_event_extraction.py
│   ├── test_deduplication.py
│   ├── test_customer_relevance.py
│   └── fixtures/
│
└── run_sector.py
```

Keep the first version simple if this feels excessive.

---

## 39. Suggested Agent Boundary

Only one small research agent may initially be necessary.

### Customer Research Agent

Input:

```json
{
  "customer": "...",
  "country": "USA",
  "sector": "Hedge Funds",
  "event": "...",
  "event_keywords": []
}
```

Available tools:

- Tavily News Search
- Tavily Web Search
- Tavily Domain Search
- Tavily Tool #4

Agent responsibilities:

- Determine whether the customer is relevant to the event.
- Find direct evidence.
- Find contradictory evidence.
- Determine whether observed impact is documented.
- Stop after search budget is reached.

The agent should **not**:

- Select unrelated customers
- Change the sector
- Create new workflow branches
- Change risk ratings
- Alter limits
- Perform autonomous credit decisions

---

## 40. Example Research-Agent Instruction

A useful system instruction could be:

```
You are a credit-intelligence research agent.
Your task is to determine whether a specific external event is relevant to a specific customer and whether there is credible evidence of an observed impact.
Use the provided Tavily search tools only when necessary.
Do not infer customer impact solely from country or sector membership.
Distinguish:
1. customer-event relevance,
2. observed impact,
3. uncertainty.
Seek evidence both supporting and contradicting the proposed relevance.
Prefer authoritative or high-quality financial sources.
Never make a credit decision.
Return structured output only.
```

---

## 41. Example Event-Extraction Prompt

```
Review the supplied news search results.
Identify distinct external events that could materially affect the specified country and sector.
Do not summarize every article separately.
Cluster articles describing the same underlying development.
For each event return:
- headline
- concise factual summary
- country
- sector
- relevant strategies/subsectors
- event type
- likely impact channels
- direction
- materiality
- keywords for customer research
- supporting sources
- confidence
Exclude generic commentary, promotional material and low-materiality stories.
```

---

## 42. Example Customer-Relevance Prompt

```
Assess whether the supplied customer is genuinely relevant to the supplied external event.
Country and sector membership alone are not sufficient.
Use documented evidence about the customer's strategy, activities, markets, financing, geography or business model.
Classify relevance as:
confirmed
probable
possible
none
insufficient_evidence
Explain the specific link between the event and customer.
Also identify contradictory evidence.
Do not infer observed financial impact unless evidence explicitly supports it.
```

---

## 43. Example Impact Prompt

```
Given the external event and customer evidence, determine whether an observed impact on the customer is documented.
Allowed outputs:
negative
positive
mixed
operational
no_observed_impact
unknown
Provide supporting claims and sources.
Do not infer impact from sector membership or strategy exposure alone.
```

---

## 44. Recommended First Implementation Sequence

Build in this order:

**Phase 1**

- Graph state
- Tavily MCP wrapper
- News discovery
- Event extraction
- Event deduplication

Test that first.

**Phase 2**

- Internal customer query
- Customer research
- Relevance classification

**Phase 3**

- Observed-impact assessment
- Risk overlay
- Analyst report

**Phase 4**

- Persistence
- Customer intelligence memory
- Evaluation harness

Do not start with UI.

---

## 45. First Work-Mode Task

The next implementation task should be:

> Inspect the available Tavily MCP tools and their exact schemas, then implement a minimal LangGraph workflow for USA + Hedge Funds covering sector news discovery, event extraction, deduplication and output of the top 3–5 material events.

Only after this works should customer matching be added.

---

## 46. Key Decisions Already Made

Do not reopen these unless implementation reveals a problem:

- Use LangGraph.
- Use a fixed orchestrator.
- Do not use one unrestricted autonomous agent.
- Run one country-sector pair during testing.
- First test is USA + Hedge Funds.
- Tavily MCP is the primary external-search mechanism.
- News search is the discovery layer.
- Domain search is the validation layer.
- Web search is primarily for background/customer enrichment.
- Country + sector produces candidate customers, not confirmed impact.
- Customer relevance and observed impact must be separate.
- Approved limits and risk appetite are used after customer relevance is determined.
- Do not prioritize simply based on current exposure.
- Human review remains mandatory.
- Persist evidence and reusable customer intelligence.
- Keep search budgets constrained.
- Do not build the full 20-sector scheduler yet.

---

## 47. Open Questions for Implementation

These can be resolved while building rather than blocking the prototype:

1. What exactly is the fourth Tavily MCP tool?
2. What internal data source contains customer, country, sector, approved limit, risk rating and risk appetite?
3. Is the customer dataset currently Excel, SQL, API, or another format?
4. Which LLM endpoint should run the LangGraph reasoning nodes?
5. Where should state and customer memory be persisted during the prototype?
6. What exact risk-appetite fields are available internally?
7. Should the first prototype search every U.S. hedge-fund customer or a manually selected validation sample first?

Recommended answer for #7: Start with a small validation set of 10–20 customers, then expand.

---

## 48. End-State Vision

Once validated, the architecture becomes:

```
            EXTERNAL INTELLIGENCE
                   │
             Tavily MCP
                   │
                   ↓
          Country + Sector Event
                   │
                   ↓
            Materiality Filter
                   │
                   ↓
              Customer Book
                   │
                   ↓
        Customer Relevance Research
                   │
                   ↓
          Observed Impact Evidence
                   │
                   ↓
       Internal Credit/Risk Context
                   │
        ┌──────────┼───────────┐
        ↓          ↓           ↓
      Limits   Risk Rating   Appetite
        └──────────┼───────────┘
                   ↓
           Analyst Prioritization
                   ↓
              Human Review
                   ↓
         Organizational Memory
```

The system should ultimately answer:

1. What happened?
2. Why does it matter to this sector?
3. Which customers on our book are actually relevant?
4. What evidence links them to the event?
5. Is there evidence of actual impact?
6. Given our limits and risk appetite, which customers deserve analyst attention first?

That is the target product.

The handover is intentionally detailed enough that Work can begin from the LangGraph + Tavily implementation without reconstructing the product decisions from this chat.
