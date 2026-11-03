import { useEffect, useState } from 'react'

type Metric = { value: number | null; unit: string | null; missing_reason: string | null }
type Item = {
  platform: string
  content_id: string
  title: string | null
  group_label: string | null
  collected_at: string | null
  source: string | null
  metrics: Record<string, Metric>
}
type PlatformStatus = { platform: string; content_count: number; last_success_at: string | null }

const PLATFORM_NAMES: Record<string, string> = { douyin: '抖音', xiaohongshu: '小红书' }

function formatMetric(m: Metric | undefined) {
  if (!m) return ''
  if (m.value === null) return `— (${m.missing_reason})`
  return m.unit === 'ratio' ? `${(m.value * 100).toFixed(1)}%` : m.value.toLocaleString()
}

export default function App() {
  const [items, setItems] = useState<Item[]>([])
  const [platforms, setPlatforms] = useState<PlatformStatus[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([fetch('/api/contents'), fetch('/api/status')])
      .then(async ([c, s]) => {
        if (!c.ok || !s.ok) throw new Error(`HTTP ${c.status}/${s.status}`)
        setItems((await c.json()).items)
        setPlatforms((await s.json()).platforms)
      })
      .catch((e: Error) => setError(e.message))
  }, [])

  const metricNames = [...new Set(items.flatMap((i) => Object.keys(i.metrics)))].sort()

  return (
    <main>
      <h1>tracepost</h1>
      <p className="muted">本地快照，数据不离开本机。空值标注缺失原因，真实的 0 原样显示。</p>
      {error && <p role="alert">无法读取本地 API：{error}</p>}
      <section className="status" aria-label="同步状态">
        {platforms.map((p) => (
          <div key={p.platform}>
            <strong>{PLATFORM_NAMES[p.platform] ?? p.platform}</strong> · {p.content_count} 条内容
            <br />
            <span className="muted">上次成功同步：{p.last_success_at ?? '从未'}</span>
          </div>
        ))}
      </section>
      {items.length === 0 && !error ? (
        <p>还没有数据。可先运行 <code>tracepost --db demo.sqlite demo</code> 查看合成示例。</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>平台</th>
              <th>内容</th>
              <th>跨平台分组</th>
              <th>观测时间</th>
              {metricNames.map((n) => (
                <th key={n}>{n}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((i) => (
              <tr key={`${i.platform}:${i.content_id}`}>
                <td>{PLATFORM_NAMES[i.platform] ?? i.platform}</td>
                <td>{i.title ?? i.content_id}</td>
                <td>{i.group_label ?? ''}</td>
                <td className="muted">{i.collected_at ?? '未观测'}</td>
                {metricNames.map((n) => (
                  <td key={n} className="num">
                    {formatMetric(i.metrics[n])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  )
}
