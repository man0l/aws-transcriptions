output "raw_media_bucket_name" {
  description = "Name of the S3 bucket for raw media input"
  value       = aws_s3_bucket.raw_media_input.id
}

output "processed_transcripts_bucket_name" {
  description = "Name of the S3 bucket for processed transcripts"
  value       = aws_s3_bucket.processed_transcripts_output.id
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.transcription_processor.function_name
} 