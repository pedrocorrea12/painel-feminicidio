output "bucket_dados" {
  description = "Nome do bucket S3 privado."
  value       = aws_s3_bucket.dados.bucket
}

output "papel_github_arn" {
  description = "ARN do papel que o workflow do GitHub deve assumir (role-to-assume). Nulo se a federação estiver desligada."
  value       = try(aws_iam_role.github_pipeline[0].arn, null)
}

output "grupo_de_logs" {
  description = "Grupo de logs do CloudWatch."
  value       = aws_cloudwatch_log_group.pipeline.name
}

output "regiao" {
  description = "Região usada."
  value       = var.aws_region
}
