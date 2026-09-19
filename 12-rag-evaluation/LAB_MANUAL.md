# Evaluate RAG Systems with Vertex AI

## Complete Implementation Lab Manual

**Prepared by:** Abdul Qaadir (@TechWorldWithAbdul)
**Series:** 30 Labs, 30 Days — Day 12 · **Last Updated:** September 2026

---

## 1. Introduction

### Overview
Build an **evaluation pipeline for a RAG (Retrieval-Augmented Generation) system** using the **Vertex AI Gen AI Evaluation Service**. You'll create custom evaluation criteria and an assessment framework for a question-answering task, working with examples from the **Stanford Question Answering Dataset (SQuAD 2.0)**.

You will configure **two evaluation styles**:
1. **Reference-free** — judge answers from the prompt/context alone (groundedness, relevance, helpfulness, safety, instruction-following)
2. **Reference-based** — compare answers to a **"golden answer"** for objective factual scoring (correctness + `exact_match`, `bleu`, `rouge`)

### Why this lab matters (the series context)
Days 1–11 built RAG systems and agents. **This lab answers: "but how do you KNOW it's good?"** Production AI without evaluation is guesswork. This is the difference between a demo and a deployable system — and the exact skill the FDE/$200K interview questions ask about ("How do you evaluate?").

### What you'll learn
- Prepare evaluation datasets for RAG systems (prompt = question + retrieved context, response, optional reference)
- Run **reference-free** evaluation: groundedness, relevance, helpfulness, safety, instruction-following
- Run **reference-based** evaluation: semantic + exact-match metrics against golden answers
- Create **custom metrics** with detailed scoring rubrics (PointwiseMetric + prompt templates)
- Visualize results (radar + bar plots) to compare models and pick the winner

### Cost
~60 minutes · **less than $1 USD** · standard Vertex AI evaluation usage.

---

## 2. The Dataset Foundation (SQuAD 2.0)

Examples span 3 domains to test how evaluation generalizes:
- **Neuroscience** — technical accuracy (which brain region handles short-term memory?)
- **History** — factual precision (why was the Roman Senate exuberant?)
- **Geography** — territorial knowledge (what did the Hasan-Jalalians command?)

The lab compares two model outputs: **Model A** (answers well) vs **Model B** (answers poorly, e.g. "the Galactic Empire commanded Utah"). The evaluation must *prove* A > B — that's the whole point.

---

## 3. Understanding RAG (60-second refresh)

RAG grounds an LLM's answer in an external knowledge base:
1. Convert the user's question into an **embedding** (numerical representation)
2. **Search** the knowledge base for documents with similar embeddings
3. Provide those documents as **context** + the question to the LLM → generate an answer

**Why RAG evaluation is complex — the Multi-Component Challenge:**
| Component | Failure mode |
|---|---|
| **Retrieval quality** | Did it find the RIGHT context? |
| **Context utilization** | Did the model USE the retrieved info? |
| **Generation quality** | Is the final answer well-written, helpful, accurate? |

A response can fail at ANY of these. The system might retrieve correctly but the model ignores the context — or generate a polished answer that's wrong because the context was irrelevant. Evaluation must isolate which part fails.

---

## 4. Project Setup

1. **Google Account** — use a personal account (not work/school).
2. **Sign in** to the Google Cloud Console.
3. **Enable billing** — use the codelab's credit banner or set up a billing account. ⏱️ Less than **$1 USD** total.
4. **Create a project** (optional) — new users get a $300 free trial.

---

## 5. Set Up Vertex AI Workbench

### Enable the API
1. Go to the **APIs & Services page** → search `aiplatform.googleapis.com` → **Enable** for **Vertex AI API**.

### Create your notebook
1. Console → **Navigation menu ☰ → Vertex AI → Workbench**
2. **Create new workbench instance** → name it **`evaluation-workbench`** → pick region/zone → **Create** (takes a few minutes)
3. Click **OPEN JUPYTERLAB** once provisioned
4. Create a new **Python 3** notebook

