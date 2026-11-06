
"""
Test Prompt Management System.

Tests:
1. Create prompt table.
2. Add prompt versions.
3. Retrieve specific prompt versions.
4. Activate prompt versions.
5. Retrieve active prompt.
6. List all prompt versions.
7. Validate invalid prompt handling.
8. Clean up test data.
"""

import uuid

from sqlalchemy import text

# Import prompt management functions.
from app.prompts.manager import (
    engine,
    create_prompt_table,
    add_prompt,
    get_prompt,
    activate_prompt,
    list_prompts,
)


def test_prompt_manager():

    # Generate a unique agent name to avoid conflicts
    # with existing production agent prompts.
    agent = f"test_{uuid.uuid4().hex[:12]}"

    print("\n1. Creating Prompt Table...")

    # Create table if it does not exist.
    create_prompt_table()

    try:

        # ----------------------------------------
        # TEST 1: ADD PROMPT VERSION 1
        # ----------------------------------------
        print("\n2. Adding Prompt Version 1...")

        add_prompt(
            agent=agent,
            version=1,
            content="You are a test investment assistant."
        )

        # Retrieve version 1 explicitly.
        prompt_v1 = get_prompt(agent, version=1)

        assert prompt_v1.agent == agent
        assert prompt_v1.version == 1
        assert prompt_v1.is_active is False

        print("PASS: Prompt version 1 created")

        # ----------------------------------------
        # TEST 2: ADD PROMPT VERSION 2
        # ----------------------------------------
        print("\n3. Adding Prompt Version 2...")

        add_prompt(
            agent=agent,
            version=2,
            content=(
                "You are a UK investment assistant. "
                "Provide clear and grounded explanations."
            )
        )

        prompt_v2 = get_prompt(agent, version=2)

        assert prompt_v2.version == 2
        assert prompt_v2.is_active is False

        print("PASS: Prompt version 2 created")

        # ----------------------------------------
        # TEST 3: ACTIVATE VERSION 1
        # ----------------------------------------
        print("\n4. Activating Version 1...")

        activate_prompt(agent, version=1)

        active_prompt = get_prompt(agent)

        assert active_prompt.version == 1
        assert active_prompt.is_active is True

        print("PASS: Version 1 activated")

        # ----------------------------------------
        # TEST 4: ACTIVATE VERSION 2
        # ----------------------------------------
        print("\n5. Activating Version 2...")

        activate_prompt(agent, version=2)

        active_prompt = get_prompt(agent)

        assert active_prompt.version == 2
        assert active_prompt.is_active is True

        # Verify version 1 is now inactive.
        old_prompt = get_prompt(agent, version=1)

        assert old_prompt.is_active is False

        print("PASS: Version 2 activated")
        print("PASS: Version 1 automatically deactivated")

        # ----------------------------------------
        # TEST 5: LIST PROMPTS
        # ----------------------------------------
        print("\n6. Listing Prompt Versions...")

        prompts = list_prompts(agent)

        assert len(prompts) == 2
        assert [p["version"] for p in prompts] == [1, 2]

        print("PASS: Both prompt versions retrieved")

        # ----------------------------------------
        # TEST 6: INVALID PROMPT
        # ----------------------------------------
        print("\n7. Testing Invalid Prompt...")

        try:
            add_prompt(
                agent=agent,
                version=0,
                content="Invalid prompt"
            )
            raise AssertionError(
                "Expected ValueError for invalid version"
            )

        except ValueError:
            print("PASS: Invalid version rejected")

        # ----------------------------------------
        # TEST 7: NONEXISTENT PROMPT
        # ----------------------------------------
        print("\n8. Testing Missing Prompt...")

        try:
            get_prompt(agent, version=999)
            raise AssertionError(
                "Expected LookupError for missing prompt"
            )

        except LookupError:
            print("PASS: Missing prompt correctly rejected")

        print("\nAll Prompt Manager tests passed!")

    finally:

        # ----------------------------------------
        # CLEANUP TEST DATA
        # ----------------------------------------
        print("\n9. Cleaning Up Test Prompts...")

        # Delete only the temporary test agent prompts.
        with engine.begin() as conn:
            conn.execute(
                text("""
                    DELETE FROM agent_prompts
                    WHERE agent = :agent
                """),
                {"agent": agent},
            )

        print("PASS: Test data removed")


# Run test directly.
if __name__ == "__main__":
    test_prompt_manager()
