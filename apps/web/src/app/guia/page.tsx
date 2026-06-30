import Link from "next/link";

export const metadata = { title: "Como funciona — FADA" };

function Capability({ icon, title, oque, ajuda, usar }: { icon: string; title: string; oque: string; ajuda: string; usar: string }) {
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <h3 className="mb-1 text-base font-bold text-leafdark">{icon} {title}</h3>
      <p className="text-sm text-stone-700">{oque}</p>
      <p className="mt-1.5 text-sm text-stone-600"><span className="font-medium text-leafdark">Como ajuda:</span> {ajuda}</p>
      <p className="mt-1 text-xs text-stone-500"><span className="font-medium">Como usar:</span> {usar}</p>
    </div>
  );
}

function Term({ t, d }: { t: string; d: string }) {
  return (
    <div className="border-b border-stone-100 py-1.5">
      <span className="text-sm font-semibold text-stone-700">{t}</span>
      <span className="text-sm text-stone-600"> — {d}</span>
    </div>
  );
}

export default function Guia() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-8">
      <header className="mb-6">
        <Link href="/" className="text-sm text-leafdark hover:underline">← voltar para a plataforma</Link>
        <h1 className="mt-2 text-3xl font-bold text-leafdark">🌱 Como o FADA ajuda na sua safra</h1>
        <p className="mt-2 text-stone-600">
          O FADA é um <strong>gêmeo digital do seu talhão</strong>: ele recria a sua lavoura no computador,
          simula a safra e te ajuda a decidir — sempre <strong>explicando o porquê de cada número</strong> e de
          onde ele vem. Não é um chute nem uma média da região: é personalizado para o <em>seu</em> talhão e
          fica mais preciso a cada safra.
        </p>
      </header>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-bold text-stone-700">A ideia em 3 passos</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <div className="rounded-xl bg-leaf/5 p-4">
            <div className="text-2xl font-bold text-leaf">1</div>
            <p className="text-sm text-stone-700">Você informa o talhão (local, solo, cultivar, manejo). Quanto mais real o dado, mais certeira a previsão.</p>
          </div>
          <div className="rounded-xl bg-leaf/5 p-4">
            <div className="text-2xl font-bold text-leaf">2</div>
            <p className="text-sm text-stone-700">O FADA simula a safra com base na ciência (Embrapa, CQFS, ZARC, clima real) e mostra quanto você deve colher, ganhar e arriscar.</p>
          </div>
          <div className="rounded-xl bg-leaf/5 p-4">
            <div className="text-2xl font-bold text-leaf">3</div>
            <p className="text-sm text-stone-700">Durante a safra, você registra o que acontece (chuva, ferrugem, aplicação) e o gêmeo aprende — corrigindo as previsões do seu talhão.</p>
          </div>
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-bold text-stone-700">O que você encontra na plataforma</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Capability icon="🛰️" title="Radar da safra (comece por aqui)"
            oque="A primeira tela: a saúde da safra em 6 notas (Solo, Clima, Sanidade, Nutrição, Mercado, Execução) e as 4 respostas que importam — maior risco, melhor decisão, quanto vale e por quê. Ele respeita a FASE da safra: só recomenda o que dá para fazer agora (não sugere antecipar plantio se a lavoura já floresceu)."
            ajuda="Em 20 segundos você sabe onde está o problema e onde colocar o dinheiro primeiro, sem procurar em gráficos — e na hora certa do ciclo."
            usar="É o topo da aba Acompanhamento. Leia as 4 respostas e a tabela 'Onde investir primeiro' (ações com a janela já passada aparecem apagadas)." />
          <Capability icon="🔬" title="Diagnóstico — por que não colho mais?"
            oque="Pensa como um agrônomo: lista as causas prováveis do talhão estar abaixo do potencial, cada uma com a cadeia de impacto (causa → efeito → … → produtividade), a probabilidade e o que medir para confirmar."
            ajuda="Em vez de só dizer 'vai colher X', mostra ONDE está o problema e por quê — e marca o que é hipótese 'a confirmar' (dado de baixa confiança)."
            usar="Na aba Acompanhamento, abra cada hipótese para ver a cadeia de impacto e a ação que a corrige." />
          <Capability icon="📋" title="Resumo da safra"
            oque="A resposta única: quanto deve colher (com faixa), quanto ganha, qual o risco e qual a ação nº 1 agora."
            ajuda="Você entende a situação do talhão em 10 segundos, sem decifrar planilhas."
            usar="É a primeira coisa na aba Acompanhamento. Leia o veredito e as ações sugeridas." />
          <Capability icon="📅" title="Acompanhamento passo a passo"
            oque="Linha do tempo da safra — do preparo do solo à colheita — com os manejos de cada fase e o impacto de cada um em sacas e R$."
            ajuda="Sabe o que fazer em cada etapa e por quê, com a base científica de cada manejo."
            usar="Abra '📚 base científica' em cada manejo; use '＋ adicionar' para incluir um manejo e ver o impacto na hora." />
          <Capability icon="⚖️" title="Plano vs. Realidade"
            oque="Compara o que você planejou com o que de fato aconteceu (a partir das evidências) e ajusta o número."
            ajuda="Ex.: aplicou e choveu — o gêmeo reconhece a lavagem, reduz a eficácia e recomenda repasse, com fonte."
            usar="Registre evidências (chuva, ferrugem, estande) e clique em 'Comparar plano com a realidade'." />
          <Capability icon="🔀" title="E se… (cenários)"
            oque="Re-simula a safra mudando uma decisão por vez: 'e se eu não tivesse aplicado o fungicida? e se plantasse antes?'."
            ajuda="Mostra o quanto cada escolha pesou — para decidir com números, não no 'achismo'."
            usar="Na aba Acompanhamento, clique em 'Explorar cenários alternativos'." />
          <Capability icon="🎯" title="Melhor plano e Decisões"
            oque="O FADA testa centenas de combinações (data × população × fungicida) e ordena as intervenções por retorno."
            ajuda="Aponta a melhor data de plantio e as ações que mais aumentam o lucro, com a probabilidade de dar certo."
            usar="Na aba Laboratório: 'Encontrar o melhor plano' e o painel de Decisões." />
          <Capability icon="🌱" title="Fertilidade (solo)"
            oque="Calcula calagem e adubação pelo método oficial (CQFS), com dose, investimento e retorno para o SEU solo."
            ajuda="Responde 'vale a pena calar/adubar?' e qual insumo é mais rentável — não um pacote genérico."
            usar="Na aba Laboratório, painel de Fertilidade. Informe a análise de solo para mais precisão." />
          <Capability icon="🎲" title="Risco e clima (ENSO)"
            oque="Simula milhares de safras variando clima e preço, e mostra a chance de prejuízo. Você escolhe o outlook (El Niño/La Niña)."
            ajuda="No Noroeste do RS, La Niña é a maior causa de quebra — planeje o ano seco antes que ele chegue."
            usar="Na aba Laboratório, escolha o outlook climático e rode a análise de risco." />
          <Capability icon="🧬" title="Personalidade do talhão"
            oque="Traços que o gêmeo aprende da sua lavoura: responde ao fósforo, risco de ferrugem, estabilidade, propensão a lavagem…"
            ajuda="Depois de algumas safras, a ferramenta praticamente 'conhece' o seu talhão e ajusta as recomendações."
            usar="Selecione um talhão salvo e registre safras e colheitas para ele aprender." />
          <Capability icon="🎯" title="Precisão dos dados"
            oque="Mostra, variável por variável, de onde vem o dado, se é do seu talhão ou um default da região, e o que medir primeiro."
            ajuda="Você sabe o quanto confiar na estimativa e onde investir para deixá-la mais verídica."
            usar="Painel 'Precisão para este talhão'. Quanto mais dado real, maior a precisão (de ~37% a ~89%)." />
        </div>
      </section>

      <section className="mb-8">
        <h2 className="mb-3 text-lg font-bold text-stone-700">Glossário rápido</h2>
        <div className="rounded-xl border border-stone-200 bg-white p-4">
          <Term t="sc/ha" d="sacas de 60 kg por hectare — a unidade de produtividade." />
          <Term t="ROI" d="retorno sobre o investimento: quantas vezes o lucro cobre o custo (ROI 2x = lucro é o dobro do custo)." />
          <Term t="Break-even (ponto de equilíbrio)" d="a produtividade (ou o preço) mínima para não ter prejuízo." />
          <Term t="Faixa p10–p90" d="em 10 safras parecidas, o resultado fica entre esses dois valores na maioria das vezes; mede a incerteza do clima." />
          <Term t="ENSO (El Niño / La Niña)" d="fenômeno climático: La Niña tende a seca e quebra no Sul; El Niño, chuva acima da média." />
          <Term t="V% (saturação por bases)" d="indicador de fertilidade/acidez do solo; a soja gosta de ~65%, alcançado com calagem." />
          <Term t="Nematoides" d="vermes do solo (cisto, galha) que causam reboleiras e perda; manejados com rotação e cultivar resistente." />
          <Term t="IPPD (decomposição)" d="o 'porquê' da produtividade: cada fator (solo, água, ferrugem…) mostrado em + ou − sacas." />
        </div>
      </section>

      <div className="flex justify-center">
        <Link href="/" className="rounded-md bg-leaf px-5 py-2.5 text-sm font-semibold text-white hover:bg-leafdark">
          Começar a usar →
        </Link>
      </div>
    </main>
  );
}