### Install the evaluation SDK
```python
%pip install --upgrade --user --quiet google-cloud-aiplatform[evaluation]
```
This installs:
- **EvalTask** — the main class for running evaluations
- **MetricPromptTemplateExamples** — predefined evaluation metrics
- **PointwiseMetric** — framework for custom metrics
- **notebook_utils** — visualization tools

> ⚠️ **Restart the kernel** after install (Kernel → Restart Kernel) or the new packages won't load.

---

## 6. Initialize the SDK + Imports

```python
import vertexai

PROJECT_ID = "YOUR PROJECT ID"
LOCATION = "YOUR LOCATION"  # @param {type:"string"}
EXPERIMENT = "rag-eval-01"  # @param {type:"string"}

if not PROJECT_ID or PROJECT_ID == "[your-project-id]":
    raise ValueError("Please set your PROJECT_ID")
```

```python
vertexai.init(project=PROJECT_ID, location=LOCATION)
```

```python
import pandas as pd
from vertexai.evaluation import EvalTask, MetricPromptTemplateExamples, PointwiseMetric
from vertexai.preview.evaluation import notebook_utils
```

---

## 7. Prepare the Evaluation Dataset

> **KEY STRUCTURE:** RAG eval datasets need:
> - **`prompt`** = User Question + Retrieved Context (so the service knows what info the model used)
> - **`response`** = the model's final answer
> - **`reference`** (for referenced eval only) = the golden answer

~**100 examples** is recommended for statistically reliable results; this lab uses 3 to demonstrate.

### Questions + two model outputs
```python
questions = [
    "Which part of the brain does short-term memory seem to rely on?",
    "What provided the Roman senate with exuberance?",
    "What area did the Hasan-jalalians command?",
]

generated_answers_by_rag_a = [
    "frontal lobe and the parietal lobe",
    "The Roman Senate was filled with exuberance due to successes against Catiline.",
    "The Hasan-Jalalians commanded the area of Syunik and Vayots Dzor.",
]

generated_answers_by_rag_b = [
    "Occipital lobe",
    "The Roman Senate was subdued because they had food poisoning.",
    "The Galactic Empire commanded the state of Utah.",
]
```

### Retrieved contexts (the RAG output)
```python
retrieved_contexts = [
    # Neuroscience — short/long-term memory, frontal + parietal lobe, hippocampus
    "Short-term memory is supported by transient patterns of neuronal communication, dependent on regions of the frontal lobe (especially dorsolateral prefrontal cortex) and the parietal lobe. Long-term memory, on the other hand, is maintained by more stable and permanent changes in neural connections widely spread throughout the brain. The hippocampus is essential (for learning new information) to the consolidation of information from short-term to long-term memory, although it does not seem to store information itself. Without the hippocampus, new memories are unable to be stored into long-term memory, as learned from patient Henry Molaison after removal of both his hippocampi, and there will be a very short attention span. Furthermore, it may be involved in changing neural connections for a period of three months or more after the initial learning.",
    # History — Pompey, Catiline, First Triumvirate
    "In 62 BC, Pompey returned victorious from Asia. The Senate, elated by its successes against Catiline, refused to ratify the arrangements that Pompey had made. Pompey, in effect, became powerless. Thus, when Julius Caesar returned from a governorship in Spain in 61 BC, he found it easy to make an arrangement with Pompey. Caesar and Pompey, along with Crassus, established a private agreement, now known as the First Triumvirate. Under the agreement, Pompey's arrangements would be ratified. Caesar would be elected consul in 59 BC, and would then serve as governor of Gaul for five years. Crassus was promised a future consulship.",
    # Geography — Zakarid Armenia, Orbelians, Hasan-Jalalians
    "The Seljuk Empire soon started to collapse. In the early 12th century, Armenian princes of the Zakarid noble family drove out the Seljuk Turks and established a semi-independent Armenian principality in Northern and Eastern Armenia, known as Zakarid Armenia, which lasted under the patronage of the Georgian Kingdom. The noble family of Orbelians shared control with the Zakarids in various parts of the country, especially in Syunik and Vayots Dzor, while the Armenian family of Hasan-Jalalians controlled provinces of Artsakh and Utik as the Kingdom of Artsakh.",
]
```

