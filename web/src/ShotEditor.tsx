import { ImageOff, Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Field, NumberField, Section, TextField, shotHint } from "./fields";
import type { Line, Shot, ShotOutputs, Storyboard } from "./types";

type Props = {
  schema: object | null;
  storyboard: Storyboard;
  shot: Shot;
  outputs?: ShotOutputs;
  onChange: (shot: Shot) => void;
};

export function ShotEditor({ schema, storyboard, shot, outputs, onChange }: Props) {
  const set = <K extends keyof Shot>(key: K, value: Shot[K]) => {
    const next = { ...shot, [key]: value };
    if (value === undefined) delete next[key];
    onChange(next);
  };
  const setLine = (index: number, line: Line) => set("lines", shot.lines.map((l, i) => (i === index ? line : l)));
  const speakers = Object.keys(storyboard.voices ?? {});
  const characters = Object.keys(storyboard.characters ?? {});
  const vertical = shot.vertical ?? { mode: "crop" as const, focus: 0.5 };

  return (
    <div className="flex flex-col gap-8">
      <div className="overflow-hidden rounded-lg border bg-muted">
        {outputs?.clip ? (
          <video key={outputs.clip} src={outputs.clip} poster={outputs.keyframe ?? undefined} controls muted loop playsInline className="aspect-video w-full" />
        ) : outputs?.keyframe ? (
          <img src={outputs.keyframe} alt="" className="aspect-video w-full object-cover" />
        ) : (
          <div className="flex aspect-video flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
            <ImageOff className="size-6" /> No picture yet. Run Pictures.
          </div>
        )}
      </div>

      <Section title="Lines">
        {shot.lines.length === 0 && <p className="text-sm text-muted-foreground">A silent shot. Add a line to give it narration.</p>}
        {shot.lines.map((line, i) => (
          <div key={i} className="flex flex-col gap-3 rounded-lg border p-4">
            <div className="flex flex-wrap items-center gap-2">
              <Select value={line.speaker} onValueChange={(speaker) => setLine(i, { ...line, speaker })}>
                <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {[...new Set([line.speaker, ...speakers])].map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
                </SelectContent>
              </Select>
              {outputs?.lines[i] && <audio src={outputs.lines[i]!} controls preload="none" className="h-8 min-w-0 flex-1" />}
              <Button variant="ghost" size="icon" className="ml-auto" aria-label="Remove line" onClick={() => set("lines", shot.lines.filter((_, j) => j !== i))}>
                <Trash2 />
              </Button>
            </div>
            <TextField label="English" help="Used for subtitles and as the translation source." rows={2} value={line.en} onChange={(en) => setLine(i, { ...line, en })} />
            <TextField
              label={`Spoken (${storyboard.narration_language})`}
              help={line.spoken && line.spoken_from_en !== line.en ? "The English changed, so Translate will redo this line." : "Edit by hand to fix a word. Your edit is kept."}
              rows={2}
              lang={storyboard.narration_language}
              inputClassName="font-ethiopic"
              value={line.spoken}
              onChange={(spoken) => setLine(i, { ...line, spoken: spoken || undefined } as Line)}
            />
          </div>
        ))}
        <Button variant="outline" className="self-start" onClick={() => set("lines", [...shot.lines, { speaker: speakers[0] ?? "narrator", en: "" }])}>
          <Plus /> Add line
        </Button>
      </Section>

      <Separator />

      <Section title="Picture">
        <TextField label="What the viewer sees" help={shotHint(schema, "description")} rows={2} value={shot.description} onChange={(v) => set("description", v)} />
        <TextField label="Why this shot exists" help={shotHint(schema, "reason")} value={shot.reason} onChange={(v) => set("reason", v)} />
        <TextField label="Image prompt" help={shotHint(schema, "image_prompt")} rows={4} value={shot.image_prompt} onChange={(v) => set("image_prompt", v || undefined)} />
        <Field label="Characters in this shot" help={shotHint(schema, "characters")}>
          <div className="flex flex-wrap gap-4">
            {characters.map((c) => (
              <div key={c} className="flex items-center gap-2">
                <Checkbox
                  id={`char-${c}`}
                  checked={shot.characters?.includes(c) ?? false}
                  onCheckedChange={(checked) => {
                    const next = checked === true ? [...(shot.characters ?? []), c] : (shot.characters ?? []).filter((x) => x !== c);
                    set("characters", next.length ? next : undefined);
                  }}
                />
                <Label htmlFor={`char-${c}`} className="font-normal">{c}</Label>
              </div>
            ))}
          </div>
        </Field>
        <NumberField label="Picture seed" help="Change it to get a different take of the same prompt." value={shot.seed} onChange={(v) => set("seed", v)} className="max-w-48" />
      </Section>

      <Separator />

      <Section title="Motion">
        <TextField label="Motion prompt" help={shotHint(schema, "motion_prompt")} rows={3} value={shot.motion_prompt} onChange={(v) => set("motion_prompt", v || undefined)} />
        <div className="grid gap-4 sm:grid-cols-2">
          <NumberField label="Clip length (s)" help={shotHint(schema, "clip_s")} value={shot.clip_s} onChange={(v) => set("clip_s", v)} />
          <NumberField label="Planned length (s)" help={shotHint(schema, "duration_s")} value={shot.duration_s} step={0.5} onChange={(v) => set("duration_s", v ?? 1)} />
        </div>
        <Field label="9:16 framing" help={shotHint(schema, "vertical")}>
          <div className="flex flex-wrap items-center gap-4">
            <Select value={vertical.mode} onValueChange={(mode) => set("vertical", mode === "fit" ? { mode: "fit" } : { mode: "crop", focus: 0.5 })}>
              <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="crop">Crop</SelectItem>
                <SelectItem value="fit">Fit</SelectItem>
              </SelectContent>
            </Select>
            {vertical.mode === "crop" && (
              <div className="flex min-w-48 flex-1 items-center gap-3 text-xs text-muted-foreground">
                Left
                <Slider min={0} max={1} step={0.05} value={[vertical.focus ?? 0.5]} onValueChange={([focus]) => set("vertical", { mode: "crop", focus })} />
                Right
              </div>
            )}
          </div>
        </Field>
      </Section>
    </div>
  );
}
