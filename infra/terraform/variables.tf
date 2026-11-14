variable "aws_region" {
  description = "Região AWS do laboratório. us-east-1 costuma ser a mais barata; dados são públicos."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Prefixo dos nomes dos recursos."
  type        = string
  default     = "painel-feminicidio-lab"
}

variable "github_repository" {
  description = "Repositório autorizado a assumir o papel, no formato dono/nome."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", var.github_repository))
    error_message = "Use o formato dono/nome, por exemplo pedrocorrea12/painel-feminicidio."
  }
}

variable "github_branches" {
  description = "Branches cujas execuções do GitHub Actions podem assumir o papel."
  type        = list(string)
  default     = ["develope"]

  validation {
    condition     = length(var.github_branches) > 0
    error_message = "Informe ao menos uma branch."
  }
}

variable "create_oidc_provider" {
  description = "Crie o provedor OIDC do GitHub. Use false se a conta já tiver um (só pode haver um por URL)."
  type        = bool
  default     = true
}

variable "budget_limit_usd" {
  description = "Teto mensal do orçamento, em dólares."
  type        = number
  default     = 5

  validation {
    condition     = var.budget_limit_usd > 0
    error_message = "O orçamento deve ser positivo."
  }
}

variable "alert_email" {
  description = "E-mail que recebe os alertas de orçamento."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.alert_email))
    error_message = "Informe um e-mail válido."
  }
}

variable "log_retention_days" {
  description = "Retenção do grupo de logs, em dias (valores aceitos pelo CloudWatch)."
  type        = number
  default     = 14

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90], var.log_retention_days)
    error_message = "Use um valor aceito pelo CloudWatch: 1, 3, 5, 7, 14, 30, 60 ou 90."
  }
}

variable "noncurrent_version_days" {
  description = "Dias até expirar versões antigas dos objetos no S3."
  type        = number
  default     = 30
}