### Build the DataFrames
```python
eval_dataset_rag_a = pd.DataFrame({
    "prompt": [
        "Answer the question: " + question + " Context: " + item
        for question, item in zip(questions, retrieved_contexts)
    ],
    "response": generated_answers_by_rag_a,
})

eval_dataset_rag_b = pd.DataFrame({
    "prompt": [
        "Answer the question: " + question + " Context: " + item
        for question, item in zip(questions, retrieved_contexts)
    ],
    "response": generated_answers_by_rag_b,
})

eval_dataset_rag_a  # view to verify
```

---

## 8. Select & Create Metrics

Two types: **predefined** (SDK built-ins) and **custom** (your own rubrics via PointwiseMetric).

### Explore predefined metrics
```python
# Full list of built-in metric names
MetricPromptTemplateExamples.list_example_metric_names()

# Inspect the evaluator LLM's instructions for one metric
print(MetricPromptTemplateExamples.get_prompt_template("question_answering_quality"))
```

### Create custom metric 1 — RELEVANCE (5→1 rubric)
```python
relevance_prompt_template = """
You are a professional writing evaluator. Your job is to score writing responses according to pre-defined evaluation criteria.

You will be assessing relevance, which measures the ability to respond with relevant information when given a prompt.

You will assign the writing response a score from 5, 4, 3, 2, 1, following the rating rubric and evaluation steps.

## Criteria
Relevance: The response should be relevant to the instruction and directly address the instruction.

## Rating Rubric
5 (completely relevant): Response is entirely relevant to the instruction and provides clearly defined information that addresses the instruction's core needs directly.
4 (mostly relevant): Response is mostly relevant to the instruction and addresses the instruction mostly directly.
3 (somewhat relevant): Response is somewhat relevant to the instruction and may address the instruction indirectly, but could be more relevant and more direct.
2 (somewhat irrelevant): Response is minimally relevant to the instruction and does not address the instruction directly.
1 (irrelevant): Response is completely irrelevant to the instruction.

## Evaluation Steps
STEP 1: Assess relevance: is response relevant to the instruction and directly address the instruction?
STEP 2: Score based on the criteria and rubrics.

Give step by step explanations for your scoring, and only choose scores from 5, 4, 3, 2, 1.

# User Inputs and AI-generated Response
## User Inputs
### Prompt
{prompt}

## AI-generated Response
{response}
"""
```

### Create custom metric 2 — HELPFULNESS (comprehensiveness + accuracy + safety)
```python
helpfulness_prompt_template = """
You are a professional writing evaluator. Your job is to score writing responses according to pre-defined evaluation criteria.

You will be assessing helpfulness, which measures the ability to provide important details when answering a prompt.

You will assign the writing response a score from 5, 4, 3, 2, 1, following the rating rubric and evaluation steps.

## Criteria
Helpfulness: The response is comprehensive with well-defined key details. The user would feel very satisfied with the content in a good response.

## Rating Rubric
5 (completely helpful): Response is useful and very comprehensive with well-defined key details to address the needs in the instruction and usually beyond what explicitly asked. The user would feel very satisfied with the content in the response.
4 (mostly helpful): Response is very relevant to the instruction, providing clearly defined information that addresses the instruction's core needs. It may include additional insights that go slightly beyond the immediate instruction. The user would feel quite satisfied with the content in the response.
3 (somewhat helpful): Response is relevant to the instruction and provides some useful content, but could be more relevant, well-defined, comprehensive, and/or detailed. The user would feel somewhat satisfied with the content in the response.
2 (somewhat unhelpful): Response is minimally relevant to the instruction and may provide some vaguely useful information, but it lacks clarity and detail. It might contain minor inaccuracies. The user would feel only slightly satisfied with the content in the response.
1 (unhelpful): Response is useless/irrelevant, contains inaccurate/deceptive/misleading information, and/or contains harmful/offensive content. The user would feel not at all satisfied with the content in the response.

## Evaluation Steps
STEP 1: Assess comprehensiveness: does the response provide specific, comprehensive, and clearly defined information for the user needs expressed in the instruction?
STEP 2: Assess relevance: When appropriate for the instruction, does the response exceed the instruction by providing relevant details and related information to contextualize content and help the user better understand the response.
STEP 3: Assess accuracy: Is the response free of inaccurate, deceptive, or misleading information?
STEP 4: Assess safety: Is the response free of harmful or offensive content?

Give step by step explanations for your scoring, and only choose scores from 5, 4, 3, 2, 1.

# User Inputs and AI-generated Response
## User Inputs
### Prompt
{prompt}

## AI-generated Response
{response}
"""
```

