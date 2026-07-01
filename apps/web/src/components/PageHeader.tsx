/** Título de página: dá identidade e ar a cada tela. Uma pergunta por página. */
export function PageHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="mb-2">
      <h1 className="text-2xl font-bold text-stone-800">{title}</h1>
      <p className="mt-0.5 text-stone-500">{subtitle}</p>
    </div>
  );
}
