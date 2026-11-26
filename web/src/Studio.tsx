import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { json } from "@codemirror/lang-json";
import Ajv2020 from "ajv/dist/2020";
import { api, ApiError, describeError } from "./api";
import { FilmSettings } from "./FilmSettings";
import { ShotEditor } from "./ShotEditor";
import type { Costs, Estimate, Outputs, RunEvent, RunSummary, Shot, StageName, Storyboard } from "./types";

type Step = { label: string; stages: StageName[]; quality: "draft" | "final"; help: string };

const STEPS: Step[] = [
  { label: "Translate", stages: ["script"], quality: "final", help: "English lines to the narration language" },
  { label: "Voice", stages: ["narration"], quality: "final", help: "One audio file per line" },
  { label: "Pictures", stages: ["keyframes"], quality: "final", help: "Character sheets, then one frame per shot" },
  { label: "Draft motion", stages: ["shots"], quality: "draft", help: "480p clips, to check motion cheaply" },
  { label: "Final motion", stages: ["shots"], quality: "final", help: "720p clips for the film" },
  { label: "Music", stages: ["music"], quality: "final", help: "One score candidate per seed" },
  { label: "Film", stages: ["film"], quality: "final", help: "Edit, mix, subtitles, end card, 9:16 + 16:9" },
];
const ALL_STAGES: StageName[] = ["script", "narration", "keyframes", "shots", "music", "film"];
const FINISHED = ["done", "failed", "cancelled"];

type Props = { projectId: string; keys: Record<string, string>; onNeedKeys: () => void };

