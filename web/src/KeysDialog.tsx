import { useState } from "react";
import { PROVIDER_KEYS, saveKeys } from "./keys";

type Props = {
  keys: Record<string, string>;
  remembered: boolean;
  onClose: (keys: Record<string, string>, remember: boolean) => void;
};

export function KeysDialog({ keys, remembered, onClose }: Props) {
  const [draft, setDraft] = useState(keys);
  const [remember, setRemember] = useState(remembered);

  function done() {
    const cleaned = Object.fromEntries(Object.entries(draft).filter(([, v]) => v.trim()).map(([k, v]) => [k, v.trim()]));
    saveKeys(cleaned, remember);
    onClose(cleaned, remember);
  }

  return (
    <div className="overlay" onClick={done}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h2>Your API keys</h2>
        <p className="small muted">
          You pay the providers directly. Keys stay in this browser and are sent only with a run, over HTTPS, to the
          pipeline process for that run. The server never saves them, and they are blanked out of every log.
        </p>
        {PROVIDER_KEYS.map((k) => (
          <label key={k.name} className="field">
            <span>
              {k.label} <a href={k.getAt} target="_blank" rel="noreferrer">get one</a>
              <small className="muted"> · {k.usedFor}</small>
            </span>
            <input
              type="password"
              autoComplete="off"
              value={draft[k.name] ?? ""}
              onChange={(e) => setDraft({ ...draft, [k.name]: e.target.value })}
            />
          </label>
        ))}
        <label className="check">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          Remember on this device
        </label>
        <div className="row end">
          <button className="primary" onClick={done}>Done</button>
        </div>
      </div>
    </div>
  );
}
