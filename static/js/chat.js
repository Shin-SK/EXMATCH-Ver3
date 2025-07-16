// @ts-nocheck   ← VSCode の型チェックも黙らせたいなら付けても可

document.addEventListener('DOMContentLoaded', () => {
  const cfg    = window.chatConfig;
  const list   = document.getElementById('messages');
  let   lastId = Number(cfg.lastId) || 0;

  /* ---------- メッセージ描画 ---------- */
  function append(m){
    const isMe = (m.sender === cfg.current);
    const li   = document.createElement('li');
    li.className = isMe ? 'me' : 'you';

    if(!isMe){
      li.insertAdjacentHTML('beforeend',
        `<img class="avatar" src="${m.avatar}" alt="">`);
    }
    li.insertAdjacentHTML('beforeend',
      `<div class="bubble">${m.text}</div>`);

    list.appendChild(li);
    li.scrollIntoView({block:'end'});
    lastId = m.id;
  }

  /* ---------- ポーリング ---------- */
  function poll(){
    fetch(`${cfg.api}?after=${lastId}`)
      .then(r => r.json())
      .then(({messages}) => messages.forEach(append))
      .catch(console.error);
  }
  poll();
  setInterval(poll, 5_000);

  /* ---------- 送信 ---------- */
  document.getElementById('chatForm')
          .addEventListener('submit', async e => {
    e.preventDefault();

    const textarea = document.getElementById('msgInput');
    const text     = textarea.value.trim();
    if(!text) return;

    if(!cfg.canSend){
      if(cfg.needPlan)   document.getElementById('upgradeModal').style.display = 'flex';
      if(cfg.needVerify) document.getElementById('verifyModal').style.display  = 'flex';
      return;
    }

    try{
      const res = await fetch(cfg.postUrl, {
        method : 'POST',
        credentials: 'same-origin',
        headers: {
          'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body : new URLSearchParams({text})
      });

      if(!res.ok){
        const j = await res.json().catch(()=>({msg:'送信に失敗しました'}));
        alert(j.msg);
        return;
      }

      textarea.value = '';
      poll();                    // すぐ反映
    }catch(err){
      console.error(err);
      alert('通信に失敗しました');
    }
  });

  /* ---------- モーダル close ---------- */
  document.querySelectorAll('.upgrade-modal .close-btn')
          .forEach(btn =>
            btn.addEventListener('click', () =>
              btn.closest('.upgrade-modal').style.display = 'none'
            ));
});
