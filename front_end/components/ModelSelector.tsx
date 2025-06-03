'use client'
import { useState, useEffect } from 'react'
import { useModels } from '../hooks/useModels'

export default function ModelSelector({ onChange }: { onChange:(m:string,v:string,ver:string)=>void }) {
  const { models, isLoading, isError } = useModels()
  const [mnames, setMnames]   = useState<string[]>([])
  const [variants, setVariants] = useState<string[]>([])
  const [versions, setVersions] = useState<string[]>([])
  const [selModel, setSelModel]     = useState('')
  const [selVariant, setSelVariant] = useState('')
  const [selVersion, setSelVersion] = useState('')

  useEffect(()=>{
    if(models){
      const ms = Object.keys(models)
      setMnames(ms)
      setSelModel(ms[0])
    }
  },[models])

  useEffect(()=>{
    if(models && selModel){
      const vs = Object.keys(models[selModel])
      setVariants(vs)
      setSelVariant(vs[0])
    }
  },[models, selModel])

  useEffect(()=>{
    if(models && selModel && selVariant){
      const ver = models[selModel][selVariant]
      setVersions(ver)
      setSelVersion(ver[0]||'')
    }
  },[models, selModel, selVariant])

  useEffect(()=>{
    if(selModel && selVariant && selVersion){
      onChange(selModel, selVariant, selVersion)
    }
  },[selModel, selVariant, selVersion,onChange])

  if(isLoading) return <p>Carregando modelos…</p>
  if(isError)   return <p>Erro ao carregar modelos</p>

  return (
    <div className="space-y-2">
      <div>
        <label>Modelo</label>
        <select value={selModel} onChange={e=>setSelModel(e.target.value)}>
          {mnames.map(m=><option key={m}>{m}</option>)}
        </select>
      </div>
      <div>
        <label>Variante</label>
        <select value={selVariant} onChange={e=>setSelVariant(e.target.value)}>
          {variants.map(v=><option key={v}>{v}</option>)}
        </select>
      </div>
      <div>
        <label>Versão</label>
        <select value={selVersion} onChange={e=>setSelVersion(e.target.value)}>
          {versions.map(ver=><option key={ver}>{ver}</option>)}
        </select>
      </div>
    </div>
  )
}
