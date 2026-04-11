# Developer Productivity Prompt Pack
**By ForgeCore / Em**
**Price:** $9
**Version:** 1.0 — April 2026

> 30 sharp, battle-tested prompts for developers who use AI daily. No fluff. No filler. Just prompts that actually work.

---

## SECTION 1: CODE REVIEW & QUALITY (6 prompts)

**1. The Brutal Reviewer**
```
Review this code as a senior engineer who has been burned by production bugs before. Don't be polite. Flag every assumption, every edge case, every place this could fail silently. Then rank your findings by severity.

[paste code]
```

**2. The Security Audit**
```
Audit this code specifically for security vulnerabilities. Check for: injection risks, improper auth, insecure data handling, exposed secrets, and trust boundary violations. For each finding, explain the attack vector and the fix.

[paste code]
```

**3. The Performance Profiler**
```
Analyze this code for performance issues. Identify: unnecessary loops, redundant computations, memory leaks, blocking operations, and inefficient data structures. Suggest concrete optimizations with expected impact.

[paste code]
```

**4. The Rubber Duck (With Teeth)**
```
I'm going to explain this code to you like a rubber duck, but you're a rubber duck that asks hard questions. After I explain it, challenge my assumptions, point out gaps in my reasoning, and ask the question I'm probably avoiding.

[explain your code/approach]
```

**5. The Test Coverage Mapper**
```
Given this function/module, write an exhaustive list of test cases I should cover — including happy paths, edge cases, error conditions, and boundary values. Then write the most important 5 tests in [language].

[paste code]
```

**6. The Legacy Decoder**
```
This code was written by someone who is no longer available. Explain what it does, why it probably does it that way (what problem was being solved), what's fragile about it, and what I should NOT touch without understanding first.

[paste legacy code]
```

---

## SECTION 2: DEBUGGING & PROBLEM SOLVING (6 prompts)

**7. The Error Archaeologist**
```
Here's an error I'm seeing. Walk me through every possible cause in order of likelihood, what I should check to confirm or rule out each one, and what the fix would be for each.

Error: [paste error]
Context: [language, framework, what you were doing]
```

**8. The Minimal Reproducer**
```
I have a bug that's hard to reproduce. Help me strip my code down to the smallest possible case that still demonstrates the problem. Ask me questions to understand what can be removed, then help me write the minimal reproducer.

Bug description: [describe the bug]
Full code: [paste code]
```

**9. The Hypothesis Generator**
```
My code isn't behaving as expected and I don't know why. Generate 10 hypotheses for what could be wrong, ranked by likelihood. For each, tell me exactly what to check or log to confirm it.

Expected behavior: [what should happen]
Actual behavior: [what's happening]
Code: [paste relevant code]
```

**10. The State Tracer**
```
Trace the state of this program step by step from input to output. At each step, tell me the value of every relevant variable. If you find a step where the state diverges from what I'd expect, flag it.

Input: [your input]
Code: [paste code]
Expected output: [what you expect]
```

**11. The Dependency Untangler**
```
I have a dependency/import/version conflict I can't resolve. Walk me through it systematically. What's actually conflicting, why, and what are my options in order from least to most disruptive?

Error: [paste error]
Environment: [language, package manager, relevant versions]
```

**12. The "Works On My Machine" Killer**
```
My code works locally but fails in [staging/production/CI]. Help me build a systematic checklist of every environmental difference that could cause this — config, secrets, versions, OS, network, file paths, timing. Then help me test each one.

Local setup: [describe]
Remote setup: [describe]
Failure: [describe]
```

---

## SECTION 3: ARCHITECTURE & DESIGN (6 prompts)

**13. The Architecture Interrogator**
```
I'm designing [system/feature]. Before I build anything, interrogate my design. Ask me the 10 most important questions I should be able to answer before writing a line of code. Then tell me which ones I probably can't answer yet.

What I'm building: [describe]
```

**14. The Tradeoff Mapper**
```
I need to choose between these approaches for [problem]. For each option, give me: the core tradeoff, who it's right for, what breaks down at scale, and the hidden cost that people don't mention.

Options: [list your options]
Context: [team size, scale, constraints]
```

**15. The Schema Designer**
```
Design a database schema for [use case]. Show me the tables, relationships, and indexes. Then tell me: what queries will be fast, what will be slow, and what will break when the data grows 100x.

Use case: [describe]
Expected scale: [rows, queries/sec, growth rate]
```

**16. The API Contract Writer**
```
Design the API contract for [feature/service]. Give me: endpoints, request/response shapes, error codes, auth approach, and versioning strategy. Then identify the three decisions I'll regret if I get them wrong now.

Feature: [describe]
Clients: [who calls this API]
```

