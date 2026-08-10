import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { resumesApi } from "@/api/resumes";
import { queryKeys } from "@/constants/queryKeys";

export function useResumes() {
  return useQuery({ queryKey: queryKeys.resumes, queryFn: resumesApi.list });
}

export function useResume(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.resume(id ?? ""),
    queryFn: () => resumesApi.get(id as string),
    enabled: !!id,
  });
}

export function useUploadResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ title, file }: { title: string; file: File }) => resumesApi.upload(title, file),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.resumes }),
  });
}

export function useDeleteResume() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => resumesApi.remove(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.resumes }),
  });
}
