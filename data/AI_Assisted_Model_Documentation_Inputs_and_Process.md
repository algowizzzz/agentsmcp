## AI‑Assisted Model Documentation — Inputs and Process

### Purpose and Outcome
Create clear, tailored documentation for a model using your own structure and writing guidance. The system analyzes your codebase and connected assets, then drafts sections you define, producing a cohesive Markdown document you can export or convert (e.g., DOCX/PDF).

This guide focuses on designing inputs (what you control) and understanding the process. It intentionally excludes run instructions.

---

### Inputs You Define

- **Codebase Path**
  - Absolute path to the project you want documented.
  - Keep the tree clean (exclude large data folders, caches); ensure core modules have helpful docstrings.

- **Template (Structure)**
  - JSON that defines the document’s sections, order, and optional subsections.
  - Supports `id`, `title`, `description`, `required`, and `subsections`.
  - Add a `prompts` block to control global and per‑section writing guidance.

- **Prompts (Writing Guidance)**
  - Master prompt (global tone, audience, evidence rules, word budgets).
  - File summary prompt (how each file is analyzed: purpose, components, algorithms, dependencies, logging, assumptions/limits).
  - Hierarchical summary prompt (how file insights synthesize into an architectural narrative).
  - Per‑section overrides (e.g., “Implementation”, “Results”, “Recommendations”).

- **Metadata (Optional)**
  - Front‑matter and style hints: model name, version, owners, dates, department tags, `max_words`.

- **Connectors / Context (Optional)**
  - Paths/exports from systems you use: GitHub/GitLab/Bitbucket repos, SharePoint libraries, internal data pipeline descriptors, schema snapshots, or other machine‑readable docs.
  - Provide as local paths so the pipeline can ingest and reference them.

- **Output Path (Optional)**
  - Target file for the final Markdown (defaults are provided if omitted).

---

### How to Design High‑Quality Inputs

- **Codebase**
  - Organize by purpose (modules map to concerns). Add short module docstrings.
  - Keep third‑party or generated code outside the scanned path.

- **Template**
  - Start from a close built‑in (concise vs. full). Keep `id`s stable; reviewers and tools can deep‑link by `id`.
  - In `description`, state “what good looks like” for the section—this steers drafting.
  - Mark critical sections as `"required": true` to guarantee coverage.

- **Prompts**
  - Master prompt (6–10 lines) should specify: audience (e.g., model developers + stakeholders), voice (clear, direct), markdown headings (##/###), evidence rules (“reference code components/files where helpful”), and budgets (e.g., `{{max_words}}`).
  - File summary prompt should force a structured output (purpose, components, algorithms, dependencies, logging/error handling, assumptions/limitations) so later synthesis is strong.
  - Section overrides: tailor what “Implementation” must enumerate (modules/components), what “Results” must include (metrics/findings), and what “Recommendations” should deliver (actionable next steps).

- **Connectors**
  - Prefer small, machine‑readable artifacts: API responses, JSON/YAML config, schema docs, pipeline graphs, lightweight markdown notes. Place under a `docs/` or `artifacts/` folder in the repo.

- **Metadata**
  - Add department tags or `max_words` limits to control voice and length without editing prompts.

---

### Process Diagram (End‑to‑End)

```mermaid
flowchart TD
    A[Codebase + Optional Context<br/>(SharePoint/GitHub/pipelines)] --> B[Scan Files]
    B --> C[Parse Structure<br/>(docstrings, imports, classes/functions)]
    C --> D[Per‑File Summaries<br/>(file summary prompt)]
    D --> E[Hierarchical Summary<br/>(synthesis prompt)]
    E --> F[Section Drafting<br/>(template + master/overrides + metadata)]
    F --> G[Assemble Document<br/>(front‑matter + TOC + sections)]
    G --> H[Final Markdown Output]

    subgraph Template & Prompts
      T1[Template: sections & order]
      T2[Master Prompt]
      T3[Section Overrides]
      T4[Metadata]
    end

    T1 --> F
    T2 --> F
    T3 --> F
    T4 --> F
```

---

### Output Artifacts

- **Final**: Markdown with YAML front‑matter, TOC, and drafted sections.
- **Optional debug bundle** (useful for review):
  - Per‑step prompts (file‑summary, hierarchical, per‑section) and generated outputs.
  - Assembled document preview and section ordering.

---

### Example Stubs

#### Template Skeleton (excerpt)
```json
{
  "name": "AI‑Assisted Model Documentation",
  "prompts": {
    "master_prompt_text": "Write clear markdown sections with ## and ###; cite code components where helpful; keep within {{max_words}} words.",
    "overrides": {
      "implementation": "Enumerate key modules, classes, and their responsibilities.",
      "results": "Summarize findings and metrics succinctly; highlight what matters to the team."
    }
  },
  "sections": [
    { "id": "executive_summary", "title": "Executive Summary", "required": true },
    { "id": "overview", "title": "Model Overview" },
    { "id": "methodology", "title": "Methodology" },
    { "id": "implementation", "title": "Implementation", "required": true },
    { "id": "results", "title": "Results" },
    { "id": "recommendations", "title": "Recommendations" }
  ]
}
```

#### Master Prompt Skeleton
```text
Audience: model developers and adjacent stakeholders.
Voice: clear, concise, practical; markdown with ##/### headings.
Evidence: reference code components by name where helpful.
Scope: cover what/how/why; avoid speculation; mark N/A when not applicable.
Length: keep within {{max_words}} words when provided.
```

---

### Personalization Examples by Department

- Data Science: emphasize experiment tracking, feature pipelines, metrics, and error bars.
- Engineering: emphasize architecture, interfaces, deployment/configuration, observability.
- Product/Risk Ops: emphasize outcomes, assumptions, dependencies, and action items.

---

### Notes

- You can evolve templates and prompt sets per department/team to standardize style while keeping content grounded in your code and connected assets.


