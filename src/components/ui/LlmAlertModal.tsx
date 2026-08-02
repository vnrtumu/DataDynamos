import React from "react";
import { AlertTriangle, KeyRound, CreditCard, ShieldAlert, X } from "lucide-react";
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";

export interface LlmAlertState {
  open: boolean;
  title: string;
  message: string;
  details?: string;
  isCreditIssue?: boolean;
}

export function LlmAlertModal({
  alert,
  onClose,
}: {
  alert: LlmAlertState | null;
  onClose: () => void;
}) {
  if (!alert || !alert.open) return null;

  return (
    <AlertDialog open={alert.open} onOpenChange={(open) => !open && onClose()}>
      <AlertDialogContent className="max-w-md border-amber-500/40 bg-card p-6 shadow-2xl">
        <AlertDialogHeader className="space-y-3 text-left">
          <div className="flex items-center justify-between">
            <div className="flex size-10 items-center justify-center rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-400">
              <ShieldAlert className="size-5" />
            </div>
            <Badge variant="outline" className="bg-amber-500/15 text-amber-400 border-amber-500/30 font-mono text-[10px]">
              {alert.isCreditIssue ? "Credit Completion Required" : "LLM API Key Alert"}
            </Badge>
          </div>

          <AlertDialogTitle className="text-base font-bold tracking-tight text-foreground flex items-center gap-2">
            {alert.title || "LLM Engine & Credit Alert"}
          </AlertDialogTitle>

          <AlertDialogDescription className="text-xs text-muted-foreground leading-relaxed space-y-2">
            <p className="text-foreground/90 font-medium">
              {alert.message}
            </p>

            <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 space-y-2 text-[11px] text-amber-300">
              <div className="flex items-start gap-2">
                <KeyRound className="size-4 shrink-0 text-amber-400 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-200">OpenRouter API Key:</span> Ensure <code className="bg-background px-1 py-0.5 rounded text-amber-300 font-mono">OPENROUTER_API_KEY</code> is set in <code className="bg-background px-1 py-0.5 rounded text-amber-300 font-mono">backend/.env</code>.
                </div>
              </div>
              <div className="flex items-start gap-2 pt-1 border-t border-amber-500/15">
                <CreditCard className="size-4 shrink-0 text-amber-400 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-200">Credit Balance:</span> Verify that your OpenRouter account has active credits for model completion.
                </div>
              </div>
            </div>

            {alert.details && (
              <div className="rounded-md border bg-muted/40 p-2 font-mono text-[10px] text-muted-foreground overflow-x-auto max-h-24">
                {alert.details}
              </div>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter className="mt-4">
          <AlertDialogAction
            onClick={onClose}
            className="w-full sm:w-auto bg-amber-500 hover:bg-amber-600 text-amber-950 font-semibold text-xs h-9 px-5"
          >
            Acknowledge & Close
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
