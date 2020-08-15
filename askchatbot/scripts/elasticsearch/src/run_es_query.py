"""Run elastic search queries from the command line"""

import asyncio
import setup_logger  # pylint: disable=unused-import

from actions import actions_config as ac
from actions.actions_main import handle_es_query


def ask_query():
    """Get the input from user"""
    question = None
    pest_name = None
    pest_problem_description = None
    pest_causes_damage = "n"
    pest_damage_description = None

    pest_name = input(
        "Enter mapped pest_name that Rasa will extract (Return if none): "
    )
    if pest_name == "":
        pest_name = None

    if input("Do you have a question? [y, n] (y): ") in ["y", ""]:
        question = input("Enter your question: ")
    elif input("Do you have a pest problem? [y, n] (y): ") in ["y", ""]:

        pest_problem_description = input("Enter pest problem description: ")
        pest_damage_description = None
        if input("Is it causing damage? [y,n] (y): ") in ["y", ""]:
            pest_damage_description = input("Enter damage description: ")

    return question, pest_name, pest_problem_description, pest_damage_description


async def my_submit(
    question, pest_name, pest_problem_description, pest_damage_description=None
):
    """similar to submit function of the form"""

    await handle_es_query(
        question,
        pest_name,
        pest_problem_description,
        pest_damage_description,
        ac.ipmdata_index_name,
        print_summary=True,
    )


async def main():
    """Run an infinite query loop. ^C to interrupt"""
    while True:
        try:
            (
                question,
                pest_name,
                pest_problem_description,
                pest_damage_description,
            ) = ask_query()

            if question or pest_problem_description:
                await my_submit(
                    question,
                    pest_name,
                    pest_problem_description,
                    pest_damage_description,
                )
            else:
                print("Please try again...")
                print(" ")

        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    asyncio.run(main(), debug=True)

    ##    loop = asyncio.new_event_loop()
    ##    asyncio.set_event_loop(loop)
    ##    result = loop.run_until_complete(run_query_loop())

    print("Done.")
