# Examples (v1.0)

Every example is runnable with a single command and ships a `README.md` stating
its purpose, command, expected output, and what **not** to claim. All examples
are deterministic and offline unless explicitly noted.

> AnchorPrune does not make models smarter. It governs what reaches them.

## Scenario examples

| Example | Shows | Command |
|---|---|---|
| [`supplier/`](../examples/supplier/) | Procurement governance: a supplier cannot be recommended without verified compliance | `anchorprune run --input examples/supplier/scenario.json` |
| [`coding_agent/`](../examples/coding_agent/) | Coding-agent governance: critical constraints survive; adversarial overrides quarantined | `anchorprune run --input examples/coding_agent/scenario.json` |
| [`contract_review/`](../examples/contract_review/) | Contract review governance: liability/threshold anchors preserved | `anchorprune run --input examples/contract_review/scenario.json` |

## Long-run scenarios (context-growth focus)

| Example | Shows | Command |
|---|---|---|
| [`long_run_coding_20_steps/`](../examples/long_run_coding_20_steps/) | 20-step coding run; context stays below full-history | `anchorprune run --input examples/long_run_coding_20_steps/scenario.json` |
| [`long_run_contract_15_steps/`](../examples/long_run_contract_15_steps/) | 15-step contract run | `anchorprune run --input examples/long_run_contract_15_steps/scenario.json` |
| [`long_run_procurement_10_steps/`](../examples/long_run_procurement_10_steps/) | 10-step procurement run | `anchorprune run --input examples/long_run_procurement_10_steps/scenario.json` |

## Integration & policy-pack examples

| Example | Shows | Command |
|---|---|---|
| [`integrations/coding_agent_loop/`](../examples/integrations/coding_agent_loop/) | Middleware governing a fake agent loop | `python examples/integrations/coding_agent_loop/loop.py` |
| [`policy_packs/contract_review_pack_demo/`](../examples/policy_packs/contract_review_pack_demo/) | Governing a scenario via a built-in policy pack | `anchorprune run --input examples/policy_packs/contract_review_pack_demo/scenario.json --policy-pack contract_review` |

## Evaluation example

| Example | Shows | Command |
|---|---|---|
| [`real_eval/`](../examples/real_eval/) | Observational real-model evaluation (mock provider, offline) | `anchorprune real-eval --provider mock --model mock-deterministic --scenarios coding_agent,contract_review --trials 2 --out real_eval_results` |
| [`real_llm_smoke/`](../examples/real_llm_smoke/) | Adapter smoke test against a real provider (optional, needs keys) | see the example README |

## What not to claim from any example

Examples demonstrate **governance behavior** on crafted scenarios. They do not
demonstrate model correctness, reasoning improvement, or production guarantees.
See [`claims.md`](claims.md).
