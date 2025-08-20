import boto3
import os
from datetime import datetime

class S3Uploader:
    def __init__(self):
        self.bucket_name = os.environ.get("S3_BUCKET_NAME", "credit-notes-files")
        self.aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.environ.get("AWS_REGION", "us-west-1")

        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables must be set.")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )

    async def upload_file_to_s3(self, file_content_bytes: bytes, original_file_name: str, center_folder_name: str) -> str:
        """
        Uploads file content to S3, organizing by date and center folder.
        Returns the S3 URL of the uploaded file.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Construct S3 key: date/center_folder_name/original_file_name
        s3_key = f"{current_date}/{center_folder_name}/{original_file_name}"

        try:
            # Use put_object with Bytes (file_content_bytes)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content_bytes,
                ContentType='application/pdf' # Assuming PDF files
            )
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            print(f"  -> ☁️ PDF subido a S3: {s3_url}")
            return s3_url
        except Exception as e:
            print(f"❌ Error subiendo PDF a S3 ({s3_key}): {str(e)}")
            raise

    async def upload_log_to_s3(self, log_content: str, log_file_name: str) -> str:
        """
        Uploads log content to S3, organizing by date.
        Returns the S3 URL of the uploaded log file.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        # Construct S3 key: date/logs/log_file_name
        s3_key = f"{current_date}/logs/{log_file_name}"

        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=log_content.encode('utf-8'),
                ContentType='application/json' # Assuming JSON logs
            )
            s3_url = f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com/{s3_key}"
            print(f"  -> ☁️ Log subido a S3: {s3_url}")
            return s3_url
        except Exception as e:
            print(f"❌ Error subiendo log a S3 ({s3_key}): {str(e)}")
            raise