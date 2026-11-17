# ReframeBench: Technical Implementation of Multi-Therapy Cognitive Restructuring

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1.0-green.svg)](https://www.langchain.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Core Technical Documentation** for "ReframeBench: A Benchmark for Multi-Therapy Cognitive Restructuring with LLMs". [cite_start]This repository implements a novel multi-agent reasoning pipeline that operationalizes 12 distinct psychotherapeutic frameworks[cite: 235, 236, 237, 238, 239, 240, 242, 243, 244, 246].

## 🧠 Methodology: Therapy-Oriented Prompt Engineering

The core innovation of ReframeBench is the transition from generic instruction following to **Persona-based In-Context Learning**. We formalize the cognitive restructuring task not merely as text rewriting, but as a conditional generation problem constrained by specific therapeutic theoretical frameworks.

### Mathematical Formulation
[cite_start]We define the generation function $R_{i,m}$ for a specific therapy modality $m$ as follows[cite: 50, 51]:

$$R_{i,m} = \text{LLM}(S_i, T_i, \mathcal{I}_{role} \oplus \mathcal{I}_{mechanism} \oplus \mathcal{I}_{safety})$$

[cite_start]Where $S_i$ is the situation, $T_i$ is the negative thought[cite: 49], and the prompt $P_m$ is composed of three strictly defined components:

1.  **$\mathcal{I}_{role}$ (Role Definition):** Establishes the expert persona to prime the model's latent space (e.g., *"You are an expert ACT therapist..."*).
2.  **$\mathcal{I}_{mechanism}$ (Theoretical Constraints):** The critical differentiator that enforces specific therapeutic techniques:
    * [cite_start]**CBT:** Focuses on *Evidence* and *Logic* (Disputation)[cite: 235].
    * [cite_start]**ACT:** Focuses on *Cognitive Defusion* and *Values* (Acceptance)[cite: 236].
    * [cite_start]**DBT:** Focuses on *Dialectics* (Balancing Acceptance and Change)[cite: 244].
3.  **$\mathcal{I}_{safety}$ (Clinical Guardrails):** Hard constraints to prevent hallucinations and unsafe medical advice (e.g., crisis resource redirection).

---

## ⚙️ Architecture: Multi-Agent Reasoning Pipeline

We implement a sophisticated reasoning pipeline that moves beyond simple zero-shot prompting. [cite_start]The architecture comprises three distinct stages, modeled after clinical workflows[cite: 234]:

### Step 1: Cognitive Distortion Detection (Zero-shot Classification)
Before reframing, the system analyzes the input thought ($T_i$) to identify specific cognitive traps (e.g., Catastrophizing, Polarization).
* **Goal:** To enable targeted intervention strategies.
* **Output:** Structured JSON list of distortions.

### Step 2: Parallel Multi-Therapy Generation
[cite_start]The system utilizes parallel threads to generate candidate reframes from $N$ different therapeutic modules simultaneously[cite: 247].
* [cite_start]**Reframer Agent:** Acts as the generator $G$ using the therapy-specific prompts defined above[cite: 245].
* **Diversity:** High temperature settings ($T \approx 0.7$) are used to ensure linguistic diversity while maintaining theoretical adherence.

### Step 3: Supervisor-Critique (LLM-as-a-Judge)
[cite_start]A specialized **Therapeutic Quality Evaluator** agent assesses the generated candidates[cite: 251].
* **Mechanism:** It acts as a clinical supervisor, scoring reframes on a scale of 1-5 based on **Empathy**, **Actionability**, and **Safety**.
* **Selection Logic:**
    $$R_{final} = \operatorname*{argmax}_{R \in \{R_{CBT}, R_{ACT}, ...\}} (\text{Score}_{supervisor}(R))$$

---

## ⛓️ Advanced Technique: Implicit Chain-of-Thought (CoT)

To prevent the model from generating superficial advice, we employ **Implicit Chain-of-Thought** prompting. We instruct the model to perform a "hidden" analysis phase before outputting the final response.

**Prompt Template Structure:**
```text
Phase 1: Analysis (Internal Monologue)
- Identify the underlying emotion.
- Identify the specific cognitive trap.
- Select the appropriate technique from the [Therapy Name] manual.

Phase 2: Drafting (Final Output)
- Draft the response applying the technique.
- Ensure the tone is validating and non-judgmental.

Output ONLY Phase 2.
