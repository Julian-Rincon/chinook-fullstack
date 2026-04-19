variable "project_name" {
  description = "Base name used for tags and resource names."
  type        = string
  default     = "chinook"
}

variable "region" {
  description = "AWS region where the infrastructure will be created."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the main VPC."
  type        = string
  default     = "10.0.0.0/16"
}

variable "frontend_public_subnet_cidr" {
  description = "CIDR block for the frontend EC2 public subnet."
  type        = string
  default     = "10.0.1.0/24"
}

variable "backend_public_subnet_cidr" {
  description = "CIDR block for the backend EC2 public subnet."
  type        = string
  default     = "10.0.2.0/24"
}

variable "database_private_subnet_1_cidr" {
  description = "CIDR block for the first private database subnet."
  type        = string
  default     = "10.0.10.0/24"
}

variable "database_private_subnet_2_cidr" {
  description = "CIDR block for the second private database subnet."
  type        = string
  default     = "10.0.11.0/24"
}

variable "frontend_instance_type" {
  description = "EC2 instance type for the frontend host."
  type        = string
  default     = "t3.micro"
}

variable "backend_instance_type" {
  description = "EC2 instance type for the backend host."
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Existing AWS EC2 key pair name used for both instances."
  type        = string
}

variable "admin_cidr_blocks" {
  description = "CIDR blocks allowed to SSH into the EC2 instances."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "db_name" {
  description = "Database name for the PostgreSQL RDS instance."
  type        = string
  default     = "chinook"
}

variable "db_username" {
  description = "Master username for the PostgreSQL RDS instance."
  type        = string
}

variable "db_password" {
  description = "Master password for the PostgreSQL RDS instance."
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class for PostgreSQL."
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GiB for PostgreSQL."
  type        = number
  default     = 20
}

variable "db_engine_version" {
  description = "PostgreSQL engine version."
  type        = string
  default     = "16.3"
}

variable "frontend_server_name" {
  description = "Optional DNS name or label for the frontend server."
  type        = string
  default     = "frontend"
}

variable "backend_server_name" {
  description = "Optional DNS name or label for the backend server."
  type        = string
  default     = "backend"
}
