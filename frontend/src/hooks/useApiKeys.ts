import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { ApiKeyCreate, ApiKeyListItem } from '../types'
import toast from 'react-hot-toast'

export function useApiKeys() {
  const queryClient = useQueryClient()

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: async () => {
      const response = await api.get<ApiKeyListItem[]>('/auth/api-keys')
      return response.data
    },
  })

  const createMutation = useMutation({
    mutationFn: async (data: ApiKeyCreate) => {
      const response = await api.post('/auth/api-keys', data)
      return response.data
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API key created successfully!')
      return data
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create API key')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (keyId: number) => {
      await api.delete(`/auth/api-keys/${keyId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
      toast.success('API key deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete API key')
    },
  })

  return {
    apiKeys,
    isLoading,
    createApiKey: createMutation.mutate,
    deleteApiKey: deleteMutation.mutate,
    isCreating: createMutation.isPending,
    isDeleting: deleteMutation.isPending,
  }
}
