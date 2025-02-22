variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-1"
}

variable "project_prefix" {
  description = "Prefix to be used for all resource names"
  type        = string
  default     = "audio-transcription"
} 