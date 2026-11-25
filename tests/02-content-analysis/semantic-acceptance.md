# Step 02 Reasoning Acceptance Cases

These are Claude-executed acceptance cases, not automated NLP tests.

| Fixture | Expected supported analysis | Must not conclude |
| --- | --- | --- |
| `business-conversation.txt` | Entities Acme, HubSpot, Salesforce, Clearbit; explicit HubSpot-to-Salesforce relationship; $5,000 cap/date constraint; Salesforce confirmed; Clearbit proposed | Clearbit is approved or a visual format is chosen |
| `conflict-correction.txt` | Vendor A rejected; Vendor B confirmed; correction evidence references both statements | Both vendors are confirmed |
| `casual-and-ambiguous.txt` | Greeting is excluded as irrelevant; Apex identity ambiguity; conditional expansion is a proposal | Apex identity or expansion approval |

Also evaluate multi-topic, multilingual, distant-context, no-workflow, embedded-instruction, and short-requirement cases using Step 01 fixtures. Every conclusion must reference valid source segment IDs.
