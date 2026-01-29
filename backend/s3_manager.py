"""
S3 Manager for Keywords Checker
Handles S3 file operations for Excel processing and Skills management
"""

import os
import logging
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Manager:
    """Manages S3 operations for Excel files and Skills"""
    
    def __init__(self, excel_bucket_name=None, skills_bucket_name=None, 
                 excel_prefix='input/', output_prefix='output/', skills_prefix=''):
        """
        Initialize S3Manager
        
        Args:
            excel_bucket_name: S3 bucket for Excel I/O (defaults to env var EXCEL_BUCKET_NAME)
            skills_bucket_name: S3 bucket for Skills (defaults to env var SKILLS_BUCKET_NAME)
            excel_prefix: Prefix for input Excel files
            output_prefix: Prefix for output Excel files
            skills_prefix: Prefix for skills files
        """
        self.excel_bucket_name = excel_bucket_name or os.getenv('EXCEL_BUCKET_NAME')
        self.skills_bucket_name = skills_bucket_name or os.getenv('SKILLS_BUCKET_NAME')
        self.excel_prefix = excel_prefix
        self.output_prefix = output_prefix
        self.skills_prefix = skills_prefix
        
        # For backward compatibility
        if not self.excel_bucket_name:
            self.excel_bucket_name = os.getenv('S3_BUCKET_NAME')
        
        if not self.excel_bucket_name:
            raise ValueError("EXCEL_BUCKET_NAME environment variable is required")
        
        # Initialize S3 client
        self.s3_client = boto3.client('s3')
        logger.info(f"S3Manager initialized - Excel: {self.excel_bucket_name}, Skills: {self.skills_bucket_name}")
    
    def get_latest_excel_file(self):
        """
        Get the latest Excel file from S3 input directory
        
        Returns:
            tuple: (file_key, file_stream) or (None, None) if no files found
        """
        try:
            # List objects in the input prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.excel_bucket_name,
                Prefix=self.excel_prefix
            )
            
            if 'Contents' not in response:
                logger.warning(f"No files found in s3://{self.excel_bucket_name}/{self.excel_prefix}")
                return None, None
            
            # Filter Excel files
            excel_files = [
                obj for obj in response['Contents']
                if obj['Key'].lower().endswith(('.xlsx', '.xls', '.xlsm'))
            ]
            
            if not excel_files:
                logger.warning(f"No Excel files found in s3://{self.excel_bucket_name}/{self.excel_prefix}")
                return None, None
            
            # Sort by LastModified (newest first)
            latest_file = sorted(excel_files, key=lambda x: x['LastModified'], reverse=True)[0]
            file_key = latest_file['Key']
            
            logger.info(f"Latest Excel file found: {file_key} (Modified: {latest_file['LastModified']})")
            
            # Download file to memory
            file_obj = self.s3_client.get_object(Bucket=self.excel_bucket_name, Key=file_key)
            file_stream = file_obj['Body'].read()
            
            return file_key, file_stream
            
        except ClientError as e:
            logger.error(f"Error accessing S3: {e}", exc_info=True)
            raise
    
    def upload_result_file(self, file_content, original_filename):
        """
        Upload processed Excel file to S3 output directory
        
        Args:
            file_content: Binary content of the Excel file
            original_filename: Original filename (used to generate output filename)
            
        Returns:
            str: S3 key of the uploaded file
        """
        try:
            # Generate output filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = os.path.splitext(os.path.basename(original_filename))[0]
            output_filename = f"{base_name}_checked_{timestamp}.xlsx"
            output_key = os.path.join(self.output_prefix, output_filename)
            
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.excel_bucket_name,
                Key=output_key,
                Body=file_content,
                ContentType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                Metadata={
                    'original_file': original_filename,
                    'processed_at': timestamp
                }
            )
            
            logger.info(f"Result file uploaded to s3://{self.excel_bucket_name}/{output_key}")
            
            return output_key
            
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}", exc_info=True)
            raise
    
    def get_file_url(self, key, bucket_type='excel', expiration=3600):
        """
        Generate a presigned URL for downloading a file
        
        Args:
            key: S3 object key
            bucket_type: 'excel' or 'skills' to specify which bucket
            expiration: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Presigned URL
        """
        try:
            bucket_name = self.excel_bucket_name if bucket_type == 'excel' else self.skills_bucket_name
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )
            
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}", exc_info=True)
            raise
    
    def list_input_files(self):
        """
        List all Excel files in the input directory
        
        Returns:
            list: List of file information dictionaries
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.excel_bucket_name,
                Prefix=self.excel_prefix
            )
            
            if 'Contents' not in response:
                return []
            
            # Filter and format Excel files
            files = []
            for obj in response['Contents']:
                if obj['Key'].lower().endswith(('.xlsx', '.xls', '.xlsm')):
                    files.append({
                        'key': obj['Key'],
                        'filename': os.path.basename(obj['Key']),
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })
            
            # Sort by last_modified (newest first)
            files.sort(key=lambda x: x['last_modified'], reverse=True)
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing S3 files: {e}", exc_info=True)
            raise
    
    def get_skill_file(self, skill_key):
        """
        Get skill or reference file from S3 skills bucket
        
        Args:
            skill_key: S3 object key for the skill file (e.g., 'SKILL.md' or 'references/keyword.md')
            
        Returns:
            str: File content as string
        """
        try:
            if not self.skills_bucket_name:
                raise ValueError("SKILLS_BUCKET_NAME is not configured")
            
            full_key = os.path.join(self.skills_prefix, skill_key) if self.skills_prefix else skill_key
            
            file_obj = self.s3_client.get_object(
                Bucket=self.skills_bucket_name,
                Key=full_key
            )
            
            content = file_obj['Body'].read().decode('utf-8')
            logger.info(f"Skill file loaded from s3://{self.skills_bucket_name}/{full_key}")
            
            return content
            
        except ClientError as e:
            logger.error(f"Error getting skill file from S3: {e}", exc_info=True)
            raise
    
    def list_skill_files(self, prefix=''):
        """
        List all skill files in the skills bucket
        
        Args:
            prefix: Optional prefix to filter files (e.g., 'references/')
            
        Returns:
            list: List of file keys
        """
        try:
            if not self.skills_bucket_name:
                raise ValueError("SKILLS_BUCKET_NAME is not configured")
            
            full_prefix = os.path.join(self.skills_prefix, prefix) if prefix else self.skills_prefix
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.skills_bucket_name,
                Prefix=full_prefix
            )
            
            if 'Contents' not in response:
                return []
            
            # Filter markdown files
            files = [
                obj['Key'] for obj in response['Contents']
                if obj['Key'].lower().endswith('.md')
            ]
            
            logger.info(f"Found {len(files)} skill files in s3://{self.skills_bucket_name}/{full_prefix}")
            
            return files
            
        except ClientError as e:
            logger.error(f"Error listing skill files: {e}", exc_info=True)
            raise
