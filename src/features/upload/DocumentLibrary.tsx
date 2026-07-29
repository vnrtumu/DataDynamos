// Grid of already-ingested documents shown under the dropzone. Lets you reopen
// a past run (without re-ingesting) or delete it. Fetches on mount; because
// UploadView only mounts when no document is open, returning here via "New
// document" re-runs this fetch and surfaces freshly ingested docs.
import { useCallback, useEffect, useState } from 'react';
import { FileText, Loader2, ReceiptText, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Badge } from '@/components/ui/badge';
import {
  ApiError,
  deleteAllDocuments,
  deleteDocument,
  fileUrl,
  listDocuments,
} from '@/lib/api';
import { formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { DocumentStatus, DocumentSummary } from '@/lib/types';
import { usePipelineContext } from '@/features/pipeline/PipelineContext';

const LOAD_ERROR = 'Could not load documents.';

const STATUS_LABEL: Record<DocumentStatus, string> = {
  uploaded: 'Uploaded',
  prescanned: 'Pre-scanned',
  ocr_done: 'OCR done',
  structured: 'Structured',
  decided: 'Decided',
  needs_review: 'Needs review',
};

// Borrow the approve/review verdict tokens (also used in the Workspace) so a
// finished doc reads green and a flagged one reads amber.
function statusBadgeClass(status: DocumentStatus): string {
  if (status === 'decided') return 'border-approve/40 text-approve';
  if (status === 'needs_review')
    return 'border-review/40 text-review-foreground';
  return 'border-border text-muted-foreground';
}

function DocumentCard({
  doc,
  onOpen,
  onDelete,
  deleting,
}: {
  doc: DocumentSummary;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
  deleting: boolean;
}) {
  const Icon = doc.doc_type === 'contract' ? FileText : ReceiptText;
  // Thumbs may not exist yet (freshly ingested) or may 404; fall back to the icon
  // instead of the browser's broken-image glyph.
  const [thumbFailed, setThumbFailed] = useState(false);
  const thumb =
    doc.page_count > 0 && !thumbFailed
      ? fileUrl(`/files/${doc.id}/thumbs/page-001.png`)
      : undefined;

  return (
    <div className="group/doc relative">
      {/* Full-card open target. The delete control is a sibling (not nested) to
          keep the HTML valid and stop its clicks reaching this button. */}
      <button
        type="button"
        onClick={() => onOpen(doc.id)}
        disabled={deleting}
        className={cn(
          'flex w-full flex-col overflow-hidden rounded-xl bg-card text-left ring-1 ring-foreground/10 transition-all',
          'hover:ring-brand/40 hover:shadow-sm focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none',
          deleting && 'pointer-events-none opacity-50',
        )}
      >
        <div className="flex aspect-4/3 items-center justify-center overflow-hidden border-b bg-muted/40">
          {thumb ? (
            <img
              src={thumb}
              alt={doc.filename}
              loading="lazy"
              onError={() => setThumbFailed(true)}
              className="size-full object-cover object-top"
            />
          ) : (
            <Icon className="size-10 text-muted-foreground/50" />
          )}
        </div>

        <div className="flex flex-col gap-2 p-3">
          <div className="flex items-center gap-2">
            <Icon className="size-4 shrink-0 text-muted-foreground" />
            <span className="truncate text-sm font-medium" title={doc.filename}>
              {doc.filename}
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            {doc.doc_type && (
              <Badge variant="secondary" className="capitalize">
                {doc.doc_type}
              </Badge>
            )}
            <Badge
              variant="outline"
              className={cn(statusBadgeClass(doc.status))}
            >
              {STATUS_LABEL[doc.status]}
            </Badge>
          </div>
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{formatDate(doc.created_at)}</span>
            <span className="font-mono">
              {doc.page_count} pg{doc.page_count === 1 ? '' : 's'}
            </span>
          </div>
        </div>
      </button>

      {/* Delete — confirmation gated. */}
      <AlertDialog>
        <AlertDialogTrigger
          aria-label={`Delete ${doc.filename}`}
          disabled={deleting}
          className={cn(
            'absolute top-2 right-2 z-10 flex size-7 items-center justify-center rounded-lg bg-background/80 text-muted-foreground backdrop-blur transition-all',
            'hover:bg-destructive/10 hover:text-destructive focus-visible:ring-3 focus-visible:ring-destructive/20 focus-visible:outline-none',
            'opacity-0 group-hover/doc:opacity-100 focus-visible:opacity-100 data-[state=open]:opacity-100',
            deleting && 'pointer-events-none',
          )}
        >
          {deleting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <Trash2 className="size-4" />
          )}
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete this document?</AlertDialogTitle>
            <AlertDialogDescription>
              <span className="font-medium text-foreground">
                {doc.filename}
              </span>{' '}
              and all of its pipeline results and files will be permanently
              removed. This can't be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              className="bg-destructive text-white hover:bg-destructive/90"
              onClick={() => onDelete(doc.id)}
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

export function DocumentLibrary() {
  const { openDocument } = usePipelineContext();
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // A set, not a single id: deletes are independent and can overlap, so one
  // in-flight delete must not clear another's spinner.
  const [deletingIds, setDeletingIds] = useState<ReadonlySet<string>>(
    () => new Set(),
  );
  const [deletingAll, setDeletingAll] = useState(false);

  // Used by the Retry button and the post-delete resync (both event-driven, so a
  // synchronous loading flip here is fine).
  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setDocs(await listDocuments());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : LOAD_ERROR);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch: state is only set after the await (or on unmount-safe paths),
  // so it doesn't trigger the cascading-render lint on synchronous effect setState.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const data = await listDocuments();
        if (!cancelled) setDocs(data);
      } catch (e) {
        if (!cancelled)
          setError(e instanceof ApiError ? e.message : LOAD_ERROR);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleDelete = useCallback(
    async (id: string) => {
      setDeletingIds((prev) => new Set(prev).add(id));
      try {
        await deleteDocument(id);
        setDocs((prev) => prev.filter((d) => d.id !== id));
        toast.success('Document deleted');
      } catch (e) {
        // Already gone (e.g. a concurrent delete won): treat as success.
        if (e instanceof ApiError && e.status === 404) {
          setDocs((prev) => prev.filter((d) => d.id !== id));
        } else {
          const msg =
            e instanceof ApiError ? e.message : 'Could not delete document.';
          toast.error('Delete failed', { description: msg });
          void load(); // resync in case the server state diverged
        }
      } finally {
        setDeletingIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }
    },
    [load],
  );

  const handleDeleteAll = useCallback(async () => {
    setDeletingAll(true);
    try {
      await deleteAllDocuments();
      setDocs([]);
      toast.success('All documents deleted');
    } catch (e) {
      const msg =
        e instanceof ApiError ? e.message : 'Could not delete documents.';
      toast.error('Delete failed', { description: msg });
      void load(); // resync in case the server state diverged
    } finally {
      setDeletingAll(false);
    }
  }, [load]);

  if (loading) {
    return (
      <div className="flex items-center justify-center gap-2 py-6 text-sm text-muted-foreground">
        <Loader2 className="size-4 animate-spin" />
        Loading documents…
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-6 text-center text-sm text-muted-foreground">
        {error}{' '}
        <button
          type="button"
          onClick={() => void load()}
          className="font-medium text-brand hover:underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (docs.length === 0) return null;

  return (
    <section className="w-full space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-sm font-medium">Ingested documents</h2>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">
            {docs.length} total
          </span>
          <AlertDialog>
            <AlertDialogTrigger
              disabled={deletingAll}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-muted-foreground transition-all',
                'hover:bg-destructive/10 hover:text-destructive focus-visible:ring-3 focus-visible:ring-destructive/20 focus-visible:outline-none',
                deletingAll && 'pointer-events-none opacity-50',
              )}
            >
              {deletingAll ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <Trash2 className="size-3.5" />
              )}
              Delete all
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete all documents?</AlertDialogTitle>
                <AlertDialogDescription>
                  All{' '}
                  <span className="font-medium text-foreground">
                    {docs.length}
                  </span>{' '}
                  documents and their pipeline results and files will be
                  permanently removed. This can't be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  className="bg-destructive text-white hover:bg-destructive/90"
                  onClick={() => void handleDeleteAll()}
                >
                  Delete all
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-3">
        {docs.map((doc) => (
          <DocumentCard
            key={doc.id}
            doc={doc}
            onOpen={openDocument}
            onDelete={handleDelete}
            deleting={deletingIds.has(doc.id) || deletingAll}
          />
        ))}
      </div>
    </section>
  );
}
