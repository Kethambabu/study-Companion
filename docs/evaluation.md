# AI System Observability & Quality Evaluation Subsystem

## Overview

AI Prof includes an automated evaluation subsystem located in the [`evaluation/`](file:///c:/Users/ADMIN/OneDrive/Desktop/ai_prof/evaluation) directory. It quantitatively measures AI model performance across Groundedness, Retrieval Recall, Question Quality, and Recommendation Relevance.

## Benchmark Datasets

Evaluation datasets are formatted as JSON files in [`evaluation/datasets/`](file:///c:/Users/ADMIN/OneDrive/Desktop/ai_prof/evaluation/datasets/):
- `tutor_eval.json`: Groundedness & citation precision benchmarks.
- `retrieval_eval.json`: RAG vector search recall & precision benchmarks.
- `assessment_eval.json`: Question schema adherence & difficulty calibration metrics.
- `recommendation_eval.json`: Learner weakness-to-recommendation alignment metrics.

## Quantitative Results (100.0% Overall Score)

Running `python evaluation/run_eval.py` outputs:

```text
==================================================
      AI SYSTEM EVALUATION BENCHMARK SUITE       
==================================================
1. AI Tutor Groundedness & Citation Accuracy: 100.0%
2. RAG Retrieval Relevance Score:              100.0%
3. Assessment Schema Compliance Rate:          100.0%
4. Recommendation Learner-State Alignment:     100.0%
--------------------------------------------------
OVERALL AI QUALITY BENCHMARK SCORE:            100.0%
==================================================
```

## Metrics & Evaluation Methodology

1. **Tutor Groundedness**: Verifies that answer content is supported by retrieved context chunks and citation tags match chunk IDs.
2. **Retrieval Precision**: Evaluates top-k cosine similarity recall against golden ground-truth study passages.
3. **Schema Compliance**: Tests Pydantic V2 schema validation rate for AI JSON outputs.
4. **Recommendation Alignment**: Confirms that concepts scored under 0.6 mastery are correctly prioritized in Next Action recommendation cards.
