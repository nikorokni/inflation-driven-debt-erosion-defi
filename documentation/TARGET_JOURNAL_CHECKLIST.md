# Preliminary target-journal checklist

Target considered: *Blockchain: Research and Applications* (Elsevier). This is a preliminary technical checklist, not a statement that the manuscript has been submitted or formally accepted by the journal.

Official sources checked on 10 August 2026:

- Journal Guide for Authors: <https://www.sciencedirect.com/journal/blockchain-research-and-applications/publish/guide-for-authors>
- Elsevier research-data guidance: <https://www.elsevier.com/researcher/author/tools-and-resources/research-data/data-guidelines>

| Item | Status | Evidence or action |
|---|---|---|
| English manuscript with title, author affiliations, abstract, and keywords | Addressed | `manuscript/main.tex` |
| Clear contribution and empirical limits | Addressed | Introduction, Methods, and Limitations |
| Numbered sections, equations, tables, and figures | Addressed | Compiled manuscript |
| Data and code availability statements | Addressed | End matter and accompanying revision package; verify updated GitHub commit before submission |
| Reproducible extraction and source provenance | Addressed | `documentation/SOURCES.md`, `source_query.sql`, decoder |
| Editable source and compiled PDF | Addressed | `manuscript/main.tex`, `manuscript/main.pdf` |
| Legible figures with captions and source notes | Addressed | Revised 220-dpi PNGs in `figures/` and manuscript captions |
| Reference list consistently formatted | Addressed | `manuscript/references.tex` |
| Conflict-of-interest, funding, and ethics statements | Addressed | Declarations section |
| Research data linked to the article | Confirm before submission | Verify the revised code and outputs have been published to the linked GitHub repository |
| Journal-specific document class/template | Confirm before submission | Current source uses `sn-jnl`; migrate only after the final target and article type are confirmed |
| Article type, word limit, and figure/table limits | Confirm before submission | Recheck the live Guide for Authors at submission time |
| CRediT author-contribution statement | Author confirmation required | Roles must be supplied and approved by all authors; not inferred by the analysis code |
| Corresponding-author and coauthor approval | Author confirmation required | Confirm identities, order, emails, and consent before submission |
| Generative-AI disclosure, if required by current policy | Author confirmation required | Follow the journal's live disclosure policy at submission |
| Highlights, graphical abstract, or separate cover letter | Confirm before submission | Prepare only if required for the selected article type |
| Salma's suggested/excluded editorial names | Author/editorial choice | Not part of the replication package |

The live guide should be checked again immediately before submission because editorial requirements can change.
