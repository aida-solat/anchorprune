"""AnchorPrune command-line interface.

Commands:
    anchorprune init --domain procurement
    anchorprune run --input examples/supplier/scenario.json
    anchorprune inspect --run-id run_123
    anchorprune benchmark --input examples/supplier/scenario.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from anchorprune.benchmark.harness import run_benchmark
from anchorprune.benchmark.pack import write_pack
from anchorprune.domains.profiles import BUILTIN_PROFILES, get_domain_profile
from anchorprune.scenario import load_scenario, run_scenario

app = typer.Typer(help="Governed Anchored State Pruning for Long-Running AI Agents.")
console = Console()

RUNS_DIR = Path(".anchorprune/runs")


def _save_run(runtime, results) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    path = RUNS_DIR / f"{runtime.graph.run_id}.json"
    payload = {
        "run_id": runtime.graph.run_id,
        "goal": runtime.graph.goal,
        "domain": runtime.domain_profile.name,
        "state": json.loads(runtime.graph.model_dump_json()),
        "audit": runtime.audit.to_list(),
        "metrics": runtime.benchmark_metrics(),
        "steps": [json.loads(r.model_dump_json()) for r in results],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _print_state_table(summary: dict) -> None:
    table = Table(title="State Graph")
    table.add_column("metric")
    table.add_column("value", justify="right")
    for key, value in summary.items():
        table.add_row(key, str(value))
    console.print(table)


def _print_pruning_table(summary: dict) -> None:
    table = Table(title="Pruning (last step)")
    table.add_column("op")
    table.add_column("count", justify="right")
    for key, value in summary.items():
        table.add_row(key, str(value))
    console.print(table)


@app.command()
def init(domain: str = typer.Option("default", help="Domain profile name.")) -> None:
    """Show the resolved domain profile (weights, budget, thresholds)."""

    if domain not in BUILTIN_PROFILES:
        console.print(
            f"[yellow]Unknown domain '{domain}', using 'default'. "
            f"Available: {', '.join(BUILTIN_PROFILES)}[/yellow]"
        )
    profile = get_domain_profile(domain)
    console.print_json(profile.model_dump_json(indent=2))


@app.command()
def run(
    input: Path = typer.Option(..., exists=True, help="Scenario JSON file."),
    goal: Optional[str] = typer.Option(None, help="Override the scenario goal."),
    config: Optional[Path] = typer.Option(
        None,
        exists=True,
        help="Pipeline config (YAML/JSON) selecting heuristic vs model-based "
        "adapters. Omit for the deterministic mock pipeline.",
    ),
) -> None:
    """Run a scenario through the AnchorPrune governed runtime."""

    scenario = load_scenario(input)
    if goal:
        scenario["goal"] = goal

    llm = None
    extractor = None
    compressor = None
    if config is not None:
        from anchorprune.config import build_pipeline, load_config

        pipeline = build_pipeline(load_config(config))
        llm, extractor, compressor = (
            pipeline.llm,
            pipeline.extractor,
            pipeline.compressor,
        )
        console.print(
            f"[dim]Pipeline: llm={pipeline.config.llm.provider.value}, "
            f"extractor={pipeline.config.extractor.mode.value}, "
            f"compressor={pipeline.config.compressor.mode.value}, "
            f"deterministic={pipeline.config.runtime.deterministic_benchmark_mode}[/dim]"
        )

    runtime, results = run_scenario(
        scenario, llm, anchor_extractor=extractor, compressor=compressor
    )
    path = _save_run(runtime, results)

    last = results[-1]
    console.rule(f"[bold green]Run {runtime.graph.run_id}[/bold green]")
    console.print(f"[bold]Goal:[/bold] {runtime.graph.goal}")
    console.print(f"[bold]Domain:[/bold] {runtime.domain_profile.name}\n")

    console.print("[bold]Final model output[/bold]")
    console.print(last.model_output)

    _print_state_table(last.state_summary)
    _print_pruning_table(last.pruning_summary)
    console.print(f"\n[dim]Saved to {path}[/dim]")


@app.command()
def inspect(run_id: str = typer.Option(..., help="Run id to inspect.")) -> None:
    """Inspect a previously saved run: anchors, milestones, audit trail."""

    path = RUNS_DIR / f"{run_id}.json"
    if not path.exists():
        console.print(f"[red]No saved run at {path}[/red]")
        raise typer.Exit(code=1)

    data = json.loads(path.read_text(encoding="utf-8"))
    state = data["state"]

    console.rule(f"[bold]Run {run_id}[/bold]")
    console.print(f"[bold]Goal:[/bold] {data['goal']}  [dim]({data['domain']})[/dim]\n")

    anchors = Table(title="Anchors")
    anchors.add_column("class")
    anchors.add_column("priority")
    anchors.add_column("weight", justify="right")
    anchors.add_column("content")
    for anchor in state["anchors"].values():
        anchors.add_row(
            anchor["anchor_class"],
            anchor["priority"],
            f"{anchor['weight']:.2f}",
            anchor["content"][:70],
        )
    console.print(anchors)

    if state["milestones"]:
        ms = Table(title="Milestones")
        ms.add_column("stage")
        ms.add_column("conf", justify="right")
        ms.add_column("finding")
        for m in state["milestones"].values():
            ms.add_row(m["stage"], f"{m['confidence']:.2f}", m["finding"][:70])
        console.print(ms)

    _print_state_table(data["metrics"]["state_summary"])
    console.print(f"\n[dim]{len(data['audit'])} audit events recorded.[/dim]")


@app.command()
def benchmark(
    input: Path = typer.Option(..., exists=True, help="Scenario JSON file."),
    window: int = typer.Option(3, help="Sliding-window size for Baseline B."),
) -> None:
    """Benchmark AnchorPrune against full-history / window / summary baselines."""

    scenario = load_scenario(input)
    results = run_benchmark(scenario, window=window)

    table = Table(title="AnchorPrune Benchmark")
    table.add_column("method")
    table.add_column("in tok", justify="right")
    table.add_column("out tok", justify="right")
    table.add_column("final ctx", justify="right")
    table.add_column("adherence", justify="right")
    table.add_column("lost anchors", justify="right")

    for res in results.values():
        table.add_row(
            res.method,
            str(res.total_input_tokens),
            str(res.total_output_tokens),
            str(res.final_context_tokens),
            f"{res.constraint_adherence_rate:.0%}",
            f"{res.lost_anchor_rate:.0%}",
        )
    console.print(table)


@app.command()
def pack(
    out: Path = typer.Option(
        Path("benchmarks"), help="Output directory for the report files."
    ),
    window: int = typer.Option(3, help="Sliding-window size for Baseline B."),
) -> None:
    """Run the full benchmark pack and write benchmark_report.md + results.json."""

    paths = write_pack(out, window=window)
    for path in paths:
        console.print(f"[green]Wrote[/green] {path}")


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Bind host."),
    port: int = typer.Option(8000, help="Bind port."),
    db: Path = typer.Option(
        Path(".anchorprune/anchorprune.db"),
        help="SQLite database path for run persistence.",
    ),
) -> None:
    """Start the local FastAPI service (requires `pip install anchorprune[api]`)."""

    try:
        import uvicorn

        from anchorprune.api.app import create_app
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised manually
        console.print(
            "[red]The API service requires the optional 'api' extra.[/red]\n"
            "Install it with: [bold]pip install -e \".[api]\"[/bold]"
        )
        raise typer.Exit(code=1) from exc

    application = create_app(database_path=str(db))
    console.print(
        f"[green]AnchorPrune API[/green] on http://{host}:{port}  "
        f"[dim](docs at /docs, db={db})[/dim]"
    )
    uvicorn.run(application, host=host, port=port)


if __name__ == "__main__":
    app()
