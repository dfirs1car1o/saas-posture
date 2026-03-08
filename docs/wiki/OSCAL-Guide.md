# OSCAL Guide — What It Is and How We Use It

> **New to OSCAL?** Start here. This guide explains the standard from scratch, then walks through exactly how this system uses it — every file, every layer, every decision.

---

## What Is OSCAL?

OSCAL stands for **Open Security Controls Assessment Language**. It is an open standard published by NIST that gives security teams a common machine-readable language to describe:

- What security controls exist (catalog)
- Which controls apply to a given system (profile)
- How a system implements those controls (component definition)
- What evidence was collected during an assessment (assessment results)
- What gaps remain and when they will be fixed (POA&M)

Before OSCAL, every tool, auditor, and GRC platform used its own proprietary format. A Salesforce security report from one vendor looked nothing like one from another. OSCAL solves that by giving everyone the same schema — think of it like JSON for compliance.

**Why this matters to you:** When your OSCAL output files are valid, tools like RegScale, IBM Trestle, and the FedRAMP 20x automation platform can read them directly — no re-entry, no translation, no manual export.

---

## The OSCAL Stack — 7 Layers

OSCAL is not a single document. It is a stack of seven interconnected models. Each layer builds on the one below it.

```mermaid
flowchart TD
    A["📚 Catalog\nWhat controls exist"]
    B["🔍 Profile\nWhich controls apply"]
    C["⚙️ Component Definition\nHow to collect evidence"]
    D["📋 System Security Plan (SSP)\nHow the system is configured"]
    E["📝 Assessment Plan\nWhat will be tested"]
    F["📊 Assessment Results\nWhat was found"]
    G["🗂️ POA&M\nWhat gaps remain and when fixed"]

    A --> B --> C --> D --> E --> F --> G

    style A fill:#4a90d9,color:#fff
    style B fill:#5ba85a,color:#fff
    style C fill:#e8932a,color:#fff
    style D fill:#9b59b6,color:#fff
    style E fill:#c0392b,color:#fff
    style F fill:#16a085,color:#fff
    style G fill:#7f8c8d,color:#fff
```

| Layer | Model | Answers the question |
|---|---|---|
| 1 | **Catalog** | What security controls exist and what do they require? |
| 2 | **Profile** | Which subset of those controls applies to my platform? |
| 3 | **Component Definition** | How do I collect evidence for each control? |
| 4 | **System Security Plan** | How is the system configured to meet each control? |
| 5 | **Assessment Plan** | What will I test, when, and how? |
| 6 | **Assessment Results** | What did I find? Pass, fail, or partial? |
| 7 | **POA&M** | What gaps exist, who owns them, and when will they be fixed? |

> **We currently implement layers 1–3 and 6–7.** Layers 4–5 (SSP and Assessment Plan) are on the roadmap.

---

## Why We Use OSCAL

### Problem Without OSCAL

Before this system, a Salesforce security assessment looked like this:

```
Spreadsheet → Manual review → Word document → Email to stakeholder
```

No machine-readable output. No regulatory crosswalk. Nothing a GRC tool could import. Every assessment was one-off work.

### With OSCAL

```
OSCAL Catalog → OSCAL Profile → Evidence Collection → OSCAL Assessment Results → OSCAL POA&M
```

The output is a structured file any compliant tool can read. The CCM v4.1 regulatory crosswalk (SOX, HIPAA, SOC2, ISO 27001, NIST 800-53, PCI DSS, GDPR) comes for free because it lives in the catalog layer and flows down automatically.

---

## Our OSCAL Architecture

Here is how the three frameworks we assess against relate to each other, and how they map to the OSCAL stack:

```mermaid
flowchart TD
    subgraph LAYER1["Layer 1 — Catalogs"]
        CCM["CSA CCM v4.1\n207 controls, 17 domains\nRegulatory crosswalk:\nSOX · HIPAA · SOC2 · ISO 27001\nNIST 800-53 · PCI DSS · GDPR"]
        SSCF["SSCF v1.0 Catalog\n36 controls, 6 domains\nCON · DSP · IAM · IPY · LOG · SEF\nconfig/sscf/sscf_v1_catalog.json"]
    end

    subgraph LAYER2["Layer 2 — Profiles (platform subsets)"]
        SBS["SBS v1.0 Profile\n35 controls\nSalesforce-specific\nconfig/salesforce/sbs_v1_profile.json"]
        WSCC["WSCC v1.0 Profile\n30 controls\nWorkday-specific\nconfig/workday/wscc_v1_profile.json"]
    end

    subgraph LAYER3["Layer 3 — Component Definitions (evidence specs)"]
        SFDC_CD["Salesforce Component\n18 implemented requirements\nSOQL · Tooling API · Metadata API\nconfig/component-definitions/salesforce_component.json"]
        WD_CD["Workday Component\n16 implemented requirements\nSOAP · RaaS · REST · ISSG perms\nconfig/component-definitions/workday_component.json"]
    end

    CCM -->|"CCM control IDs\nembedded via ccm-controls prop"| SSCF
    SSCF --> SBS
    SSCF --> WSCC
    SBS --> SFDC_CD
    WSCC --> WD_CD

    style CCM fill:#4a90d9,color:#fff
    style SSCF fill:#4a90d9,color:#fff
    style SBS fill:#5ba85a,color:#fff
    style WSCC fill:#5ba85a,color:#fff
    style SFDC_CD fill:#e8932a,color:#fff
    style WD_CD fill:#e8932a,color:#fff
```

