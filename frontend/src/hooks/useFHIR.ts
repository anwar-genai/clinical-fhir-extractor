import { useMutation } from '@tanstack/react-query'
import { api } from '../lib/api'
import { FHIRBundle } from '../types'
import toast from 'react-hot-toast'

export function useFHIRExtraction() {
  const mutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post<FHIRBundle>('/extract-fhir', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })
      return response.data
    },
    onSuccess: () => {
      toast.success('FHIR data extracted successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Extraction failed')
    },
  })

  return {
    extractFHIR: mutation.mutate,
    isLoading: mutation.isPending,
    data: mutation.data,
    error: mutation.error,
  }
}
