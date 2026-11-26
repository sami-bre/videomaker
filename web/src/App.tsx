import { useEffect, useState } from "react";
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.showcase().then(setShowcase).catch((e) => {
      // A server without the example film still serves blank projects.
      if (!(e instanceof ApiError && e.status === 404)) setError(describeError(e).join(" "));
    });
  }, []);

  async function newProject(source: "example" | "blank") {
    try {
      const { id } = await api.createProject(source);
      window.history.pushState(null, "", `?p=${id}#studio`);
      setProjectId(id);
    } catch (e) {
      setError(describeError(e).join(" "));
    }
  }

  return (
    <>
      <header className="top">
        <a href="/" className="brand">videomaker</a>
        <a href="https://github.com/sami-bre/videomaker" target="_blank" rel="noreferrer">GitHub</a>
      </header>
      {error && <p className="warning">{error}</p>}
      {showcase && <Showcase storyboard={showcase.storyboard} outputs={showcase.outputs} />}

      <section id="studio" className="studio-section">
        <div className="row">
          <h2>Studio</h2>
          <span className="spacer" />
          <button className="ghost" onClick={() => setShowKeys(true)}>
            API keys ({Object.keys(keys).length} set)
          </button>
        </div>
        {projectId ? (
          <>
            <p className="small muted">
              This project lives at this page's link. Anyone with the link can open and edit it, so keep it to yourself.
            </p>
            <Studio key={projectId} projectId={projectId} keys={keys} onNeedKeys={() => setShowKeys(true)} />
          </>
        ) : (
          <div className="start">
            <p>
              {showcase
                ? "Start from the film above and change what you like (only what you change costs money), or start from an empty storyboard."
                : "Start from an empty storyboard."}
            </p>
            <div className="row">
              {showcase && <button className="primary" onClick={() => newProject("example")}>Remix this film</button>}
              <button className={showcase ? "" : "primary"} onClick={() => newProject("blank")}>Start blank</button>
            </div>
          </div>
        )}
      </section>

      {showKeys && (
        <KeysDialog
          keys={keys}
          remembered={remembered}
          onClose={(next, remember) => { setKeys(next); setRemembered(remember); setShowKeys(false); }}
        />
      )}
    </>
  );
}
