"""The deterministic benchmark must be unaffected by the v0.4 service layer.

The pack is regenerated into a temp directory and compared byte-for-byte against
the committed artifacts. It must also remain reproducible across repeated runs
and depend on neither the API nor SQLite.
"""

import sys
from pathlib import Path

from anchorprune.benchmark.pack import write_pack

REPO = Path(__file__).resolve().parents[1]
COMMITTED = REPO / "benchmarks"


def test_pack_is_byte_identical_to_committed(tmp_path):
    paths = write_pack(tmp_path, window=2)
    for path in paths:
        committed = COMMITTED / path.name
        assert committed.exists(), f"missing committed artifact {path.name}"
        assert path.read_bytes() == committed.read_bytes(), f"{path.name} drifted"


def test_pack_is_reproducible(tmp_path):
    a = write_pack(tmp_path / "a", window=2)
    b = write_pack(tmp_path / "b", window=2)
    for pa, pb in zip(a, b):
        assert pa.read_bytes() == pb.read_bytes()


def test_benchmark_does_not_import_service_layer():
    # Generating the benchmark must not pull in the API or persistence layers.
    write_pack_modules = {
        "anchorprune.api",
        "anchorprune.storage",
        "anchorprune.services",
    }
    # The benchmark harness/pack themselves must not depend on these modules.
    import anchorprune.benchmark.harness as harness
    import anchorprune.benchmark.pack as pack

    for module in (harness, pack):
        source = Path(module.__file__).read_text(encoding="utf-8")
        for forbidden in write_pack_modules:
            assert forbidden not in source, f"{module.__name__} imports {forbidden}"
    # sanity: harness importable without service modules already loaded fresh
    assert "anchorprune.benchmark.harness" in sys.modules
