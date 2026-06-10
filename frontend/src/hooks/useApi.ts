import { useEffect, useState } from 'react'

export function useApi<T>(loader: () => Promise<{ data: T }>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)
    loader()
      .then((response) => {
        if (mounted) {
          setData(response.data)
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(err?.message ?? 'Request failed')
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, deps)

  return { data, loading, error, setData }
}