### Wrap both into PointwiseMetric objects
```python
relevance = PointwiseMetric(metric="relevance", metric_prompt_template=relevance_prompt_template)
helpfulness = PointwiseMetric(metric="helpfulness", metric_prompt_template=helpfulness_prompt_template)
```

---

## 9. Run the (Reference-Free) Evaluation

```python
rag_eval_task_rag_a = EvalTask(
    dataset=eval_dataset_rag_a,
    metrics=[
        "question_answering_quality",
        relevance,
        helpfulness,
        "groundedness",
        "safety",
        "instruction_following",
    ],
    experiment=EXPERIMENT,
)

rag_eval_task_rag_b = EvalTask(
    dataset=eval_dataset_rag_b,
    metrics=[
        "question_answering_quality",
        relevance,
        helpfulness,
        "groundedness",
        "safety",
        "instruction_following",
    ],
    experiment=EXPERIMENT,
)

result_rag_a = rag_eval_task_rag_a.evaluate()
result_rag_b = rag_eval_task_rag_b.evaluate()
```
⏱️ Evaluation runs on the Vertex AI backend — takes several minutes.

> **Note the mix:** predefined metrics (safety, groundedness, question_answering_quality) + your custom PointwiseMetric objects (relevance, helpfulness) in one list.

---

## 10. Analyze the Reference-Free Results

### Aggregate summaries
```python
notebook_utils.display_eval_result(title="Model A Eval Result", eval_result=result_rag_a)
notebook_utils.display_eval_result(title="Model B Eval Result", eval_result=result_rag_b)
```

### Visualize — radar + bar plots
```python
eval_results = []
eval_results.append(("Model A", result_rag_a))
eval_results.append(("Model B", result_rag_b))

notebook_utils.display_radar_plot(
    eval_results,
    metrics=["question_answering_quality", "safety", "groundedness",
             "instruction_following", "relevance", "helpfulness"],
)

notebook_utils.display_bar_plot(
    eval_results,
    metrics=["question_answering_quality", "safety", "groundedness",
             "instruction_following", "relevance", "helpfulness"],
)
```
📊 **Radar plot:** larger shape = better all-around. **Bar plot:** direct per-metric comparison. Model A should clearly win.

### Drill into individual explanations (the debugging layer)
```python
# Why did example #2 score what it did?
notebook_utils.display_explanations(result_rag_a, num=2)

# Debug a specific weak metric across ALL examples (e.g. Model B groundedness)
notebook_utils.display_explanations(result_rag_b, metrics=["groundedness"])
```
This is where the evaluator LLM's step-by-step reasoning appears — the raw material for fixing your RAG system.

---

## 11. Referenced Evaluation ("Golden Answer")

Reference-free is subjective. **Referenced** adds a ground-truth answer → objective scoring of **factual correctness**, **semantic similarity**, and **completeness**.

