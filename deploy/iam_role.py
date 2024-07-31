import boto3
import json
from botocore.exceptions import ClientError

def create_iam_role(role_name, policy_name):
    iam_client = boto3.client('iam')

    # Check the role
    try:
        role = iam_client.get_role(RoleName=role_name)
        print(f"Role {role_name} already exists.")
        return role['Role']['Arn']
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            # create IAM role
            assume_role_policy_document = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {
                            "Service": "lambda.amazonaws.com"
                        },
                        "Action": "sts:AssumeRole"
                    }
                ]
            }

            role = iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(assume_role_policy_document),
                Description='Role with access to SQS and DynamoDB'
            )
            print(f"Created role: {role_name}")
        else:
            raise

    # Define the privilege of role
    policy_document = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "sqs:*",
                    "dynamodb:*"
                ],
                "Resource": "*"
            }
        ]
    }

    # Check the policy
    try:
        policy = iam_client.get_policy(PolicyArn=f'arn:aws:iam::aws:policy/{policy_name}')
        print(f"Policy {policy_name} already exists.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchEntity':
            # 创建并附加策略
            policy = iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=json.dumps(policy_document)
            )
            print(f"Created policy: {policy_name}")

        else:
            raise

    iam_client.attach_role_policy(
        RoleName=role_name,
        PolicyArn=policy['Policy']['Arn']
    )

    return role['Role']['Arn']

if __name__ == "__main__":
    role_name = 'LambdaSQSAndDynamoDBRole'
    policy_name = 'LambdaSQSAndDynamoDBPolicy'
    role = create_iam_role(role_name, policy_name)
    print(f"Role ARN: {role}")