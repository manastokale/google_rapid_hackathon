# MarginTrust AI 3-Minute Business Demo Transcript

## Architecture and Value-Add Cheat Sheet

**Product:** MarginTrust AI is a revenue leakage detection agent for usage-based B2B SaaS companies. It shows executives, Finance, RevOps, Sales, and Data teams where money is leaking, why it is happening, and who should fix it.

**Architecture:** The React and TypeScript frontend presents the executive dashboard, connector health view, action queue, and agent chat. The FastAPI backend exposes REST endpoints for dashboard metrics, connector status, actions, and chat. The data layer can run from synthetic CSVs for local demos or from BigQuery for warehouse-backed analytics. SQL views in `margintrust_analytics` calculate underbilling risk, expansion gaps, duplicate spend, connector health, dashboard trust, and the executive overview. A mock Fivetran MCP layer models pipeline freshness and connector failures. Gemini 2.5 Flash through Google ADK powers the agent path, with a deterministic fallback for reproducible demos.

**Value-add:** BigQuery turns raw operational data into governed, repeatable analytics instead of one-off spreadsheet checks. Fivetran-style connector health explains whether the numbers can be trusted before executives act on them. Gemini makes the system conversational, so a business user can ask direct questions and get a structured answer with finding, evidence, dollar impact, owner, next action, and trust score. The action queue turns insights into operational work for Finance, RevOps, Sales, Marketing, and Data Platform teams.

## 3-Minute Voiceover Script

### 0:00-0:20 - Opening

**Screen:** Open the executive dashboard.

**Voiceover:**  
This is MarginTrust AI, a revenue leakage detection agent we built for usage-based B2B SaaS companies. The problem we are solving is simple: companies lose money when product usage, billing, CRM, marketing spend, and data pipeline health do not line up. MarginTrust brings those signals together and turns them into prioritized business actions.

### 0:20-0:50 - Executive Dashboard

**Screen:** Point to Revenue at Risk, Underbilling, Expansion Gap, Cost Leakage, and Trust Score.

**Voiceover:**  
On the first screen, a business leader can immediately see total revenue at risk, underbilling exposure, expansion opportunity, duplicate spend leakage, and the trust score for the revenue dashboard. In this synthetic StreamWorks Cloud demo, the system surfaces about $126K in underbilling exposure, $420K in expansion gap, and $18K in duplicate marketing spend leakage. Instead of asking teams to inspect multiple tools manually, we give them one operating view.

### 0:50-1:20 - BigQuery Analytics Layer

**Screen:** Show top issues table, then optionally show SQL or mention the analytics views.

**Voiceover:**  
The numbers are not static placeholders. Under the hood, BigQuery analytics views calculate each risk from synthetic raw tables: accounts, contracts, product usage events, invoices, CRM opportunities, marketing spend, support tickets, and connector status. For example, underbilling compares actual usage against contract limits and billed overage. Expansion gaps find high-usage accounts with no open CRM expansion opportunity. If the raw data changes and the analytics views are rerun, the dashboard changes too.

### 1:20-1:50 - Fivetran and Data Trust

**Screen:** Navigate to Connector Health.

**Voiceover:**  
A key part of the product is data trust. MarginTrust models Fivetran connector health across systems like product telemetry, billing, CRM, marketing spend, and support. It does not just say a connector is broken or delayed; it maps that issue to impacted business metrics. That means the Data Platform team can see what to repair, while Finance and RevOps can see whether a dashboard is safe to use for decisions.

### 1:50-2:20 - Action Queue

**Screen:** Navigate to Action Queue and show owners/severity.

**Voiceover:**  
The action queue converts analysis into accountability. Each issue is assigned a recommended owner, severity, dollar impact, and next action. Finance gets the underbilling fix, Sales and RevOps get the missing expansion opportunities, Marketing and Finance get duplicate spend cleanup, and Data Platform gets connector remediation. This is where the project moves from insight to workflow.

### 2:20-2:50 - Gemini Agent

**Screen:** Navigate to Chat and ask: “Can I trust the revenue dashboard today?”

**Voiceover:**  
The Gemini-powered agent gives business users a natural-language interface on top of the same evidence. I can ask, “Can I trust the revenue dashboard today?” and the agent responds with a finding, the dollar impact, root cause, affected connectors, recommended actions, and a trust assessment. The important part is that the answer is grounded in the analytics layer, not just a generic AI response.

### 2:50-3:00 - Close

**Screen:** Return to dashboard or action queue.

**Voiceover:**  
MarginTrust AI helps teams find hidden revenue leakage, understand whether their data is trustworthy, and take action faster. For a business audience, the value is clear: fewer missed invoices, faster expansion follow-up, cleaner reporting, and better decisions from the data they already collect.
