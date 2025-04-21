import unittest
from unittest.mock import MagicMock, patch
import json
import boto3
from botocore.exceptions import ClientError
import os

# It's generally better to import the function under test once,
# but given the patching strategy used in other tests (importing within the patch context),
# we'll keep that pattern for consistency, importing it where needed.
# If lambda_function.py initializes boto3 globally, this pattern is necessary.
# from lambda_function import lambda_handler # Potential alternative placement


class TestLambdaFunction(unittest.TestCase):

    def setUp(self):
        """
        Set up test environment before each test.
        - Mocks environment variables.
        - Creates a mock context object.
        """
        os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'  # Mock the table name
        self.mock_context = MagicMock()  # Create a mock Lambda context object

    def test_post_success(self):
        """
        Test successful POST request (visit tracking).
        - Mocks DynamoDB update_item to return a successful response.
        - Asserts that the Lambda function returns 200 and the correct message.
        """
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        # Mock successful update
        mock_table.update_item.return_value = {'Attributes': {'visits': 1}}

        with patch('boto3.resource', return_value=mock_dynamodb):
            # Import the function here to ensure it uses the patched boto3
            from lambda_function import lambda_handler
            event = {'httpMethod': 'POST'}
            response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {
                         'message': 'Visit tracked successfully'})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])

    def test_post_dynamodb_error(self):
        """
        Test POST request when DynamoDB update fails.
        - Mocks DynamoDB update_item to raise a ClientError exception.
        - Asserts that the Lambda function returns 500 and the error message.
        """
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        # Mock DynamoDB error
        mock_table.update_item.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Test error'}},
            operation_name='update_item'
        )

        with patch('boto3.resource', return_value=mock_dynamodb):
            # Import the function here to ensure it uses the patched boto3
            from lambda_function import lambda_handler
            event = {'httpMethod': 'POST'}
            response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), {
                         'error': 'An error occurred (500) when calling the update_item operation: Test error'})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])

    def test_get_success(self):
        """
        Test successful GET request (visit count retrieval).
        - Mocks DynamoDB get_item to return an item with visit count.
        - Asserts that the Lambda function returns 200 and the visit count.
        """
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        # Mock successful retrieval
        mock_table.get_item.return_value = {'Item': {'visits': 10}}

        with patch('boto3.resource', return_value=mock_dynamodb):
            # Import the function here to ensure it uses the patched boto3
            from lambda_function import lambda_handler
            event = {'httpMethod': 'GET'}
            response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {'visits': 10})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])

    def test_get_item_not_found(self):
        """
        Test GET request when the item is not found in DynamoDB.
        - Mocks DynamoDB get_item to return an empty response (item not found).
        - Asserts that the Lambda function returns 404 and the "Item not found" message.
        """
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_table.get_item.return_value = {}  # Mock item not found

        with patch('boto3.resource', return_value=mock_dynamodb):
            # Import the function here to ensure it uses the patched boto3
            from lambda_function import lambda_handler
            event = {'httpMethod': 'GET'}
            response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 404)
        self.assertEqual(json.loads(response['body']), {
                         'message': 'Item not found'})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])

    def test_get_dynamodb_error(self):
        """
        Test GET request when DynamoDB retrieval fails.
        - Mocks DynamoDB get_item to raise a ClientError exception.
        - Asserts that the Lambda function returns 500 and the error message.
        """
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        # Mock DynamoDB error
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': '500', 'Message': 'Test error'}},
            operation_name='get_item'
        )

        with patch('boto3.resource', return_value=mock_dynamodb):
            # Import the function here to ensure it uses the patched boto3
            from lambda_function import lambda_handler
            event = {'httpMethod': 'GET'}
            response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body']), {
                         'error': 'An error occurred (500) when calling the get_item operation: Test error'})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])

    def test_invalid_method(self):
        """
        Test handling of an invalid HTTP method.
        - Sends a request with an HTTP method other than GET or POST.
        - Asserts that the Lambda function returns 405 and the "Method not allowed" error.
        """
        # Import here as this test doesn't need the boto3 patch context
        from lambda_function import lambda_handler
        event = {'httpMethod': 'PUT'}  # Invalid method
        response = lambda_handler(event, self.mock_context)

        self.assertEqual(response['statusCode'], 405)
        self.assertEqual(json.loads(response['body']), {
                         'error': 'Method not allowed'})
        # Check for CORS header
        self.assertIn('Access-Control-Allow-Origin', response['headers'])


if __name__ == '__main__':
    unittest.main()
