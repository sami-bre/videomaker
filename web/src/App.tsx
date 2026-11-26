import { type ReactNode, useEffect, useState } from "react";
import { Clapperboard, FilePlus2, KeyRound, Shuffle } from "lucide-react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api, ApiError, describeError } from "./api";
import { KeysDialog } from "./KeysDialog";
import { loadSavedKeys } from "./keys";
import { Showcase } from "./Showcase";
import { Studio } from "./Studio";
import type { Outputs, Storyboard } from "./types";

function projectFromUrl() {
  return new URLSearchParams(window.location.search).get("p");
}

export function App() {
  const [showcase, setShowcase] = useState<{ storyboard: Storyboard; outputs: Outputs } | null>(null);
  const [projectId, setProjectId] = useState(projectFromUrl());
  const [keys, setKeys] = useState<Record<string, string>>(loadSavedKeys);
  const [remembered, setRemembered] = useState(Object.keys(loadSavedKeys()).length > 0);
  const [showKeys, setShowKeys] = useState(false);

  useEffect(() => {
    api.showcase().then(setShowcase).catch((e) => {
      // A server without the example film still serves blank projects.
      if (!(e instanceof ApiError && e.status === 404)) toast.error(describeError(e).join(" "));
    });
  }, []);

  useEffect(() => {
    if (projectId) document.getElementById("studio")?.scrollIntoView();
  }, [projectId]);

  async function newProject(source: "example" | "blank") {
    try {
      const { id } = await api.createProject(source);
      window.history.pushState(null, "", `?p=${id}#studio`);
      setProjectId(id);
    } catch (e) {
      toast.error(describeError(e).join(" "));
    }
  }

  const keyCount = Object.keys(keys).length;

  return (
    <div className="min-h-svh">
      <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <a href="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <Clapperboard className="size-5 text-primary" /> videomaker
          </a>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setShowKeys(true)}>
              <KeyRound /> API keys {keyCount > 0 && <Badge variant="secondary">{keyCount}</Badge>}
            </Button>
            <Button variant="ghost" size="sm" asChild>
              <a href="https://github.com/sami-bre/videomaker" target="_blank" rel="noreferrer">GitHub</a>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4">
        {showcase && <Showcase storyboard={showcase.storyboard} outputs={showcase.outputs} />}

        <section id="studio" className="scroll-mt-16 py-16">
          <div className="mb-6 flex flex-col gap-1">
            <h2 className="text-3xl font-semibold tracking-tight">Studio</h2>
            <p className="text-muted-foreground">Write the storyboard, run each step, and watch your film come together.</p>
          </div>
          {projectId ? (
            <Studio key={projectId} projectId={projectId} keys={keys} onNeedKeys={() => setShowKeys(true)} />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {showcase && (
                <StartCard
                  icon={<Shuffle />}
                  title="Remix this film"
                  text="Start from the film above and change anything. Everything you don't change is reused, so you only pay for your edits."
                  action="Remix"
                  primary
                  onClick={() => newProject("example")}
                />
              )}
              <StartCard
                icon={<FilePlus2 />}
                title="Start blank"
                text="An empty storyboard with one shot, ready for your own story, characters and look."
                action="Start blank"
                primary={!showcase}
                onClick={() => newProject("blank")}
              />
            </div>
          )}
        </section>
      </main>

      <KeysDialog
        open={showKeys}
        keys={keys}
        remembered={remembered}
        onSave={(next, remember) => { setKeys(next); setRemembered(remember); }}
        onOpenChange={setShowKeys}
      />
    </div>
  );
}

type StartCardProps = { icon: ReactNode; title: string; text: string; action: string; primary?: boolean; onClick: () => void };

function StartCard({ icon, title, text, action, primary, onClick }: StartCardProps) {
  return (
    <Card className={primary ? "ring-2 ring-primary/40" : ""}>
      <CardHeader>
        <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary [&_svg]:size-5">{icon}</div>
        <CardTitle className="text-xl">{title}</CardTitle>
        <CardDescription>{text}</CardDescription>
      </CardHeader>
      <CardContent>
        <Button size="lg" variant={primary ? "default" : "outline"} onClick={onClick}>{action}</Button>
      </CardContent>
    </Card>
  );
}
