import useSWR from 'swr'
const fetcher = (url: string) => fetch(url).then(r => r.json())

export function useModels() {
  // antes: fetch('http://localhost:8000/api/modelos')
  // agora:
  const { data, error } = useSWR('/api/modelos', fetcher)
  return {
    models: data as any,
    isLoading: !error && !data,
    isError: !!error
  }
}
