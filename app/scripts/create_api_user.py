import asyncio
import getpass

# Used to construct SQL SELECT queries.
from sqlalchemy import select

# APIUser: Database model for storing application users.
# CustomerAccess: Database model for mapping users to customers.
from app.models.api_user import APIUser, CustomerAccess

# SQLAlchemy asynchronous session factory for authentication database.
from app.auth.database import AuthSessionLocal

# Custom function to securely hash passwords before storing them.
from app.auth.security import hash_password


# Main asynchronous function to create a development user.
async def main():

    # Ask the administrator to enter a username.
    # strip() removes leading and trailing whitespace.
    username = input("Username: ").strip()

    # Ask for a password without displaying typed characters.
    password = getpass.getpass("Password: ")

    # Validate username and password.
    # Username cannot be empty.
    # Password must contain at least 12 characters.
    if not username or len(password) < 12:
        raise ValueError(
            "Username is required and password must "
            "contain at least 12 characters"
        )

    # Create an asynchronous database session.
    # The session is automatically closed after this block.
    async with AuthSessionLocal() as session:

        # Check whether the username already exists in the database.
        existing = await session.scalar(
            select(APIUser).where(
                APIUser.username == username
            )
        )

        # Prevent creating duplicate usernames.
        if existing:
            raise ValueError("Username already exists")

        # Create a new APIUser object.
        user = APIUser(
            # Store the entered username.
            username=username,

            # Hash the password before storing it.
            # Never store passwords in plain text.
            hashed_password=hash_password(password),

            # Mark the newly created user as active.
            is_active=True,
        )

        # Add the new user object to the current database session.
        # This does not immediately commit the data.
        session.add(user)

        # Send pending INSERT statements to the database.
        # This allows the database-generated user.id
        # to become available before committing.
        await session.flush()

        # Create an authorization mapping for the new user.
        # This user will be allowed to access customer CUST-003.
        session.add(
            CustomerAccess(
                # Reference the newly created user's primary key.
                user_id=user.id,

                # Customer ID the user is authorized to access.
                customer_id="CUST-003",
            )
        )

        # Commit both records to the database:
        # 1. New API user
        # 2. User-to-customer access mapping
        await session.commit()

    # Display confirmation after successful database commit.
    print("Development user created.")
    print("Authorized customer: CUST-003")


# Execute the script only when run directly.
# This block does not execute when the module is imported.
if __name__ == "__main__":

    # Start the asyncio event loop and execute main().
    asyncio.run(main())
