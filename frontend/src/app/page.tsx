const PHASES = [
  { id: "0", title: "التأسيس", detail: "Monorepo + Docker + حواجز الجودة + CI", done: true },
  { id: "1", title: "قاعدة البيانات والمصادقة", detail: "Auth + RBAC + Audit Log", done: true },
  { id: "2", title: "نموذج البيانات الكامل", detail: "الجداول والقيود وآلة الحالات", done: false },
  { id: "4", title: "محرك القواعد", detail: "المنطق العلمي + Golden Tests", done: false },
];

export default function HomePage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-3xl flex-col justify-center gap-10 px-6 py-16">
      <header className="space-y-3">
        <p className="text-primary text-sm font-medium">FitFlow v2</p>
        <h1 className="text-3xl font-bold sm:text-4xl">المنصة الذكية للصحة والتأهيل الرياضي</h1>
        <p className="text-muted">
          أداة دعم قرار للأخصائيين — تجمع بين التأهيل من الإصابات، وإدارة الوزن، والتغذية الشخصية،
          والتحليل الفسيولوجي.
        </p>
      </header>

      <section aria-labelledby="roadmap-heading" className="space-y-4">
        <h2 id="roadmap-heading" className="text-lg font-semibold">
          حالة التنفيذ
        </h2>
        <ul className="divide-border border-border divide-y rounded-lg border">
          {PHASES.map((phase) => (
            <li key={phase.id} className="flex items-center gap-4 p-4">
              <span
                aria-hidden
                className={`flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                  phase.done ? "bg-primary text-white" : "border-border text-muted border"
                }`}
              >
                {phase.id}
              </span>
              <span className="min-w-0">
                <span className="block font-medium">{phase.title}</span>
                <span className="text-muted block text-sm">{phase.detail}</span>
              </span>
              <span className="text-muted ms-auto text-sm">{phase.done ? "مكتملة" : "قادمة"}</span>
            </li>
          ))}
        </ul>
      </section>

      <footer className="border-border text-muted rounded-lg border p-4 text-sm">
        <strong className="text-foreground font-semibold">تنبيه طبي:</strong> هذه المنصة أداة دعم
        قرار ولا تُغني عن استشارة الطبيب أو الأخصائي المختص.
      </footer>
    </main>
  );
}
