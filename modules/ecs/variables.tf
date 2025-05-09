variable "project_prefix" {
  description = "Prefix to be used for all resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones to use"
  type        = list(string)
}

variable "task_cpu" {
  description = "CPU units for the ECS task (1024 = 1 vCPU)"
  type        = number
  default     = 1024
}

variable "task_memory" {
  description = "Memory for the ECS task in MiB"
  type        = number
  default     = 2048
}

variable "desired_count" {
  description = "Desired number of tasks to run"
  type        = number
  default     = 1
}

variable "raw_media_bucket" {
  description = "Name of the S3 bucket for raw media"
  type        = string
}

variable "processed_transcripts_bucket" {
  description = "Name of the S3 bucket for processed transcripts"
  type        = string
}

variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
}

variable "supabase_service_key_arn" {
  description = "ARN of the Supabase service key in AWS Secrets Manager"
  type        = string
}

variable "container_image" {
  description = "Container image name without tag (e.g. ghcr.io/man0l/aihub-worker)"
  type        = string
  default     = "ghcr.io/man0l/aihub-worker"
}

variable "container_image_tag" {
  description = "Container image tag to use"
  type        = string
  default     = "latest"
}

variable "aws_access_key_id" {
  description = "AWS access key ID for the worker"
  type        = string
}

variable "aws_secret_access_key" {
  description = "AWS secret access key for the worker"
  type        = string
}

variable "youtube_api_key" {
  description = "YouTube API key for the worker"
  type        = string
}

variable "openai_api_key" {
  description = "OpenAI API key for frontend content extraction"
  type        = string
  sensitive   = true
}

variable "proxy_enabled" {
  description = "Whether to enable proxy for the ECS tasks"
  type        = string
  default     = "false"
}

variable "proxy_host" {
  description = "Proxy host address"
  type        = string
  default     = ""
}

variable "proxy_port" {
  description = "Proxy port number"
  type        = string
  default     = ""
}

variable "proxy_username" {
  description = "Proxy authentication username"
  type        = string
  default     = ""
}

variable "proxy_password" {
  description = "Proxy authentication password"
  type        = string
  default     = ""
} 