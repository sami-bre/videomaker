import { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Field, NumberField, Section, TextField, topHint } from "./fields";
import type { Outputs, Storyboard } from "./types";

type Props = { schema: object | null; storyboard: Storyboard; outputs: Outputs | null; onChange: (s: Storyboard) => void };

const ID_PATTERN = /^[a-z_]+$/;

export function FilmSettings({ schema, storyboard, outputs, onChange }: Props) {
  const set = <K extends keyof Storyboard>(key: K, value: Storyboard[K]) => {
    const next = { ...storyboard, [key]: value };
    if (value === undefined || value === "") delete next[key];
    onChange(next);
  };
  const characters = storyboard.characters ?? {};
  const voices = storyboard.voices ?? {};
  const music = storyboard.music ?? { caption: "", seeds: [1, 2, 3] };

  return (
    <div className="flex flex-col gap-8">
      <Section title="Story">
        <TextField label="Title" value={storyboard.title} onChange={(v) => set("title", v)} />
        <TextField label="Logline" rows={2} value={storyboard.logline} onChange={(v) => set("logline", v)} />
        <TextField label="Narration language" help={topHint(schema, "narration_language")} value={storyboard.narration_language} onChange={(v) => set("narration_language", v)} className="max-w-48" />
        <TextField label="Notes for the translator" help={topHint(schema, "translation_notes")} rows={3} value={storyboard.translation_notes} onChange={(v) => set("translation_notes", v)} />
      </Section>

      <Separator />

      <Section title="Look">
        <TextField label="Style" help={topHint(schema, "style")} rows={4} value={storyboard.style} onChange={(v) => set("style", v)} />
        <TextField label="Motion style" help={topHint(schema, "motion_style")} rows={2} value={storyboard.motion_style} onChange={(v) => set("motion_style", v)} />
        <Field label="Video engine" help={topHint(schema, "video_engine")}>
          <Select value={storyboard.video_engine ?? "wan"} onValueChange={(v) => set("video_engine", v as "wan" | "grok")}>
            <SelectTrigger className="w-full sm:w-96"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="grok">Grok Imagine (OpenRouter), 1–15 s clips</SelectItem>
              <SelectItem value="wan">Wan 2.2 (WaveSpeed), 5 or 8 s clips</SelectItem>
            </SelectContent>
          </Select>
        </Field>
      </Section>

      <Separator />

      <Section title="Characters">
        {Object.entries(characters).map(([id, c]) => (
          <div key={id} className="flex gap-4 rounded-lg border p-4">
            {outputs?.references[id] && <img className="size-20 shrink-0 rounded-md border object-cover" src={outputs.references[id]!} alt={id} />}
            <div className="flex flex-1 flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="font-medium">{id}</span>
                <Button variant="ghost" size="icon" aria-label={`Remove ${id}`} onClick={() => { const { [id]: _, ...rest } = characters; set("characters", rest); }}>
                  <Trash2 />
                </Button>
              </div>
              <TextField label="Looks" rows={3} value={c.description} onChange={(v) => set("characters", { ...characters, [id]: { ...c, description: v } })} />
              <NumberField label="Seed" value={c.seed} onChange={(v) => set("characters", { ...characters, [id]: { ...c, seed: v } })} className="max-w-40" />
            </div>
          </div>
        ))}
        <AddById label="character" example="grandma" taken={Object.keys(characters)} onAdd={(id) => set("characters", { ...characters, [id]: { description: "" } })} />
      </Section>

      <Separator />

      <Section title="Voices">
        <p className="text-sm text-muted-foreground">One voice per speaker. Voice names are Gemini TTS voices, e.g. Algenib, Puck, Kore.</p>
        {Object.entries(voices).map(([id, v]) => (
          <div key={id} className="flex flex-col gap-3 rounded-lg border p-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">{id}</span>
              <Button variant="ghost" size="icon" aria-label={`Remove ${id}`} onClick={() => { const { [id]: _, ...rest } = voices; set("voices", rest); }}>
                <Trash2 />
              </Button>
            </div>
            <div className="grid gap-3 sm:grid-cols-[12rem_1fr]">
              <TextField label="Voice" value={v.voice} onChange={(voice) => set("voices", { ...voices, [id]: { ...v, voice } })} />
              <TextField label="How they speak" value={v.style} onChange={(style) => set("voices", { ...voices, [id]: { ...v, style } })} />
            </div>
          </div>
        ))}
        <AddById label="speaker" example="teacher" taken={Object.keys(voices)} onAdd={(id) => set("voices", { ...voices, [id]: { voice: "Algenib" } })} />
      </Section>

      <Separator />

      <Section title="Music">
        <TextField label="Music description" help={topHint(schema, "music")} rows={3} value={music.caption} onChange={(caption) => set("music", { ...music, caption })} />
        <TextField
          label="Seeds (one candidate each)"
          value={music.seeds.join(", ")}
          onChange={(v) => set("music", { ...music, seeds: v.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !Number.isNaN(n)) })}
          className="max-w-64"
        />
      </Section>

      <Separator />

      <Section title="End card">
        <div className="grid gap-4 sm:grid-cols-2">
          <TextField label="Title" value={storyboard.end_card?.title} onChange={(title) => set("end_card", { ...storyboard.end_card, title })} />
          <TextField label="Made by" help="Shown above the model credits." value={storyboard.end_card?.made_by} onChange={(made_by) => set("end_card", { ...storyboard.end_card, made_by: made_by || undefined })} />
        </div>
      </Section>
    </div>
  );
}

function AddById({ label, example, taken, onAdd }: { label: string; example: string; taken: string[]; onAdd: (id: string) => void }) {
  const [id, setId] = useState("");
  const valid = ID_PATTERN.test(id) && !taken.includes(id);
  return (
    <div className="flex gap-2">
      <Input placeholder={`New ${label} id, e.g. ${example}`} value={id} onChange={(e) => setId(e.target.value.toLowerCase())} className="max-w-64" />
      <Button variant="outline" disabled={!valid} onClick={() => { onAdd(id); setId(""); }}>
        <Plus /> Add {label}
      </Button>
    </div>
  );
}
