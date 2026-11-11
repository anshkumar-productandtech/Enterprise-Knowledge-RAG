# Corpus check

Run: 2026-11-11T15:06:24Z, commit 1582d0e

## Handbook clone
```
Cloning into '/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/data/handbook'...
repo:   https://gitlab.com/gitlab-com/content-sites/handbook.git
commit: 76aef42d3c4a4248628bff82106d52c7e98a6602
date:   2026-11-11T14:57:42+01:00
Markdown pages: 4201
Next: python -m scripts.validate_golden_set && python -m scripts.ingest --dry-run
```

## Golden set against this snapshot
```
Pages per configured section:
      4  handbook/people-group/time-off-and-absence
     18  handbook/people-group/learning-and-development
      1  handbook/people-group/acceptable-use-policy
      9  handbook/people-policies
     25  handbook/total-rewards
      5  handbook/entity
     57  handbook/finance
     14  handbook/engineering/infrastructure-platforms/incident-management
    324  handbook/security
    171  handbook/sales
    105  handbook/legal

50 questions (45 answerable), 733 pages in corpus
Golden set matches the corpus.
```

## Corpus size per chunking setup (dry run, nothing embedded)

### 256-token chunks, sentence splitter
```json
{
  "table": "eka.data_c256o32_se_baaibgesmallenv15",
  "pages": 733,
  "chunks": 9280,
  "embed_tokens_est": 2016397,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 181,
    "finance": 592,
    "general": 1165,
    "legal": 1763,
    "sales": 2870,
    "security": 2709
  },
  "chunks_over_model_limit_pct": 0.06,
  "status": "dry_run"
}
```

### 128-token chunks, sentence splitter
```json
{
  "table": "eka.data_c128o16_se_baaibgesmallenv15",
  "pages": 733,
  "chunks": 19589,
  "embed_tokens_est": 2062933,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 377,
    "finance": 1216,
    "general": 2483,
    "legal": 3776,
    "sales": 6092,
    "security": 5645
  },
  "chunks_over_model_limit_pct": 0.01,
  "status": "dry_run"
}
```

### 384-token chunks, sentence splitter
```json
{
  "table": "eka.data_c384o48_se_baaibgesmallenv15",
  "pages": 733,
  "chunks": 6155,
  "embed_tokens_est": 2017183,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 119,
    "finance": 386,
    "general": 771,
    "legal": 1156,
    "sales": 1889,
    "security": 1834
  },
  "chunks_over_model_limit_pct": 1.54,
  "status": "dry_run"
}
```

### 256-token chunks, markdown splitter
```json
{
  "table": "eka.data_c256o32_ma_baaibgesmallenv15",
  "pages": 733,
  "chunks": 13876,
  "embed_tokens_est": 2126474,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 303,
    "finance": 935,
    "general": 1840,
    "legal": 2277,
    "sales": 4142,
    "security": 4379
  },
  "chunks_over_model_limit_pct": 0.03,
  "status": "dry_run"
}
```
