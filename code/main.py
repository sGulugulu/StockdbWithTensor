from pathlib import Path
import argparse

from stock_tensor.pipeline import run_experiment


def main() -> None:
    default_config = Path(__file__).resolve().parent / "configs" / "default.yaml"
    parser = argparse.ArgumentParser(description="Run the thesis tensor-factorization experiment.")
    parser.add_argument(
        "--config",
        type=Path,
        default=default_config,
        help="Path to a YAML experiment config.",
    )
    args = parser.parse_args()
    output_dir = run_experiment(args.config)
    print(f"Experiment artifacts written to: {output_dir}")


if __name__ == "__main__":
    main()
