import { useState } from "react";
import type { Outputs, Storyboard } from "./types";

type Props = { storyboard: Storyboard; outputs: Outputs };

export function Showcase({ storyboard, outputs }: Props) {
  const [orientation, setOrientation] = useState<"9x16" | "16x9">("9x16");
  const film = outputs.films[orientation];

  return (
    <section className="showcase">
      <div className="showcase-intro">
        <p className="eyebrow">Made with videomaker</p>
        <h1>{storyboard.title}</h1>
        <p className="logline">{storyboard.logline}</p>
        <p>
          One <code>storyboard.json</code> goes in. A translated, narrated, scored and subtitled film comes out, in 9:16 and
          16:9. Every picture, voice line, clip and note of music below was made by the pipeline from that one file.
        </p>
        <div className="toggle">
          {(["9x16", "16x9"] as const).map((o) => (
            <button key={o} className={o === orientation ? "active" : ""} onClick={() => setOrientation(o)}>
              {o.replace("x", ":")}
            </button>
          ))}
        </div>
        <a className="button primary" href="#studio">Make your own film ↓</a>
      </div>
      <div className={`player player-${orientation}`}>
        {film && <video key={film} src={film} controls playsInline preload="metadata" />}
      </div>

      <h2>How it was made</h2>
      <div className="strip">
        {storyboard.shots.map((shot) => (
          <ShotCard key={shot.id} shot={shot} outputs={outputs.shots[shot.id]} />
        ))}
      </div>
    </section>
  );
}

function ShotCard({ shot, outputs }: { shot: Storyboard["shots"][number]; outputs?: Outputs["shots"][string] }) {
  const [playing, setPlaying] = useState(false);
  return (
    <article className="shot-card">
      <div className="frame" onMouseEnter={() => setPlaying(true)} onMouseLeave={() => setPlaying(false)}>
        {playing && outputs?.clip ? (
          <video src={outputs.clip} autoPlay muted loop playsInline />
        ) : (
          outputs?.keyframe && <img src={outputs.keyframe} alt={shot.description} loading="lazy" />
        )}
        <span className="badge">{shot.id}</span>
      </div>
      <p className="muted small">{shot.description}</p>
      {shot.lines.map((line, i) => (
        <div key={i} className="line">
          <span className="speaker">{line.speaker}</span>
          {line.spoken && <p className="spoken">{line.spoken}</p>}
          <p className="en">{line.en}</p>
        </div>
      ))}
      <details>
        <summary>Prompts</summary>
        <p className="small"><b>Picture:</b> {shot.image_prompt}</p>
        <p className="small"><b>Motion:</b> {shot.motion_prompt}</p>
      </details>
    </article>
  );
}
