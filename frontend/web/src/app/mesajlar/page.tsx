'use client'

import { FormEvent, useCallback, useEffect, useState } from 'react'
import AppShell from '@/components/layout/AppShell'
import apiClient from '@/lib/api-client'
import { supabase } from '@/lib/supabase'

interface Session { id:string; source:string; visitor_name?:string; visitor_email?:string; status:string; last_message_at?:string }
interface Message { id:string; role:string; content:string; created_at:string }

export default function MessagesPage(){
  const [sessions,setSessions]=useState<Session[]>([]),[selected,setSelected]=useState<Session|null>(null),[messages,setMessages]=useState<Message[]>([]),[draft,setDraft]=useState('')
  const loadSessions=useCallback(async()=>{const {data}=await apiClient.get('/messages/sessions');setSessions(data)},[])
  const loadMessages=useCallback(async(id:string)=>{const {data}=await apiClient.get(`/messages/sessions/${id}`);setMessages(data)},[])
  useEffect(()=>{loadSessions()},[loadSessions])
  useEffect(()=>{if(selected)loadMessages(selected.id)},[selected,loadMessages])
  useEffect(()=>{const channel=supabase.channel('chat_messages').on('postgres_changes',{event:'INSERT',schema:'public',table:'chat_messages'},payload=>{const row=payload.new as Message&{session_id:string};loadSessions();if(row.session_id===selected?.id)setMessages(current=>[...current,row])}).subscribe();return()=>{supabase.removeChannel(channel)}},[selected?.id,loadSessions])
  const reply=async(e:FormEvent)=>{e.preventDefault();if(!selected||!draft.trim())return;await apiClient.post(`/messages/sessions/${selected.id}/reply`,{content:draft});setDraft('');await loadMessages(selected.id)}
  const toggleMode=async()=>{if(!selected)return;const manual=selected.status!=='manual';const {data}=await apiClient.post(`/messages/sessions/${selected.id}/mode`,{manual});setSelected(data);loadSessions()}
  return <AppShell><div style={{height:'calc(100vh - 110px)',display:'grid',gridTemplateColumns:'330px 1fr',background:'#fff',border:'1px solid #e2e8f0',borderRadius:14,overflow:'hidden'}}>
    <aside style={{borderRight:'1px solid #e2e8f0',overflowY:'auto'}}>{sessions.map(s=><button key={s.id} onClick={()=>setSelected(s)} style={{width:'100%',textAlign:'left',border:0,borderBottom:'1px solid #f1f5f9',background:selected?.id===s.id?'#eff6ff':'#fff',padding:16,cursor:'pointer'}}><strong>{s.visitor_name||'Anonim'}</strong><div style={{fontSize:12,color:'#64748b'}}>{s.source} · {s.status}</div><time style={{fontSize:11,color:'#94a3b8'}}>{s.last_message_at?new Date(s.last_message_at).toLocaleString('tr-TR'):''}</time></button>)}</aside>
    <section style={{display:'flex',flexDirection:'column'}}>{selected?<><header style={{padding:16,borderBottom:'1px solid #e2e8f0',display:'flex',justifyContent:'space-between'}}><span><strong>{selected.visitor_name||'Anonim'}</strong> · {selected.source}</span><button onClick={toggleMode}>{selected.status==='manual'?'Bota devret':'Manuel moda al'}</button></header><div style={{flex:1,overflowY:'auto',padding:20,display:'flex',flexDirection:'column',gap:10}}>{messages.map(m=><div key={m.id} style={{alignSelf:m.role==='user'?'flex-end':'flex-start',maxWidth:'75%',background:m.role==='user'?'#1b458c':'#f4f6fa',color:m.role==='user'?'#fff':'#1b2a41',padding:'10px 13px',borderRadius:12}}>{m.content}</div>)}</div><form onSubmit={reply} style={{display:'flex',gap:8,padding:14,borderTop:'1px solid #e2e8f0'}}><input value={draft} onChange={e=>setDraft(e.target.value)} style={{flex:1,padding:10}} placeholder="Manuel yanıt…"/><button>Gönder</button></form></>:<div style={{margin:'auto',color:'#94a3b8'}}>Bir oturum seçin.</div>}</section>
  </div></AppShell>
}
