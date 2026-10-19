# Comando para disparar ciclo

No painel de chat do Antigravity, execute:

```text
/startcycle
```

Ou, para uso manual em instalações sem invocação direta de Skills:

```text
Leia AGENTS.md, .agents/agents.md, todas as regras pertinentes em .agents/rules e rules/, specs e config/entradas.yaml. Atue como orquestrador e execute o ciclo @pm -> @arquiteto -> gate de aprovação humana -> @coleta -> @datalake -> @nlp -> @clusterizacao -> @tendencias -> @mlflow -> @api -> @observabilidade -> @qa -> @devops. Produza handoffs em production_artifacts, aplique gates de qualidade e não ultrapasse o gate humano. Não crie um segundo Docker Compose, não escreva dados coletados localmente, não invente resultados, e use app/ para o código.
```

Para executar uma fase isolada, use `/fase-coleta`, `/fase-nlp`, `/fase-qa` etc., se a instalação tiver indexado as Skills.
