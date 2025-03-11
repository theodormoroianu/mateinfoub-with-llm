#! /usr/bin/env python3

import os
import argparse
import logging

import statements_processor

logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Play around with MateInfoUB tasks")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Translate the statements from ro to en.
    parser_data_translation = subparsers.add_parser(
        "translate", help="Translate data from romanian to english."
    )
    parser_data_translation.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists.",
        default=False,
    )

    # Run the models on the statements.
    parser_run_models = subparsers.add_parser(
        "run_models", help="Run the models on the statements."
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.command == "translate":
        statements_processor.translate_statements(force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
