<img width="1400" alt="Descope Cognito Migration Tool" src="https://github.com/descope/descope-Cognito-migration/assets/32936811/992ee6e4-682c-4659-b333-f1d32c16258f">

# Descope Cognito User Migration Tool

This repository includes a Python utility for migrating your Cognito users to Descope.

> **Note**: Cognito does not support the export of hashed passwords, therefore you'll need to create temporary passwords for these users and they will have to be reset by each individual user when they sign in with Descope for the first time.

This tool will be able to get the current user pool configuration schema from the AWS SDK, using the given environment variables. You may need to alter the implementation with roles/tenants, and various role permissions.

## Setup 💿

1. Clone the Repo:

```
git clone https://github.com/descope/descope-cognito-migration.git
```

2. Create a Virtual Environment

```
python3 -m venv venv
source venv/bin/activate
```

3. Install the Necessary Python libraries

```
pip3 install -r requirements.txt
```

4. Setup Your Environment Variables

You can change the name of the `.env.example` file to `.env` to use as a template.

```
AWS_ACCESS_KEY_ID="<Your AWS Access Key>"
AWS_SECRET_ACCESS_KEY="<Your AWS SECRET ACCESS KEY>"
COGNITO_USER_POOL_ID="<YOUR USER POOL ID>"
DESCOPE_PROJECT_ID="<Your Descope Project ID>"
DESCOPE_MANAGEMENT_KEY="Your Descope Management Key>"
```

a. **Access Key ID and Secret Access Key**: Obtain your Access Key ID and Secret Access Key by following the steps outlined on the [AWS Guide](https://aws.amazon.com/blogs/security/wheres-my-secret-access-key/) and update your `.env` file.

Both can be found after an Access Key is created:

<img width="500" alt="AWS Access Key ID" src="https://github.com/descope/descope-Cognito-migration/assets/32936811/992ee6e4-682c-4659-b333-f1d32c16258f">

> **Note:** The Secret Access Key itself will be permanently hidden once first generated.

b. **Cognito User Pool ID**: This can be found in the AWS Cognito console.

<img width="500" alt="AWS User Pool ID" src="https://github.com/descope/descope-Cognito-migration/assets/32936811/992ee6e4-682c-4659-b333-f1d32c16258f">

c. **Descope Project ID and Management Key**: Obtain these from your Descope account under [Project Settings](https://app.descope.com/settings/project) and [Management Keys](https://app.descope.com/settings/company/managementkeys).

## Running the Migration Script 🚀

To migrate your Cognito users, execute the script with the path to the password hash export file:

```
python3 src/main.py
```

The output will include the responses of the created users within Descope:

```
User successfully created
2023-12-04 13:10:48,735 - INFO - Found credentials in environment variables.
2023-12-04 13:10:49,766 - INFO - User gaokevin successfully created in Descope with Cognito User ID 3c50e5ad-c340-4b48-945a-3cda903c2ca1
2023-12-04 13:10:50,830 - INFO - User gaokevin successfully associated with role TestGroup
2023-12-04 13:10:50,832 - INFO - Migration process completed.
...
```

## Testing 🧪

Unit testing can be performed by running the following command:

```
python3 -m unittest tests.test_migration
```

## Issue Reporting ⚠️

For any issues or suggestions, feel free to open an issue in the GitHub repository.

## License 📜

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
