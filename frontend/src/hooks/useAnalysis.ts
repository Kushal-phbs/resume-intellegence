import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analysisApi } from "@/api/analysis";
import { queryKeys } from "@/constants/queryKeys";

export function useLatestAnalysis(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.analysis(resumeId ?? ""),
    queryFn: () => analysisApi.latest(resumeId as string),
    enabled: !!resumeId,
    retry: false, // a 404 here just means "no analysis yet" — don't retry-spam it
  });
}

export function useAnalysisHistory(resumeId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.analysisHistory(resumeId ?? ""),
    queryFn: () => analysisApi.history(resumeId as string),
    enabled: !!resumeId,
  });
}

export function useRunAnalysis(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => analysisApi.run(resumeId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis(resumeId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysisHistory(resumeId) });
    },
  });
}

export function useDeleteAnalysis(resumeId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (analysisId: string) => analysisApi.remove(analysisId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.analysis(resumeId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.analysisHistory(resumeId) });
    },
  });
}
