import sys
import logging
import argparse
from migration_utils import (
    fetch_cognito_users,
    process_users,
    fetch_cognito_user_groups,
    process_user_groups,
    get_cognito_user_pool_schema,
)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    """
    Main function to process Cognito users and groups, creating and mapping them within your Descope project.
    """
    parser = argparse.ArgumentParser(
        description="This program assists you in migrating your users and user groups from AWS Cognito to Descope."
    )
    parser.add_argument("--dry-run", action="store_true", help="Enable dry run mode")
    args = parser.parse_args()
    dry_run = args.dry_run

    response = (
        input(
            "Have you already created custom attributes in Descope that match your Cognito user pool? (yes/no): "
        )
        .strip()
        .lower()
    )
    if response not in ["yes", "y"]:
        print(
            "Please ensure that your Descope custom attributes match your Cognito user pool before proceeding."
        )
        return

    schema_attributes = get_cognito_user_pool_schema()

    # Fetch and Create Users from Cognito
    cognito_users = fetch_cognito_users()
    process_users(cognito_users, schema_attributes, dry_run)

    # Fetch and Process User Groups (Roles) from Cognito
    cognito_groups = fetch_cognito_user_groups()
    process_user_groups(cognito_groups, dry_run)

    logging.info("Migration process completed.")


if __name__ == "__main__":
    main()
