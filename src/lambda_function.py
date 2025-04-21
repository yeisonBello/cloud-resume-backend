import json
import boto3
import os

def lambda_handler(event, context):
    """
    Handles website visit tracking (POST) and count retrieval (GET) 
    for DynamoDB table "count".
    """

    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'count')
    table = dynamodb.Table(table_name)

    item_key = {'key': 1}

    # CORS Headers (Important!)
    cors_headers = {
        'Access-Control-Allow-Origin': '*',  # Or your specific origin
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 
        'Access-Control-Allow-Headers': 'Content-Type, Authorization', 
    }

    # Check the HTTP method
    if event['httpMethod'] == 'POST':
        try:
            response = table.update_item(
                Key=item_key,
                AttributeUpdates={
                    'visits': {
                        'Value': 1,
                        'Action': 'ADD'
                    }
                },
                ReturnValues="UPDATED_NEW"
            )
            print(f"DynamoDB update response: {response}")
            return {
                'statusCode': 200,
                'headers': cors_headers,  # Include CORS headers
                'body': json.dumps({'message': 'Visit tracked successfully'})
            }

        except Exception as e:
            print(f"Error updating DynamoDB: {e}")
            return {
                'statusCode': 500,
                'headers': cors_headers,  # Include CORS headers
                'body': json.dumps({'error': str(e)})
            }

    elif event['httpMethod'] == 'GET':
        try:
            response = table.get_item(Key=item_key)
            item = response.get('Item')

            if item and 'visits' in item:
                visits = int(item['visits'])
                return {
                    'statusCode': 200,
                    'headers': cors_headers,  # Include CORS headers
                    'body': json.dumps({'visits': visits})
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': cors_headers,  # Include CORS headers
                    'body': json.dumps({'message': 'Item not found'})
                }

        except Exception as e:
            return {
                'statusCode': 500,
                'headers': cors_headers,  # Include CORS headers
                'body': json.dumps({'error': str(e)})
            }

    else:
        return {
            'statusCode': 405,  # Method Not Allowed
            'headers': cors_headers,  # Include CORS headers
            'body': json.dumps({'error': 'Method not allowed'})
        }
