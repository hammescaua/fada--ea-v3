// Explicações em linguagem do agricultor. Cada indicador do FADA responde às
// quatro perguntas que dão confiança: o que é, de onde vem, por que importa e
// o que fazer com isso. Nada aparece na tela sem ter uma entrada aqui.

export interface Explanation {
  titulo: string;
  o_que_e: string;
  de_onde_vem: string;
  por_que_importa: string;
  o_que_fazer: string;
}

export const EXPLANATIONS: Record<string, Explanation> = {
  potencial: {
    titulo: "Potencial produtivo",
    o_que_e:
      "Quanto sua lavoura pode produzir nesta safra, considerando tudo o que o FADA sabe até hoje sobre o talhão, o clima e o manejo.",
    de_onde_vem:
      "Parte do potencial genético da cultivar e desconta, um a um, os fatores do seu talhão: solo, água por estádio, nutrição, população, janela de plantio e sanidade.",
    por_que_importa:
      "É o número que muda ao longo da safra. Quanto melhores os dados, mais preciso ele fica — e mais cedo você enxerga uma quebra antes que ela aconteça.",
    o_que_fazer:
      "Se estiver abaixo do esperado, abra o Talhão: o diagnóstico mostra qual fator está puxando para baixo e o que dá para recuperar.",
  },
  situacao: {
    titulo: "Situação da safra",
    o_que_e:
      "Um resumo em três cores de como a safra está: verde (boa), amarelo (requer atenção) e vermelho (problema grave).",
    de_onde_vem:
      "Vem do radar da safra, que cruza o estádio atual da cultura com os fatores de maior risco no momento.",
    por_que_importa:
      "Diz, num relance, se você pode ficar tranquilo hoje ou se algo pede ação — sem precisar ler número nenhum.",
    o_que_fazer:
      "Amarelo ou vermelho: veja as decisões de hoje logo abaixo. Elas já vêm ordenadas pelo que rende mais.",
  },
  lucro: {
    titulo: "Lucro estimado por hectare",
    o_que_e:
      "O que deve sobrar por hectare nesta safra: receita esperada menos todos os custos que você informou.",
    de_onde_vem:
      "Receita = produtividade esperada × preço da soca. Custos = sementes, fertilizantes, defensivos, operações e o mais que estiver no plano.",
    por_que_importa:
      "Traduz a agronomia em dinheiro. Toda recomendação do FADA é medida pelo quanto muda esse número.",
    o_que_fazer:
      "Quer testar o efeito de uma mudança no bolso antes de ir a campo? Use a aba Testar cenários.",
  },
  confianca: {
    titulo: "Confiança / precisão dos dados",
    o_que_e:
      "O quanto o FADA confia na própria previsão, dado o que você já informou sobre o talhão.",
    de_onde_vem:
      "Cada variável tem uma qualidade (dado real do talhão vale mais que média regional). A confiança é a soma ponderada dessas qualidades.",
    por_que_importa:
      "Um número honesto sobre a própria incerteza. Confiança baixa não é erro — é um convite para informar o que falta.",
    o_que_fazer:
      "Veja 'o que falta informar': cada item que você preenche (análise de solo, monitoramento) aumenta a precisão.",
  },
  decisao: {
    titulo: "Decisões de hoje",
    o_que_e:
      "As ações que valem a pena tomar agora, ordenadas pela urgência (impacto × prazo × probabilidade de dar certo).",
    de_onde_vem:
      "Saem da fila de decisões: o FADA simula cada manejo possível e mantém só os que aumentam seu lucro dentro da janela certa.",
    por_que_importa:
      "Em vez de olhar quinze gráficos, você vê no máximo as duas coisas que mais mudam sua safra hoje.",
    o_que_fazer:
      "Toque em 'Entender recomendação' para ver, no Talhão, por que ela foi calculada e de onde vêm os números.",
  },
  digitalizacao: {
    titulo: "Nível de digitalização",
    o_que_e:
      "O quanto da sua propriedade o FADA já conhece — de localização e cultivar até solo, rotação e manejos registrados.",
    de_onde_vem:
      "Conta, sem inventar nada, quais informações reais você já forneceu sobre o talhão.",
    por_que_importa:
      "Cada dado real que entra deixa a previsão menos genérica e mais sua. Não é obrigação — é o que separa uma média regional da sua lavoura.",
    o_que_fazer:
      "Informe o próximo item da lista quando puder. Dois minutos hoje viram uma decisão melhor amanhã.",
  },
};
