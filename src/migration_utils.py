import json
import os
import requests
from dotenv import load_dotenv
import logging
import time
import descope
import boto3

DESCOPE_API_URL = "https://api.descope.com"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load and read environment variables from .env file
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_REGION = os.getenv("COGNITO_REGION")
DESCOPE_PROJECT_ID = os.getenv("DESCOPE_PROJECT_ID")
DESCOPE_MANAGEMENT_KEY = os.getenv("DESCOPE_MANAGEMENT_KEY")


def api_request_with_retry(action, url, headers, data=None, max_retries=4, timeout=10):
    """
    Handles API requests with additional retry on timeout and rate limit.

    Args:
    - action (string): 'get' or 'post'
    - url (string): The URL of the path for the api request
    - headers (dict): Headers to be sent with the request
    - data (json): Optional and used only for post, but the payload to post
    - max_retries (int): The max number of retries
    - timeout (int): The timeout for the request in seconds
    Returns:
    - API Response
    - Or None
    """
    retries = 0
    while retries < max_retries:
        try:
            if action == "get":
                response = requests.get(url, headers=headers, timeout=timeout)
            else:
                response = requests.post(
                    url, headers=headers, data=data, timeout=timeout
                )

            if (
                response.status_code != 429
            ):  # Not a rate limit error, proceed with response
                return response

            # If rate limit error, prepare for retry
            retries += 1
            wait_time = 5**retries
            logging.info(f"Rate limit reached. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

        except requests.exceptions.ReadTimeout as e:
            # Handle read timeout exception
            logging.warning(f"Read timed out. (read timeout={timeout}): {e}")
            retries += 1
            wait_time = 5**retries
            logging.info(f"Retrying attempt {retries}/{max_retries}...")
            time.sleep(
                wait_time
            )  # Wait for 5 seconds before retrying or use a backoff strategy

        except requests.exceptions.RequestException as e:
            # Handle other request exceptions
            logging.error(f"A request exception occurred: {e}")
            break  # In case of other exceptions, you may want to break the loop

    logging.error("Max retries reached. Giving up.")
    return None


def fetch_cognito_users():
    """
    Fetch and parse Cognito users from the provided endpoint.

    Returns:
    - all_users (List): A list of parsed Cognito users if successful, empty list otherwise.
    """
    client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
    user_pool_id = COGNITO_USER_POOL_ID

    all_users = []
    pagination_token = None

    while True:
        if pagination_token:
            response = client.list_users(
                UserPoolId=user_pool_id, PaginationToken=pagination_token
            )
        else:
            response = client.list_users(UserPoolId=user_pool_id)

        all_users.extend(response["Users"])

        if "PaginationToken" in response:
            pagination_token = response["PaginationToken"]
        else:
            break

    return all_users


def fetch_cognito_user_groups():
    """
    Fetch and parse Cognito user groups from the provided endpoint.

    Returns:
    - all_groups (List): A list of parsed Cognito user groups if successful, empty list otherwise.
    """
    client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
    user_pool_id = COGNITO_USER_POOL_ID

    all_groups = []
    pagination_token = None

    while True:
        if pagination_token:
            response = client.list_groups(
                UserPoolId=user_pool_id, NextToken=pagination_token
            )
        else:
            response = client.list_groups(UserPoolId=user_pool_id)

        all_groups.extend(response["Groups"])

        if "NextToken" in response:
            pagination_token = response["NextToken"]
        else:
            break

    return all_groups


def get_users_in_group(group_name):
    """
    Get and parse Cognito users associated with the provided group.

    Args:
    - group_name (string): The group name to get the associated members

    Returns:
    - all_users (List): A list of users in the given group.
    """
    client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
    user_pool_id = COGNITO_USER_POOL_ID

    all_users = []
    pagination_token = None

    while True:
        if pagination_token:
            response = client.list_users_in_group(
                UserPoolId=user_pool_id,
                GroupName=group_name,
                NextToken=pagination_token,
            )
        else:
            response = client.list_users_in_group(
                UserPoolId=user_pool_id, GroupName=group_name
            )

        all_users.extend(response["Users"])

        if "NextToken" in response:
            pagination_token = response["NextToken"]
        else:
            break

    return all_users


def create_descope_role_and_permissions(role, permissions):
    """
    Create a Descope role and it's associated permissions based on matched Cognito.

    Args:
    - role (dict): A dictionary containing role details from the Cognito.
    - permissions (dict): A dictionary containing permissions details from the Cognito.
    """
    permissionNames = []
    for permission in permissions:
        permissionNames.append(permission["permission_name"])
        payload_data = {
            "name": permission["permission_name"],
            "description": permission["description"],
        }
        payload = json.dumps(payload_data)
        url = "https://api.descope.com/v1/mgmt/permission/create"
        headers = {
            "Authorization": f"Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}",
            "Content-Type": "application/json",
        }
        response = api_request_with_retry("post", url, headers=headers, data=payload)
        if response.status_code != 200:
            logging.error(
                f"Unable to create permission.  Status code: {response.status_code}"
            )
        else:
            logging.info("Permission successfully created")
            logging.info(response.text)

    payload_data = {
        "name": role["name"],
        "description": role["description"],
        "permissionNames": permissionNames,
    }
    payload = json.dumps(payload_data)
    url = "https://api.descope.com/v1/mgmt/role/create"
    headers = {
        "Authorization": f"Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}",
        "Content-Type": "application/json",
    }
    response = api_request_with_retry("post", url, headers=headers, data=payload)
    if response.status_code != 200:
        logging.error(f"Unable to create role.  Status code: {response.status_code}")
    else:
        logging.info("Role successfully created")
        logging.info(response.text)


def create_descope_user(user):
    """
    Create a Descope user based on matched Cognito user data.

    Args:
    - user (dict): A dictionary containing user details fetched from Cognito SDK.
    """
    try:
        for identity in user.get("identities", []):
            if "Username" in identity["connection"]:
                loginId = user.get("email")
            elif "sms" in identity["connection"]:
                loginId = user.get("phone_number")
            elif "-" in identity["connection"]:
                loginId = (
                    identity["connection"].split("-")[0] + "-" + identity["user_id"]
                )
            else:
                loginId = identity["connection"] + "-" + identity["user_id"]

            payload_data = {
                "loginId": loginId,
                "displayName": user.get("name"),
                "invite": False,
                "test": False,
                "picture": user.get("picture"),
                "customAttributes": {
                    "connection": identity.get("connection"),
                    "freshlyMigrated": True,
                },
            }

            # Add email and verifiedEmail only if email is present and not empty
            if user.get(
                "email"
            ):  # This will be False if email is None or an empty string
                payload_data["email"] = user["email"]
                payload_data["verifiedEmail"] = user.get("email_verified", False)

            if identity.get("provider") == "sms":
                payload_data.update(
                    {
                        "phone": user.get("phone_number"),
                        "verifiedPhone": user.get("phone_verified", False),
                    }
                )

            # Check if the user is blocked and set status accordingly
            status = "disabled" if user.get("blocked", False) else "enabled"

            # Prepare API call to create or update the user
            payload = json.dumps(payload_data)
            headers = {
                "Authorization": f"Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}",
                "Content-Type": "application/json",
            }

            # Create or update user profile
            success = create_or_update_user(payload, headers)
            if success == True:
                # Update user status
                success = update_user_status(loginId, status, headers)
            else:
                logging.warning(f"User failed to create {user}")

    except Exception as e:
        logging.warning(f"User failed to create {user}")
        logging.warning(e)


def create_or_update_user(payload, headers):
    url = "https://api.descope.com/v1/mgmt/user/create"
    response = api_request_with_retry("post", url, headers=headers, data=payload)
    if response.status_code != 200:
        logging.error(
            f"Unable to create or update user. Status code: {response.status_code}"
        )
        return False
    else:
        logging.info("User successfully created or updated")
        return True


def update_user_status(loginId, status, headers):
    active_inactive_payload = {"loginId": loginId, "status": status}
    payload = json.dumps(active_inactive_payload)
    url = "https://api.descope.com/v1/mgmt/user/update/status"
    response = api_request_with_retry("post", url, headers=headers, data=payload)
    if response.status_code != 200:
        logging.error(f"Failed to set user status. Status code: {response.status_code}")
        return False
    else:
        logging.info("Successfully set user status")
        return True


def add_user_to_descope_role(user, role):
    """
    Add a Descope user based on matched Auth0 user data.

    Args:
    - user (string): Login ID of the user you wish to add to role
    - role (string): The name of the role which you want to add the user to
    """
    payload_data = {"loginId": user, "roleNames": [role]}
    payload = json.dumps(payload_data)

    # Endpoint
    url = "https://api.descope.com/v1/mgmt/user/create"

    # Headers
    headers = {
        "Authorization": f"Bearer {DESCOPE_PROJECT_ID}:{DESCOPE_MANAGEMENT_KEY}",
        "Content-Type": "application/json",
    }
    # Make the POST request
    response = api_request_with_retry("post", url, headers=headers, data=payload)
    if response.status_code != 200:
        logging.error(
            f"Unable to add role to user.  Status code: {response.status_code}"
        )
    else:
        logging.info("User role successfully added")
        logging.info(response.text)


### Begin Process Functions


def process_users(api_response_users, dry_run):
    """
    Process the list of users from Cognito by mapping and creating them in Descope.

    Args:
    - api_response_users (list): A list of users fetched from Cognito API.
    """
    for user in api_response_users:
        # Extracting email, phone number and custom attribute from Cognito user
        email, phone_number, custom_attribute = None, None, None
        for attribute in user.get("Attributes", []):
            if attribute["Name"] == "email":
                email = attribute["Value"]
            elif attribute["Name"] == "phone_number":
                phone_number = attribute["Value"]
            elif (
                attribute["Name"] == "custom:customAttribute"
            ):  # Adjust the custom attribute name
                custom_attribute = attribute["Value"]

        # Map Cognito user attributes to Descope user attributes
        descope_user_data = {
            "loginId": user.get("Username"),  # Using Username as the login ID
            "email": email,
            "phone": phone_number,
            "customAttributes": {
                # Adjust as needed
                # "customAttribute": custom_attribute
            },
        }

        if dry_run:
            logging.info(f"Dry run: Would create user {descope_user_data['loginId']}")
            continue

        # Make a POST request to Descope API to create the user
        response = requests.post(
            f"{DESCOPE_API_URL}/v1/mgmt/user/create",
            json=descope_user_data,
            headers={
                "Authorization": f"Bearer {os.getenv('DESCOPE_PROJECT_ID')}:{os.getenv('DESCOPE_MANAGEMENT_KEY')}"
            },
        )

        if response.status_code == 200:
            logging.info(
                f"User {descope_user_data['loginId']} successfully created in Descope"
            )
        else:
            logging.error(
                f"Failed to create user {descope_user_data['loginId']}: {response.text}"
            )


def process_user_groups(cognito_groups, dry_run):
    """
    Process the Cognito user groups - creating roles in Descope and associating users

    Args:
    - cognito_groups (list): List of groups fetched from Cognito
    """
    for group in cognito_groups:
        group_name = group.get("GroupName")
        descope_role_data = {
            "name": group.get("GroupName"),
            # Add other necessary mappings or attributes
        }

        if dry_run:
            logging.info(f"Dry run: Would create role {descope_role_data['name']}")
            continue

        # Make a POST request to Descope API to create the role
        response = requests.post(
            f"{DESCOPE_API_URL}/v1/mgmt/role/create",  # Update with the correct endpoint
            json=descope_role_data,
            headers={
                "Authorization": f"Bearer {os.getenv('DESCOPE_PROJECT_ID')}:{os.getenv('DESCOPE_MANAGEMENT_KEY')}"
            },
        )

        if response.status_code == 200:
            logging.info(
                f"Role {descope_role_data['name']} successfully created in Descope"
            )
        else:
            logging.error(
                f"Failed to create role {descope_role_data['name']}: {response.text}"
            )

        # Fetch users in this group from Cognito
        cognito_users_in_group = get_users_in_group(group_name)

        # Associate these users with the role in Descope
        if not dry_run:
            associate_users_with_role_in_descope(
                cognito_users_in_group, descope_role_data["name"]
            )


def associate_users_with_role_in_descope(users, role_name):
    """
    Associate a list of users with a role in Descope.

    Args:
    - users (list): List of user identifiers (e.g., email or username).
    - role_name (string): The name of the role in Descope.
    """
    for user in users:
        # Assuming user is a dictionary with user details from Cognito
        descope_user_identifier = user.get("Username")  # Or any other unique identifier

        # Prepare the payload for the Descope API to associate user with the role
        data = {
            "email": descope_user_identifier,  # Adjust based on Descope's API requirements
            "role": role_name,
        }

        # Make the API call
        response = requests.post(
            f"{DESCOPE_API_URL}/assign-role",  # Update with the correct endpoint
            json=data,
            headers={"Authorization": f"Bearer {os.getenv('DESCOPE_MANAGEMENT_KEY')}"},
        )

        if response.status_code == 200:
            logging.info(
                f"User {descope_user_identifier} successfully associated with role {role_name}"
            )
        else:
            logging.error(
                f"Failed to associate user {descope_user_identifier} with role {role_name}: {response.text}"
            )


### End Process Functions
