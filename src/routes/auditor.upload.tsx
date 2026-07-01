import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageHeader } from "@/components/app-shell";
import { Upload, Lock } from "lucide-react";

export const Route = createFileRoute("/auditor/upload")({ component: UploadPage });

const categories = ["فاتورة", "كشف حساب بنكي", "عقد", "تقرير جرد", "تقرير محاسبي مشفر", "أخرى"];

function UploadPage() {
  const [over, setOver] = useState(false);
  const [files, setFiles] = useState<string[]>([]);
  return (
    <div>
      <PageHeader
        title="رفع مستند جديد"
        subtitle="الملفات تُشفّر فوراً بصيغة AES-256 ولا تُحفظ بدون تشفير."
      />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setOver(true);
            }}
            onDragLeave={() => setOver(false)}
            onDrop={(e) => {
              e.preventDefault();
              setOver(false);
              const names = Array.from(e.dataTransfer.files).map((f) => f.name);
              setFiles((p) => [...p, ...names]);
            }}
            className={`p-12 rounded-xl border-2 border-dashed text-center transition ${over ? "border-primary bg-primary/5" : "border-border bg-card"}`}
          >
            <Upload className="w-10 h-10 mx-auto text-primary mb-4" />
            <div className="font-bold text-lg mb-2">اسحب الملفات هنا أو اضغط للاختيار</div>
            <div className="text-xs text-muted-foreground">
              يدعم: xlsx, csv, docx, pdf, jpg, png, tiff, json — أقصى حجم 50MB
            </div>
            <div className="mt-4 inline-flex items-center gap-1 text-xs text-success">
              <Lock className="w-3 h-3" /> تشفير AES-256 لحظي
            </div>
          </div>

          {files.length > 0 && (
            <div className="mt-6 space-y-2">
              {files.map((f, i) => (
                <div
                  key={i}
                  className="p-3 rounded-md bg-card border border-border flex items-center justify-between"
                >
                  <span className="text-sm" dir="ltr">
                    {f}
                  </span>
                  <span className="text-xs text-success">مشفّر · بانتظار التصنيف</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-6 rounded-xl bg-card border border-border">
          <h3 className="font-bold mb-4">التصنيف الافتراضي</h3>
          <div className="space-y-2">
            {categories.map((c) => (
              <label
                key={c}
                className="flex items-center gap-2 p-2 rounded-md hover:bg-secondary cursor-pointer"
              >
                <input type="radio" name="cat" className="accent-primary" />
                <span className="text-sm">{c}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
