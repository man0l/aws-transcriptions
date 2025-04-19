# Configure AWS Provider
provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}

# Add this at the beginning of the file, after the provider block
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}

# Create a ZIP file for chapter generator lambda with dependencies
resource "null_resource" "install_dependencies" {
  triggers = {
    dependencies_versions = filemd5("${path.module}/requirements.txt")
    source_code = filemd5("${path.module}/chapter_generator.py")
    force_rebuild = timestamp()
  }

  provisioner "local-exec" {
    command = "${path.module}/create_lambda_package.sh"
  }
}

data "archive_file" "chapter_generator_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_package"
  output_path = "${path.module}/chapter_generator.zip"
  
  depends_on = [null_resource.install_dependencies]
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

# Document Upload S3 Bucket
resource "aws_s3_bucket" "document_upload" {
  bucket = "${var.project_prefix}-document-upload"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "document_upload" {
  bucket = aws_s3_bucket.document_upload.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "document_upload" {
  bucket = aws_s3_bucket.document_upload.id

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

# IAM Role for the Chapter Generator Lambda
resource "aws_iam_role" "chapter_generator_lambda_role" {
  name = "${var.project_prefix}-chapter-generator-role"

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

# IAM Policy for Chapter Generator Lambda
resource "aws_iam_role_policy" "chapter_generator_lambda_policy" {
  name = "${var.project_prefix}-chapter-generator-policy"
  role = aws_iam_role.chapter_generator_lambda_role.id

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
          aws_s3_bucket.processed_transcripts_output.arn,
          "${aws_s3_bucket.processed_transcripts_output.arn}/*"
        ]
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

# Chapter Generator Lambda Function
resource "aws_lambda_function" "chapter_generator" {
  filename         = data.archive_file.chapter_generator_zip.output_path
  function_name    = "${var.project_prefix}-chapter-generator"
  role             = aws_iam_role.chapter_generator_lambda_role.arn
  handler          = "chapter_generator.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 256
  source_code_hash = data.archive_file.chapter_generator_zip.output_base64sha256

  environment {
    variables = {
      GEMINI_API_KEY = var.gemini_api_key
      GEMINI_MODEL_NAME = var.gemini_model_name
      REGION = var.aws_region
      SUPABASE_URL = var.supabase_url
      SUPABASE_SERVICE_KEY = var.supabase_service_key
    }
  }
}

# S3 Event Trigger for Chapter Generator Lambda
resource "aws_s3_bucket_notification" "transcript_notification" {
  bucket = aws_s3_bucket.processed_transcripts_output.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.chapter_generator.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "transcripts/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.allow_transcript_bucket]
}

# Lambda permission to allow S3 invocation for chapter generator
resource "aws_lambda_permission" "allow_transcript_bucket" {
  statement_id  = "AllowS3InvokeChapterGenerator"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chapter_generator.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.processed_transcripts_output.arn
}

# IAM Role for Summary Generator Lambda
resource "aws_iam_role" "summary_generator_lambda_role" {
  name = "${var.project_prefix}-summary-generator-role"

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

# IAM Policy for Summary Generator Lambda
resource "aws_iam_role_policy" "summary_generator_lambda_policy" {
  name = "${var.project_prefix}-summary-generator-policy"
  role = aws_iam_role.summary_generator_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.processed_transcripts_output.arn,
          "${aws_s3_bucket.processed_transcripts_output.arn}/*"
        ]
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

# Summary Generator Lambda Function
resource "aws_lambda_function" "summary_generator" {
  filename         = data.archive_file.chapter_generator_zip.output_path
  function_name    = "${var.project_prefix}-summary-generator"
  role             = aws_iam_role.summary_generator_lambda_role.arn
  handler          = "summary_generator.lambda_handler"
  runtime          = "python3.9"
  timeout          = 300
  memory_size      = 256
  source_code_hash = data.archive_file.chapter_generator_zip.output_base64sha256

  environment {
    variables = {
      GEMINI_API_KEY = var.gemini_api_key
      GEMINI_MODEL_NAME = var.gemini_model_name
      SUPABASE_URL = var.supabase_url
      SUPABASE_SERVICE_KEY = var.supabase_service_key
    }
  }
}

# IAM Policy for Chapter Generator Lambda to allow EventBridge
resource "aws_iam_role_policy_attachment" "chapter_generator_eventbridge" {
  role       = aws_iam_role.chapter_generator_lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
}

# Additional EventBridge permissions for Chapter Generator Lambda
resource "aws_iam_role_policy" "chapter_generator_eventbridge_policy" {
  name = "${var.project_prefix}-chapter-generator-eventbridge-policy"
  role = aws_iam_role.chapter_generator_lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = ["*"]
      }
    ]
  })
}

# EventBridge IAM Role
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project_prefix}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })
}

# EventBridge IAM Policy
resource "aws_iam_role_policy" "eventbridge_policy" {
  name = "${var.project_prefix}-eventbridge-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          aws_lambda_function.summary_generator.arn
        ]
      }
    ]
  })
}

# EventBridge Rule for Summary Generation
resource "aws_cloudwatch_event_rule" "summary_generation" {
  name        = "${var.project_prefix}-summary-generation"
  description = "Rule to trigger summary generation Lambda"

  event_pattern = jsonencode({
    source      = ["custom.transcription"]
    detail-type = ["SummaryGenerationRequest"]
  })
}

# EventBridge Target for Summary Generation
resource "aws_cloudwatch_event_target" "summary_generation" {
  rule      = aws_cloudwatch_event_rule.summary_generation.name
  target_id = "SummaryGeneratorLambda"
  arn       = aws_lambda_function.summary_generator.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}

# Lambda permission to allow EventBridge invocation
resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.summary_generator.function_name
  principal     = "events.amazonaws.com"
  source_arn    = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/*"
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Create a secret for Supabase service key
resource "aws_secretsmanager_secret" "supabase_service_key" {
  name = "${var.project_prefix}-supabase-service-key"
}

resource "aws_secretsmanager_secret_version" "supabase_service_key" {
  secret_id     = aws_secretsmanager_secret.supabase_service_key.id
  secret_string = var.supabase_service_key
}

# ECS Worker Module
module "ecs_worker" {
  source = "./modules/ecs"

  project_prefix               = var.project_prefix
  aws_region                  = var.aws_region
  availability_zones          = ["${var.aws_region}a", "${var.aws_region}b"]
  raw_media_bucket           = aws_s3_bucket.raw_media_input.id
  processed_transcripts_bucket = aws_s3_bucket.processed_transcripts_output.id
  supabase_url               = var.supabase_url
  supabase_service_key_arn   = aws_secretsmanager_secret.supabase_service_key.arn

  # Optional customizations
  task_cpu       = 2048    # 2 vCPU
  task_memory    = 4096    # 4GB RAM
  desired_count  = 1       # Number of tasks to run

  # New variables
  aws_access_key_id     = var.aws_access_key_id
  aws_secret_access_key = var.aws_secret_access_key
  youtube_api_key       = var.youtube_api_key
} 