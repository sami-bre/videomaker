import { useState } from "react";
import { Field, NumberField, TextField, topHint } from "./fields";
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
    <div className="editor">
      <h3>Story</h3>
      <TextField label="Title" value={storyboard.title} onChange={(v) => set("title", v)} />
      <TextField label="Logline" rows={2} value={storyboard.logline} onChange={(v) => set("logline", v)} />
      <TextField label="Narration language" help={topHint(schema, "narration_language")} value={storyboard.narration_language} onChange={(v) => set("narration_language", v)} />
      <TextField label="Notes for the translator" help={topHint(schema, "translation_notes")} rows={3} value={storyboard.translation_notes} onChange={(v) => set("translation_notes", v)} />

      <h3>Look</h3>
      <TextField label="Style" help={topHint(schema, "style")} rows={4} value={storyboard.style} onChange={(v) => set("style", v)} />
      <TextField label="Motion style" help={topHint(schema, "motion_style")} rows={2} value={storyboard.motion_style} onChange={(v) => set("motion_style", v)} />
      <Field label="Video engine" help={topHint(schema, "video_engine")}>
        <select value={storyboard.video_engine ?? "wan"} onChange={(e) => set("video_engine", e.target.value as "wan" | "grok")}>
          <option value="grok">Grok Imagine (OpenRouter), 1–15 s clips</option>
          <option value="wan">Wan 2.2 (WaveSpeed), 5 or 8 s clips</option>
        </select>
      </Field>

      <h3>Characters</h3>
      {Object.entries(characters).map(([id, c]) => (
        <div key={id} className="card">
          <div className="row">
            {outputs?.references[id] && <img className="thumb" src={outputs.references[id]!} alt={id} />}
            <b>{id}</b>
            <button className="ghost" onClick={() => { const { [id]: _, ...rest } = characters; set("characters", rest); }}>Remove</button>
          </div>
          <TextField label="Looks" rows={3} value={c.description} onChange={(v) => set("characters", { ...characters, [id]: { ...c, description: v } })} />
          <NumberField label="Seed" value={c.seed} onChange={(v) => set("characters", { ...characters, [id]: { ...c, seed: v } })} />
        </div>
      ))}
      <AddById label="character" taken={Object.keys(characters)} onAdd={(id) => set("characters", { ...characters, [id]: { description: "" } })} />

      <h3>Voices</h3>
      <p className="small muted">One voice per speaker. Voice names are Gemini TTS voices, e.g. Algenib, Puck, Kore.</p>
      {Object.entries(voices).map(([id, v]) => (
        <div key={id} className="card">
          <div className="row">
            <b>{id}</b>
            <button className="ghost" onClick={() => { const { [id]: _, ...rest } = voices; set("voices", rest); }}>Remove</button>
          </div>
          <TextField label="Voice" value={v.voice} onChange={(voice) => set("voices", { ...voices, [id]: { ...v, voice } })} />
          <TextField label="How they speak" rows={2} value={v.style} onChange={(style) => set("voices", { ...voices, [id]: { ...v, style } })} />
        </div>
      ))}
      <AddById label="speaker" taken={Object.keys(voices)} onAdd={(id) => set("voices", { ...voices, [id]: { voice: "Algenib" } })} />

      <h3>Music</h3>
      <TextField label="Music description" help={topHint(schema, "music")} rows={3} value={music.caption} onChange={(caption) => set("music", { ...music, caption })} />
      <TextField
        label="Seeds (one candidate each)"
        value={music.seeds.join(", ")}
        onChange={(v) => set("music", { ...music, seeds: v.split(",").map((s) => parseInt(s.trim(), 10)).filter((n) => !Number.isNaN(n)) })}
      />

      <h3>End card</h3>
      <TextField label="Title" value={storyboard.end_card?.title} onChange={(title) => set("end_card", { ...storyboard.end_card, title })} />
      <TextField label="Made by" help="Shown above the model credits." value={storyboard.end_card?.made_by} onChange={(made_by) => set("end_card", { ...storyboard.end_card, made_by: made_by || undefined })} />
    </div>
  );
}

function AddById({ label, taken, onAdd }: { label: string; taken: string[]; onAdd: (id: string) => void }) {
  const [id, setId] = useState("");
  const valid = ID_PATTERN.test(id) && !taken.includes(id);
  return (
    <div className="row">
      <input placeholder={`new ${label} id, e.g. grandma`} value={id} onChange={(e) => setId(e.target.value.toLowerCase())} />
      <button className="ghost" disabled={!valid} onClick={() => { onAdd(id); setId(""); }}>+ Add {label}</button>
    </div>
  );
}
