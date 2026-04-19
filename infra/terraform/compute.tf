data "aws_ami" "ubuntu_2404" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "frontend" {
  ami                         = data.aws_ami.ubuntu_2404.id
  instance_type               = var.frontend_instance_type
  subnet_id                   = aws_subnet.frontend_public.id
  vpc_security_group_ids      = [aws_security_group.frontend.id]
  key_name                    = var.key_pair_name
  associate_public_ip_address = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.frontend_server_name}"
    Role = "frontend"
  })
}

resource "aws_instance" "backend" {
  ami                         = data.aws_ami.ubuntu_2404.id
  instance_type               = var.backend_instance_type
  subnet_id                   = aws_subnet.backend_public.id
  vpc_security_group_ids      = [aws_security_group.backend.id]
  key_name                    = var.key_pair_name
  associate_public_ip_address = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-${var.backend_server_name}"
    Role = "backend"
  })
}
