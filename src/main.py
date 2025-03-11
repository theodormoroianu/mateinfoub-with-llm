#! /usr/bin/env python3

import os
import argparse

import statements_importer


def main():
    parser = argparse.ArgumentParser(description="Play around with MateInfoUB tasks")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Define the 'generate' command parser
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

    # Parse the arguments
    args = parser.parse_args()

    if args.command == "translate":
        statements_importer.convert_statements(force=args.force)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
