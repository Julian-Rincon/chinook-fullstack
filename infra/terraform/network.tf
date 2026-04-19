data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  common_tags = {
    Project = var.project_name
  }
}

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-vpc"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-igw"
  })
}

resource "aws_subnet" "frontend_public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.frontend_public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-frontend-public"
    Tier = "frontend"
  })
}

resource "aws_subnet" "backend_public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.backend_public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[1]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-backend-public"
    Tier = "backend"
  })
}

resource "aws_subnet" "database_private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_private_subnet_1_cidr
  availability_zone = data.aws_availability_zones.available.names[0]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-database-private-a"
    Tier = "database"
  })
}

resource "aws_subnet" "database_private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.database_private_subnet_2_cidr
  availability_zone = data.aws_availability_zones.available.names[1]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-database-private-b"
    Tier = "database"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-public-rt"
  })
}

resource "aws_route_table_association" "frontend_public" {
  subnet_id      = aws_subnet.frontend_public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "backend_public" {
  subnet_id      = aws_subnet.backend_public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_db_subnet_group" "main" {
  name = "${var.project_name}-db-subnets"
  subnet_ids = [
    aws_subnet.database_private_a.id,
    aws_subnet.database_private_b.id,
  ]

  tags = merge(local.common_tags, {
    Name = "${var.project_name}-db-subnet-group"
  })
}