### Prepare the referenced dataset
```python
golden_answers = [
    "frontal lobe and the parietal lobe",            # Q1: A's answer matches exactly
    "Due to successes against Catiline.",            # Q2: A is semantically similar, different wording
    "The Hasan-Jalalians commanded the area of Artsakh and Utik.",  # Q3: A is WRONG per context
]

referenced_eval_dataset_rag_a = pd.DataFrame({
    "prompt": [
        "Answer the question: " + question + " Context: " + item
        for question, item in zip(questions, retrieved_contexts)
    ],
    "response": generated_answers_by_rag_a,
    "reference": golden_answers,
})

referenced_eval_dataset_rag_b = pd.DataFrame({
    "prompt": [
        "Answer the question: " + question + " Context: " + item
        for question, item in zip(questions, retrieved_contexts)
    ],
    "response": generated_answers_by_rag_b,
    "reference": golden_answers,
})
```

### Create a custom REFERENCED metric (strict 1/0 correctness)
```python
question_answering_correctness_prompt_template = """
You are a professional writing evaluator. Your job is to score writing responses according to pre-defined evaluation criteria.

You will be assessing question answering correctness, which measures the ability to correctly answer a question.

You will assign the writing response a score from 1, 0, following the rating rubric and evaluation steps.

### Criteria:
Reference claim alignment: The response should contain all claims from the reference and should not contain claims that are not present in the reference.

### Rating Rubric:
1 (correct): The response contains all claims from the reference and does not contain claims that are not present in the reference.
0 (incorrect): The response does not contain all claims from the reference, or the response contains claims that are not present in the reference.

### Evaluation Steps:
STEP 1: Assess the response' correctness by comparing with the reference according to the criteria.
STEP 2: Score based on the rubrics.

Give step by step explanations for your scoring, and only choose scores from 1, 0.

# User Inputs and AI-generated Response
## User Inputs
### Prompt
{prompt}

## Reference
{reference}

## AI-generated Response
{response}
"""

question_answering_correctness = PointwiseMetric(
    metric="question_answering_correctness",
    metric_prompt_template=question_answering_correctness_prompt_template,
)
```
> Key detail: the template now includes the **`{reference}`** placeholder, and scoring is **strict binary** (1/0) since we have a definitive correct answer.

---

## 12. Run the Referenced Evaluation

Adds **computation-based metrics** (mathematical, not LLM-judged):
- **`exact_match`** — 1 only if identical to reference, else 0
- **`bleu`** — PRECISION: how many generated words appear in the reference
- **`rouge`** — RECALL: how many reference words are captured in the generation

```python
referenced_answer_eval_task_rag_a = EvalTask(
    dataset=referenced_eval_dataset_rag_a,
    metrics=[question_answering_correctness, "rouge", "bleu", "exact_match"],
    experiment=EXPERIMENT,
)

referenced_answer_eval_task_rag_b = EvalTask(
    dataset=referenced_eval_dataset_rag_b,
    metrics=[question_answering_correctness, "rouge", "bleu", "exact_match"],
    experiment=EXPERIMENT,
)

referenced_result_rag_a = referenced_answer_eval_task_rag_a.evaluate()
referenced_result_rag_b = referenced_answer_eval_task_rag_b.evaluate()
```

---

## 13. Analyze the Referenced Results

```python
notebook_utils.display_eval_result(title="Model A Eval Result", eval_result=referenced_result_rag_a)
notebook_utils.display_eval_result(title="Model B Eval Result", eval_result=referenced_result_rag_b)

referenced_eval_results = []
referenced_eval_results.append(("Model A", referenced_result_rag_a))
referenced_eval_results.append(("Model B", referenced_result_rag_b))

notebook_utils.display_radar_plot(
    referenced_eval_results,
    metrics=["question_answering_correctness", "rouge", "bleu", "exact_match"],
)

notebook_utils.display_bar_plot(
    referenced_eval_results,
    metrics=["question_answering_correctness", "rouge", "bleu", "exact_match"],
)
```

### The insight to catch
Model A scores **high on `question_answering_correctness` but lower on `exact_match`** — because its Q2 answer ("…successes against Catiline") is semantically correct but worded differently from the golden answer. That's the classic case where **model-based metrics recognize semantic equivalence that exact-match math cannot** — and why you need BOTH metric families.

