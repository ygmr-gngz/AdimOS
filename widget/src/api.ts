const BASE='https://adimos-production.up.railway.app/api/v1/chat'
export class ChatApi{
  constructor(private key:string){}
  private headers(){return {'Content-Type':'application/json','X-Adimos-Key':this.key}}
  async session(){const r=await fetch(`${BASE}/session`,{method:'POST',headers:this.headers(),body:'{"source":"website"}'});if(!r.ok)throw new Error(await r.text());return (await r.json()).session_id as string}
  async message(session_id:string,message:string,contact?:{visitor_name:string;visitor_email:string}){const r=await fetch(`${BASE}/message`,{method:'POST',headers:this.headers(),body:JSON.stringify({session_id,message,...contact})});if(!r.ok)throw new Error(await r.text());return r.json() as Promise<{answer:string;request_contact:boolean}>}
}
