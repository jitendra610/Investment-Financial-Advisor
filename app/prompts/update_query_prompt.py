
"""
Update Query Agent prompt in PostgreSQL.

1. Read prompt from query_v2.txt.
2. Insert prompt version 2.
3. Activate version 2.
4. Verify the active prompt.
"""

from pathlib import Path

from dotenv import load_dotenv

from app.prompts.manager import (
    add_prompt,
    activate_prompt,
    get_prompt,
    list_prompts,
)

# Load environment variables.
load_dotenv()

# Locate prompt file.
PROMPT_FILE = (
    Path(__file__).resolve().parent
    / "query_v2.txt"
)


def main():

    # Read the new prompt content.
    prompt_content = PROMPT_FILE.read_text(
        encoding="utf-8"
    )

    # Store new version without overwriting version 1.
    add_prompt(
        agent="query",
        version=3,
        content=prompt_content,
    )

    print("Query Agent prompt version 2 stored")

    # Activate version 2.
    activate_prompt(
        agent="query",
        version=3,
    )

    print("Query Agent prompt version 2 activated")

    # Retrieve the active prompt.
    active_prompt = get_prompt("query")

    print("\nActive Prompt Details:")
    print("Agent:", active_prompt.agent)
    print("Prompt ID:", active_prompt.id)
    print("Version:", active_prompt.version)
    print("Active:", active_prompt.is_active)

    # Display available prompt versions.
    print("\nAvailable Versions:")

    for prompt in list_prompts("query"):
        print(prompt)


if __name__ == "__main__":
    main()
