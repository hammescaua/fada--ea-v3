# Base de Conhecimento — de onde vêm os números

Pergunta central: *"como a ferramenta sabe o impacto de cada variável e o preço de
cada insumo?"*. Resposta: de uma **base de conhecimento auditável e com fonte**, não de
números mágicos no código.

## Onde fica

`data/knowledge/` (JSON versionado, com fonte citada em cada coeficiente):

| Arquivo | Conteúdo | Fontes |
|--------|----------|--------|
| `agronomic_responses.json` | coeficientes de resposta da soja (pressões de doença/praga/daninha, eficiência de controle, limiares de suficiência, método/alvo de calagem, doses de construção P/K, penalidade de janela, estresse hídrico/térmico, anos de residual) | **Embrapa Soja**, **CQFS-RS/SC 2016**, **FAO-56**, **ZARC/MAPA** |
| `inputs_catalog.json` | insumos: composição (N-P₂O₅-K₂O, PRNT) e **preço de referência** com data/fonte | mercado BR nov/2025 (farmnews/Scot/ABRACAL), **CONAB/CEPEA** para soja |

O motor lê esses arquivos via `agro_engine/kb.py`. O `reference.py` é sincronizado a
partir da KB no carregamento (os literais no código são apenas fallback). Assim os
coeficientes são **atualizáveis sem mexer no código** e cada número é rastreável à fonte
(`kb.source("calagem.v_alvo_soja")` devolve a citação).

## Como o impacto de cada manejo é calculado

Não é uma tabela fixa de "fungicida = +X sc". O impacto é **derivado do modelo**:

1. Os coeficientes da KB (ex.: pressão de ferrugem 0,18; eficiência do fungicida 0,55)
   alimentam os fatores do **IPPD** (decomposição transparente da produtividade).
2. Para medir "quanto um manejo representa", o motor **re-simula o talhão com e sem
   aquele manejo** e mede a diferença (`operations_impact`). O número sai do mesmo modelo
   que gera a produtividade — é coerente e auditável, não um chute.
3. Conforme o agricultor registra safras reais, o **Knowledge Engine** ajusta a correção
   por talhão — os coeficientes de literatura viram o ponto de partida, não a verdade final.

## Fertilidade: dose, preço, impacto e alternativa mais rentável

`fertility.py` responde "vale a pena calcário/adubar no MEU solo?":

- **Dose** pela fórmula oficial — calagem por **saturação por bases** (CQFS-RS/SC):
  `NC = (V_alvo − V) × CTC / 100`, ajustada pelo PRNT do calcário; P e K por
  construção + manutenção.
- **Investimento** = dose × preço do insumo (catálogo), **amortizado pelo efeito
  residual** (calagem ~4 anos, P ~2, K ~1) para comparar com o ganho de uma safra.
- **Impacto** = re-simulação do talhão com o solo corrigido (mesmo IPPD).
- **Ranking por rentabilidade** = responde "qual investimento é melhor para o meu solo"
  (ex.: num solo ácido, a calagem costuma liderar — base da fertilidade, melhor R$/resposta).

## Honestidade

Os preços são **referência** e devem ser substituídos pelo preço real negociado pelo
agricultor (próximo passo de UI: editor de custos). Os coeficientes são conservadores e
de literatura — explicitamente o ponto de partida que a IA por talhão refina com dados
reais. Nada aqui promete exatidão; o objetivo é **reduzir a incerteza com transparência**.