### Why This Hierarchy?

**CCM is the foundation.** The Cloud Security Alliance CCM v4.1 is the authoritative cloud security control framework, with 207 controls and a built-in regulatory crosswalk. Rather than rebuilding that crosswalk ourselves, we embed CCM control IDs in our catalog and let the CCM carry the regulatory weight.

**SSCF is our working layer.** The SaaS Security Customer Framework is a 36-control subset of CCM focused on what a SaaS *customer* can configure and assess — not what the vendor controls. SSCF is our catalog.

**SBS and WSCC are the platform lenses.** The Security Benchmark for Salesforce (SBS) and Workday Security Control Catalog (WSCC) are OSCAL profiles that select the SSCF controls relevant to each platform and add platform-specific evidence collection notes.

**Component Definitions are the automation engine.** They specify exactly which API to call, which field to check, and what the pass/fail condition is for every control. This is what makes the collector generic — it reads the component definition rather than having logic hardcoded in Python.

---

## The SSCF v1.0 Control Domains

SSCF v1.0 has 36 controls across 6 domains. Domain codes match CCM v4.1 for interoperability.

```mermaid
pie title SSCF v1.0 — Controls by Domain
    "CON — Configuration Hardening" : 6
    "DSP — Data Security & Privacy" : 6
    "IAM — Identity & Access Management" : 8
    "IPY — Interoperability & Portability" : 5
    "LOG — Logging & Monitoring" : 6
    "SEF — Security Incident Management" : 5
```

| Domain | Code | Controls | What it covers |
|---|---|---|---|
| Configuration Hardening | CON | 6 | Baselines, drift detection, credential lifecycle, hardening, patching |
| Data Security & Privacy | DSP | 6 | Sensitive data access, export controls, classification, retention, privacy rights |
| Identity & Access Management | IAM | 8 | MFA, privileged access, SSO, user lifecycle, service accounts, sessions, JIT, guest access |
| Interoperability & Portability | IPY | 5 | Data portability, API security, integration inventory, vendor exit, data residency |
| Logging & Monitoring | LOG | 6 | Telemetry, admin logging, retention, real-time alerting, SIEM integration, UEBA |
| Security Incident Management | SEF | 5 | Threat enforcement, alert triage, IR plan, forensics, exception governance |

---

## How a Control Flows Through the System

This shows exactly what happens to a single control — `SSCF-IAM-001 (MFA Enforcement)` — from definition to finding:

```mermaid
flowchart LR
    A["SSCF v1.0 Catalog\nsscf-iam-001\nccm-controls: IAM-02\nseverity: critical"]
    B["SBS v1.0 Profile\nselects sscf-iam-001\n+ Salesforce platform note"]
    C["Component Definition\ncollection-method: tooling\napi: SecurityHealthCheckRisks\npass: MFA_Required=true"]
    D["sfdc_connect.py\ncollects evidence\nqueries Tooling API"]
    E["gap_analysis.json\ncontrol: SSCF-IAM-001\nstatus: fail\nevidence: MFA disabled"]
    F["sscf_report.json\nIAM domain: 50% AMBER"]
    G["Report\nCritical finding: MFA\nnot enforced"]

    A --> B --> C --> D --> E --> F --> G

    style A fill:#4a90d9,color:#fff
    style B fill:#5ba85a,color:#fff
    style C fill:#e8932a,color:#fff
    style D fill:#9b59b6,color:#fff
    style E fill:#c0392b,color:#fff
    style F fill:#16a085,color:#fff
    style G fill:#7f8c8d,color:#fff
```

---

## What Each Config File Does

Here is every OSCAL-related file in this repo and what it is for:

