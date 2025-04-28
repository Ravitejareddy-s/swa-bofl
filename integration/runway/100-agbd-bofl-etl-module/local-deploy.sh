#!/bin/bash
##### CHANGE THE XID to your XID in all the places in this file for local deployment. #####

# Execute the commands sequentially, ensuring each step only runs after successful execution of the previous command.
echo ""
echo "Step 1: Getting AWS credentials..."
if awssaml get-credentials --account-id 437298529078 --name technology-dev-idfdatalake-x325200 --role swa/SWACSDeveloper --user-name x325200 --force-refresh; then
    echo "Successfully obtained AWS credentials."
else
    echo "Failed to obtain AWS credentials."
    exit 1
fi

echo ""
echo ""
echo "Step 2: Populating AWS credentials..."
if awssaml populate-aws-credentials; then
    echo "Successfully populated AWS credentials."
else
    echo "Failed to populate AWS credentials."
    exit 1
fi

echo ""
echo ""
echo "Step 3: Exporting environment variables..."
export AWS_DEFAULT_PROFILE=437298529078-SWACSDeveloper
export AWS_DEFAULT_REGION=us-east-1
export LINUX_TEST_USER=x325200
echo "Environment variables set: AWS_DEFAULT_PROFILE, AWS_DEFAULT_REGION, LINUX_TEST_USER."

echo ""
echo ""
echo "Step 4: Getting AWS caller identity..."
if aws sts get-caller-identity; then
    echo "Successfully retrieved AWS caller identity."
else
    echo "Failed to retrieve AWS caller identity."
    exit 1
fi

echo ""
echo ""
echo "Step 5: Logging into AWS ECR..."
if aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 290503755741.dkr.ecr.us-east-1.amazonaws.com; then
    echo "Successfully logged into AWS ECR."
else
    echo "Failed to log into AWS ECR."
    exit 1
fi

echo ""
echo ""
echo "Step 6: Running Docker Compose test suite..."
if make local-deploy; then
    echo "Docker Compose test suite deployed successfully."
else
    echo "Failed to deploy Docker Compose test suite."
    exit 1
fi

echo ""
echo ""
echo "All steps executed successfully."
