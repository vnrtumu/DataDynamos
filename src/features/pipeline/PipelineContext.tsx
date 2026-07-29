// Shares one usePipeline instance across the stepper, inspector, and decision
// card without prop-drilling.
import { createContext, useContext, type ReactNode } from "react";
import { usePipeline, type UsePipeline } from "@/features/pipeline/usePipeline";

const PipelineContext = createContext<UsePipeline | null>(null);

export function PipelineProvider({ children }: { children: ReactNode }) {
  const pipeline = usePipeline();
  return (
    <PipelineContext.Provider value={pipeline}>
      {children}
    </PipelineContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePipelineContext(): UsePipeline {
  const ctx = useContext(PipelineContext);
  if (!ctx) {
    throw new Error(
      "usePipelineContext must be used within a PipelineProvider",
    );
  }
  return ctx;
}
