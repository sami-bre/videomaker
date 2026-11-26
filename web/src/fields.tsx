import { useId, type ReactNode } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

type Schema = Record<string, any>;

export function hint(schema: Schema | null, ...path: string[]): string | undefined {
  let node: any = schema;
  for (const key of path) node = node?.[key];
  return node?.description;
}

export function shotHint(schema: Schema | null, field: string) {
  return hint(schema, "$defs", "shot", "properties", field);
}

export function topHint(schema: Schema | null, field: string) {
  return hint(schema, "properties", field);
}

type FieldProps = { label: string; help?: string; htmlFor?: string; className?: string; children: ReactNode };

export function Field({ label, help, htmlFor, className, children }: FieldProps) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {help && <p className="text-xs text-muted-foreground">{help}</p>}
    </div>
  );
}

type TextProps = {
  label: string; help?: string; value?: string; onChange: (value: string) => void;
  rows?: number; lang?: string; className?: string; inputClassName?: string;
};

export function TextField({ label, help, value, onChange, rows = 1, lang, className, inputClassName }: TextProps) {
  const id = useId();
  return (
    <Field label={label} help={help} htmlFor={id} className={className}>
      {rows > 1 ? (
        <Textarea id={id} rows={rows} lang={lang} className={inputClassName} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <Input id={id} lang={lang} className={inputClassName} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
      )}
    </Field>
  );
}

type NumberProps = { label: string; help?: string; value?: number; onChange: (value: number | undefined) => void; step?: number; className?: string };

export function NumberField({ label, help, value, onChange, step = 1, className }: NumberProps) {
  const id = useId();
  return (
    <Field label={label} help={help} htmlFor={id} className={className}>
      <Input
        id={id}
        type="number"
        step={step}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
      />
    </Field>
  );
}

export function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase">{title}</h3>
      {children}
    </section>
  );
}
