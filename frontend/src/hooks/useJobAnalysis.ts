import { jobAnalysisApi } from "@/api/jobAnalysis";
import { queryKeys } from "@/constants/queryKeys";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export function useJobAnalysisHistory() {
  return useQuery({ queryKey: queryKeys.jobAnalysisHistory, queryFn: jobAnalysisApi.history });
}

export function useJobAnalysis(analysisId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.jobAnalysis(analysisId ?? ""),
    queryFn: () => jobAnalysisApi.get(analysisId as string),
    enabled: !!analysisId,
  });
}

export function useRunJobAnalysis() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ resumeId, jobId }: { resumeId: string; jobId: string }) =>
      jobAnalysisApi.run(resumeId, jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobAnalysisHistory });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
}
