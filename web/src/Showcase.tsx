import { useState } from "react";
import { ArrowDown, AudioLines, Clapperboard, Eye, FileJson, Film, ImageIcon, Languages, Music } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Outputs, Storyboard } from "./types";

type Props = { storyboard: Storyboard; outputs: Outputs };

const STEPS = [
  { icon: FileJson, title: "Storyboard", text: "Shots, lines, characters and look in one file." },
  { icon: Languages, title: "Translate", text: "English lines into the narration language." },
  { icon: AudioLines, title: "Voice", text: "A voice for every character." },
  { icon: ImageIcon, title: "Pictures", text: "Consistent characters, one frame per shot." },
  { icon: Clapperboard, title: "Motion", text: "Each frame becomes a moving clip." },
  { icon: Music, title: "Music", text: "An original score, ducked under the voice." },
  { icon: Film, title: "Film", text: "Edited, subtitled, in 16:9 and 9:16." },
];

export function Showcase({ storyboard, outputs }: Props) {
  const [orientation, setOrientation] = useState<"16x9" | "9x16">("16x9");
  const film = outputs.films[orientation];

  return (
    <section className="flex flex-col items-center gap-10 pt-14 pb-8 text-center">
      <div className="flex max-w-3xl flex-col items-center gap-5">
        <Badge variant="secondary" className="px-3 py-1">AI film pipeline · bring your own keys</Badge>
        <h1 className="text-4xl font-bold tracking-tight text-balance sm:text-6xl">
          One storyboard in.<br />A finished film out.
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground text-balance">
          Write your shots and lines. videomaker translates, voices, draws, animates, scores and edits them into a
          narrated, subtitled short film.
        </p>
        <Button asChild size="lg" className="mt-2 h-14 rounded-full px-10 text-lg shadow-lg shadow-primary/25 [&_svg]:size-5">
          <a href="#studio">Make your own film <ArrowDown /></a>
        </Button>
      </div>

      <div className="flex w-full flex-col items-center gap-4">
        <div className="flex w-full max-w-4xl flex-wrap items-end justify-between gap-3 text-left">
          <div>
            <p className="text-sm text-muted-foreground">Made with videomaker</p>
            <h2 className="text-2xl font-semibold tracking-tight">{storyboard.title}</h2>
            <p className="text-sm text-muted-foreground">A short comedy · Amharic with English subtitles · sound on</p>
          </div>
          <Tabs value={orientation} onValueChange={(v) => setOrientation(v as "16x9" | "9x16")}>
            <TabsList>
              <TabsTrigger value="16x9">16:9</TabsTrigger>
              <TabsTrigger value="9x16">9:16</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
        <div className={orientation === "16x9" ? "w-full max-w-4xl" : "w-full max-w-sm"}>
          {film && (
            <video
              key={film}
              src={film}
              controls
              playsInline
              preload="metadata"
              className={`w-full rounded-xl border bg-black shadow-2xl ${orientation === "16x9" ? "aspect-video" : "aspect-[9/16]"}`}
            />
          )}
        </div>
      </div>

      <div className="grid w-full max-w-5xl grid-cols-2 gap-3 text-left sm:grid-cols-4 lg:grid-cols-7">
        {STEPS.map(({ icon: Icon, title, text }, i) => (
          <div key={title} className="rounded-xl border bg-card p-3">
            <div className="mb-2 flex items-center gap-2 text-primary">
              <Icon className="size-4" />
              <span className="text-xs text-muted-foreground">{i + 1}</span>
            </div>
            <p className="text-sm font-medium">{title}</p>
            <p className="text-xs text-muted-foreground">{text}</p>
          </div>
        ))}
      </div>

      <Collapsible className="w-full text-left">
        <CollapsibleTrigger asChild>
          <Button variant="outline" className="mx-auto flex">
            <Eye /> Behind the scenes, shot by shot (spoilers: watch the film first)
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent className="mt-6">
          <div className="flex snap-x gap-4 overflow-x-auto pb-4">
            {storyboard.shots.map((shot) => (
              <ShotCard key={shot.id} shot={shot} outputs={outputs.shots[shot.id]} />
            ))}
          </div>
        </CollapsibleContent>
      </Collapsible>
    </section>
  );
}

function ShotCard({ shot, outputs }: { shot: Storyboard["shots"][number]; outputs?: Outputs["shots"][string] }) {
  const [playing, setPlaying] = useState(false);
  return (
    <Card className="w-72 shrink-0 snap-start gap-3 py-0 overflow-hidden">
      <div
        className="relative aspect-video bg-muted"
        onMouseEnter={() => setPlaying(true)}
        onMouseLeave={() => setPlaying(false)}
      >
        {playing && outputs?.clip ? (
          <video src={outputs.clip} autoPlay muted loop playsInline className="size-full object-cover" />
        ) : (
          outputs?.keyframe && <img src={outputs.keyframe} alt={shot.description} loading="lazy" className="size-full object-cover" />
        )}
        <Badge className="absolute top-2 left-2">{shot.id}</Badge>
      </div>
      <CardContent className="flex flex-col gap-2 pb-4 text-sm">
        {shot.lines.map((line, i) => (
          <div key={i}>
            <p className="text-[10px] font-medium tracking-wider text-muted-foreground uppercase">{line.speaker}</p>
            {line.spoken && <p className="font-ethiopic">{line.spoken}</p>}
            <p className="text-muted-foreground">{line.en}</p>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
