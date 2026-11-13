# Manual audit results — Day 06

This audit records the results from the actual stored benchmark trace. AI was used to extract the selected records and calculate averages; the labels below are based on inspection of the retrieved chunk text and must be reviewed by the author before submission.

## 1. Chunk coherence

The same ten physical pages were sampled for A, B and C. C uses the same chunks as B, so its coherence labels are identical to B.

Scoring: `0` = broken or unintelligible, `1` = partly understandable, `2` = self-contained and coherent.

| Physical page | A score | B score | C score | Rationale |
|---:|---:|---:|---:|---|
| 20 | 1 | 1 | 1 | Page begins in continuing prose; fixed and paragraph chunks inherit the page boundary. |
| 25 | 2 | 2 | 2 | Main limitation example is contained in the selected chunk. |
| 40 | 1 | 2 | 2 | Fixed chunk crosses a topic boundary; paragraph chunk preserves the social-good explanation. |
| 41 | 1 | 2 | 2 | Fixed chunk splits the biased-data explanation; paragraph chunk keeps more context. |
| 52 | 1 | 1 | 1 | Page contains several computational-thinking bullets and transitions. |
| 53 | 2 | 2 | 2 | Decomposition and the related techniques are readable in context. |
| 71 | 1 | 2 | 2 | Fixed chunks split the process description; paragraph chunks preserve process units better. |
| 300 | 2 | 2 | 2 | Process and PID definitions remain understandable. |
| 468 | 1 | 2 | 2 | Fixed chunk divides the waterfall advantages/disadvantages boundary. |
| 700 | 1 | 2 | 2 | Paragraph chunk keeps the private-cloud definition; fixed chunks divide it. |
| **Average /2** | **1.3** | **1.8** | **1.8** | 10 positions per strategy |

## 2. Metadata usefulness on the five test questions

The 15 top-3 records for each strategy were checked for `document_id`, `source`, `page` and `chapter`.

| Strategy | Metadata sufficient and correct | Filter compliance |
|---|---:|---:|
| A | 15/15 | N/A — A does not apply filters |
| B | 15/15 | N/A — B does not apply filters |
| C | 15/15 | 3/3 retrieved records for q19 had `chapter=12` |

The `chapter` field is useful for restricting retrieval to a book chapter. A limitation is that the mapping is based on the PDF contents and physical-page offset, so it should be rechecked if the source edition changes.

## 3. Grounding quality on five test questions

Scoring: `0` = no useful evidence, `1` = partial evidence, `2` = enough evidence and source context.

| Question | A | B | C | Note |
|---|---:|---:|---:|---|
| q16 | 2 | 2 | 2 | Waterfall advantage evidence retrieved. |
| q17 | 1 | 2 | 2 | B/C preserve the requirement-change limitation more completely. |
| q18 | 1 | 2 | 2 | A splits the Bootstrap explanation; B/C retain enough surrounding context. |
| q19 | 2 | 2 | 2 | Private-cloud evidence retrieved; C also obeys chapter filter. |
| q20 | 2 | 2 | 2 | The retrieved page/chapter context states the nanotechnology size range. |
| **Average /2** | **1.6** | **2.0** | **2.0** | 5 test questions per strategy |

## 4. Retrieval evidence

Automatic results are in `benchmark_summary.json`; complete top-3 records are in `benchmark_traces.jsonl`. The automatic and manual results must be reported together; Evidence Hit@3 does not replace the grounding or coherence audit.

## 5. Data strategy impact

### A versus B — chunking change

- Chunk count decreased from `5953` to `3628` (about 39.1% fewer chunks).
- Test Hit@1 increased from `1/5` to `3/5`.
- Test Evidence Hit@3 increased from `2/5` to `3/5`.
- Coherence increased from `1.3/2` to `1.8/2`.
- Grounding increased from `1.6/2` to `2.0/2`.
- Trade-off: paragraph chunking produced fewer, longer chunks and preserved context better, but it did not solve every retrieval miss; q18 and q20 still failed the strict automatic evidence check.

### B versus C — metadata filter change

- Corpus, chunks, embeddings and model were held constant.
- C applied `chapter` only when the question provided a filter.
- For q19, all three returned records complied with `chapter=12` (`3/3`).
- Metrics were unchanged because the benchmark has only one test filter question and B already returned the correct chapter for that question.
- Therefore, this experiment demonstrates filter compliance, not a general claim that filtering improves retrieval.

### Observed errors

1. `q18`: A returned pages 588, 601 and 600; the relevant Bootstrap explanation was split across chunks, so the strict evidence check failed. B/C returned page 600 first but still did not contain the exact gold quote in one chunk.
2. `q20`: B/C returned page 800 in the top result and the correct size context, but the strict quote/page match did not pass because the evidence was extracted across a page/chunk boundary. This is a limitation of the current exact evidence definition and chunk boundary.

## 6. Audit provenance

- Evidence source: `results/benchmark_traces.jsonl` and `data/openstax_computer_science.pdf`.
- Automatic metrics source: `results/benchmark_summary.json`.
- AI assistance: selected trace rows, checked metadata fields, and calculated aggregate values.
- Manual criteria: coherence uses 10 fixed physical pages; metadata uses 5 test questions x top-3; grounding uses the 5 test questions for each strategy.

## 7. Submission checklist review

This is a repository-status review against `SUBMISSION.md`, not a claim that external publication or LMS submission has occurred.

| Requirement | Status | Evidence or remaining action |
|---|---|---|
| At least 30 valid content pages, manifest, source, permission, page rule | PASS | 902 included physical pages (19-920) are recorded in `data/manifest.json`; pages 1-18 and 921-939 are explicitly excluded. |
| At least 20 benchmark questions, checked evidence, 15 dev/5 test | PASS | `benchmark/questions.json`; 20/20 evidence quotes checked, 15 dev, 5 test, 3 filters, one test filter. |
| Real embedding, persistent vector store, vector search, metadata filter | PASS | `text-embedding-3-small`, 1536 dimensions, PostgreSQL 16.16, pgvector 0.8.7, A/B/C top-3 and C filter test passed. |
| Three controlled strategies with same corpus/model/benchmark | PASS | A fixed-size, B paragraph, C B plus conditional chapter filter. |
| Top-3 traces, dev/test metrics, model, cost and time | PASS WITH COST LIMITATION | Trace and summary exist; model and 473.69-second total run are recorded. Exact API usage cost was not captured by the embedding adapter and must be reported as unavailable/estimated. |
| Manual audit and analysis of all five dimensions | PASS | This file covers retrieval, coherence, metadata, grounding and strategy impact; the author confirmed the manual labels. |
| Commands, code, manifest, experiment log and individual report | PASS | `STUDENT.md`, `artifacts/experiment_log.csv`, README run instructions, code and final individual report are present. |
| No secret/private/unlicensed data | PASS WITH FINAL GIT CHECK | `.env` is ignored and untracked; OpenStax CC BY-NC-SA attribution and source are recorded. Check staged files once more before pushing. |
| Public repository and submission link | PENDING EXTERNAL SUBMISSION | The repository URL is recorded in `STUDENT.md`; final commit/push and class-channel submission are external actions. |
