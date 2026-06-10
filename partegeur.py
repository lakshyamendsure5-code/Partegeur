from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid, time, threading, os, json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'partegeur-redrock-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

USERS_FILE = 'users.json'
GROUPS_FILE = 'groups.json'

def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def save_users_to_file():
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)
    except: pass

def load_groups():
    try:
        if os.path.exists(GROUPS_FILE):
            with open(GROUPS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def save_groups_to_file():
    try:
        with open(GROUPS_FILE, 'w') as f:
            json.dump(groups, f)
    except: pass

users = load_users()
messages = []
groups = load_groups()

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="black"/>
<meta name="apple-mobile-web-app-title" content="PARTEGEUR"/>
<meta name="theme-color" content="#0a0a0a"/>
<link rel="manifest" href="/manifest.json"/>
<title>PARTEGEUR by REDrock</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;height:100vh;overflow:hidden;}
.screen{display:none;flex-direction:column;height:100vh;}
.screen.active{display:flex;}
input{background:#141414;border:1px solid #222;border-radius:10px;padding:13px 16px;color:#fff;font-size:14px;width:100%;outline:none;margin-bottom:12px;}
button{cursor:pointer;border:none;border-radius:10px;font-size:14px;}
.btn-red{background:#e8000d;color:#fff;padding:14px;width:100%;font-weight:700;font-size:15px;margin-bottom:12px;}
.btn-dark{background:#1a1a1a;color:#888;padding:14px;width:100%;border:1px solid #222;}
.header{padding:14px 18px;background:#0f0f0f;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:10;}
.back-btn{background:none;color:#e8000d;font-size:26px;padding:0 4px;}
.avatar{width:40px;height:40px;border-radius:20px;background:#e8000d22;border:2px solid #e8000d44;display:flex;align-items:center;justify-content:center;color:#e8000d;font-weight:700;font-size:16px;flex-shrink:0;overflow:hidden;}
.avatar img{width:100%;height:100%;object-fit:cover;border-radius:20px;}
.avatar-lg{width:80px;height:80px;border-radius:40px;background:#e8000d22;border:3px solid #e8000d;display:flex;align-items:center;justify-content:center;color:#e8000d;font-weight:700;font-size:32px;overflow:hidden;cursor:pointer;position:relative;margin:0 auto 16px;}
.avatar-lg img{width:100%;height:100%;object-fit:cover;border-radius:40px;}
.avatar-lg .edit-overlay{position:absolute;bottom:0;left:0;right:0;background:#00000099;text-align:center;font-size:11px;color:#fff;padding:4px;border-radius:0 0 40px 40px;}
.card{background:#111;border:1px solid #1e1e1e;border-radius:14px;padding:16px 18px;margin-bottom:10px;cursor:pointer;display:flex;align-items:center;gap:14px;}
.badge{background:#e8000d;color:#fff;border-radius:20px;padding:2px 8px;font-size:12px;font-weight:700;}
.msg-input-row{padding:10px 14px;background:#0f0f0f;display:flex;gap:8px;align-items:center;border-top:1px solid #1a1a1a;}
.msg-input-row input{margin:0;flex:1;}
.send-btn{background:#e8000d;color:#fff;padding:10px 16px;font-weight:700;font-size:16px;}
.icon-btn{background:#1a1a1a;color:#888;padding:10px 12px;border:1px solid #222;font-size:16px;}
.messages{flex:1;overflow-y:auto;padding:12px 16px;}
.bubble-wrap{display:flex;margin-bottom:10px;gap:8px;}
.bubble-wrap.mine{justify-content:flex-end;}
.bubble{max-width:75%;padding:10px 14px;border-radius:18px;font-size:14px;}
.bubble.mine{background:#e8000d;border-bottom-right-radius:4px;}
.bubble.theirs{background:#1a1a1a;border-bottom-left-radius:4px;}
.bubble .time{font-size:10px;color:#ffffff55;margin-top:4px;text-align:right;}
.bubble.theirs .time{color:#444;}
.sender-name{font-size:11px;color:#e8000d;margin-bottom:3px;margin-left:4px;}
.scroll-list{flex:1;overflow-y:auto;padding:16px;}
.logo{font-size:34px;font-weight:900;color:#e8000d;letter-spacing:3px;font-family:Georgia,serif;}
.sub{color:#444;font-size:11px;letter-spacing:5px;margin-bottom:28px;}
.section-label{color:#444;font-size:11px;letter-spacing:3px;margin-bottom:12px;margin-top:16px;}
.photo-prev{padding:8px 14px;background:#111;display:flex;align-items:center;gap:10px;border-top:1px solid #1a1a1a;}
.photo-prev img{height:50px;border-radius:6px;}
.rm-photo{background:none;color:#e8000d;font-size:18px;}
img.chat-img{max-width:180px;border-radius:8px;}
.splash{background:#0a0a0a;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;}
.avatar-sm{width:32px;height:32px;border-radius:16px;overflow:hidden;background:#e8000d22;border:2px solid #e8000d44;display:flex;align-items:center;justify-content:center;color:#e8000d;font-weight:700;font-size:13px;flex-shrink:0;}
.avatar-sm img{width:100%;height:100%;object-fit:cover;}
</style>
</head>
<body>

<!-- SPLASH -->
<div class="screen active" id="splash">
  <div class="splash">
    <div class="logo">PARTEGEUR</div>
    <div class="sub">by REDrock</div>
    <div style="color:#333;font-size:12px;margin-top:20px;">share once. vanish forever.</div>
  </div>
</div>

<!-- JOIN -->
<div class="screen" id="join">
  <div style="padding:32px 28px;flex:1;display:flex;flex-direction:column;justify-content:center;overflow-y:auto;">
    <div class="logo">PARTEGEUR</div>
    <div class="sub">by REDrock</div>

    <!-- Profile Photo Upload -->
    <div style="text-align:center;margin-bottom:20px;">
      <div class="avatar-lg" id="avatar-preview" onclick="document.getElementById('profile-photo-input').click()">
        <span id="avatar-initials">👤</span>
        <div class="edit-overlay">tap to add photo</div>
      </div>
      <input type="file" id="profile-photo-input" accept="image/*" style="display:none;" onchange="handleProfilePhoto(event)"/>
      <div style="color:#444;font-size:11px;">Profile Photo (optional)</div>
    </div>

    <input id="j-name" placeholder="Your name" oninput="updateInitials()"/>
    <div style="display:flex;gap:8px;margin-bottom:12px;">
      <button id="ct-phone" onclick="setContactType('phone')" style="flex:1;padding:9px;background:#e8000d;color:#fff;border-radius:8px;font-size:12px;border:1px solid #e8000d;">📞 Phone</button>
      <button id="ct-address" onclick="setContactType('address')" style="flex:1;padding:9px;background:#1a1a1a;color:#555;border-radius:8px;font-size:12px;border:1px solid #222;">🏠 Address</button>
    </div>
    <input id="j-contact" placeholder="Your phone number"/>
    <div id="j-err" style="color:#e8000d;font-size:12px;margin-bottom:10px;display:none;"></div>
    <button class="btn-red" onclick="doJoin()">Enter PARTEGEUR →</button>
    <div style="color:#333;font-size:11px;text-align:center;margin-top:12px;">Messages vanish after being viewed once.<br/>Accounts saved permanently.</div>
  </div>
</div>

<!-- HOME -->
<div class="screen" id="home">
  <div class="header">
    <div><div class="logo" style="font-size:20px;letter-spacing:2px;">PARTEGEUR</div><div style="color:#444;font-size:10px;">by REDrock</div></div>
    <div style="display:flex;align-items:center;gap:10px;">
      <div id="home-avatar" class="avatar" style="width:34px;height:34px;border-radius:17px;"></div>
      <div id="home-greeting" style="color:#888;font-size:13px;"></div>
    </div>
  </div>
  <div class="scroll-list">
    <div class="section-label">QUICK ACCESS</div>
    <div class="card" onclick="showScreen('dm-list')">
      <div style="font-size:26px;">💬</div>
      <div style="flex:1;"><div style="color:#fff;font-weight:600;">Direct Messages</div><div id="dm-sub" style="color:#555;font-size:12px;margin-top:2px;">Chat privately</div></div>
      <div id="dm-badge" class="badge" style="display:none;"></div>
      <div style="color:#333;">›</div>
    </div>
    <div class="card" onclick="showScreen('groups')">
      <div style="font-size:26px;">👥</div>
      <div style="flex:1;"><div style="color:#fff;font-weight:600;">Groups</div><div id="grp-sub" style="color:#555;font-size:12px;margin-top:2px;">Create or join a group</div></div>
      <div style="color:#333;">›</div>
    </div>
    <div class="card" onclick="showScreen('people')">
      <div style="font-size:26px;">👤</div>
      <div style="flex:1;"><div style="color:#fff;font-weight:600;">Find People</div><div id="ppl-sub" style="color:#555;font-size:12px;margin-top:2px;">See who's here</div></div>
      <div style="color:#333;">›</div>
    </div>
    <div style="background:#0f0f0f;border:1px solid #1a1a1a;border-radius:14px;padding:16px;margin-top:12px;">
      <div style="color:#e8000d;font-size:12px;font-weight:700;margin-bottom:8px;">🔴 HOW IT WORKS</div>
      <div style="color:#555;font-size:12px;line-height:1.8;">
        • Messages seen <span style="color:#888">once</span>, then deleted forever<br/>
        • Photos vanish after receiver opens them<br/>
        • Accounts saved permanently<br/>
        • Share link with anyone to start chatting
      </div>
    </div>
    <div style="text-align:center;margin-top:20px;">
      <div style="color:#333;font-size:11px;margin-bottom:6px;">Share app link:</div>
      <div id="app-link" style="color:#e8000d;font-size:12px;word-break:break-all;background:#111;padding:10px;border-radius:8px;cursor:pointer;" onclick="copyLink()"></div>
      <div id="copy-msg" style="color:#00cc44;font-size:11px;margin-top:4px;display:none;">Copied!</div>
    </div>
  </div>
</div>

<!-- PEOPLE -->
<div class="screen" id="people">
  <div class="header">
    <button class="back-btn" onclick="showScreen('home')">‹</button>
    <div style="color:#fff;font-weight:700;">Find People</div>
    <div></div>
  </div>
  <div class="scroll-list" id="people-list"></div>
</div>

<!-- DM LIST -->
<div class="screen" id="dm-list">
  <div class="header">
    <button class="back-btn" onclick="showScreen('home')">‹</button>
    <div style="color:#fff;font-weight:700;">Direct Messages</div>
    <div></div>
  </div>
  <div class="scroll-list" id="dm-list-content"></div>
</div>

<!-- CHAT -->
<div class="screen" id="chat">
  <div class="header">
    <button class="back-btn" onclick="showScreen('dm-list')">‹</button>
    <div style="display:flex;align-items:center;gap:10px;">
      <div class="avatar" id="chat-avatar"></div>
      <div><div id="chat-name" style="color:#fff;font-weight:700;font-size:14px;"></div><div style="color:#444;font-size:11px;">vanishes after viewing</div></div>
    </div>
    <div></div>
  </div>
  <div class="messages" id="chat-messages"></div>
  <div id="chat-photo-prev" class="photo-prev" style="display:none;">
    <img id="chat-prev-img" src=""/>
    <button class="rm-photo" onclick="clearPhoto('chat')">✕</button>
  </div>
  <div class="msg-input-row">
    <input type="file" id="chat-file" accept="image/*" style="display:none;" onchange="handlePhoto(event,'chat')"/>
    <button class="icon-btn" onclick="document.getElementById('chat-file').click()">📷</button>
    <input id="chat-input" placeholder="Message..." onkeydown="if(event.key==='Enter')sendDM()"/>
    <button class="send-btn" onclick="sendDM()">↑</button>
  </div>
</div>

<!-- GROUPS -->
<div class="screen" id="groups">
  <div class="header">
    <button class="back-btn" onclick="showScreen('home')">‹</button>
    <div style="color:#fff;font-weight:700;">Groups</div>
    <button style="background:none;color:#e8000d;font-size:24px;" onclick="toggleCreateGroup()">+</button>
  </div>
  <div id="create-group-form" style="display:none;padding:14px 18px;background:#111;border-bottom:1px solid #1a1a1a;">
    <input id="new-group-name" placeholder="Group name"/>
    <div style="display:flex;gap:8px;">
      <button class="btn-red" style="flex:1;margin:0;padding:10px;" onclick="createGroup()">Create</button>
      <button class="btn-dark" style="flex:1;padding:10px;border-radius:10px;" onclick="toggleCreateGroup()">Cancel</button>
    </div>
  </div>
  <div class="scroll-list" id="groups-list"></div>
</div>

<!-- GROUP CHAT -->
<div class="screen" id="group-chat">
  <div class="header">
    <button class="back-btn" onclick="showScreen('groups')">‹</button>
    <div><div id="grp-chat-name" style="color:#fff;font-weight:700;font-size:14px;"></div><div id="grp-chat-members" style="color:#444;font-size:11px;"></div></div>
    <div></div>
  </div>
  <div class="messages" id="grp-messages"></div>
  <div id="grp-photo-prev" class="photo-prev" style="display:none;">
    <img id="grp-prev-img" src=""/>
    <button class="rm-photo" onclick="clearPhoto('grp')">✕</button>
  </div>
  <div class="msg-input-row">
    <input type="file" id="grp-file" accept="image/*" style="display:none;" onchange="handlePhoto(event,'grp')"/>
    <button class="icon-btn" onclick="document.getElementById('grp-file').click()">📷</button>
    <input id="grp-input" placeholder="Message group..." onkeydown="if(event.key==='Enter')sendGroupMsg()"/>
    <button class="send-btn" onclick="sendGroupMsg()">↑</button>
  </div>
</div>

<script>
const socket = io();
let currentUser = null;
let chatTarget = null;
let currentGroup = null;
let contactType = 'phone';
let chatPhoto = null;
let grpPhoto = null;
let profilePhotoData = null;
let pollInterval = null;

function avatarHtml(user, size=40) {
  const r = size/2;
  if(user && user.photo) return `<img src="${user.photo}" style="width:${size}px;height:${size}px;border-radius:${r}px;object-fit:cover;"/>`;
  return `<div style="width:${size}px;height:${size}px;border-radius:${r}px;background:#e8000d22;border:2px solid #e8000d44;display:flex;align-items:center;justify-content:center;color:#e8000d;font-weight:700;font-size:${size*0.4}px;">${user?user.name[0].toUpperCase():'?'}</div>`;
}

function updateInitials() {
  if(profilePhotoData) return;
  const name = document.getElementById('j-name').value.trim();
  document.getElementById('avatar-initials').textContent = name ? name[0].toUpperCase() : '👤';
}

function handleProfilePhoto(e) {
  const file = e.target.files[0]; if(!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    profilePhotoData = ev.target.result;
    const prev = document.getElementById('avatar-preview');
    prev.innerHTML = `<img src="${profilePhotoData}" style="width:80px;height:80px;object-fit:cover;border-radius:40px;"/><div class="edit-overlay">tap to change</div>`;
  };
  reader.readAsDataURL(file);
}

function setContactType(t) {
  contactType = t;
  document.getElementById('ct-phone').style.background = t==='phone'?'#e8000d':'#1a1a1a';
  document.getElementById('ct-phone').style.color = t==='phone'?'#fff':'#555';
  document.getElementById('ct-phone').style.borderColor = t==='phone'?'#e8000d':'#222';
  document.getElementById('ct-address').style.background = t==='address'?'#e8000d':'#1a1a1a';
  document.getElementById('ct-address').style.color = t==='address'?'#fff':'#555';
  document.getElementById('ct-address').style.borderColor = t==='address'?'#e8000d':'#222';
  document.getElementById('j-contact').placeholder = t==='phone'?'Your phone number':'Your home address';
}

function showError(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg; el.style.display = 'block';
  setTimeout(()=>el.style.display='none', 3000);
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  if(id==='home') refreshHome();
  if(id==='people') loadPeople();
  if(id==='dm-list') loadDMList();
  if(id==='groups') loadGroups();
  if(id==='chat') startChatPoll();
  if(id==='group-chat') startGrpPoll();
  if(id!=='chat'&&id!=='group-chat') stopPoll();
}

function doJoin() {
  const name = document.getElementById('j-name').value.trim();
  const contact = document.getElementById('j-contact').value.trim();
  if(!name) return showError('j-err','Enter your name');
  if(!contact) return showError('j-err','Enter your phone or address');
  fetch('/api/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,contact,contactType,photo:profilePhotoData})})
  .then(r=>r.json()).then(data=>{
    if(data.user){ currentUser=data.user; socket.emit('join_user',{userId:currentUser.id}); showScreen('home'); }
  });
}

function refreshHome() {
  if(!currentUser) return;
  document.getElementById('home-greeting').textContent = currentUser.name;
  document.getElementById('home-avatar').innerHTML = avatarHtml(currentUser, 34);
  document.getElementById('app-link').textContent = window.location.origin;
  fetch('/api/unread/'+currentUser.id).then(r=>r.json()).then(d=>{
    const badge = document.getElementById('dm-badge');
    if(d.count>0){badge.textContent=d.count;badge.style.display='inline-block';}
    else badge.style.display='none';
    document.getElementById('dm-sub').textContent = d.count>0?d.count+' unread':'Chat privately';
  });
  fetch('/api/users').then(r=>r.json()).then(d=>{
    document.getElementById('ppl-sub').textContent = (d.users.length-1)+' people here';
  });
  fetch('/api/groups').then(r=>r.json()).then(d=>{
    const mine = d.groups.filter(g=>g.members.includes(currentUser.id));
    document.getElementById('grp-sub').textContent = mine.length>0?mine.length+' groups':'Create or join a group';
  });
}

function copyLink(){
  navigator.clipboard.writeText(window.location.origin).then(()=>{
    document.getElementById('copy-msg').style.display='block';
    setTimeout(()=>document.getElementById('copy-msg').style.display='none',2000);
  });
}

function loadPeople() {
  fetch('/api/users').then(r=>r.json()).then(d=>{
    const list = document.getElementById('people-list');
    const others = d.users.filter(u=>u.id!==currentUser.id);
    if(!others.length){list.innerHTML='<div style="text-align:center;color:#333;margin-top:60px;font-size:14px;">No one else here yet.<br/>Share the link to invite friends!</div>';return;}
    list.innerHTML = others.map(u=>`
      <div class="card" onclick='openChat(${JSON.stringify(u)})'>
        ${avatarHtml(u,42)}
        <div style="flex:1;">
          <div style="color:#fff;font-weight:600;">${u.name}</div>
          <div style="color:#444;font-size:12px;">${u.contactType==='phone'?'📞':'🏠'} ${u.contact}</div>
        </div>
        <div style="color:#333;">›</div>
      </div>`).join('');
  });
}

function openChat(u) {
  chatTarget = typeof u === 'string' ? JSON.parse(u) : u;
  document.getElementById('chat-name').textContent = chatTarget.name;
  document.getElementById('chat-avatar').innerHTML = avatarHtml(chatTarget, 38);
  showScreen('chat');
}

function loadDMs() {
  if(!chatTarget||!currentUser) return;
  fetch(`/api/messages/dm/${currentUser.id}/${chatTarget.id}`).then(r=>r.json()).then(d=>{
    const box = document.getElementById('chat-messages');
    if(!d.messages.length){box.innerHTML='<div style="text-align:center;color:#333;margin-top:40px;font-size:13px;">Start a conversation.<br/><span style="color:#e8000d;font-size:11px;">Messages vanish once seen.</span></div>';return;}
    box.innerHTML = d.messages.map(m=>{
      const mine = m.fromId===currentUser.id;
      let content = m.type==='photo'&&m.photo?`<img class="chat-img" src="${m.photo}"/>`:`<div>${m.text}</div>`;
      const avatarStr = !mine ? `<div style="align-self:flex-end;">${avatarHtml(chatTarget,28)}</div>` : '';
      return `<div class="bubble-wrap ${mine?'mine':''}">${avatarStr}<div class="bubble ${mine?'mine':'theirs'}">${content}<div class="time">${timeAgo(m.ts)}${mine?' · '+(m.viewed?'seen 👁':'sent'):''}</div></div></div>`;
    }).join('');
    box.scrollTop = box.scrollHeight;
  });
}

function startChatPoll(){ stopPoll(); loadDMs(); pollInterval=setInterval(loadDMs,2000); }

function sendDM() {
  const text = document.getElementById('chat-input').value.trim();
  if(!text&&!chatPhoto) return;
  fetch('/api/messages/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fromId:currentUser.id,fromName:currentUser.name,fromPhoto:currentUser.photo||null,toId:chatTarget.id,text,type:chatPhoto?'photo':'text',photo:chatPhoto})})
  .then(()=>{ document.getElementById('chat-input').value=''; chatPhoto=null; document.getElementById('chat-photo-prev').style.display='none'; loadDMs(); });
}

function loadGroups() {
  fetch('/api/groups').then(r=>r.json()).then(d=>{
    const list = document.getElementById('groups-list');
    const mine = d.groups.filter(g=>g.members.includes(currentUser.id));
    const others = d.groups.filter(g=>!g.members.includes(currentUser.id));
    let html = '';
    if(mine.length) html += '<div class="section-label">MY GROUPS</div>'+mine.map(g=>`<div class="card" onclick='openGroup(${JSON.stringify(g)})'><div style="font-size:24px;">👥</div><div style="flex:1;"><div style="color:#fff;font-weight:600;">${g.name}</div><div style="color:#444;font-size:12px;">${g.members.length} members</div></div><div style="color:#333;">›</div></div>`).join('');
    if(others.length) html += '<div class="section-label" style="margin-top:20px;">JOIN A GROUP</div>'+others.map(g=>`<div class="card" onclick='joinGroup(${JSON.stringify(g)})'><div style="font-size:24px;">👥</div><div style="flex:1;"><div style="color:#888;font-weight:600;">${g.name}</div><div style="color:#333;font-size:12px;">${g.members.length} members · tap to join</div></div></div>`).join('');
    if(!d.groups.length) html = '<div style="text-align:center;color:#333;margin-top:60px;font-size:14px;">No groups yet.<br/>Tap <span style="color:#e8000d;">+</span> to create one.</div>';
    list.innerHTML = html;
  });
}

function toggleCreateGroup(){ const f=document.getElementById('create-group-form'); f.style.display=f.style.display==='none'?'block':'none'; }

function createGroup() {
  const name = document.getElementById('new-group-name').value.trim();
  if(!name) return;
  fetch('/api/groups/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,createdBy:currentUser.id})})
  .then(r=>r.json()).then(()=>{ document.getElementById('new-group-name').value=''; toggleCreateGroup(); loadGroups(); });
}

function joinGroup(g) {
  if(typeof g === 'string') g = JSON.parse(g);
  fetch('/api/groups/join',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({groupId:g.id,userId:currentUser.id})})
  .then(()=>openGroup(g));
}

function openGroup(g) {
  if(typeof g === 'string') g = JSON.parse(g);
  currentGroup = g;
  document.getElementById('grp-chat-name').textContent = g.name;
  document.getElementById('grp-chat-members').textContent = g.members.length+' members';
  showScreen('group-chat');
}

function loadGrpMsgs() {
  if(!currentGroup) return;
  fetch('/api/messages/group/'+currentGroup.id).then(r=>r.json()).then(d=>{
    const box = document.getElementById('grp-messages');
    if(!d.messages.length){box.innerHTML='<div style="text-align:center;color:#333;margin-top:40px;font-size:13px;">Group created! Start chatting.</div>';return;}
    box.innerHTML = d.messages.map(m=>{
      const mine = m.fromId===currentUser.id;
      let content = m.type==='photo'&&m.photo?`<img class="chat-img" src="${m.photo}"/>`:`<div>${m.text}</div>`;
      const senderUser = {name: m.fromName, photo: m.fromPhoto||null};
      const avatarStr = !mine ? `<div style="align-self:flex-end;">${avatarHtml(senderUser,28)}</div>` : '';
      return `<div class="bubble-wrap ${mine?'mine':''}">
        ${avatarStr}
        <div>${!mine?`<div class="sender-name">${m.fromName}</div>`:''}<div class="bubble ${mine?'mine':'theirs'}">${content}<div class="time">${timeAgo(m.ts)}</div></div></div>
      </div>`;
    }).join('');
    box.scrollTop = box.scrollHeight;
  });
}

function startGrpPoll(){ stopPoll(); loadGrpMsgs(); pollInterval=setInterval(loadGrpMsgs,2000); }
function stopPoll(){ if(pollInterval){clearInterval(pollInterval);pollInterval=null;} }

function sendGroupMsg() {
  const text = document.getElementById('grp-input').value.trim();
  if(!text&&!grpPhoto) return;
  fetch('/api/messages/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fromId:currentUser.id,fromName:currentUser.name,fromPhoto:currentUser.photo||null,groupId:currentGroup.id,text,type:grpPhoto?'photo':'text',photo:grpPhoto})})
  .then(()=>{ document.getElementById('grp-input').value=''; grpPhoto=null; document.getElementById('grp-photo-prev').style.display='none'; loadGrpMsgs(); });
}

function loadDMList() {
  fetch('/api/messages/conversations/'+currentUser.id).then(r=>r.json()).then(d=>{
    const list = document.getElementById('dm-list-content');
    if(!d.conversations.length){list.innerHTML='<div style="text-align:center;color:#333;margin-top:60px;font-size:14px;">No conversations yet.<br/>Go to <span style="color:#e8000d;">Find People</span> to start chatting.</div>';return;}
    list.innerHTML = d.conversations.map(c=>{
      const last = c.messages[c.messages.length-1];
      const unread = c.messages.filter(m=>m.toId===currentUser.id&&!m.viewed).length;
      return `<div class="card" style="border-color:${unread?'#e8000d44':'#1e1e1e'}" onclick='openChat(${JSON.stringify(c.user)})'>
        ${avatarHtml(c.user,42)}
        <div style="flex:1;"><div style="color:#fff;font-weight:600;">${c.user.name}</div><div style="color:#444;font-size:12px;">${last.type==='photo'?'📷 Photo':(last.text||'').substring(0,30)+'...'}</div></div>
        ${unread?`<div class="badge">${unread}</div>`:''}
      </div>`;
    }).join('');
  });
}

function handlePhoto(e, prefix) {
  const file = e.target.files[0]; if(!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    if(prefix==='chat'){chatPhoto=ev.target.result;document.getElementById('chat-prev-img').src=chatPhoto;document.getElementById('chat-photo-prev').style.display='flex';}
    else{grpPhoto=ev.target.result;document.getElementById('grp-prev-img').src=grpPhoto;document.getElementById('grp-photo-prev').style.display='flex';}
  };
  reader.readAsDataURL(file);
}

function clearPhoto(prefix) {
  if(prefix==='chat'){chatPhoto=null;document.getElementById('chat-photo-prev').style.display='none';}
  else{grpPhoto=null;document.getElementById('grp-photo-prev').style.display='none';}
}

function timeAgo(ts) {
  const diff = Date.now()-ts;
  if(diff<60000) return 'just now';
  if(diff<3600000) return Math.floor(diff/60000)+'m ago';
  if(diff<86400000) return Math.floor(diff/3600000)+'h ago';
  return Math.floor(diff/86400000)+'d ago';
}

socket.on('new_message', ()=>{
  if(document.getElementById('chat').classList.contains('active')) loadDMs();
  if(document.getElementById('group-chat').classList.contains('active')) loadGrpMsgs();
  refreshHome();
});

setTimeout(()=>{
  document.getElementById('splash').classList.remove('active');
  document.getElementById('join').classList.add('active');
}, 2000);
</script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "PARTEGEUR",
        "short_name": "PARTEGEUR",
        "description": "Share once. Vanish forever.",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#0a0a0a",
        "theme_color": "#e8000d",
        "icons": [{"src": "https://via.placeholder.com/192x192/e8000d/ffffff?text=P", "sizes": "192x192", "type": "image/png"}]
    })

@app.route('/api/join', methods=['POST'])
def join():
    data = request.json
    name = data.get('name', '').strip()
    existing = next((u for u in users.values() if u['name'].lower() == name.lower()), None)
    if existing:
        # Update photo if provided
        if data.get('photo'):
            existing['photo'] = data.get('photo')
            save_users_to_file()
        return jsonify({'user': existing})
    user = {
        'id': str(uuid.uuid4()),
        'name': name,
        'contact': data.get('contact', ''),
        'contactType': data.get('contactType', 'phone'),
        'photo': data.get('photo', None),
        'joinedAt': int(time.time() * 1000)
    }
    users[user['id']] = user
    save_users_to_file()
    socketio.emit('user_joined', user)
    return jsonify({'user': user})

@app.route('/api/users')
def get_users():
    return jsonify({'users': list(users.values())})

@app.route('/api/unread/<user_id>')
def get_unread(user_id):
    count = sum(1 for m in messages if m.get('toId') == user_id and not m.get('viewed') and not m.get('groupId'))
    return jsonify({'count': count})

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    data = request.json
    msg = {
        'id': str(uuid.uuid4()),
        'fromId': data.get('fromId'),
        'fromName': data.get('fromName'),
        'fromPhoto': data.get('fromPhoto'),
        'toId': data.get('toId'),
        'groupId': data.get('groupId'),
        'text': data.get('text', ''),
        'type': data.get('type', 'text'),
        'photo': data.get('photo'),
        'viewed': False,
        'ts': int(time.time() * 1000)
    }
    messages.append(msg)
    socketio.emit('new_message', {'msgId': msg['id']})
    return jsonify({'ok': True})

@app.route('/api/messages/dm/<user1>/<user2>')
def get_dm(user1, user2):
    conv = [m for m in messages if not m.get('groupId') and
            ((m.get('fromId') == user1 and m.get('toId') == user2) or
             (m.get('fromId') == user2 and m.get('toId') == user1))]
    for m in conv:
        if m.get('toId') == user1 and not m.get('viewed'):
            m['viewed'] = True
    return jsonify({'messages': conv})

@app.route('/api/messages/group/<group_id>')
def get_group_messages(group_id):
    gmsgs = [m for m in messages if m.get('groupId') == group_id]
    return jsonify({'messages': gmsgs})

@app.route('/api/messages/conversations/<user_id>')
def get_conversations(user_id):
    convs = {}
    for m in messages:
        if m.get('groupId'): continue
        if m.get('fromId') == user_id or m.get('toId') == user_id:
            other_id = m.get('toId') if m.get('fromId') == user_id else m.get('fromId')
            if other_id not in convs: convs[other_id] = []
            convs[other_id].append(m)
    result = []
    for uid, msgs_list in convs.items():
        if uid in users:
            result.append({'user': users[uid], 'messages': msgs_list})
    return jsonify({'conversations': result})

@app.route('/api/groups')
def get_groups():
    return jsonify({'groups': list(groups.values())})

@app.route('/api/groups/create', methods=['POST'])
def create_group():
    data = request.json
    group = {
        'id': str(uuid.uuid4()),
        'name': data.get('name'),
        'createdBy': data.get('createdBy'),
        'members': [data.get('createdBy')],
        'ts': int(time.time() * 1000)
    }
    groups[group['id']] = group
    save_groups_to_file()
    return jsonify({'group': group})

@app.route('/api/groups/join', methods=['POST'])
def join_group():
    data = request.json
    g = groups.get(data.get('groupId'))
    if g and data.get('userId') not in g['members']:
        g['members'].append(data.get('userId'))
        save_groups_to_file()
    return jsonify({'ok': True})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@socketio.on('join_user')
def on_join(data):
    join_room(data.get('userId'))

if __name__ == '__main__':
    print("\n🔴 PARTEGEUR by REDrock")
    print("━━━━━━━━━━━━━━━━━━━━━━━")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
