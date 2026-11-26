import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import CodeMirror from "@uiw/react-codemirror";
import { json } from "@codemirror/lang-json";
import Ajv2020 from "ajv/dist/2020";
import {
  ArrowDown, ArrowUp, AudioLines, Check, Clapperboard, Download, Film, ImageIcon, Languages, Loader2,
  Music, Play, Plus, Save, Sparkles, Square, Trash2, TriangleAlert, Wand2, X,
} from "lucide-react";
import { toast } from "sonner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { api, ApiError, describeError, firstStep } from "./api";
import { FilmSettings } from "./FilmSettings";
import { ShotEditor } from "./ShotEditor";
import type { Costs, Estimate, Outputs, RunEvent, RunSummary, Shot, StageName, Storyboard } from "./types";

type Step = { label: string; stages: StageName[]; quality: "draft" | "final"; help: string; icon: typeof Film };

const STEPS: Step[] = [
  { label: "Translate", stages: ["script"], quality: "final", help: "English lines to the narration language", icon: Languages },
  { label: "Voice", stages: ["narration"], quality: "final", help: "One audio file per line", icon: AudioLines },
  { label: "Pictures", stages: ["keyframes"], quality: "final", help: "Character sheets, then one frame per shot", icon: ImageIcon },
  { label: "Draft motion", stages: ["shots"], quality: "draft", help: "480p clips, to check motion cheaply", icon: Wand2 },
  { label: "Final motion", stages: ["shots"], quality: "final", help: "720p clips for the film", icon: Clapperboard },
  { label: "Music", stages: ["music"], quality: "final", help: "One score candidate per seed", icon: Music },
  { label: "Film", stages: ["film"], quality: "final", help: "Edit, mix, subtitles, end card", icon: Film },
];
const ALL_STAGES: StageName[] = ["script", "narration", "keyframes", "shots", "music", "film"];
const FINISHED = ["done", "failed", "cancelled"];
const RUN_BADGE: Record<RunSummary["status"], "default" | "secondary" | "destructive" | "outline"> = {
  queued: "outline", running: "default", done: "secondary", failed: "destructive", cancelled: "outline",
};

type Props = { projectId: string; keys: Record<string, string>; onNeedKeys: () => void };

