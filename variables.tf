variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-1"
}

variable "aws_profile" {
  description = "AWS profile to use"
  type        = string
  default     = "default"
}

variable "project_prefix" {
  description = "Prefix to be used for all resource names"
  type        = string
  default     = "transcribe-manol-eu1-20240222"
}

variable "gemini_api_key" {
  description = "API key for the Google Gemini API"
  type        = string
  sensitive   = true
}

variable "gemini_model_name" {
  description = "Model name for the Google Gemini API"
  type        = string
  default     = "gemini-2.0-pro-exp-02-05"
}

variable "supabase_url" {
  description = "URL for the Supabase API"
  type        = string
  sensitive   = true
}

variable "supabase_anon_key" {
  description = "Anonymous key for the Supabase API"
  type        = string
  sensitive   = true
} 