<!-- real run | last updated 2026-11-11T16:08:10+00:00 -->
| Experiment | Chunk | Search | Rerank | Hit@5 | MRR | Faithful | Correct | Pass rate | Refusal acc | Retrieval p95 ms | Answer p95 ms | $/query | ACL leaks |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0-baseline | 256 sentence | vector | no | 87% | 0.654 | n/a | n/a | n/a | n/a | 16 | n/a | n/a | 0 |
| 1a-chunks-128 | 128 sentence | vector | no | 89% | 0.695 | n/a | n/a | n/a | n/a | 14 | n/a | n/a | 0 |
| 1b-chunks-384 | 384 sentence | vector | no | 78% | 0.620 | n/a | n/a | n/a | n/a | 39 | n/a | n/a | 0 |
| 2-hybrid | 128 sentence | hybrid | no | 93% | 0.770 | n/a | n/a | n/a | n/a | 62 | n/a | n/a | 0 |
| 3-hybrid-rerank | 128 sentence | hybrid | yes | 93% | 0.816 | n/a | n/a | n/a | n/a | 1167 | n/a | n/a | 0 |
| 4-heading-aware | 128 markdown | hybrid | yes | 93% | 0.822 | n/a | n/a | n/a | n/a | 840 | n/a | n/a | 0 |

Measured on 50 golden questions; 5 chunks go to the model. Embeddings: local/BAAI/bge-small-en-v1.5. Reranker: local/Xenova/ms-marco-MiniLM-L-12-v2. Answer model: none. Judge: none. Rows showing n/a for answer metrics were run retrieval-only.

Corpus: repo:   https://gitlab.com/gitlab-com/content-sites/handbook.git, commit: 76aef42d3c4a4248628bff82106d52c7e98a6602, date:   2026-11-11T14:57:42+01:00.

Chunk size carried into the later rows: 128 tokens (best hit rate in the chunk sweep).
