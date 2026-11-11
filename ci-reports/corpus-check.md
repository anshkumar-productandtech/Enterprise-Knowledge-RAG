# Corpus check

Run: 2026-11-11T14:52:33Z, commit 6c71339

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
      0  handbook/engineering/infrastructure/incident-management   <-- nothing found, check the path
    324  handbook/security
    171  handbook/sales
    105  handbook/legal

50 questions (45 answerable), 733 pages in corpus

5 problem(s):
  - corpus.yaml: no pages under handbook/engineering/infrastructure/incident-management
  - g07: fact no longer on the page: 'Paid Caregiver Sick Time'
  - e06: source not in corpus: https://handbook.gitlab.com/handbook/engineering/infrastructure/incident-management/incident-manager-onboarding/ (similar files: handbook/engineering/infrastructure-platforms/incident-management/incident-manager-onboarding.md)
  - e07: source not in corpus: https://handbook.gitlab.com/handbook/engineering/infrastructure/incident-management/incident-manager-onboarding/ (similar files: handbook/engineering/infrastructure-platforms/incident-management/incident-manager-onboarding.md)
  - s02: fact no longer on the page: 'Personal Data Exception'
VALIDATION FAILED
```

## Corpus size per chunking setup (dry run, nothing embedded)

### 256-token chunks, sentence splitter
```json
  nltk_find("corpora/stopwords", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
  for msg in self.incr_download(
  for msg in self.incr_download(info_or_id, download_dir, force, (), extract):
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  nltk_find("tokenizers/punkt_tab", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  root = nltk.data.find(f"{self.subdir}/{self.__name}")
  root = nltk.data.find(f"{self.subdir}/{zip_name}")
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 85, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords.zip/stopwords/'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************


During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 203, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 54, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 35, in main
    plan = ingest(s, policy, spec, embed_model, dry_run=True)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 128, in ingest
    nodes = build_nodes(settings, policy, spec)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 114, in build_nodes
    return splitter.get_nodes_from_documents(docs)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 176, in get_nodes_from_documents
    nodes = self._parse_nodes(documents, show_progress=show_progress, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 291, in _parse_nodes
    splits = self.split_text_metadata_aware(
        node.get_content(metadata_mode=MetadataMode.NONE),
        metadata_str=metadata_str,
    )
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 174, in split_text_metadata_aware
    return self._split_text(text, chunk_size=effective_chunk_size)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 191, in _split_text
    splits = self._split(text, chunk_size)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 213, in _split
    text_splits_by_fns, is_sentence = self._get_splits_by_fns(text)
                                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 336, in _get_splits_by_fns
    splits = split_fn(text)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/utils.py", line 93, in <lambda>
    text, globals_helper.punkt_tokenizer
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/utils.py", line 130, in punkt_tokenizer
    self._stopwords = stopwords.words("english")
                      ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 129, in __getattr__
    self.__load()
    ~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 87, in __load
    raise e
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 82, in __load
    root = nltk.data.find(f"{self.subdir}/{self.__name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************

DRY RUN FAILED
```

### 128-token chunks, sentence splitter
```json
  nltk_find("corpora/stopwords", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
  for msg in self.incr_download(
  for msg in self.incr_download(info_or_id, download_dir, force, (), extract):
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  nltk_find("tokenizers/punkt_tab", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  root = nltk.data.find(f"{self.subdir}/{self.__name}")
  root = nltk.data.find(f"{self.subdir}/{zip_name}")
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 85, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords.zip/stopwords/'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************


During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 203, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 54, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 35, in main
    plan = ingest(s, policy, spec, embed_model, dry_run=True)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 128, in ingest
    nodes = build_nodes(settings, policy, spec)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 114, in build_nodes
    return splitter.get_nodes_from_documents(docs)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 176, in get_nodes_from_documents
    nodes = self._parse_nodes(documents, show_progress=show_progress, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 291, in _parse_nodes
    splits = self.split_text_metadata_aware(
        node.get_content(metadata_mode=MetadataMode.NONE),
        metadata_str=metadata_str,
    )
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 174, in split_text_metadata_aware
    return self._split_text(text, chunk_size=effective_chunk_size)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 191, in _split_text
    splits = self._split(text, chunk_size)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 213, in _split
    text_splits_by_fns, is_sentence = self._get_splits_by_fns(text)
                                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 336, in _get_splits_by_fns
    splits = split_fn(text)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/utils.py", line 93, in <lambda>
    text, globals_helper.punkt_tokenizer
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/utils.py", line 130, in punkt_tokenizer
    self._stopwords = stopwords.words("english")
                      ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 129, in __getattr__
    self.__load()
    ~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 87, in __load
    raise e
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 82, in __load
    root = nltk.data.find(f"{self.subdir}/{self.__name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************

DRY RUN FAILED
```

### 384-token chunks, sentence splitter
```json
  nltk_find("corpora/stopwords", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
  for msg in self.incr_download(
  for msg in self.incr_download(info_or_id, download_dir, force, (), extract):
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  nltk_find("tokenizers/punkt_tab", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  root = nltk.data.find(f"{self.subdir}/{self.__name}")
  root = nltk.data.find(f"{self.subdir}/{zip_name}")
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 85, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords.zip/stopwords/'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************


During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 203, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 54, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 35, in main
    plan = ingest(s, policy, spec, embed_model, dry_run=True)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 128, in ingest
    nodes = build_nodes(settings, policy, spec)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 114, in build_nodes
    return splitter.get_nodes_from_documents(docs)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 176, in get_nodes_from_documents
    nodes = self._parse_nodes(documents, show_progress=show_progress, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 291, in _parse_nodes
    splits = self.split_text_metadata_aware(
        node.get_content(metadata_mode=MetadataMode.NONE),
        metadata_str=metadata_str,
    )
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 174, in split_text_metadata_aware
    return self._split_text(text, chunk_size=effective_chunk_size)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 191, in _split_text
    splits = self._split(text, chunk_size)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 213, in _split
    text_splits_by_fns, is_sentence = self._get_splits_by_fns(text)
                                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 336, in _get_splits_by_fns
    splits = split_fn(text)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/utils.py", line 93, in <lambda>
    text, globals_helper.punkt_tokenizer
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/utils.py", line 130, in punkt_tokenizer
    self._stopwords = stopwords.words("english")
                      ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 129, in __getattr__
    self.__load()
    ~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 87, in __load
    raise e
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 82, in __load
    root = nltk.data.find(f"{self.subdir}/{self.__name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************

DRY RUN FAILED
```

### 256-token chunks, markdown splitter
```json
  nltk_find("corpora/stopwords", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
  for msg in self.incr_download(
  for msg in self.incr_download(info_or_id, download_dir, force, (), extract):
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  nltk_find("tokenizers/punkt_tab", paths=[self._nltk_data_dir])
  return find(modified_name, paths)
[nltk_data] Refusing to install into '/opt/hostedtoolcache/Python/3.13
[nltk_data]     .18/x64/lib/python3.13/site-
[nltk_data]     packages/llama_index/core/_static/nltk_cache': it is
[nltk_data]     writable by, or owned by, another account, so a file
[nltk_data]     swapped in during the install would be installed as
[nltk_data]     trusted data. Make it private to its owner (chmod
[nltk_data]     go-w).
  root = nltk.data.find(f"{self.subdir}/{self.__name}")
  root = nltk.data.find(f"{self.subdir}/{zip_name}")
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 85, in __load
    root = nltk.data.find(f"{self.subdir}/{zip_name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords.zip/stopwords/'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************


During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "<frozen runpy>", line 203, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 54, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/scripts/ingest.py", line 35, in main
    plan = ingest(s, policy, spec, embed_model, dry_run=True)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 128, in ingest
    nodes = build_nodes(settings, policy, spec)
  File "/home/runner/work/Enterprise-Knowledge-RAG/Enterprise-Knowledge-RAG/backend/eka/index.py", line 113, in build_nodes
    return splitter(sections)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 204, in __call__
    return self.get_nodes_from_documents(nodes, **kwargs)  # type: ignore
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 176, in get_nodes_from_documents
    nodes = self._parse_nodes(documents, show_progress=show_progress, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/interface.py", line 291, in _parse_nodes
    splits = self.split_text_metadata_aware(
        node.get_content(metadata_mode=MetadataMode.NONE),
        metadata_str=metadata_str,
    )
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index_instrumentation/dispatcher.py", line 413, in wrapper
    result = func(*args, **kwargs)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 174, in split_text_metadata_aware
    return self._split_text(text, chunk_size=effective_chunk_size)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 191, in _split_text
    splits = self._split(text, chunk_size)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 213, in _split
    text_splits_by_fns, is_sentence = self._get_splits_by_fns(text)
                                      ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/sentence.py", line 336, in _get_splits_by_fns
    splits = split_fn(text)
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/node_parser/text/utils.py", line 93, in <lambda>
    text, globals_helper.punkt_tokenizer
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/utils.py", line 130, in punkt_tokenizer
    self._stopwords = stopwords.words("english")
                      ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 129, in __getattr__
    self.__load()
    ~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 87, in __load
    raise e
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/corpus/util.py", line 82, in __load
    root = nltk.data.find(f"{self.subdir}/{self.__name}")
  File "/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/nltk/data.py", line 1636, in find
    raise exc
LookupError: 
**********************************************************************
  Resource 'stopwords' not found.
  Please use the NLTK Downloader to obtain the resource:

  >>> import nltk
  >>> nltk.download('stopwords')

  For more information see: https://www.nltk.org/data.html

  Attempted to load 'corpora/stopwords'

  Refused, writable by other accounts (a file planted or
  rewritten there would be loaded as trusted data):
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  Make each one private to its owner, e.g.:
    chmod go-w '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
  then download the packages it holds again (force=True): a
  file changed while it was writable keeps the change.

  Searched in:
    - '/home/runner/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/share/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/nltk_data'
    - '/usr/share/nltk_data'
    - '/usr/local/share/nltk_data'
    - '/usr/lib/nltk_data'
    - '/usr/local/lib/nltk_data'
    - '/opt/hostedtoolcache/Python/3.13.18/x64/lib/python3.13/site-packages/llama_index/core/_static/nltk_cache'
**********************************************************************

DRY RUN FAILED
```
