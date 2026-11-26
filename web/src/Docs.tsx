import type { ReactNode } from "react";
import { Info, Lightbulb } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { PROVIDER_KEYS } from "./keys";
import { SiteHeader } from "./SiteHeader";

const SECTIONS = [
  { id: "quick-start", title: "Quick start" },
  { id: "steps", title: "How a film is made" },
  { id: "projects", title: "Projects and saving" },
  { id: "keys", title: "API keys" },
  { id: "shots", title: "Shots" },
  { id: "lines", title: "Lines and translation" },
  { id: "speakers", title: "Speakers and voices" },
  { id: "characters", title: "Characters and the look" },
  { id: "music", title: "Music" },
  { id: "running", title: "Running the steps" },
  { id: "costs", title: "What it costs" },
  { id: "your-film", title: "Getting your film" },
  { id: "faq", title: "Problems and questions" },
];

export function Docs() {
  return (
    <div className="min-h-svh">
      <SiteHeader />
      <div className="mx-auto grid max-w-6xl gap-10 px-4 py-10 lg:grid-cols-[200px_1fr]">
        <nav className="hidden lg:block">
          <div className="sticky top-20 flex flex-col gap-1 text-sm">
            <p className="mb-2 text-xs font-semibold tracking-wider text-muted-foreground uppercase">On this page</p>
            {SECTIONS.map((s) => (
              <a key={s.id} href={`#${s.id}`} className="rounded-md px-2 py-1 text-muted-foreground hover:bg-muted hover:text-foreground">
                {s.title}
              </a>
            ))}
          </div>
        </nav>

        <article className="flex max-w-3xl flex-col gap-12 leading-relaxed">
          <header className="flex flex-col gap-3">
            <h1 className="text-4xl font-bold tracking-tight">How to use videomaker</h1>
            <p className="text-lg text-muted-foreground">
              videomaker turns a storyboard (your shots, lines, characters and look) into a narrated, scored, subtitled
              short film in 16:9 and 9:16. This page covers everything from your first film to fixing a bad shot.
            </p>
            <Button asChild className="self-start"><a href="/#studio">Open the studio</a></Button>
          </header>

          <Section id="quick-start" title="Quick start">
            <ol className="flex list-decimal flex-col gap-2 pl-5">
              <li>On the home page, scroll to <b>Studio</b> and click <b>Remix this film</b> (or <b>Start blank</b>).</li>
              <li>Click <b>API keys</b> at the top and paste your keys. See <A href="#keys">API keys</A> for where to get them.</li>
              <li>Edit a shot: change a line, a picture prompt, anything. Click <b>Save</b>.</li>
              <li>In <b>Pipeline</b>, click the steps in order, or <b>Run everything</b>. Each step tells you what it will make and the rough cost before you click.</li>
              <li>Scroll to <b>Your film</b> to watch and download it.</li>
            </ol>
            <Tip>
              Remixing is the cheapest way to start. Everything you don't change is reused from the example film, so
              changing one line costs one voice line, not a whole film.
            </Tip>
          </Section>

          <Section id="steps" title="How a film is made">
            <p>Seven steps, always in this order. Each one uses what the steps before it made.</p>
            <Table
              head={["Step", "What it does", "Made with"]}
              rows={[
                ["Translate", "Turns each line's English into the narration language.", "Addis AI (Amharic, Afaan Oromo); Gemini 2.5 Flash for others"],
                ["Voice", "Speaks every line in its speaker's voice.", "Gemini TTS"],
                ["Pictures", "Draws each character once, then one frame per shot with those characters in it.", "FLUX.2 klein on Cloudflare"],
                ["Draft motion", "Turns each frame into a short 480p clip, to check the motion cheaply.", "Grok Imagine or Wan 2.2"],
                ["Final motion", "The same at 720p, for the finished film.", "Grok Imagine or Wan 2.2"],
                ["Music", "Writes one score candidate per seed, for the whole film.", "ACE-Step 1.5"],
                ["Film", "Cuts everything together, ducks the music under the voice, adds subtitles and the end card.", "FFmpeg (no AI)"],
              ]}
            />
            <p>
              The film always uses the best clip it has for each shot: final over draft. So you can run Draft motion,
              then Film, to see a cheap rough cut before paying for 720p.
            </p>
          </Section>

          <Section id="projects" title="Projects and saving">
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li><b>There are no accounts.</b> Each project lives at its own link (the <code>?p=…</code> part of the address). Bookmark it to come back.</li>
              <li><b>Anyone with the link can open and edit the project.</b> Keep it to yourself, or share it with someone you want to work with.</li>
              <li><b>Lost the link?</b> There is no way to find a project without it, so bookmark it.</li>
              <li><b>Edits are not saved until you click Save.</b> The button says <b>Saved</b> when there is nothing new. Running a step saves first.</li>
              <li>Nothing can be saved while a step is running. Wait for it to finish.</li>
              <li>The example film itself is read-only. <b>Remix this film</b> makes your own copy.</li>
            </ul>
          </Section>

          <Section id="keys" title="API keys">
            <p>
              You bring your own keys, so you pay the providers directly and only for what you make. You only need the
              keys for the steps you run.
            </p>
            <Table
              head={["Key", "Used for", "Get it"]}
              rows={PROVIDER_KEYS.map((k) => [k.label, k.usedFor, <A key={k.name} href={k.getAt} external>Get one</A>])}
            />
            <Note>
              Your keys stay in your browser. They are sent only with a run, to the process doing that run, and are
              blanked out of every log. The server never saves them. Tick <b>Remember on this device</b> to keep them
              in this browser between visits; leave it off on a shared computer.
            </Note>
            <p>
              If a step needs a key you haven't added, it won't start: you'll see which key is missing and the keys
              window opens.
            </p>
          </Section>

          <Section id="shots" title="Shots">
            <p>A film is a list of shots (up to 20). Pick one in the <b>Shots</b> list to edit it.</p>
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li><b>+</b> adds a shot at the end, <b>↑ ↓</b> move the selected shot, the bin deletes it.</li>
              <li><b>What the viewer sees</b> and <b>Why this shot exists</b> are notes for you. They don't change the picture.</li>
              <li><b>Image prompt</b> describes the first frame: place, action, framing. The style and the characters' looks are added for you, so don't repeat them.</li>
              <li><b>Picture seed</b>: same prompt + same seed = same picture. Change the seed to get a different take.</li>
              <li><b>Motion prompt</b> describes only what moves and how the camera moves. The frame already holds who and where.</li>
              <li><b>Clip length</b> is how long the generated clip is. Grok Imagine makes 1 to 15 seconds; Wan 2.2 makes 5 or 8.</li>
              <li><b>Planned length</b> is the shortest the shot will be in the film. If the lines take longer, the shot grows to fit them.</li>
              <li><b>9:16 framing</b>: <b>Crop</b> takes a tall slice of the wide frame (slide to pick where). <b>Fit</b> shows the whole wide frame over a blurred copy, for shots with something important on both sides.</li>
            </ul>
            <Tip>A shot's id (s01, s02…) never changes, even when you move it. Its files are named after it.</Tip>
          </Section>

          <Section id="lines" title="Lines and translation">
            <p>Each shot has spoken lines, in order. A shot with no lines is silent.</p>
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li><b>English</b> is what the subtitles show, and what gets translated.</li>
              <li><b>Spoken</b> is what the voice says, in the narration language. <b>Translate</b> fills it in.</li>
              <li><b>Change the English</b> and Translate redoes that line (and only that line).</li>
              <li><b>Fix a word by hand</b> in Spoken and your edit is kept. Translate won't overwrite it unless you change the English again.</li>
              <li>
                Set the language and give the translator extra instructions (tone, tense, how to spell a name) in
                <b> Film settings → Story</b>.
              </li>
            </ul>
          </Section>

          <Section id="speakers" title="Speakers and voices">
            <p>
              The dropdown on each line picks who says it. That list comes from <b>Film settings → Voices</b>.
            </p>
            <p className="font-medium">To add someone who can speak:</p>
            <ol className="flex list-decimal flex-col gap-2 pl-5">
              <li>Open the <b>Film settings</b> tab.</li>
              <li>Under <b>Voices</b>, type an id (lowercase letters and <code>_</code> only, e.g. <code>grandma</code>) and click <b>+ Add speaker</b>.</li>
              <li>Set its <b>Voice</b> to a Gemini voice name, e.g. <code>Kore</code>, <code>Puck</code>, <code>Algenib</code>.</li>
              <li>Describe <b>How they speak</b> in plain words, e.g. "an old woman, slow and warm".</li>
              <li>Click <b>Save</b>. The speaker now appears in every line's dropdown.</li>
            </ol>
            <Note>
              Speakers (how someone <i>sounds</i>) and characters (how someone <i>looks</i>) are separate lists. For a
              person who is both seen and heard, add them to both, with the same id.
            </Note>
          </Section>

          <Section id="characters" title="Characters and the look">
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li><b>Characters</b> (Film settings) are people or animals who appear in more than one shot. Describe exactly how they look. Pictures draws each one once and uses that drawing for every shot they're in, so they stay the same.</li>
              <li>Tick who is in each shot under <b>Characters in this shot</b> (at most 4 per shot).</li>
              <li><b>Style</b> is added to every picture: medium, line, colours, and what to avoid. Change it and every picture is redrawn.</li>
              <li><b>Motion style</b> is added to every motion prompt. Use it to stop clips drifting from the drawn look.</li>
              <li><b>Video engine</b>: Grok Imagine (clips of 1 to 15 s, through OpenRouter) or Wan 2.2 (5 or 8 s, through WaveSpeed).</li>
            </ul>
            <Tip>Change one character's looks and only the shots with that character are redrawn.</Tip>
          </Section>

          <Section id="music" title="Music">
            <ol className="flex list-decimal flex-col gap-2 pl-5">
              <li>In <b>Film settings → Music</b>, describe the music: instruments, mood, texture. Leave tempo and key out.</li>
              <li>List a few <b>seeds</b> (e.g. 1, 2, 3). Each seed makes one candidate.</li>
              <li>Run <b>Music</b>, then listen to each candidate in the <b>Music</b> card.</li>
              <li>Click <b>Use this one</b> on your favourite, <b>Save</b>, and run <b>Film</b>.</li>
            </ol>
            <p>Until you pick one, the film uses the first seed's candidate (marked <b>Default</b>).</p>
            <p>The music is as long as the whole film, so if the narration gets longer or shorter, Music has to run again.</p>
          </Section>

          <Section id="running" title="Running the steps">
            <p>Each step's tile tells you, before you click:</p>
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li><b>N to make</b>: new files it will generate (these cost money or free-tier quota).</li>
              <li><b>N cached</b>: files it already has and will reuse for free.</li>
              <li><b>Up to date</b>: nothing to make.</li>
              <li><b>≈ $</b>: the rough cost at list price.</li>
              <li><b>Run Voice first…</b> (in orange): an earlier step has to run before this one can. The tile is disabled until it has.</li>
            </ul>
            <p>
              <b>Run everything</b> runs all steps in order, making only what is missing. While a step runs, the
              <b> Run</b> card shows live progress and the log. <b>Cancel</b> stops it; what was already made is kept.
              One step runs at a time per project.
            </p>
          </Section>

          <Section id="costs" title="What it costs">
            <Table
              head={["Step", "Cost"]}
              rows={[
                ["Translate", "A fraction of a cent per film"],
                ["Voice", "Free (Gemini free tier)"],
                ["Pictures", "Free (Cloudflare gives about 75 images a day)"],
                ["Draft motion (Grok, 480p)", "$0.02 per second of clip + $0.01 per shot"],
                ["Final motion (Grok, 720p)", "$0.03 per second of clip + $0.01 per shot"],
                ["Music", "About $0.03 per candidate"],
                ["Film", "Free"],
              ]}
            />
            <p>
              The example film (8 shots, 88 seconds) cost about <b>$2.70</b>, almost all of it Final motion. Anything
              already made is reused, so editing and re-running is cheap: you pay only for what changed. The bottom of
              the studio shows what this project has spent so far.
            </p>
          </Section>

          <Section id="your-film" title="Getting your film">
            <ul className="flex list-disc flex-col gap-2 pl-5">
              <li>Run <b>Film</b>. It takes about two minutes and is free.</li>
              <li>The <b>Your film</b> card has a 16:9 and a 9:16 version, each with a <b>Download</b> button.</li>
              <li>Both have English subtitles burned in, and end with a card listing which AI models made each part.</li>
              <li>Changed something? Run the steps it affects, then Film again.</li>
            </ul>
            <Note>When you post the film, switch on the platform's "made with AI" label. The end card already says so.</Note>
          </Section>

          <Section id="faq" title="Problems and questions">
            <Faq q="A step tile is greyed out and says “Run … first”.">
              An earlier step hasn't made what this one needs. Run the step it names. For example, Film needs every
              voice line, a clip for every shot, and the music.
            </Faq>
            <Faq q="It says “Add these keys first”.">
              The step needs a provider you have no key for. Add it in <b>API keys</b>. See <A href="#keys">which key does what</A>.
            </Faq>
            <Faq q="“Clip too short for its narration”.">
              The lines in that shot are longer than its clip. Raise the shot's <b>Clip length</b> to the number the
              message suggests, or shorten the lines. This is checked before any money is spent.
            </Faq>
            <Faq q="The storyboard has problems / Save fails.">
              The red box above the editor lists what's wrong, e.g. a required field left empty or a speaker with no
              voice. Fix those and save again.
            </Faq>
            <Faq q="A line is translated badly.">
              Fix it by hand in <b>Spoken</b> and save. Your edit is kept. Or add an instruction for the translator in
              <b> Film settings → Story</b> and change the English slightly so the line is translated again.
            </Faq>
            <Faq q="A picture is wrong.">
              Change the shot's <b>Image prompt</b> (say the action first, then the details) or its <b>Picture seed</b>,
              then run Pictures. Only that shot is redrawn. Its clip will need making again too.
            </Faq>
            <Faq q="A character looks different from shot to shot.">
              Make their description in <b>Characters</b> more exact, and make sure they're ticked in each shot they
              appear in.
            </Faq>
            <Faq q="The motion drifts away from the drawn style.">
              Add a firmer <b>Motion style</b> (e.g. "keep the flat 2D look, no 3D, no shading"), then run Draft motion
              to check before Final motion.
            </Faq>
            <Faq q="A run failed.">
              The <b>Run</b> card shows the reason at the top, and the full log below. Fix the cause and run the step
              again. Everything made before the failure is kept.
            </Faq>
            <Faq q="Can other people see my project?">
              Only people who have its link. There is no list of projects anywhere.
            </Faq>
            <Faq q="Can I edit the storyboard as a file?">
              Yes: the <b>Raw JSON</b> tab shows the whole storyboard. It's checked as you type, and saved with the same
              Save button.
            </Faq>
          </Section>
        </article>
      </div>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="flex scroll-mt-20 flex-col gap-4">
      <h2 className="border-b pb-2 text-2xl font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

function A({ href, external, children }: { href: string; external?: boolean; children: ReactNode }) {
  return (
    <a href={href} className="font-medium text-primary underline-offset-4 hover:underline" {...(external ? { target: "_blank", rel: "noreferrer" } : {})}>
      {children}
    </a>
  );
}

function Tip({ children }: { children: ReactNode }) {
  return (
    <Alert>
      <Lightbulb />
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  );
}

function Note({ children }: { children: ReactNode }) {
  return (
    <Alert>
      <Info />
      <AlertDescription>{children}</AlertDescription>
    </Alert>
  );
}

function Table({ head, rows }: { head: string[]; rows: ReactNode[][] }) {
  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-left">
          <tr>{head.map((h) => <th key={h} className="px-3 py-2 font-medium">{h}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t align-top">
              {row.map((cell, j) => <td key={j} className={j === 0 ? "px-3 py-2 font-medium whitespace-nowrap" : "px-3 py-2 text-muted-foreground"}>{cell}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Faq({ q, children }: { q: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <h3 className="font-semibold">{q}</h3>
      <p className="text-muted-foreground">{children}</p>
    </div>
  );
}
