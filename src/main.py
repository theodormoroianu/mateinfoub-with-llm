#! /usr/bin/env python3

import os
import argparse
import logging

import exp1_get_solutions
import exp2_no_reasoning
import exp3_no_multiple_choice
import exp4_no_python

import statements_processor
import compare_answers

logging.basicConfig(level=logging.INFO)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)
logging.getLogger("together").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


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
    parser_solve_problems = subparsers.add_parser(
        "solve", help="Run the models on the statements."
    )
    parser_solve_problems.add_argument(
        "-r", "--round", type=int, help="The round number.", default=1
    )

    parser_solve_problems_no_reasoning = subparsers.add_parser(
        "solve-no-reasoning", help="Run the models without asking for reasoning."
    )
    parser_solve_problems_no_reasoning.add_argument(
        "-r", "--round", type=int, help="The round number.", default=1
    )

    parser_solve_problems_no_choices = subparsers.add_parser(
        "solve-no-multiple-choice",
        help="Run the models without providing the multiple choices.",
    )
    parser_solve_problems_no_choices.add_argument(
        "-r", "--round", type=int, help="The round number.", default=1
    )

    parser_solve_no_python = subparsers.add_parser(
        "solve-no-python",
        help="Run the models without asking for reasoning.",
    )
    parser_solve_no_python.add_argument(
        "-r", "--round", type=int, help="The round number.", default=1
    )

    # Run the models on the statements.
    parser_compare_answers = subparsers.add_parser(
        "compare-no-multiple-choice", help="Run the models on the statements."
    )

    # Parse the arguments
    args = parser.parse_args()

    if args.command == "translate":
        statements_processor.translate_statements(force=args.force)
    elif args.command == "solve":
        round = args.round
        exp1_get_solutions.solve_tasks_asking_llms(round)
    elif args.command == "solve-no-reasoning":
        round = args.round
        exp2_no_reasoning.solve_tasks_asking_llms(round)
    elif args.command == "solve-no-multiple-choice":
        round = args.round
        exp3_no_multiple_choice.solve_tasks_asking_llms(round)
    elif args.command == "solve-no-python":
        round = args.round
        exp4_no_python.solve_tasks_asking_llms(round)
    elif args.command == "compare-no-multiple-choice":
        compare_answers.compute_matchings_for_answers()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