export function Studio({ projectId, keys, onNeedKeys }: Props) {
  const [schema, setSchema] = useState<object | null>(null);
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [savedJson, setSavedJson] = useState("");
  const [outputs, setOutputs] = useState<Outputs | null>(null);
  const [estimates, setEstimates] = useState<{ final?: Estimate; draft?: Estimate }>({});
  const [costs, setCosts] = useState<Costs | null>(null);
  const [tab, setTab] = useState<"shot" | "film" | "json">("shot");
  const [selected, setSelected] = useState(0);
  const [messages, setMessages] = useState<string[]>([]);
  const [run, setRun] = useState<RunSummary | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [runError, setRunError] = useState<string | null>(null);
  const [rawJson, setRawJson] = useState("");
  const events = useRef<EventSource | null>(null);
  const logEnd = useRef<HTMLDivElement | null>(null);

  const validate = useMemo(() => (schema ? new Ajv2020({ allErrors: true, strict: false }).compile(schema) : null), [schema]);
  const dirty = storyboard !== null && JSON.stringify(storyboard) !== savedJson;
  const running = run !== null && !FINISHED.includes(run.status);
  const schemaErrors = useMemo(() => {
    if (!validate || !storyboard || validate(storyboard)) return [];
    return (validate.errors ?? []).map((e) => `${e.instancePath || "(top)"} ${e.message}`);
  }, [validate, storyboard]);

  const refresh = useCallback(async () => {
    const board = await api.storyboard(projectId);
    setStoryboard(board);
    setSavedJson(JSON.stringify(board));
    setRawJson(JSON.stringify(board, null, 2));
    const [outs, final, draft, spent] = await Promise.all([
      api.outputs(projectId),
      api.estimate(projectId, ALL_STAGES, "final").catch(() => undefined),
      api.estimate(projectId, ["shots"], "draft").catch(() => undefined),
      api.costs(projectId),
    ]);
    setOutputs(outs);
    setEstimates({ final, draft });
    setCosts(spent);
  }, [projectId]);

  const attach = useCallback((summary: RunSummary) => {
    events.current?.close();
    setRun(summary);
    const source = new EventSource(`/api/runs/${summary.id}/events`);
    events.current = source;
    source.onopen = () => {
      setLog([]);
      setRunError(null);
    };
    source.onmessage = (message) => {
      const event: RunEvent = JSON.parse(message.data);
      if (event.type === "log") setLog((lines) => [...lines, event.line]);
      if (event.type === "stage" && event.error) setRunError(`${event.stage}: ${event.error}`);
      if (event.type === "stage") setRun((r) => r && { ...r, stage_status: { ...r.stage_status, [event.stage]: event.status } });
      if (event.type === "status") {
        setRun((r) => r && { ...r, status: event.status });
        if (FINISHED.includes(event.status)) {
          source.close();
          refresh();
        }
      }
    };
  }, [refresh]);

  useEffect(() => {
    api.schema().then(setSchema);
    refresh().catch((e) => setMessages(describeError(e)));
    api.activeRun(projectId).then((active) => active && attach(active));
    return () => events.current?.close();
  }, [projectId, refresh, attach]);

  useEffect(() => {
    logEnd.current?.scrollIntoView({ block: "nearest" });
  }, [log]);

  if (!storyboard) return <p className="muted">Loading project…</p>;
  const shot = storyboard.shots[Math.min(selected, storyboard.shots.length - 1)];

  function edit(next: Storyboard) {
    setStoryboard(next);
    setRawJson(JSON.stringify(next, null, 2));
  }

  function editShot(next: Shot) {
    edit({ ...storyboard!, shots: storyboard!.shots.map((s) => (s.id === shot.id ? next : s)) });
  }

  async function save() {
    try {
      await api.saveStoryboard(projectId, storyboard!);
      setMessages(["Saved."]);
      await refresh();
      return true;
    } catch (e) {
      setMessages(describeError(e));
      return false;
    }
  }

  async function start(step: { stages: StageName[]; quality: "draft" | "final" }) {
    if (dirty && !(await save())) return;
    try {
      setMessages([]);
      attach(await api.startRun(projectId, step.stages, step.quality, keys));
    } catch (e) {
      setMessages(describeError(e));
      if (e instanceof ApiError && (e.detail as { missing_keys?: string[] })?.missing_keys) onNeedKeys();
    }
  }

  function stepEstimate(step: Step) {
    const source = step.quality === "draft" ? estimates.draft : estimates.final;
    return source?.stages[step.stages[0]];
  }

  function addShot() {
    const taken = new Set(storyboard!.shots.map((s) => s.id));
    const number = Array.from({ length: 20 }, (_, i) => i + 1).find((n) => !taken.has(`s${String(n).padStart(2, "0")}`));
    if (!number) return;
    const id = `s${String(number).padStart(2, "0")}`;
    const fresh: Shot = {
      id, reason: "Why this shot is in the film.", description: "What happens in this shot.",
      image_prompt: "What the first frame shows.", motion_prompt: "What moves, and how the camera moves.",
      seed: 100 + number, clip_s: 8, duration_s: 8, lines: [],
    };
    edit({ ...storyboard!, shots: [...storyboard!.shots, fresh] });
    setSelected(storyboard!.shots.length);
  }

  function moveShot(offset: number) {
    const index = storyboard!.shots.indexOf(shot);
    const target = index + offset;
    if (target < 0 || target >= storyboard!.shots.length) return;
    const shots = [...storyboard!.shots];
    [shots[index], shots[target]] = [shots[target], shots[index]];
    edit({ ...storyboard!, shots });
    setSelected(target);
  }

  function removeShot() {
    if (storyboard!.shots.length === 1) return;
    edit({ ...storyboard!, shots: storyboard!.shots.filter((s) => s.id !== shot.id) });
    setSelected(0);
  }

  return (
    <div className="studio">
      <div className="steps">
        {STEPS.map((step) => {
          const est = stepEstimate(step);
          return (
            <button key={step.label} className="step" disabled={running} title={step.help} onClick={() => start(step)}>
              <b>{step.label}</b>
              <small>
                {est ? `${est.to_make} to make · ${est.cached} cached${est.est_usd ? ` · ≈ $${est.est_usd.toFixed(2)}` : ""}` : step.help}
              </small>
            </button>
          );
        })}
        <button className="step primary" disabled={running} onClick={() => start({ stages: ALL_STAGES, quality: "final" })}>
          <b>Run everything</b>
          <small>
            ≈ ${Object.values(estimates.final?.stages ?? {}).reduce((sum, s) => sum + (s?.est_usd ?? 0), 0).toFixed(2)}
          </small>
        </button>
      </div>
      {estimates.final?.problems.map((p) => <p key={p} className="warning">{p}</p>)}
      {messages.map((m) => <p key={m} className={m === "Saved." ? "ok" : "warning"}>{m}</p>)}

      {run && (
        <div className="run-panel">
          <div className="row">
            <b>Run: {run.status}</b>
            {run.stages.map((s) => <span key={s} className={`pill ${run.stage_status[s] ?? "waiting"}`}>{s}</span>)}
            {running && <button className="ghost" onClick={() => api.cancelRun(run.id)}>Cancel</button>}
          </div>
          {runError && <p className="warning">{runError}</p>}
          <pre className="log">{log.join("\n")}<div ref={logEnd} /></pre>
        </div>
      )}

      <div className="workbench">
        <nav className="shot-list">
          {storyboard.shots.map((s, i) => (
            <button key={s.id} className={s.id === shot.id && tab === "shot" ? "active" : ""} onClick={() => { setSelected(i); setTab("shot"); }}>
              {outputs?.shots[s.id]?.keyframe ? <img src={outputs.shots[s.id].keyframe!} alt="" /> : <span className="thumb-empty" />}
              <span><b>{s.id}</b> {s.description.slice(0, 40)}</span>
            </button>
          ))}
          <div className="row">
            <button className="ghost" onClick={addShot}>+ Shot</button>
            <button className="ghost" onClick={() => moveShot(-1)}>↑</button>
            <button className="ghost" onClick={() => moveShot(1)}>↓</button>
            <button className="ghost" onClick={removeShot}>Delete</button>
          </div>
        </nav>

        <div className="main">
          <div className="tabs">
            <button className={tab === "shot" ? "active" : ""} onClick={() => setTab("shot")}>Shot {shot.id}</button>
            <button className={tab === "film" ? "active" : ""} onClick={() => setTab("film")}>Film settings</button>
            <button className={tab === "json" ? "active" : ""} onClick={() => setTab("json")}>Raw JSON</button>
            <span className="spacer" />
            <button className="primary" disabled={!dirty || running} onClick={save}>{dirty ? "Save" : "Saved"}</button>
          </div>
          {schemaErrors.length > 0 && (
            <ul className="errors">{schemaErrors.slice(0, 8).map((e) => <li key={e}>{e}</li>)}</ul>
          )}
          {tab === "shot" && <ShotEditor schema={schema} storyboard={storyboard} shot={shot} outputs={outputs?.shots[shot.id]} onChange={editShot} />}
          {tab === "film" && <FilmSettings schema={schema} storyboard={storyboard} outputs={outputs} onChange={edit} />}
          {tab === "json" && (
            <CodeMirror
              value={rawJson}
              extensions={[json()]}
              onChange={(text) => {
                setRawJson(text);
                try { setStoryboard(JSON.parse(text)); } catch { /* keep the last parsable version until the JSON is whole again */ }
              }}
            />
          )}
        </div>
      </div>

      <h3>Music</h3>
      <div className="music">
        {outputs?.music.map(({ seed, url }) => (
          <div key={seed} className={`card ${storyboard.music?.chosen_seed === seed ? "chosen" : ""}`}>
            <b>Seed {seed}</b>
            {url ? <audio src={url} controls preload="none" /> : <span className="muted small">Not made yet. Run Music.</span>}
            <button
              className="ghost"
              disabled={!url}
              onClick={() => edit({ ...storyboard, music: { ...storyboard.music!, chosen_seed: seed } })}
            >
              {storyboard.music?.chosen_seed === seed ? "Chosen" : "Use this one"}
            </button>
          </div>
        ))}
      </div>

      <h3>Your film</h3>
      <div className="films">
        {(["9x16", "16x9"] as const).map((o) =>
          outputs?.films[o] ? (
            <div key={o} className={`player player-${o}`}>
              <video key={outputs.films[o]!} src={`${outputs.films[o]}?v=${run?.id ?? ""}`} controls playsInline preload="metadata" />
              <a href={outputs.films[o]!} download>Download {o.replace("x", ":")}</a>
            </div>
          ) : (
            <p key={o} className="muted">No {o.replace("x", ":")} film yet. Run Film.</p>
          ),
        )}
      </div>

      {costs && (
        <p className="small muted">
          Spent in this project: ${costs.total.billed.toFixed(2)} over {costs.total.calls} model calls
          {costs.total.failed ? ` (${costs.total.failed} failed)` : ""}.
        </p>
      )}
    </div>
  );
}
