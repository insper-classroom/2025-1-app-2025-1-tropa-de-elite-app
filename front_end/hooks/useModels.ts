import useSWR from 'swr'
const fetcher = (url: string) => fetch(url).then(r => r.json())

export function useModels() {
  const { data, error } = useSWR('/api/models', fetcher)
  return {
    models: data as Record<string,Record<string,string[]>>|undefined,
    isLoading: !error && !data,
    isError: !!error
  }
}
