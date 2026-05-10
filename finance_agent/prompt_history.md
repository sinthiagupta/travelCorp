# Prompt Engineering & Iteration Log
*Project: Finance Credit Follow-Up Agent*

This document serves as an engineering log detailing the iterative development of the core LLM prompt. The goal of this evolution was to transition from a naive zero-shot approach to a highly deterministic, production-ready prompt that strictly enforces UI constraints, dynamic data injection, and specific tone architectures.

---

## Phase 1: Naive Zero-Shot Implementation

**Initial Approach:**
We began with a basic zero-shot prompt passing minimal context:
*"Write an email to {client_name} for invoice {invoice_id} that is {days_overdue} days late using a {assigned_tone} tone."*

**Engineering Challenges:**
- **Hallucination & Autonomy:** Without explicit guardrails, the LLM made assumptions. It erroneously included payment links in highly formal/stern emails and completely fabricated missing details (like the original due date).
- **Tone Drift:** The model struggled to differentiate between "Polite" and "Stern" without explicit behavioral definitions, often defaulting to a standard, overly friendly customer service tone regardless of the days overdue.

**Architectural Decision:** We needed to implement strict behavioral guardrails and explicit variable constraints.

---

## Phase 2: Context Overload & Static Rules

**Initial Approach:**
We over-corrected by providing the LLM with the entire rulebook. We listed all mandatory data fields and explicitly provided the definitions for all four tones (Warm, Polite, Formal, Stern) in every single prompt execution.

**Engineering Challenges:**
- **Context Pollution:** By passing the rules for all four tones simultaneously, we polluted the LLM's context window. Even when tasked with writing a "Stern" email, the LLM had to process the "Warm" instructions, occasionally blending the tones.
- **Placeholder Generation:** The model lacked global state context, frequently hallucinating the sender identity (e.g., generating "Sincerely, [Your Company Name]").

**Architectural Decision:** Transition from static, monolithic prompts to dynamic, state-driven prompt generation.

---

## Phase 3: Dynamic State-Driven Prompting (The Core Architecture)

**Initial Approach:**
We refactored the Python logic to use a state-driven dictionary (`TONE_CTA`). The application logic now evaluates the `days_overdue`, selects the correct tone, and injects *only* the specific Call to Action (CTA) instruction relevant to that tone into the prompt. Furthermore, the company identity ("TravelCorp") was hardcoded into the system context.

**Results:**
- **Precision:** Tone drift was completely eliminated. The LLM executed the exact required behavior with 100% adherence because it only received the rules pertinent to its current graph state.
- **Efficiency:** The token count of the prompt was significantly reduced, lowering latency and API costs.

---

## Phase 4: Output Parsing & Anti-Hallucination Tactics

**Initial Approach:**
With the logic stabilized, we noticed a UX issue. We instructed the LLM: `INVOICE DETAILS (include ALL in the email):` followed by a raw bulleted list.

**Engineering Challenges:**
The LLM acted lazily. Instead of generating a cohesive, professional business email, it literally copied and pasted the raw bulleted list into the center of the email body. It read like a database dump rather than a communication from a human collections agent.

**Architectural Decision:** We explicitly forbade raw data dumps in the prompt instructions, forcing the LLM to weave the injected variables naturally into human-readable paragraphs.

---

## Phase 5: UI Integration & Strict Structural Templating

**Initial Approach:**
The natural paragraphs from Phase 4 were grammatically perfect, but they surfaced a critical UI rendering constraint. The LLM generated the email as one massive, unbroken block of text. Furthermore, the paragraphs lacked the formal, structural layout expected in enterprise communications.

**Engineering Challenges:**
- **Rendering Errors:** Streamlit UI components squished the text together due to a lack of explicit newline characters in the LLM's JSON response.
- **UX Inconsistency:** The emails did not look like formal letters. 

**Architectural Decision (Current Production State):**
We overhauled the prompt to utilize a **Strict Spatial Template**. We explicitly commanded the LLM to follow a hardcoded letter structure (Subject, Formal Greeting, a cleanly formatted row-wise "Invoice Details" block, the tone-specific body paragraph, and a standardized sign-off). 
Most importantly, we injected a critical programmatic instruction: `You MUST use exact newline characters (\n\n) to separate paragraphs in the body.`

**Results:** The output is now flawlessly formatted, highly deterministic, and renders beautifully within the Streamlit Master-Detail UI.

---

## Engineering Retrospective

The evolution of this prompt highlights a critical lesson in Agentic AI development: **LLMs require programmatic boundaries.** 

We transitioned from treating the LLM as a human assistant (giving it vague instructions) to treating it as a function within a larger pipeline. By moving logic out of the prompt and into Python (dynamic state injection) and enforcing strict structural templates (newline characters and spatial layouts), we transformed a highly volatile text generator into a deterministic, enterprise-ready engine.