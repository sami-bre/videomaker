import { NumberField, Field, TextField, shotHint } from "./fields";
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
  const vertical = shot.vertical ?? { mode: "crop", focus: 0.5 };

  return (
    <div className="editor">
      <div className="preview">
        {outputs?.clip ? (
          <video key={outputs.clip} src={outputs.clip} poster={outputs.keyframe ?? undefined} controls muted loop playsInline />
        ) : outputs?.keyframe ? (
          <img src={outputs.keyframe} alt="" />
        ) : (
          <div className="empty">No picture yet. Run Pictures.</div>
        )}
      </div>

      <h3>Lines</h3>
      {shot.lines.map((line, i) => (
        <div key={i} className="line-editor">
          <div className="row">
            <select value={line.speaker} onChange={(e) => setLine(i, { ...line, speaker: e.target.value })}>
              {[...new Set([line.speaker, ...speakers])].map((s) => <option key={s}>{s}</option>)}
            </select>
            {outputs?.lines[i] && <audio src={outputs.lines[i]!} controls preload="none" />}
            <button className="ghost" onClick={() => set("lines", shot.lines.filter((_, j) => j !== i))}>Remove</button>
          </div>
          <TextField label="English (subtitle and translation source)" rows={2} value={line.en} onChange={(en) => setLine(i, { ...line, en })} />
          <TextField
            label={`Spoken (${storyboard.narration_language})`}
            help={line.spoken && line.spoken_from_en !== line.en ? "The English changed, so Translate will redo this line." : "Edit by hand to fix a word; your edit is kept."}
            rows={2}
            lang={storyboard.narration_language}
            value={line.spoken}
            onChange={(spoken) => setLine(i, { ...line, spoken: spoken || undefined } as Line)}
          />
        </div>
      ))}
      <button className="ghost" onClick={() => set("lines", [...shot.lines, { speaker: speakers[0] ?? "narrator", en: "" }])}>+ Add line</button>

      <h3>Picture</h3>
      <TextField label="What the viewer sees" help={shotHint(schema, "description")} rows={2} value={shot.description} onChange={(v) => set("description", v)} />
      <TextField label="Why this shot exists" help={shotHint(schema, "reason")} value={shot.reason} onChange={(v) => set("reason", v)} />
      <TextField label="Image prompt" help={shotHint(schema, "image_prompt")} rows={4} value={shot.image_prompt} onChange={(v) => set("image_prompt", v || undefined)} />
      <Field label="Characters in this shot" help={shotHint(schema, "characters")}>
        <div className="chips">
          {characters.map((c) => (
            <label key={c} className="check">
              <input
                type="checkbox"
                checked={shot.characters?.includes(c) ?? false}
                onChange={(e) => {
                  const next = e.target.checked ? [...(shot.characters ?? []), c] : (shot.characters ?? []).filter((x) => x !== c);
                  set("characters", next.length ? next : undefined);
                }}
              />
              {c}
            </label>
          ))}
        </div>
      </Field>
      <NumberField label="Picture seed" help="Change it to get a different take of the same prompt." value={shot.seed} onChange={(v) => set("seed", v)} />

      <h3>Motion</h3>
      <TextField label="Motion prompt" help={shotHint(schema, "motion_prompt")} rows={3} value={shot.motion_prompt} onChange={(v) => set("motion_prompt", v || undefined)} />
      <div className="row">
        <NumberField label="Clip length (s)" help={shotHint(schema, "clip_s")} value={shot.clip_s} onChange={(v) => set("clip_s", v)} />
        <NumberField label="Planned length (s)" help={shotHint(schema, "duration_s")} value={shot.duration_s} step={0.5} onChange={(v) => set("duration_s", v ?? 1)} />
      </div>
      <Field label="9:16 framing" help={shotHint(schema, "vertical")}>
        <div className="row">
          <select value={vertical.mode} onChange={(e) => set("vertical", e.target.value === "fit" ? { mode: "fit" } : { mode: "crop", focus: 0.5 })}>
            <option value="crop">crop</option>
            <option value="fit">fit</option>
          </select>
          {vertical.mode === "crop" && (
            <input type="range" min={0} max={1} step={0.05} value={vertical.focus ?? 0.5}
              onChange={(e) => set("vertical", { mode: "crop", focus: Number(e.target.value) })} />
          )}
        </div>
      </Field>
    </div>
  );
}
