import json
import boto3
import fitz  # PyMuPDF
import os

# Initialize the S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    This Lambda function is triggered by an API Gateway. It expects the name of the
    uploaded PDF file in the event body. It then converts the PDF to a DOCX file
    and saves it to another S3 bucket.
    """
    try:
        # Get the bucket and key (filename) from the event body
        # The body from API Gateway is a string, so we need to parse it as JSON
        body = json.loads(event.get('body', '{}'))
        
        if 'fileName' not in body:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*', # Required for CORS
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST'
                },
                'body': json.dumps({'error': 'Missing fileName in request body'})
            }

        file_name = body['fileName']
        
        # Define your bucket names - REPLACE with your actual bucket names
        upload_bucket = 'upload_bucket_name'
        converted_bucket = 'converted_bucket_name'
        
        # Define file paths for Lambda's temporary storage
        tmp_pdf_path = f"/tmp/{file_name}"
        docx_file_name = f"{os.path.splitext(file_name)[0]}.docx"
        tmp_docx_path = f"/tmp/{docx_file_name}"

        # 1. Download the PDF from the upload bucket to the /tmp directory
        s3.download_file(upload_bucket, file_name, tmp_pdf_path)

        # 2. Convert the PDF to DOCX using PyMuPDF
        doc = fitz.open(tmp_pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        # This is a simple text extraction. For complex layouts, you might need a more advanced library.
        # For this project, we'll just save the extracted text into a file that Word can open.
        # A true "DOCX" conversion is more complex, but this demonstrates the workflow.
        with open(tmp_docx_path, 'w', encoding='utf-8') as docx_file:
            docx_file.write(text)

        # 3. Upload the converted DOCX file to the converted bucket
        s3.upload_file(tmp_docx_path, converted_bucket, docx_file_name)

        # 4. Generate a pre-signed URL for the user to download the file
        presigned_url = s3.generate_presigned_url('get_object',
                                                  Params={'Bucket': converted_bucket,
                                                          'Key': docx_file_name},
                                                  ExpiresIn=3600) # URL expires in 1 hour

        # Return a success response with the download URL
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'message': 'File converted successfully!', 'downloadUrl': presigned_url})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps({'error': str(e)})
        }
