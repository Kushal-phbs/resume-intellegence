import { useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Upload, FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { getApiErrorMessage } from "@/api/client";
import { useUploadResume } from "@/hooks/useResumes";

// Mirrors backend allowed extensions (resume_allowed_extensions_csv default: pdf,doc,docx)
const ACCEPTED_EXT = [".pdf", ".doc", ".docx"];

const schema = z.object({
  title: z.string().min(1, "Title is required").max(255),
});
type FormValues = z.infer<typeof schema>;

export function UploadResumeForm({ onSuccess }: { onSuccess?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const upload = useUploadResume();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const pickFile = (f: File | null) => {
    setFileError(null);
    if (!f) return setFile(null);
    const ext = "." + f.name.split(".").pop()?.toLowerCase();
    if (!ACCEPTED_EXT.includes(ext)) {
      setFileError(`Unsupported file type. Allowed: ${ACCEPTED_EXT.join(", ")}`);
      setFile(null);
      return;
    }
    setFile(f);
  };

  const onSubmit = (values: FormValues) => {
    if (!file) {
      setFileError("Please choose a resume file");
      return;
    }
    upload.mutate(
      { title: values.title, file },
      {
        onSuccess: () => {
          reset();
          setFile(null);
          if (inputRef.current) inputRef.current.value = "";
          onSuccess?.();
        },
      }
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div>
        <Label htmlFor="title">Resume title</Label>
        <Input id="title" placeholder="Senior Developer Resume" {...register("title")} />
        {errors.title && <p className="mt-1 text-xs text-destructive">{errors.title.message}</p>}
      </div>

      <div>
        <Label>File</Label>
        {!file ? (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="flex w-full flex-col items-center gap-1.5 rounded-md border border-dashed border-border bg-muted/30 py-6 text-sm text-muted-foreground transition-colors hover:bg-muted/60"
          >
            <Upload className="h-5 w-5" />
            Click to choose a PDF, DOC, or DOCX file
          </button>
        ) : (
          <div className="flex items-center gap-2 rounded-md border border-border bg-muted/50 px-3 py-2 text-sm">
            <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="min-w-0 flex-1 truncate">{file.name}</span>
            <button type="button" onClick={() => pickFile(null)} aria-label="Remove file">
              <X className="h-4 w-4 text-muted-foreground hover:text-destructive" />
            </button>
          </div>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_EXT.join(",")}
          className="hidden"
          onChange={(e) => pickFile(e.target.files?.[0] ?? null)}
        />
        {fileError && <p className="mt-1 text-xs text-destructive">{fileError}</p>}
      </div>

      {upload.isError && <ErrorMessage message={getApiErrorMessage(upload.error)} />}

      <Button type="submit" className="w-full" isLoading={upload.isPending}>
        <Upload className="h-4 w-4" />
        Upload Resume
      </Button>
    </form>
  );
}