```mermaid
flowchart TD
    subgraph CATALOG["Catalog Layer"]
        C1["config/sscf/sscf_v1_catalog.json\n✦ The SSCF v1.0 catalog\n✦ 36 controls, 6 domains\n✦ CCM v4.1 IDs in ccm-controls prop\n✦ Statement · Guidance · Objective per control"]
        C2["config/sscf/sscf_catalog.json\n✦ Legacy v0 catalog (14 controls)\n✦ Kept for pipeline backward-compat\n✦ Will be deprecated after Phase I"]
    end

    subgraph PROFILE["Profile Layer"]
        P1["config/sscf/sscf_v1_profile.json\n✦ Selects all 36 SSCF v1.0 controls\n✦ Base profile — platforms inherit from this"]
        P2["config/salesforce/sbs_v1_profile.json\n✦ Selects 35 SSCF controls for Salesforce\n✦ Adds Salesforce-specific platform notes\n✦ (JWT, Event Monitoring, Health Check)"]
        P3["config/workday/wscc_v1_profile.json\n✦ Selects 30 SSCF controls for Workday\n✦ Adds ISSG permission notes\n✦ (SOAP/RaaS/REST, OAuth 2.0)"]
    end

    subgraph COMPDEF["Component Definition Layer"]
        D1["config/component-definitions/salesforce_component.json\n✦ 18 controls with API evidence specs\n✦ Tooling API · SOQL · Metadata API\n✦ Pass/fail criteria per control"]
        D2["config/component-definitions/workday_component.json\n✦ 16 controls with API evidence specs\n✦ SOAP operations · RaaS reports · REST endpoints\n✦ ISSG permission listed per control"]
    end

    subgraph MAPPING["Mapping / Reference"]
        M1["config/sscf/sscf_to_ccm_mapping.yaml\n✦ SSCF → CCM v4.1 bridge\n✦ Regulatory highlights per CCM control\n✦ Mapping strength: direct · partial"]
        M2["config/ccm/ccm_v4.1_oscal_ref.yaml\n✦ CCM v4.1 reference pointer\n✦ Download URL, domains, control count\n✦ Not copied — linked by reference"]
        M3["config/sscf_control_index.yaml\n✦ Quick-reference index, 36 controls\n✦ Domain · severity · owner · v0 equivalent"]
    end

    C1 --> P1 --> P2 --> D1
    P1 --> P3 --> D2
    C1 --> M1 --> M2
```

---

## The Assessment Pipeline

This shows how the collector and assessor skills use the OSCAL config files to produce findings:

```mermaid
sequenceDiagram
    participant ORC as Orchestrator Agent
    participant COL as Collector Skill
    participant PLT as Platform (Salesforce / Workday)
    participant COMP as Component Definition
    participant ASS as Assessor Skill
    participant BENCH as SSCF Benchmark
    participant RPT as Report Generator

    ORC->>COL: collect --scope all
    COL->>COMP: read evidence spec for each control
    COMP-->>COL: api-endpoint, pass-criteria, fail-criteria
    COL->>PLT: query API (Tooling/SOQL/SOAP/RaaS)
    PLT-->>COL: raw evidence JSON
    COL-->>ORC: sfdc_raw.json / workday_raw.json

    ORC->>ASS: assess (gap mapping)
    ASS->>COMP: read SSCF control requirements
    ASS->>ASS: compare evidence vs pass-criteria
    ASS-->>ORC: gap_analysis.json (status per control)

    ORC->>BENCH: benchmark (score by domain)
    BENCH->>BENCH: aggregate by SSCF domain
    BENCH-->>ORC: sscf_report.json (% scores, RED/AMBER/GREEN)

    ORC->>RPT: generate (app-owner + security)
    RPT-->>ORC: .md + .docx governance reports
```

---

## CCM Regulatory Crosswalk — How It Flows

Because every SSCF control references one or more CCM v4.1 controls via the `ccm-controls` prop, the regulatory mapping comes for free:

```mermaid
flowchart LR
    subgraph SSCF["SSCF Control"]
        S1["SSCF-IAM-001\nMFA Enforcement"]
    end

    subgraph CCM["CCM v4.1"]
        C1["IAM-02\nMulti-Factor Authentication"]
    end

    subgraph REG["Regulatory Coverage (from CCM)"]
        R1["SOC2 CC6.1"]
        R2["HIPAA §164.312(d)"]
        R3["ISO 27001 A.9.4.2"]
        R4["PCI DSS 8.4"]
        R5["NIST 800-53 IA-2"]
    end

    S1 -->|ccm-controls: IAM-02| C1
    C1 --> R1
    C1 --> R2
    C1 --> R3
    C1 --> R4
    C1 --> R5
```

**You do not need to maintain the regulatory crosswalk.** When a new regulation maps to CCM controls, and we reference those CCM controls in our SSCF catalog, the regulatory coverage updates automatically.

---

## OSCAL Interoperability