---

## 14. From Practice to Production

### 4 production best practices
1. **Automate with CI/CD** — integrate the eval suite (Cloud Build/GitHub Actions); block deploys when quality drops below thresholds.
2. **Evolve your datasets** — version-control golden test sets (Git LFS/Cloud Storage); keep adding hard examples sampled from real (anonymized) user queries. Static datasets go stale.
3. **Evaluate the retriever, not just the generator** — great answers need great context. Separate retrieval eval with **Hit Rate** (found the right doc?) and **MRR** (how high was it ranked?).
4. **Monitor over time** — export scores to Cloud Monitoring, dashboards, and alerts for significant drops.

### Evaluation methodology matrix
| Approach | Best for | Advantages | Limitations |
|---|---|---|---|
| **Reference-free** | Production monitoring | No golden answers; captures subjective quality | More expensive; evaluator bias |
| **Reference-based** | Model comparison, benchmarking | Objective; fast computation | Needs golden answers; may miss semantic equivalence |
| **Custom metrics** | Domain-specific assessment | Tailored to business needs | Needs validation; dev overhead |
| **Hybrid** | Comprehensive production | Best of all | Higher complexity, cost tuning |

### Key technical insights
- **Groundedness is THE metric for RAG** — it consistently separates high/low-quality RAG systems; essential for production monitoring.
- **Multiple metrics = robustness** — no single metric captures RAG quality.
- **Custom metrics add real value** — domain rubrics catch what generic ones miss.
- **Statistical rigor** — proper sample sizes + significance testing turn evaluation into reliable decision-making.

### Production deployment decision framework
- **Phase 1 – Development:** reference-based eval with known test sets → model selection
- **Phase 2 – Pre-Production:** comprehensive (both approaches) → readiness validation
- **Phase 3 – Production:** reference-free monitoring → continuous quality (no golden answers needed)
- **Phase 4 – Optimization:** eval insights → retrieval + generation improvements

---

## 15. Gotchas & Pro Tips

- **Prompt must = question + context** — if `prompt` omits the retrieved context, groundedness is meaningless. The evaluator must see exactly what the model saw.
- **Restart the kernel** after `%pip install google-cloud-aiplatform[evaluation]` — no restart = ModuleNotFoundError on EvalTask.
- **~100 examples for real confidence** — the 3-example lab proves mechanics, not statistics. Production eval needs sample sizes that survive significance testing.
- **`notebook_utils` lives in `vertexai.preview.evaluation`** — not the stable namespace. Preview imports can change between SDK versions.
- **Model-based vs computation-based metrics are complementary** — exact_match can't see "semantically right, differently worded"; the LLM-judged correctness metric can. Use both and expect them to disagree on paraphrase-heavy datasets.
- **radar/bar plots hide per-row detail** — when a metric regresses, always drop to `display_explanations(..., metrics=[...])` for the evaluator's reasoning before touching the system.
- **Watch region availability** — Vertex AI evaluation (esp. preview features) is region-specific; use a supported location for your project.
- **Retriever eval is a separate job** — Hit Rate + MRR need their own dataset (query → expected doc IDs), don't fold them into generation eval.

---

## 16. Recap — What You Learned

- Prepared RAG evaluation datasets (question + retrieved-context prompts, responses, golden references)
- Ran **reference-free** evaluation: groundedness, relevance, helpfulness, safety, instruction-following
- Ran **referenced** evaluation: custom correctness (1/0) + `exact_match`, `bleu`, `rouge`
- Built **custom metrics** with real scoring rubrics via PointwiseMetric
- Visualized results (radar/bar) and drilled into per-instance explanations
- Learned the production playbook: CI/CD, dataset evolution, retriever eval, monitoring

*This lab is part of the Production-Ready AI with Google Cloud learning path — share progress with #ProductionReadyAI.*

**Follow along with the video:** [Link to be added when published]