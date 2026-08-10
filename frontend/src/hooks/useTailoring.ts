import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tailoringApi } from "@/api/tailoring";
import { queryKeys } from "@/constants/queryKeys";

export function useTailoringHistory() {
  return useQuery({ queryKey: queryKeys.tailoringHistory, queryFn: tailoringApi.history });
}

export function useTailoringSession(sessionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tailoringSession(sessionId ?? ""),
    queryFn: () => tailoringApi.session(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useTailoringResumeVersion(sessionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tailoringResume(sessionId ?? ""),
    queryFn: () => tailoringApi.resumeVersion(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useTailoringCoverLetter(sessionId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.tailoringCoverLetter(sessionId ?? ""),
    queryFn: () => tailoringApi.coverLetter(sessionId as string),
    enabled: !!sessionId,
  });
}

export function useCreateTailoring() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ resumeId, jobId }: { resumeId: string; jobId: string }) =>
      tailoringApi.create(resumeId, jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.tailoringHistory }),
  });
}
