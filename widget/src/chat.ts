import {ChatApi} from './api'
import {styles} from './styles'
import {message,template} from './ui'

const script=document.currentScript as HTMLScriptElement|null
const key=script?.dataset.adimosKey
if(!key){console.error('[AdimOS Widget] data-adimos-key eksik')}else{
  const host=document.createElement('div');host.id='adimos-chat-widget';document.body.append(host)
  const root=host.attachShadow({mode:'open'});root.innerHTML=`<style>${styles}</style>${template()}`
  const panel=root.querySelector('.panel') as HTMLElement,bubble=root.querySelector('.bubble') as HTMLButtonElement,close=root.querySelector('.close') as HTMLButtonElement,form=root.querySelector('.form') as HTMLFormElement,contact=root.querySelector('.contact') as HTMLFormElement,input=root.querySelector('.input') as HTMLInputElement,messages=root.querySelector('.messages') as HTMLElement
  const api=new ChatApi(key);let session='';bubble.onclick=()=>panel.classList.add('open');close.onclick=()=>panel.classList.remove('open')
  message(messages,'assistant','Merhaba! SGS ve muhasebe konularında nasıl yardımcı olabilirim?')
  form.onsubmit=async e=>{e.preventDefault();const text=input.value.trim();if(!text)return;input.value='';message(messages,'user',text);try{session=session||await api.session();const result=await api.message(session,text);message(messages,'assistant',result.answer);if(result.request_contact){message(messages,'assistant','Size daha iyi yardımcı olabilmem için adınızı ve e-posta adresinizi paylaşır mısınız?');contact.classList.add('show')}}catch{message(messages,'assistant','Şu an yanıt veremiyorum. Lütfen daha sonra tekrar deneyin.')}}
  contact.onsubmit=async e=>{e.preventDefault();const data=new FormData(contact),name=String(data.get('name')||''),email=String(data.get('email')||'');try{await api.message(session,'İletişim bilgilerimi paylaşıyorum.',{visitor_name:name,visitor_email:email});contact.classList.remove('show');message(messages,'assistant','Teşekkürler, bilgileriniz kaydedildi.')}catch{message(messages,'assistant','Bilgiler kaydedilemedi. Lütfen tekrar deneyin.')}}
}
