# Especificação 01 — Visão geral

## Objetivo
Agrupar avaliações/recomendações da Steam com aprendizado não supervisionado e oferecer análises compreensíveis para equipes técnicas e de negócio.

## Premissas
- PLN desativado por padrão.
- O texto da avaliação é consultável por humanos, mas não entra na matriz de treino por padrão.
- Coleta diária, com suporte a vários `appid`.
- A solução deve permitir trocar fonte, motor de processamento e algoritmo.
- Parâmetros e regras variáveis são configuráveis em YAML.

## Componentes
1. Coleta Steam API.
2. Persistência Bronze/Silver/Gold.
3. Validação e qualidade dos dados.
4. Engenharia e seleção de atributos.
5. Pré-processamento.
6. Treino e avaliação de clustering.
7. Tracking MLflow.
8. Análises de clusters.
9. API de consulta, se aprovada.
10. Observabilidade e dashboards.
