# Especificação 03 — Atributos e pré-processamento

## Separação
- Identificadores: `recommendationid`, `steamid`, `appid` e chaves técnicas.
- Treino: atributos explicitamente selecionados na configuração.
- Avaliação/consulta: atributos reservados para interpretação, sem entrar no treino salvo autorização explícita.

## Atributos candidatos
`num_reviews`, `playtime_forever`, `playtime_last_two_weeks`, `playtime_at_review`, `last_played`, `votes_up`, `votes_funny`, `weighted_vote_score`, `comment_count`, `voted_up` e outros campos estruturados aprovados.

## Transformações possíveis
Imputação, escalonamento, transformação log/power, encoding, remoção de baixa variância, filtragem por correlação, detecção de outliers e redução dimensional.

Cada transformação deve ser selecionada e parametrizada por YAML, com validação de tipo e catálogo seguro de operações. Não executar expressões Python arbitrárias.
