Architectural Decision Records (ADRs): On-Demand Template

This rule provides an on-demand ADR template. When a developer types @adr, the system responds with the standard Michael Nygard ADR structure. This pattern avoids consuming context window tokens until needed.

<b>Activation:</b> Manual Activation   
<b>Description:</b> When user types @adr, provide the standard ADR template.

When the user types @adr, respond with this markdown template, guiding them section-by-section. Ensure Context, Decision, and Consequences are always completed.   

Store it in an /adr folder under the root repo folder

ADR-XXX:


Status: (Proposed | Accepted | Deprecated | Superseded by ADR-XXX)


Context:


Decision:


Consequences: