import json
import boto3
import os
import logging
import time

logger = logging.getLogger(__name__)

class SQSPoller:
    def __init__(self, queue_url):
        self.queue_url = queue_url
        self.sqs_client = boto3.client(
            "sqs", 
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )

    def poll_for_message(self):
        logger.info(f"Polling SQS queue: {self.queue_url}")
        while True:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=1,
                    WaitTimeSeconds=20,
                    AttributeNames=['All']
                )

                if "Messages" in response:
                    message = response["Messages"][0]
                    receipt_handle = message["ReceiptHandle"]
                    target_date = message["Body"]
                    
                    # Delete the message from the queue
                    self.sqs_client.delete_message(
                        QueueUrl=self.queue_url,
                        ReceiptHandle=receipt_handle
                    )
                    
                    logger.info(f"Received and deleted message. Target date: {target_date}")
                    return target_date
                else:
                    logger.info("No messages in queue. Waiting...")
            except Exception as e:
                logger.error(f"Error polling SQS: {e}")
                # In case of error, wait before retrying
                time.sleep(60)
