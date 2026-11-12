# Corpus check

Run: 2026-11-12T09:33:10Z, commit 2a5f5c8

## Handbook clone
```
Cloning into '/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/data/handbook'...
repo:   https://gitlab.com/gitlab-com/content-sites/handbook.git
commit: 6204c3c9c5c32c4bdb9062f3e88d5d153404a51f
date:   2026-11-12T12:56:45+05:30
Markdown pages: 4200
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
  "chunks": 9277,
  "embed_tokens_est": 2015726,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 181,
    "finance": 575,
    "general": 1165,
    "legal": 1763,
    "sales": 2884,
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
  "chunks": 19580,
  "embed_tokens_est": 2062094,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 377,
    "finance": 1178,
    "general": 2483,
    "legal": 3776,
    "sales": 6121,
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
  "chunks": 6153,
  "embed_tokens_est": 2016522,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 119,
    "finance": 375,
    "general": 771,
    "legal": 1156,
    "sales": 1898,
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
  "chunks": 13870,
  "embed_tokens_est": 2125895,
  "embed_cost_usd_est": 0.0,
  "groups": {
    "engineering": 303,
    "finance": 913,
    "general": 1840,
    "legal": 2277,
    "sales": 4158,
    "security": 4379
  },
  "chunks_over_model_limit_pct": 0.03,
  "status": "dry_run"
}
```
