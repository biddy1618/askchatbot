"""Run elastic search queries from the command line"""

import asyncio
import setup_logger  # pylint: disable=unused-import

from actions import actions_config as ac
from actions.actions_main import handle_es_query


def ask_query():
    """Get the input from user"""
    pest_name = input("Enter mapped pest_name (Return if none): ")
    if pest_name == "":
        pest_name = None
    pest_problem_description = input("Enter problem description: ")
    pest_causes_damage = input("Is it causing damage? [y,n]: ")
    pest_damage_description = None
    if pest_causes_damage == "y":
        pest_damage_description = input("Enter damage description: ")

    return pest_name, pest_problem_description, pest_damage_description


async def my_submit(pest_name, pest_problem_description, pest_damage_description=None):
    """similar to submit function of the form"""

    hits = await handle_es_query(
        pest_name,
        pest_problem_description,
        pest_damage_description,
        ac.ipmdata_index_name,
        print_summary=True,
    )

    print(f"Found {len(hits)} hits for:")
    print(f"- problem: {pest_problem_description}")
    print(f"- damage : {pest_damage_description}")
    print("---")


async def main():
    """Run an infinite query loop. ^C to interrupt"""
    while True:
        try:
            (pest_name, pest_problem_description, pest_damage_description) = ask_query()

            await my_submit(
                pest_name, pest_problem_description, pest_damage_description
            )

        except KeyboardInterrupt:
            return


if __name__ == "__main__":
    asyncio.run(main(), debug=True)

    ##    loop = asyncio.new_event_loop()
    ##    asyncio.set_event_loop(loop)
    ##    result = loop.run_until_complete(run_query_loop())

    print("Done.")
