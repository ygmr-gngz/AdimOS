;(function () {
  'use strict'

  var script = document.currentScript
  var siteId = (script && script.getAttribute('data-site-id')) || 'default'
  var title = (script && script.getAttribute('data-title')) || 'Asistan'
  var baseUrl = (script && script.getAttribute('data-base-url')) || 'https://adimos.vercel.app'

  var isOpen = false
  var storageKey = 'adimos_widget_open_' + siteId

  // --- Floating button ---
  var btn = document.createElement('button')
  btn.id = 'adimos-widget-btn'
  btn.setAttribute('aria-label', 'Asistanı aç')
  btn.style.cssText = [
    'position:fixed',
    'bottom:20px',
    'right:20px',
    'width:56px',
    'height:56px',
    'border-radius:50%',
    'background:linear-gradient(135deg,#3b5bdb,#7048e8)',
    'color:#fff',
    'border:none',
    'cursor:pointer',
    'z-index:2147483646',
    'display:flex',
    'align-items:center',
    'justify-content:center',
    'box-shadow:0 4px 24px rgba(59,91,219,0.45)',
    'transition:transform 0.2s,box-shadow 0.2s',
    'font-family:system-ui,sans-serif',
  ].join(';')

  btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>'

  btn.addEventListener('mouseenter', function () {
    btn.style.transform = 'scale(1.08)'
    btn.style.boxShadow = '0 6px 32px rgba(59,91,219,0.6)'
  })
  btn.addEventListener('mouseleave', function () {
    btn.style.transform = 'scale(1)'
    btn.style.boxShadow = '0 4px 24px rgba(59,91,219,0.45)'
  })

  // --- iframe ---
  var iframe = document.createElement('iframe')
  var src = baseUrl + '/widget?siteId=' + encodeURIComponent(siteId) + '&title=' + encodeURIComponent(title)
  iframe.src = src
  iframe.setAttribute('title', title)
  iframe.setAttribute('allow', 'microphone')
  iframe.style.cssText = [
    'position:fixed',
    'bottom:86px',
    'right:20px',
    'width:380px',
    'height:600px',
    'border:none',
    'border-radius:16px',
    'z-index:2147483645',
    'box-shadow:0 20px 60px rgba(0,0,0,0.25)',
    'display:none',
    'opacity:0',
    'transform:translateY(12px)',
    'transition:opacity 0.2s,transform 0.2s',
  ].join(';')

  // --- Toggle ---
  function openWidget() {
    isOpen = true
    iframe.style.display = 'block'
    requestAnimationFrame(function () {
      iframe.style.opacity = '1'
      iframe.style.transform = 'translateY(0)'
    })
    btn.setAttribute('aria-label', 'Asistanı kapat')
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>'
    try { sessionStorage.setItem(storageKey, '1') } catch (e) {}
  }

  function closeWidget() {
    isOpen = false
    iframe.style.opacity = '0'
    iframe.style.transform = 'translateY(12px)'
    setTimeout(function () { iframe.style.display = 'none' }, 210)
    btn.setAttribute('aria-label', 'Asistanı aç')
    btn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg>'
    try { sessionStorage.removeItem(storageKey) } catch (e) {}
  }

  btn.addEventListener('click', function () {
    isOpen ? closeWidget() : openWidget()
  })

  // Restore state
  try {
    if (sessionStorage.getItem(storageKey)) openWidget()
  } catch (e) {}

  document.body.appendChild(iframe)
  document.body.appendChild(btn)

  // Mobile: narrow iframe
  function adjustForMobile() {
    if (window.innerWidth < 420) {
      iframe.style.width = (window.innerWidth - 16) + 'px'
      iframe.style.right = '8px'
      btn.style.right = '12px'
      iframe.style.bottom = '80px'
    } else {
      iframe.style.width = '380px'
      iframe.style.right = '20px'
      btn.style.right = '20px'
      iframe.style.bottom = '86px'
    }
  }
  adjustForMobile()
  window.addEventListener('resize', adjustForMobile)
})()
