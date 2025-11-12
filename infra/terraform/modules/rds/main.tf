# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-keiba-db-subnet-group"
  subnet_ids = var.private_subnets

  tags = {
    Name = "${var.environment}-keiba-db-subnet-group"
  }
}

# Security Group
resource "aws_security_group" "rds" {
  name        = "${var.environment}-keiba-rds-sg"
  description = "Security group for RDS"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_groups
    description     = "PostgreSQL access from ECS tasks"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-keiba-rds-sg"
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  identifier     = "${var.environment}-keiba-db"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.environment == "production" ? "db.t3.medium" : "db.t3.micro"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted      = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  backup_retention_period = var.environment == "production" ? 7 : 1
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot       = var.environment != "production"
  final_snapshot_identifier = var.environment == "production" ? "${var.environment}-keiba-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}" : null

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = var.environment == "production"
  performance_insights_retention_period = var.environment == "production" ? 7 : null

  tags = {
    Name = "${var.environment}-keiba-db"
  }
}

