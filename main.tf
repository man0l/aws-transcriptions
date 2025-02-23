# Configure AWS Provider
provider "aws" {
  region = "eu-central-1"
}

# Add this at the beginning of the file, after the provider block
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

# S3 Buckets
resource "aws_s3_bucket" "raw_media_input" {
  bucket = "${var.project_prefix}-raw-media-input"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "raw_media_input" {
  bucket = aws_s3_bucket.raw_media_input.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "processed_transcripts_output" {
  bucket = "${var.project_prefix}-processed-transcripts-output"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "processed_transcripts_output" {
  bucket = aws_s3_bucket.processed_transcripts_output.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Configurations
resource "aws_s3_bucket_public_access_block" "raw_media_input" {
  bucket = aws_s3_bucket.raw_media_input.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed_transcripts_output" {
  bucket = aws_s3_bucket.processed_transcripts_output.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# IAM Role for Lambda
resource "aws_iam_role" "transcription_lambda_role" {
  name = "${var.project_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for Lambda
resource "aws_iam_role_policy" "transcription_lambda_policy" {
  name = "${var.project_prefix}-lambda-policy"
  role = aws_iam_role.transcription_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          aws_s3_bucket.raw_media_input.arn,
          "${aws_s3_bucket.raw_media_input.arn}/*",
          aws_s3_bucket.processed_transcripts_output.arn,
          "${aws_s3_bucket.processed_transcripts_output.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob"
        ]
        Resource = ["*"]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = ["arn:aws:logs:*:*:*"]
      }
    ]
  })
}

# Lambda Function
resource "aws_lambda_function" "transcription_processor" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_prefix}-processor"
  role            = aws_iam_role.transcription_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.9"
  timeout         = 300
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      OUTPUT_BUCKET = aws_s3_bucket.processed_transcripts_output.id
      REGION        = var.aws_region
    }
  }
}

# S3 Event Trigger for Lambda
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.raw_media_input.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.transcription_processor.arn
    events              = ["s3:ObjectCreated:*"]
  }
}

# Lambda permission to allow S3 invocation
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.transcription_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw_media_input.arn
} 