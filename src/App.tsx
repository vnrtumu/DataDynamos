import { ShieldCheck } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  PipelineProvider,
  usePipelineContext,
} from "@/features/pipeline/PipelineContext";
import { UploadView } from "@/features/upload/UploadView";
import { Workspace } from "@/features/Workspace";

function Shell() {
  const { document } = usePipelineContext();
  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center gap-2.5 px-4 sm:px-6">
          <div className="flex size-8 items-center justify-center rounded-lg bg-brand text-brand-foreground">
            <ShieldCheck className="size-4.5" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="font-semibold tracking-tight">Made By Agents</span>
            <span className="text-sm text-muted-foreground">
              Document Approval
            </span>
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        {document ? <Workspace /> : <UploadView />}
      </main>
    </div>
  );
}

function App() {
  return (
    <PipelineProvider>
      <TooltipProvider delayDuration={200}>
        <Shell />
        <Toaster position="bottom-right" richColors />
      </TooltipProvider>
    </PipelineProvider>
  );
}

export default App;
