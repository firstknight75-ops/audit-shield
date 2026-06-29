<div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
    <div className="lg:col-span-1 p-8 rounded-xl bg-card border border-border flex flex-col items-center justify-center">
      <div className="relative w-44 h-44">
        <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
          <circle cx="50" cy="50" r="42" fill="none" stroke="oklch(0.32 0.03 250)" strokeWidth="10" />
          <circle
            cx="50" cy="50" r="42" fill="none"
            stroke={`oklch(var(--${meta.color}))`}
            strokeWidth="10"
            strokeDasharray={`${(data.score / 100) * 264} 264`}
            strokeLinecap="round"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-4xl font-bold font-display">{data.score}</div>
          <div className="text-xs text-muted-foreground">{t.score_label}</div>
        </div>
      </div>
      <div className={`inline-flex items-center gap-1 mt-3 px-3 py-1 rounded-full bg-${meta.color}/15 text-${meta.color} border ${meta.ring} text-sm font-bold`}>
        <ShieldCheck className="w-3 h-3" /> {meta.label}
      </div>
      {data.generatedAt && (
        <div className="text-xs text-muted-foreground mt-3 font-mono">
          {t.last_run}: {data.generatedAt}
        </div>
      )}
    </div>

    <div className="lg:col-span-2 grid grid-cols-2 gap-4">
      <Component label={t.coverage_label} value={`${data.coverage_pct}%`} sub={`${data.total_documents} ${locale === "ar" ? "مستند" : "بەڵگەنامە"}`} tone="primary" />
      <Component label={t.certified_label} value={`${data.certified_pct}%`} sub={`${data.certified_documents} / ${data.total_documents}`} tone="success" />
      <Component label={t.missing_label} value={`${data.missing_field_pct}%`} sub={`${data.missing_fields_total} ${locale === "ar" ? "حقل" : "خانە"}`} tone="warning" />
      <Component label={t.duplicate_label} value={`${data.duplicate_pct}%`} sub={`${data.duplicate_documents} ${locale === "ar" ? "مستند" : "بەڵگەنامە"}`} tone="danger" />
    </div>
  </div>

  <div className="p-6 rounded-2xl bg-card border border-border">
    <h3 className="font-bold mb-4">{t.trend_6}</h3>
    <div className="grid grid-cols-6 gap-3">
      {(data.trend ?? []).map((point, i) => (
        <div key={i} className="text-center">
          <div className="text-xs text-muted-foreground mb-1">{point.cycle}</div>
          <div className={`text-2xl font-bold font-display ${point.score >= 80 ? "text-success" : point.score >= 60 ? "text-warning" : "text-danger"}`}>
            {point.score}
          </div>
          <div className="h-2 rounded-full bg-secondary overflow-hidden mt-2">
            <div className={`h-full bg-${point.score >= 80 ? "success" : point.score >= 60 ? "warning" : "danger"}`} style={{ width: `${point.score}%` }} />
          </div>
        </div>
      ))}
    </div>
  </div>
</div>
