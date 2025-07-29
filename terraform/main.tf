provider "aws" {
  region = "ap-south-1"
}

resource "aws_key_pair" "main" {
  key_name   = "mumbai"
  public_key = file("~/.ssh/id_rsa.pub") 
}

resource "aws_iam_role" "ec2_role" {
  name = "ec2-spot-embedding"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-spot-embedding"
  role = aws_iam_role.ec2_role.name
}

resource "aws_security_group" "main_sg" {
  name        = "mongo-emb-sg"
  description = "Allow SSH and custom ports"
  ingress = [
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
  egress = [
    {
      from_port   = 0
      to_port     = 0
      protocol    = "-1"
      cidr_blocks = ["0.0.0.0/0"]
    }
  ]
}

resource "aws_launch_template" "mongo_emb_lt" {
  name = "mongo-emb-lt"

  image_id      = "ami-xxxxxx" # Replace with valid Deep Learning AMI in ap-south-1
  instance_type = "g4dn.xlarge"

  key_name = aws_key_pair.main.key_name

  iam_instance_profile {
    name = aws_iam_instance_profile.ec2_profile.name
  }

  instance_market_options {
    market_type = "spot"
    spot_options {
      spot_instance_type            = "one-time"
      instance_interruption_behavior = "terminate"
    }
  }

  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      volume_size = 100
      volume_type = "gp3"
      delete_on_termination = false
    }
  }

  security_group_names = [aws_security_group.main_sg.name]

  user_data = base64encode(file("userdata.sh"))
}
