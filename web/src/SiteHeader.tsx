import { BookOpen, Clapperboard, KeyRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type Props = { keyCount?: number; onKeys?: () => void };

export function SiteHeader({ keyCount = 0, onKeys }: Props) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <a href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <Clapperboard className="size-5 text-primary" /> videomaker
        </a>
        <nav className="flex items-center gap-1 sm:gap-2">
          {onKeys && (
            <Button variant="ghost" size="sm" onClick={onKeys}>
              <KeyRound /> <span className="hidden sm:inline">API keys</span> {keyCount > 0 && <Badge variant="secondary">{keyCount}</Badge>}
            </Button>
          )}
          <Button variant="ghost" size="sm" asChild>
            <a href="/docs/"><BookOpen /> Docs</a>
          </Button>
          <Button variant="ghost" size="sm" asChild>
            <a href="https://github.com/sami-bre/videomaker" target="_blank" rel="noreferrer">GitHub</a>
          </Button>
        </nav>
      </div>
    </header>
  );
}
