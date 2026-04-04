import os
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

# Simple dotenv parser so we don't need additional packages
def load_env():
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, val = line.strip().split('=', 1)
                    os.environ[key] = val

load_env()

# Connect using the keys in .env
session = boto3.Session(
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
    region_name=os.environ.get('AWS_REGION', 'ap-south-1')
)

dynamodb = session.resource('dynamodb')

def run_test():
    print("1. Connecting to DynamoDB 'spendwise-budgets' table...")
    budgets_table = dynamodb.Table('spendwise-budgets')
    
    print("2. Ensuring test budget 'budget_ENG_Q1' exists...")
    budgets_table.put_item(
        Item={
            "id": "budget_ENG_Q1",
            "department": "Engineering",
            "total_budget": Decimal('50000'),
            "reserved_amount": Decimal('0'),
            "consumed_amount": Decimal('0')
        }
    )
    
    budget_id = "budget_ENG_Q1"
    expense_amount = Decimal('1000')
    
    print(f"3. Reading current budget for {budget_id}...")
    response = budgets_table.get_item(Key={'id': budget_id})
    budget = response.get('Item')
    
    current_consumed = budget.get('consumed_amount', Decimal('0'))
    new_consumed = current_consumed + expense_amount

    print(f"4. Optimistic Locking Test: Current consumed = {current_consumed}. Attempting pure atomic update to {new_consumed}...")
    
    try:
        budgets_table.update_item(
            Key={'id': budget_id},
            UpdateExpression="SET consumed_amount = :new_val",
            ConditionExpression="consumed_amount = :curr_val",
            ExpressionAttributeValues={
                ':curr_val': current_consumed, 
                ':new_val': new_consumed
            }
        )
        print(f"   [GREEN SIGNAL] SUCCESS! Budget locked and consumed amount atomically updated to: {new_consumed}")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            print("   [RED SIGNAL] Race condition detected! Expected value mutated.")
        else:
            print(f"AWS Error: {e}")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Script Error: {e}")
