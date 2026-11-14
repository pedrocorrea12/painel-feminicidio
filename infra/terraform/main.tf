data "aws_caller_identity" "atual" {}

locals {
  nome_bucket = "${var.project}-${data.aws_caller_identity.atual.account_id}"

  assuntos_oidc = [
    for branch in var.github_branches :
    "repo:${var.github_repository}:ref:refs/heads/${branch}"
  ]
}

# ---------------------------------------------------------------------------
# S3: Gold publicada, manifestos de execução e cache da Bronze.
# Privado, versionado, criptografado, só por TLS. force_destroy permite remover o
# laboratório inteiro com `terraform destroy` (inclui versões antigas).
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "dados" {
  bucket        = local.nome_bucket
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "dados" {
  bucket                  = aws_s3_bucket.dados.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "dados" {
  bucket = aws_s3_bucket.dados.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_versioning" "dados" {
  bucket = aws_s3_bucket.dados.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "dados" {
  bucket = aws_s3_bucket.dados.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "dados" {
  bucket = aws_s3_bucket.dados.id

  rule {
    id     = "expirar-versoes-antigas"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.dados]
}

data "aws_iam_policy_document" "somente_tls" {
  statement {
    sid     = "NegarSemTLS"
    effect  = "Deny"
    actions = ["s3:*"]
    resources = [
      aws_s3_bucket.dados.arn,
      "${aws_s3_bucket.dados.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "dados" {
  bucket = aws_s3_bucket.dados.id
  policy = data.aws_iam_policy_document.somente_tls.json

  depends_on = [aws_s3_bucket_public_access_block.dados]
}

# ---------------------------------------------------------------------------
# Logs: retenção curta para limitar custo.
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "pipeline" {
  name              = "/${var.project}/pipeline"
  retention_in_days = var.log_retention_days
}

# ---------------------------------------------------------------------------
# Federação OIDC do GitHub: sem chave de acesso de longa duração.
# O papel só pode ser assumido por execuções do repositório e das branches listadas.
# ---------------------------------------------------------------------------

resource "aws_iam_openid_connect_provider" "github" {
  count = var.create_oidc_provider ? 1 : 0

  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_openid_connect_provider" "github_existente" {
  count = var.create_oidc_provider ? 0 : 1

  url = "https://token.actions.githubusercontent.com"

  lifecycle {
    postcondition {
      condition     = contains(self.client_id_list, "sts.amazonaws.com")
      error_message = "O provedor OIDC existente não aceita a audiência sts.amazonaws.com."
    }
  }
}

locals {
  arn_provedor_oidc = (
    var.create_oidc_provider
    ? aws_iam_openid_connect_provider.github[0].arn
    : data.aws_iam_openid_connect_provider.github_existente[0].arn
  )
}

data "aws_iam_policy_document" "confianca_github" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.arn_provedor_oidc]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:sub"
      values   = local.assuntos_oidc
    }
  }
}

resource "aws_iam_role" "github_pipeline" {
  name                 = "${var.project}-github-pipeline"
  assume_role_policy   = data.aws_iam_policy_document.confianca_github.json
  max_session_duration = 3600
}

data "aws_iam_policy_document" "permissoes_pipeline" {
  statement {
    sid       = "ListarBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.dados.arn]
  }

  statement {
    sid       = "LerEGravarObjetos"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject"]
    resources = ["${aws_s3_bucket.dados.arn}/*"]
  }

  statement {
    sid       = "EscreverLogs"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.pipeline.arn}:*"]
  }
}

resource "aws_iam_role_policy" "pipeline" {
  name   = "${var.project}-pipeline"
  role   = aws_iam_role.github_pipeline.id
  policy = data.aws_iam_policy_document.permissoes_pipeline.json
}

# ---------------------------------------------------------------------------
# Orçamento com alerta por e-mail.
# ---------------------------------------------------------------------------

resource "aws_budgets_budget" "mensal" {
  name         = "${var.project}-mensal"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = [50, 80, 100]

    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = [var.alert_email]
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
