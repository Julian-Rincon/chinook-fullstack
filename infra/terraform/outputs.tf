output "frontend_public_ip" {
  description = "Public IP of the frontend EC2 instance."
  value       = aws_instance.frontend.public_ip
}

output "frontend_public_dns" {
  description = "Public DNS of the frontend EC2 instance."
  value       = aws_instance.frontend.public_dns
}

output "frontend_private_ip" {
  description = "Private IP of the frontend EC2 instance."
  value       = aws_instance.frontend.private_ip
}

output "backend_public_ip" {
  description = "Public IP of the backend EC2 instance."
  value       = aws_instance.backend.public_ip
}

output "backend_public_dns" {
  description = "Public DNS of the backend EC2 instance."
  value       = aws_instance.backend.public_dns
}

output "backend_private_ip" {
  description = "Private IP of the backend EC2 instance."
  value       = aws_instance.backend.private_ip
}

output "rds_endpoint" {
  description = "Endpoint hostname of the PostgreSQL RDS instance."
  value       = aws_db_instance.postgres.address
}

output "security_group_ids" {
  description = "Security group IDs created by Terraform."
  value = {
    frontend = aws_security_group.frontend.id
    backend  = aws_security_group.backend.id
    database = aws_security_group.database.id
  }
}
