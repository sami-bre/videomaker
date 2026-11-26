import type { ReactNode } from "react";

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

type FieldProps = { label: string; help?: string; children: ReactNode };

export function Field({ label, help, children }: FieldProps) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {help && <small className="muted">{help}</small>}
    </label>
  );
}

type TextProps = { label: string; help?: string; value?: string; onChange: (value: string) => void; rows?: number; lang?: string };

export function TextField({ label, help, value, onChange, rows = 1, lang }: TextProps) {
  return (
    <Field label={label} help={help}>
      {rows > 1 ? (
        <textarea rows={rows} lang={lang} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <input lang={lang} value={value ?? ""} onChange={(e) => onChange(e.target.value)} />
      )}
    </Field>
  );
}

type NumberProps = { label: string; help?: string; value?: number; onChange: (value: number | undefined) => void; step?: number };

export function NumberField({ label, help, value, onChange, step = 1 }: NumberProps) {
  return (
    <Field label={label} help={help}>
      <input
        type="number"
        step={step}
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value === "" ? undefined : Number(e.target.value))}
      />
    </Field>
  );
}