**17. The Refactor Planner**
```
I need to refactor this code but I can't break anything and I can't do it all at once. Create a step-by-step refactor plan where each step leaves the code in a working, deployable state. Flag which steps are highest risk.

Current code: [paste or describe]
Goal: [what you want it to look like]
```

**18. The Second System Warning**
```
I'm about to build [thing]. Based on what I've described, tell me: where am I over-engineering, where am I under-engineering, and what's the simplest version of this that would actually solve the problem?

What I'm planning: [describe in detail]
```

---

## SECTION 4: WRITING & COMMUNICATION (6 prompts)

**19. The PR Description Writer**
```
Write a pull request description for this change. Include: what changed and why, what the reviewer should focus on, any risks or side effects, and how to test it. Be specific, not generic.

Change summary: [describe what you did]
Key files changed: [list them]
```

**20. The Commit Message Crafter**
```
Write a commit message for this change following conventional commits format. Give me 3 options: one minimal, one detailed, one that would make future-me grateful at 2am during an incident.

What changed: [describe]
```

**21. The Tech Debt Documenter**
```
Help me write a tech debt ticket for this shortcut I'm taking. Include: what we're doing, why we're doing it now, what the real solution is, what the cost of NOT fixing it is, and what the trigger should be for fixing it.

Shortcut: [describe]
```

**22. The Postmortem Writer**
```
Help me write a blameless postmortem for this incident. Structure: timeline, root cause, contributing factors, impact, what went well, what didn't, and action items with owners. Tone: honest, forward-looking, not defensive.

Incident: [describe what happened]
```

**23. The README Generator**
```
Write a README for this project that a new developer could actually use. Include: what it does (one sentence), why it exists, how to set it up from zero, the most common use cases with examples, and the gotchas that will waste their time if they don't know.

Project: [describe]
Stack: [list technologies]
```

**24. The Decision Record**
```
Help me write an Architecture Decision Record (ADR) for this choice. Include: context, decision, alternatives considered, consequences, and the date this should be revisited.

Decision: [what you decided]
Alternatives: [what you considered]
```

---

## SECTION 5: PRODUCTIVITY & WORKFLOW (6 prompts)

**25. The Task Decomposer**
```
Break this feature/task down into the smallest possible units of work that are each independently completable and testable. Order them by dependency. Flag which ones I can parallelize.

Feature: [describe]
Constraints: [team size, deadline, tech stack]
```

**26. The Estimation Calibrator**
```
I need to estimate this work. Help me think through it systematically: what do I know, what am I assuming, where are the unknowns, and what's the distribution of possible outcomes (best case / likely / nightmare). Give me a range, not a number.

Work to estimate: [describe]
```

**27. The Context Switcher**
```
I'm about to context switch away from this for [time period]. Help me write a "parking note" — a summary of exactly where I am, what I was thinking, what's next, and what I'll need to re-load when I come back.

Current state: [describe where you are]
```

**28. The Scope Negotiator**
```
I've been asked to build [feature] by [deadline] and it's not realistic. Help me prepare for a scope negotiation. What's the MVP that delivers real value? What can be cut without killing the core? What's the cost of each cut in concrete terms?

Full ask: [describe]
Deadline: [when]
Actual capacity: [honest estimate]
```

**29. The Learning Accelerator**
```
I need to get productive in [technology/framework/language] as fast as possible. I already know [what you know]. Give me: the 20% I need to know to do 80% of the work, the most common mistakes beginners make, and the one resource that's actually worth my time.

Target: [what you're learning]
Background: [what you already know]
```

**30. The End-of-Day Closer**
```
Here's what I worked on today: [summary]. Help me: identify what I actually accomplished vs. what I just stayed busy doing, write tomorrow's top 3 priorities in order of real impact, and flag anything I'm avoiding that I shouldn't be.

Today's work: [describe your day]
```

---

## How to Get the Most Out of These

- **Be specific.** The more context you give, the sharper the output. These prompts have placeholders in brackets — fill them in with real details, not vague descriptions.
- **Stack them.** Start with #13 (Architecture Interrogator) before you build, use #1 (Brutal Reviewer) when you're done, and end with #22 (Postmortem Writer) when something breaks.
- **Iterate.** If the first response isn't quite right, say "push harder" or "be more specific about X." These are starting points, not magic spells.
- **Save your best results.** When a prompt produces something genuinely useful, save the prompt + response as a template. You're building your own pack on top of this one.

---

*Built by Em for ForgeCore. If this saved you time, tell a developer friend.*
*Questions or feedback: forgecore.co*
