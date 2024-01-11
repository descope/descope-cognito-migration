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
    dry_run = False

    if args.dry_run:
        dry_run = True

    schema_attributes = get_cognito_user_pool_schema()

    # Fetch and Create Users from Cognito
    cognito_users = fetch_cognito_users()

    # Fetch and Process User Groups (Roles) from Cognito
    cognito_groups = fetch_cognito_user_groups()

    logging.info("Migration process completed.")

    if dry_run == False:
        process_users(cognito_users, schema_attributes, dry_run)
        process_user_groups(cognito_groups, dry_run)


if __name__ == "__main__":
    main()
