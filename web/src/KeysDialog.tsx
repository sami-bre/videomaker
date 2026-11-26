import { useEffect, useState } from "react";
import { ExternalLink, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PROVIDER_KEYS, saveKeys } from "./keys";

type Props = {
  open: boolean;
  keys: Record<string, string>;
  remembered: boolean;
  onSave: (keys: Record<string, string>, remember: boolean) => void;
  onOpenChange: (open: boolean) => void;
};

export function KeysDialog({ open, keys, remembered, onSave, onOpenChange }: Props) {
  const [draft, setDraft] = useState(keys);
  const [remember, setRemember] = useState(remembered);

  useEffect(() => {
    if (open) {
      setDraft(keys);
      setRemember(remembered);
    }
  }, [open, keys, remembered]);

  function save() {
    const cleaned = Object.fromEntries(Object.entries(draft).filter(([, v]) => v.trim()).map(([k, v]) => [k, v.trim()]));
    saveKeys(cleaned, remember);
    onSave(cleaned, remember);
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90svh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Your API keys</DialogTitle>
          <DialogDescription className="flex gap-2">
            <ShieldCheck className="mt-0.5 size-4 shrink-0 text-primary" />
            You pay the providers directly. Keys stay in this browser and are sent only with a run, to that run's
            process. The server never saves them and blanks them out of every log.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-col gap-4">
          {PROVIDER_KEYS.map((k) => (
            <div key={k.name} className="flex flex-col gap-1.5">
              <div className="flex items-baseline justify-between gap-2">
                <Label htmlFor={k.name}>{k.label}</Label>
                <a href={k.getAt} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                  Get one <ExternalLink className="size-3" />
                </a>
              </div>
              <Input
                id={k.name}
                type="password"
                autoComplete="off"
                value={draft[k.name] ?? ""}
                onChange={(e) => setDraft({ ...draft, [k.name]: e.target.value })}
              />
              <p className="text-xs text-muted-foreground">{k.usedFor}</p>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <Checkbox id="remember-keys" checked={remember} onCheckedChange={(v) => setRemember(v === true)} />
            <Label htmlFor="remember-keys" className="font-normal">Remember on this device</Label>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={save}>Save keys</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
