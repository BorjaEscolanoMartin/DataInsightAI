from pathlib import Path

from demo.generate_demo_data import DAILY_SALES_CSV, HOUSING_CSV, generate

DEMO_DIR = Path(__file__).resolve().parent.parent / "demo"


def test_generator_reproduces_the_committed_demo_files(tmp_path):
    written = generate(tmp_path)

    assert [path.name for path in written] == [DAILY_SALES_CSV, HOUSING_CSV]
    for path in written:
        assert path.read_bytes() == (DEMO_DIR / path.name).read_bytes()


def test_two_runs_write_identical_files(tmp_path):
    first = generate(tmp_path / "first")
    second = generate(tmp_path / "second")

    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
