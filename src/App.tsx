import { useState } from "react";
import { ShieldCheck, Layers, FileSpreadsheet, Sliders } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import {
  PipelineProvider,
  usePipelineContext,
} from "@/features/pipeline/PipelineContext";
import { UploadView } from "@/features/upload/UploadView";
import { Workspace } from "@/features/Workspace";
import { DeliverablesView } from "@/features/deliverables/DeliverablesView";
import { RuleSettingsView } from "@/features/rules/RuleSettingsView";

function Shell() {
  const { document } = usePipelineContext();
  const [activeTab, setActiveTab] = useState<"workspace" | "rules" | "deliverables">("workspace");

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex size-8 items-center justify-center rounded-lg bg-brand text-brand-foreground shadow-xs">
              <ShieldCheck className="size-4.5" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-semibold tracking-tight">DataDynamos</span>
              <span className="text-sm text-muted-foreground hidden sm:inline">
                Healthcare Claims Approval
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === "workspace" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("workspace")}
              className="text-xs gap-1.5"
            >
              <FileSpreadsheet className="size-3.5 text-brand" />
              Claims Workspace
            </Button>
            <Button
              variant={activeTab === "rules" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("rules")}
              className="text-xs gap-1.5"
            >
              <Sliders className="size-3.5 text-purple-400" />
              Rule Defining Settings
            </Button>
            <Button
              variant={activeTab === "deliverables" ? "secondary" : "ghost"}
              size="sm"
              onClick={() => setActiveTab("deliverables")}
              className="text-xs gap-1.5"
            >
              <Layers className="size-3.5 text-sky-400" />
              Hackathon Deliverables & Architecture
            </Button>
          </div>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        {activeTab === "deliverables" ? (
          <DeliverablesView />
        ) : activeTab === "rules" ? (
          <RuleSettingsView />
        ) : document ? (
          <Workspace />
        ) : (
          <UploadView />
        )}
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
