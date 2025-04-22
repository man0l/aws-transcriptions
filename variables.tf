variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "aws_profile" {
  description = "AWS profile to use for deployment"
  type        = string
}

variable "project_prefix" {
  description = "Prefix to be used for all resource names"
  type        = string
}

variable "gemini_api_key" {
  description = "Google Gemini API key"
  type        = string
}

variable "gemini_model_name" {
  description = "Google Gemini model name"
  type        = string
}

variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
}

variable "supabase_service_key" {
  description = "Supabase service role key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "youtube_api_key" {
  description = "YouTube API key"
  type        = string
  sensitive   = true
}

variable "supabase_anon_key" {
  description = "Supabase anonymous key"
  type        = string
  sensitive   = true
}

variable "aws_access_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
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
  sensitive   = true
  default     = ""
} 