Because this system produces OSCAL-structured outputs, other tools can consume them directly:

```mermaid
flowchart LR
    subgraph OUR["This System"]
        AR["Assessment Results\n(gap_analysis.json → OSCAL AR)"]
        POAM["POA&M\n(backlog.json → OSCAL POA&M)"]
    end

    subgraph TOOLS["Compatible Tools"]
        RS["RegScale\nGRC automation"]
        TR["IBM Compliance Trestle\nOSCAL authoring"]
        FED["FedRAMP 20x\nFederal compliance"]
        CLI["oscal-cli\nValidation & profile resolution"]
        SC["oscal-compass\nCommunity tooling"]
    end

    AR --> RS
    AR --> TR
    AR --> FED
    POAM --> RS
    POAM --> TR
    POAM --> CLI

    style AR fill:#16a085,color:#fff
    style POAM fill:#7f8c8d,color:#fff
```

> **Note:** Full OSCAL AR and POA&M output is on the roadmap (Phase I). The current `gap_analysis.json` and `backlog.json` follow OSCAL field naming conventions but are not yet fully OSCAL-schema-valid. Phase I migrates them to the official formats.

---

## SSCF v1.0 → OSCAL v0 Control Migration

When we rebuilt from 14 controls (v0) to 36 controls (v1.0), some controls moved domains. Here is the mapping:

| Old ID (v0) | Old Domain | New ID (v1.0) | New Domain | Reason |
|---|---|---|---|---|
| SSCF-CKM-001 | Cryptography (non-standard) | SSCF-CON-003 | Configuration Hardening | Credential lifecycle is a config control per SSCF v1.0 |
| SSCF-TDR-001 | Threat Detection (non-standard) | SSCF-SEF-001 | Security Incident Mgmt | TDR is not a CCM domain; SEF is the correct mapping |
| SSCF-TDR-002 | Threat Detection (non-standard) | SSCF-SEF-002 | Security Incident Mgmt | Same as above |
| SSCF-GOV-001 | Governance (non-standard) | SSCF-SEF-005 | Security Incident Mgmt | Exception governance belongs in SEF per SSCF v1.0 |

The `sscf-v0-equivalent` prop in the v1.0 catalog records these mappings so tools can trace findings across versions.

---

## Common Questions

**Q: Do I need to register anywhere or download anything to use OSCAL?**
No. OSCAL is an open JSON/YAML schema standard. All the OSCAL files in this repo are self-contained. We reference CCM v4.1 control IDs in properties rather than embedding the full CCM catalog, so no download or account is required.

**Q: What does an OSCAL catalog look like in plain English?**
It is a JSON file that says: "Control IAM-001 is called 'MFA Enforcement'. It says: require MFA for all accounts. The guidance is: FIDO2 is preferred, SMS is discouraged for admins. The objective is: verify MFA is enforced, not just offered."

**Q: What is the difference between a catalog and a profile?**
A catalog is a library of all possible controls. A profile is "these are the controls that apply to us" — a curated subset. Think of a catalog as a textbook and a profile as the syllabus for your class.

**Q: What is a component definition?**
It answers "how specifically do I check this control in Salesforce (or Workday)?" For example, the Salesforce component definition for MFA says: call the Tooling API, query `SecurityHealthCheckRisks`, look for the MFA risk row, and check if `EnableMfaDirectUi=true`. That is the pass condition.

**Q: What is the CCM and why does it matter?**
The CSA Cloud Controls Matrix (CCM) v4.1 has 207 controls across 17 cloud security domains. Its main value is a built-in regulatory crosswalk — every CCM control is already mapped to SOX, HIPAA, SOC2, ISO 27001, NIST 800-53, PCI DSS, and GDPR. By referencing CCM control IDs, our SSCF controls inherit those regulatory mappings for free.

**Q: Will findings from this tool be accepted by a FedRAMP auditor?**
After Phase I (OSCAL AR + POA&M), the output files will be OSCAL-schema-valid and compatible with FedRAMP 20x automation tooling. Acceptance by a specific auditor depends on their tooling and process — but OSCAL-valid output is the baseline requirement.

---

## Further Reading

| Resource | Link |
|---|---|
| NIST OSCAL project | https://pages.nist.gov/OSCAL/ |
| OSCAL catalog schema | https://pages.nist.gov/OSCAL/reference/latest/catalog/ |
| CSA CCM v4.1 | https://cloudsecurityalliance.org/artifacts/cloud-controls-matrix-v4-1 |
| awesome-oscal community list | https://github.com/oscal-club/awesome-oscal |
| IBM Compliance Trestle | https://github.com/oscal-compass/compliance-trestle |
| CivicActions OSCAL components | https://github.com/CivicActions/oscal-component-definitions |