export function Studio({ projectId, keys, onNeedKeys }: Props) {
  const [schema, setSchema] = useState<object | null>(null);
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [savedJson, setSavedJson] = useState("");
  const [outputs, setOutputs] = useState<Outputs | null>(null);
  const [estimates, setEstimates] = useState<{ final?: Estimate; draft?: Estimate }>({});
  const [costs, setCosts] = useState<Costs | null>(null);
  const [tab, setTab] = useState("shot");
  const [selected, setSelected] = useState(0);
  const [run, setRun] = useState<RunSummary | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [runError, setRunError] = useState<string | null>(null);
  const [rawJson, setRawJson] = useState("");
  const [filmOrientation, setFilmOrientation] = useState("16x9");
  const events = useRef<EventSource | null>(null);
  const logBox = useRef<HTMLPreElement | null>(null);

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
          if (event.status === "done") toast.success("Run finished");
          refresh();
        }
      }
    };
  }, [refresh]);

  useEffect(() => {
    api.schema().then(setSchema);
    refresh().catch((e) => toast.error(describeError(e).join(" ")));
    api.activeRun(projectId).then((active) => active && attach(active));
    return () => events.current?.close();
  }, [projectId, refresh, attach]);

  useEffect(() => {
    if (logBox.current) logBox.current.scrollTop = logBox.current.scrollHeight;
  }, [log]);

  if (!storyboard) {
    return <div className="flex items-center gap-2 text-muted-foreground"><Loader2 className="size-4 animate-spin" /> Loading project…</div>;
  }
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
      toast.success("Storyboard saved");
      await refresh();
      return true;
    } catch (e) {
      toast.error("Not saved", { description: describeError(e).join("\n") });
      return false;
    }
  }

  async function start(step: { stages: StageName[]; quality: "draft" | "final" }) {
    if (dirty && !(await save())) return;
    try {
      attach(await api.startRun(projectId, step.stages, step.quality, keys));
    } catch (e) {
      const missing = e instanceof ApiError && (e.detail as { missing_keys?: string[] })?.missing_keys;
      toast.error(missing ? "API keys needed" : "Not ready yet", {
        description: describeError(e).join("\n"),
        action: missing ? { label: "Add keys", onClick: onNeedKeys } : undefined,
      });
      if (missing) onNeedKeys();
    }
  }

  function stepEstimate(step: Step) {
    const source = step.quality === "draft" ? estimates.draft : estimates.final;
    return source?.stages[step.stages[0]];
  }

  function stepState(step: Step) {
    const stage = step.stages[0];
    if (!run || !run.stages.includes(stage)) return null;
    if (stage === "shots" && run.quality !== step.quality) return null;
    return run.stage_status[stage] ?? null;
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
    setTab("shot");
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

  const totalUsd = Object.values(estimates.final?.stages ?? {}).reduce((sum, s) => sum + (s?.est_usd ?? 0), 0);

  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground">
        This project lives at this page's link. Anyone with the link can open and edit it, so keep it to yourself.
      </p>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline</CardTitle>
          <CardDescription>Run the steps in order. Each one shows what it will make, what it will reuse, and the rough cost.</CardDescription>
          <CardAction>
            <Button disabled={running} onClick={() => start({ stages: ALL_STAGES, quality: "final" })}>
              <Sparkles /> Run everything {totalUsd > 0 && <span className="opacity-80">≈ ${totalUsd.toFixed(2)}</span>}
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
            {STEPS.map((step, i) => {
              const est = stepEstimate(step);
              const state = stepState(step);
              const waiting = est?.waiting_for ?? [];
              const Icon = step.icon;
              return (
                <button
                  key={step.label}
                  disabled={running || waiting.length > 0}
                  title={waiting.length ? waiting.map(firstStep).join("\n") : step.help}
                  onClick={() => start(step)}
                  className={cn(
                    "group flex flex-col gap-2 rounded-xl border bg-card p-3 text-left transition hover:border-primary/60 hover:shadow-sm disabled:pointer-events-none",
                    state === "started" && "border-primary ring-2 ring-primary/30",
                    (running && state !== "started" || waiting.length > 0) && "opacity-60",
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      {state === "started" ? <Loader2 className="size-4 animate-spin" /> : state === "done" ? <Check className="size-4" /> : state === "failed" ? <X className="size-4" /> : <Icon className="size-4" />}
                    </span>
                    <span className="text-xs text-muted-foreground">{i + 1}</span>
                  </div>
                  <span className="text-sm font-medium">{step.label}</span>
                  <span className="text-xs text-muted-foreground">
                    {waiting.length > 0 ? (
                      waiting.map((need) => <span key={need} className="block text-amber-600 dark:text-amber-400">{firstStep(need)}</span>)
                    ) : step.stages[0] === "film" ? (
                      "Edits both films · free"
                    ) : est ? (
                      <>
                        {est.to_make > 0 ? <span className="font-medium text-foreground">{est.to_make} to make</span> : "Up to date"}
                        {est.cached > 0 && ` · ${est.cached} cached`}
                        {est.est_usd > 0 && <span className="block">≈ ${est.est_usd.toFixed(2)}</span>}
                      </>
                    ) : step.help}
                  </span>
                  <span className="mt-auto flex items-center gap-1 text-xs font-medium text-primary opacity-0 transition group-hover:opacity-100">
                    <Play className="size-3" /> Run
                  </span>
                </button>
              );
            })}
          </div>
          {estimates.final?.problems.map((p) => (
            <Alert key={p} variant="destructive">
              <TriangleAlert />
              <AlertTitle>Fix before rendering motion</AlertTitle>
              <AlertDescription>{p}</AlertDescription>
            </Alert>
          ))}
        </CardContent>
      </Card>

      {run && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {running && <Loader2 className="size-4 animate-spin text-primary" />}
              Run <Badge variant={RUN_BADGE[run.status]}>{run.status}</Badge>
            </CardTitle>
            <CardDescription className="flex flex-wrap gap-1.5">
              {run.stages.map((s) => (
                <Badge key={s} variant={run.stage_status[s] === "done" ? "secondary" : run.stage_status[s] === "failed" ? "destructive" : "outline"}>
                  {run.stage_status[s] === "started" && <Loader2 className="animate-spin" />}
                  {run.stage_status[s] === "done" && <Check />}
                  {s}
                </Badge>
              ))}
            </CardDescription>
            {running && (
              <CardAction>
                <Button variant="outline" size="sm" onClick={() => api.cancelRun(run.id)}><Square /> Cancel</Button>
              </CardAction>
            )}
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {runError && (
              <Alert variant="destructive">
                <TriangleAlert />
                <AlertTitle>The run stopped</AlertTitle>
                <AlertDescription>{runError}</AlertDescription>
              </Alert>
            )}
            <pre ref={logBox} className="max-h-64 overflow-auto rounded-lg bg-muted p-3 font-mono text-xs leading-relaxed whitespace-pre-wrap">
              {log.join("\n") || "Waiting for output…"}
            </pre>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-[260px_1fr]">
        <Card className="h-fit gap-3 lg:sticky lg:top-20">
          <CardHeader>
            <CardTitle>Shots</CardTitle>
            <CardAction>
              <Button variant="ghost" size="icon-sm" aria-label="Add shot" onClick={addShot}><Plus /></Button>
            </CardAction>
          </CardHeader>
          <CardContent className="flex gap-2 overflow-x-auto lg:flex-col lg:overflow-visible">
            {storyboard.shots.map((s, i) => (
              <button
                key={s.id}
                onClick={() => { setSelected(i); setTab("shot"); }}
                className={cn(
                  "flex min-w-44 items-center gap-3 rounded-lg border p-1.5 text-left text-sm transition hover:bg-muted lg:min-w-0",
                  s.id === shot.id && tab === "shot" && "border-primary bg-primary/5",
                )}
              >
                {outputs?.shots[s.id]?.keyframe
                  ? <img src={outputs.shots[s.id].keyframe!} alt="" className="aspect-video w-16 shrink-0 rounded object-cover" />
                  : <span className="aspect-video w-16 shrink-0 rounded bg-muted" />}
                <span className="min-w-0">
                  <span className="block text-xs font-medium text-muted-foreground">{s.id}</span>
                  <span className="line-clamp-2 text-xs">{s.description}</span>
                </span>
              </button>
            ))}
          </CardContent>
          <CardContent className="flex gap-1">
            <Button variant="outline" size="icon-sm" aria-label="Move shot up" onClick={() => moveShot(-1)}><ArrowUp /></Button>
            <Button variant="outline" size="icon-sm" aria-label="Move shot down" onClick={() => moveShot(1)}><ArrowDown /></Button>
            <Button variant="outline" size="icon-sm" aria-label="Delete shot" className="ml-auto" disabled={storyboard.shots.length === 1} onClick={removeShot}><Trash2 /></Button>
          </CardContent>
        </Card>

        <Card>
          <Tabs value={tab} onValueChange={setTab} className="gap-6">
            <CardHeader>
              <TabsList>
                <TabsTrigger value="shot">Shot {shot.id}</TabsTrigger>
                <TabsTrigger value="film">Film settings</TabsTrigger>
                <TabsTrigger value="json">Raw JSON</TabsTrigger>
              </TabsList>
              <CardAction>
                <Button disabled={!dirty || running} onClick={save}>
                  {dirty ? <><Save /> Save</> : <><Check /> Saved</>}
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              {schemaErrors.length > 0 && (
                <Alert variant="destructive">
                  <TriangleAlert />
                  <AlertTitle>The storyboard has {schemaErrors.length} problem{schemaErrors.length > 1 ? "s" : ""}</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc pl-4">{schemaErrors.slice(0, 6).map((e) => <li key={e}>{e}</li>)}</ul>
                  </AlertDescription>
                </Alert>
              )}
              <TabsContent value="shot">
                <ShotEditor schema={schema} storyboard={storyboard} shot={shot} outputs={outputs?.shots[shot.id]} onChange={editShot} />
              </TabsContent>
              <TabsContent value="film">
                <FilmSettings schema={schema} storyboard={storyboard} outputs={outputs} onChange={edit} />
              </TabsContent>
              <TabsContent value="json">
                <div className="overflow-hidden rounded-lg border text-sm">
                  <CodeMirror
                    value={rawJson}
                    theme={document.documentElement.classList.contains("dark") ? "dark" : "light"}
                    extensions={[json()]}
                    onChange={(text) => {
                      setRawJson(text);
                      try { setStoryboard(JSON.parse(text)); } catch { /* keep the last parsable version until the JSON is whole again */ }
                    }}
                  />
                </div>
              </TabsContent>
            </CardContent>
          </Tabs>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Music</CardTitle>
          <CardDescription>Listen to each candidate and pick the one the film uses (the first, until you pick). Then save and run Film.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {outputs?.music.length ? outputs.music.map(({ seed, url }) => {
            const picked = storyboard.music?.chosen_seed !== undefined;
            const chosen = (storyboard.music?.chosen_seed ?? storyboard.music?.seeds[0]) === seed;
            return (
              <div key={seed} className={cn("flex flex-col gap-3 rounded-xl border p-4", chosen && "border-primary ring-2 ring-primary/30")}>
                <div className="flex items-center justify-between">
                  <span className="font-medium">Seed {seed}</span>
                  {chosen && <Badge variant={picked ? "default" : "secondary"}>{picked ? "Chosen" : "Default"}</Badge>}
                </div>
                {url ? <audio src={url} controls preload="none" className="w-full" /> : <p className="text-sm text-muted-foreground">Not made yet. Run Music.</p>}
                <Button variant={chosen && picked ? "secondary" : "outline"} size="sm" disabled={!url || (chosen && picked)}
                  onClick={() => edit({ ...storyboard, music: { ...storyboard.music!, chosen_seed: seed } })}>
                  {chosen && picked ? "In the film" : "Use this one"}
                </Button>
              </div>
            );
          }) : <p className="text-sm text-muted-foreground">Add a music description and seeds in Film settings.</p>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Your film</CardTitle>
          <CardDescription>
            {costs ? `Spent in this project so far: $${costs.total.billed.toFixed(2)} over ${costs.total.calls} model calls${costs.total.failed ? ` (${costs.total.failed} failed)` : ""}.` : ""}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={filmOrientation} onValueChange={setFilmOrientation} className="gap-4">
            <TabsList>
              <TabsTrigger value="16x9">16:9</TabsTrigger>
              <TabsTrigger value="9x16">9:16</TabsTrigger>
            </TabsList>
            {(["16x9", "9x16"] as const).map((o) => (
              <TabsContent key={o} value={o} className="flex flex-col items-start gap-3">
                {outputs?.films[o] ? (
                  <>
                    <video
                      key={`${outputs.films[o]}-${run?.id ?? ""}`}
                      src={`${outputs.films[o]}?v=${run?.id ?? ""}`}
                      controls playsInline preload="metadata"
                      className={cn("rounded-xl border bg-black", o === "16x9" ? "aspect-video w-full max-w-3xl" : "aspect-[9/16] w-full max-w-xs")}
                    />
                    <Button variant="outline" asChild>
                      <a href={outputs.films[o]!} download><Download /> Download {o.replace("x", ":")}</a>
                    </Button>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">No {o.replace("x", ":")} film yet. Run Film.</p>
                )}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
