import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import type { ExtractionListItem, ExtractionResponse } from '../types'

export function useExtractionsList() {
  return useQuery({
    queryKey: ['extractions'],
    queryFn: async () => {
      const res = await api.get<ExtractionListItem[]>('/extractions/')
      return res.data
    },
  })
}

export async function fetchExtractionById(id: number) {
  const res = await api.get<ExtractionResponse>(`/extractions/${id}`)
  return res.data
}


