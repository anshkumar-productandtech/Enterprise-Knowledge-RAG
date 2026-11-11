"""LLM-judged answer quality, via Ragas.

faithfulness        is every claim in the answer supported by the retrieved chunks? (hallucination check)
answer_correctness  does the answer agree with the reference answer in the golden set?

Both are scored by a judge model, so they are estimates. Read 10 answers
yourself and compare with the scores before quoting them.

Ragas is isolated in this file because its API moves quickly. Pinned: ragas==0.4.3.
The LlamaIndex wrappers used here are marked deprecated upstream but are what
keeps the judge provider swappable; revisit when upgrading.
"""

from __future__ import annotations

import os
import warnings

# Ragas sends anonymous usage analytics unless told not to. Off by default here.
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")


def judge_answers(samples: list[dict], judge_llm, embed_model) -> list[dict]:
    """samples: [{question, answer, contexts, reference}] -> [{faithfulness, answer_correctness}]"""
    if not samples:
        return []

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        from ragas import EvaluationDataset, SingleTurnSample, evaluate
        from ragas.embeddings import LlamaIndexEmbeddingsWrapper
        from ragas.llms import LlamaIndexLLMWrapper
        from ragas.metrics import AnswerCorrectness, Faithfulness

        dataset = EvaluationDataset(
            samples=[
                SingleTurnSample(
                    user_input=s["question"],
                    response=s["answer"],
                    retrieved_contexts=s["contexts"],
                    reference=s["reference"],
                )
                for s in samples
            ]
        )
        from ragas.run_config import RunConfig

        result = evaluate(
            dataset,
            metrics=[Faithfulness(), AnswerCorrectness()],
            llm=LlamaIndexLLMWrapper(judge_llm),
            embeddings=LlamaIndexEmbeddingsWrapper(embed_model),
            # JUDGE_WORKERS=1 keeps a rate-limited key from being flooded; retries ride out 429s.
            run_config=RunConfig(
                max_workers=int(os.environ.get("JUDGE_WORKERS", "4")), max_retries=8, max_wait=120, timeout=240
            ),
            raise_exceptions=False,  # a failed judgement becomes NaN, not a crashed run
            show_progress=True,
        )

    frame = result.to_pandas()
    out = []
    for _, row in frame.iterrows():
        out.append(
            {
                "faithfulness": _num(row.get("faithfulness")),
                "answer_correctness": _num(row.get("answer_correctness")),
            }
        )
    return out


def _num(value) -> float | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return None if f != f else round(f, 4)  # NaN -> None
