# Runbooks do pipeline

Este diretório receberá procedimentos executáveis e verificáveis para operação
do pipeline. Os primeiros runbooks deverão cobrir:

1. indisponibilidade ou limitação da fonte pública;
2. mudança inesperada de esquema;
3. reprocessamento de um período sem duplicação;
4. falha de validação antes da publicação Gold;
5. restauração da última versão válida do dashboard;
6. desligamento e remoção do laboratório AWS.

Cada procedimento deve registrar sintomas, diagnóstico, ação segura, validação
da recuperação e evidência que pode ser compartilhada sem dados sensíveis.
