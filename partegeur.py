from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, join_room
import uuid, time, os, json, threading, base64

app = Flask(__name__)
app.config['SECRET_KEY'] = 'partegeur-redrock-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

DATA_FILE = 'partegeur_data.json'

def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                d = json.load(f)
                return d.get('users',{}), d.get('groups',{}), d.get('stories',[]), d.get('posts',[])
    except: pass
    return {},{},{},[]

def save_data():
    try:
        with open(DATA_FILE,'w') as f:
            json.dump({'users':users,'groups':groups,'stories':stories,'posts':posts},f)
    except Exception as e:
        print("Save error:",e)

users, groups, stories, posts = load_data()
messages = []

def clean_stories():
    global stories
    now = int(time.time()*1000)
    before = len(stories)
    stories = [s for s in stories if now - s['ts'] < 48*3600*1000]
    if len(stories) != before: save_data()
    threading.Timer(3600, clean_stories).start()

clean_stories()

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
<meta name="theme-color" content="#0a0a0a"/>
<title>PARTEGEUR by REDrock</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Cormorant+Garamond:wght@600;700&display=swap" rel="stylesheet"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent;}
:root{--red:#e8000d;--red2:#a0000a;--glass:rgba(255,255,255,0.05);--glass-border:rgba(255,255,255,0.09);--glass-dark:rgba(0,0,0,0.5);}
body{background:#080608;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:480px;margin:0 auto;height:100vh;overflow:hidden;position:relative;}

/* BG */
.bg-grad{position:fixed;inset:0;z-index:0;background:radial-gradient(ellipse at 15% 15%,#1a0008 0%,#080608 45%,#00080f 100%);pointer-events:none;}
.bg-orb1{position:fixed;width:300px;height:300px;border-radius:50%;background:radial-gradient(circle,rgba(232,0,13,0.08),transparent 70%);top:-80px;left:-80px;pointer-events:none;z-index:0;}
.bg-orb2{position:fixed;width:250px;height:250px;border-radius:50%;background:radial-gradient(circle,rgba(0,60,120,0.06),transparent 70%);bottom:-60px;right:-60px;pointer-events:none;z-index:0;}

/* Glass */
.glass{background:var(--glass);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border:1px solid var(--glass-border);}
.glass-dark{background:var(--glass-dark);backdrop-filter:blur(24px);-webkit-backdrop-filter:blur(24px);border:1px solid var(--glass-border);}
.glass-red{background:rgba(232,0,13,0.08);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border:1px solid rgba(232,0,13,0.2);}

/* Screens */
.screen{display:none;flex-direction:column;height:100vh;position:relative;z-index:1;}
.screen.active{display:flex;}

/* Inputs */
input,textarea{background:rgba(255,255,255,0.06);border:1px solid rgba(255,255,255,0.1);border-radius:14px;padding:13px 16px;color:#fff;font-size:14px;width:100%;outline:none;margin-bottom:12px;backdrop-filter:blur(8px);font-family:inherit;}
input::placeholder,textarea::placeholder{color:#444;}
input:focus,textarea:focus{border-color:rgba(232,0,13,0.5);background:rgba(255,255,255,0.09);}
textarea{resize:none;min-height:80px;}

/* Buttons */
button{cursor:pointer;border:none;border-radius:12px;font-size:14px;font-family:inherit;}
.btn-red{background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;padding:14px;width:100%;font-weight:700;font-size:15px;margin-bottom:12px;box-shadow:0 4px 24px rgba(232,0,13,0.35);}
.btn-ghost{background:rgba(255,255,255,0.06);color:#888;padding:14px;width:100%;border:1px solid rgba(255,255,255,0.1);}

/* Header */
.header{padding:12px 16px;background:rgba(8,6,8,0.75);backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);border-bottom:1px solid rgba(255,255,255,0.07);display:flex;align-items:center;justify-content:space-between;flex-shrink:0;z-index:10;}
.back-btn{background:none;color:var(--red);font-size:26px;padding:0 4px;}

/* Logo */
.redrock-logo{width:32px;height:32px;border-radius:50%;border:2px solid var(--red);object-fit:cover;box-shadow:0 0 12px rgba(232,0,13,0.4);}
.site-title{font-family:'Playfair Display',serif;font-weight:900;color:#fff;letter-spacing:3px;font-size:18px;text-shadow:0 0 30px rgba(232,0,13,0.3);}
.site-title span{color:var(--red);}

/* Avatar */
.av{border-radius:50%;object-fit:cover;border:2px solid rgba(232,0,13,0.4);flex-shrink:0;}
.av-placeholder{border-radius:50%;background:rgba(232,0,13,0.12);border:2px solid rgba(232,0,13,0.4);display:flex;align-items:center;justify-content:center;color:var(--red);font-weight:700;flex-shrink:0;}

/* Bottom nav */
.bottom-nav{display:flex;background:rgba(8,6,8,0.85);backdrop-filter:blur(28px);-webkit-backdrop-filter:blur(28px);border-top:1px solid rgba(255,255,255,0.07);flex-shrink:0;}
.nav-btn{flex:1;padding:10px 4px 8px;display:flex;flex-direction:column;align-items:center;gap:3px;background:none;color:#444;font-size:10px;border-radius:0;transition:color 0.2s;}
.nav-btn.active{color:var(--red);}
.nav-btn svg{width:22px;height:22px;fill:currentColor;}
.nav-badge{background:var(--red);color:#fff;border-radius:10px;padding:1px 5px;font-size:9px;position:absolute;top:6px;right:calc(50% - 18px);}

/* Cards */
.card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:18px;margin-bottom:12px;overflow:hidden;backdrop-filter:blur(12px);}
.card-tap{cursor:pointer;display:flex;align-items:center;gap:12px;padding:14px 16px;transition:background 0.15s;}
.card-tap:active{background:rgba(255,255,255,0.06);}

/* Badge */
.badge{background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;border-radius:20px;padding:2px 8px;font-size:11px;font-weight:700;}

/* Post card */
.post-card{background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);border-radius:20px;margin-bottom:16px;overflow:hidden;backdrop-filter:blur(16px);}
.post-header{display:flex;align-items:center;gap:10px;padding:12px 14px 8px;}
.post-img{width:100%;max-height:340px;object-fit:cover;}
.post-actions{display:flex;gap:16px;padding:10px 14px;}
.post-action-btn{background:none;color:#666;display:flex;align-items:center;gap:5px;font-size:13px;padding:4px 0;}
.post-action-btn.liked{color:var(--red);}
.post-caption{padding:4px 14px 12px;font-size:13px;color:rgba(255,255,255,0.75);line-height:1.5;}

/* Story card */
.story-card{flex-shrink:0;width:110px;height:180px;border-radius:16px;overflow:hidden;position:relative;cursor:pointer;border:2px solid rgba(232,0,13,0.4);}
.story-card img{width:100%;height:100%;object-fit:cover;}
.story-card-overlay{position:absolute;inset:0;background:linear-gradient(to bottom,transparent 40%,rgba(0,0,0,0.8));display:flex;flex-direction:column;justify-content:flex-end;padding:8px;}
.story-avatar-ring{position:absolute;top:8px;left:50%;transform:translateX(-50%);width:44px;height:44px;border-radius:50%;border:2px solid var(--red);overflow:hidden;box-shadow:0 0 12px rgba(232,0,13,0.5);}

/* Chat bubbles */
.bubble-wrap{display:flex;margin-bottom:10px;gap:7px;}
.bubble-wrap.mine{justify-content:flex-end;}
.bubble{max-width:76%;padding:10px 14px;border-radius:18px;font-size:14px;line-height:1.45;}
.bubble.mine{background:linear-gradient(135deg,rgba(232,0,13,0.82),rgba(140,0,8,0.82));border-bottom-right-radius:4px;border:1px solid rgba(232,0,13,0.25);}
.bubble.theirs{background:rgba(255,255,255,0.07);border-bottom-left-radius:4px;border:1px solid rgba(255,255,255,0.1);}
.bubble .btime{font-size:10px;color:rgba(255,255,255,0.3);margin-top:4px;text-align:right;}

/* Scroll list */
.scroll-list{flex:1;overflow-y:auto;padding:14px;}
.scroll-list::-webkit-scrollbar{width:3px;}
.scroll-list::-webkit-scrollbar-thumb{background:rgba(232,0,13,0.3);border-radius:2px;}

/* Search */
.search-box{padding:10px 14px;background:rgba(0,0,0,0.3);border-bottom:1px solid rgba(255,255,255,0.06);flex-shrink:0;}
.search-box input{margin:0;border-radius:20px;padding:10px 16px 10px 36px;font-size:13px;}
.search-wrap{position:relative;}
.search-icon{position:absolute;left:12px;top:50%;transform:translateY(-50%);color:#444;font-size:14px;pointer-events:none;}

/* Msg input */
.msg-row{padding:9px 12px;background:rgba(8,6,8,0.8);backdrop-filter:blur(24px);display:flex;gap:8px;align-items:center;border-top:1px solid rgba(255,255,255,0.07);flex-shrink:0;}
.msg-row input{margin:0;flex:1;border-radius:20px;padding:10px 14px;}
.icon-btn{background:rgba(255,255,255,0.06);color:#888;padding:9px 11px;border:1px solid rgba(255,255,255,0.1);font-size:16px;border-radius:12px;}
.send-btn{background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;padding:9px 16px;font-weight:700;font-size:16px;box-shadow:0 2px 12px rgba(232,0,13,0.3);}

/* Photo preview */
.photo-prev{padding:7px 12px;background:rgba(0,0,0,0.5);display:none;align-items:center;gap:10px;border-top:1px solid rgba(255,255,255,0.07);}
.photo-prev img{height:48px;border-radius:8px;}

/* Profile */
.profile-cover{height:120px;background:linear-gradient(135deg,#1a0005,#000510);position:relative;flex-shrink:0;}
.profile-av-wrap{position:absolute;bottom:-36px;left:50%;transform:translateX(-50%);}

/* Modal */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,0.7);backdrop-filter:blur(10px);z-index:50;display:none;align-items:flex-end;max-width:480px;margin:0 auto;}
.modal-bg.open{display:flex;}
.modal-box{background:rgba(12,10,12,0.97);backdrop-filter:blur(28px);border:1px solid rgba(255,255,255,0.1);border-radius:24px 24px 0 0;padding:22px 20px;width:100%;max-height:90vh;overflow-y:auto;}

/* Story viewer */
.sv-overlay{position:fixed;inset:0;background:#000;z-index:100;display:none;flex-direction:column;max-width:480px;margin:0 auto;}
.sv-overlay.open{display:flex;}

/* Splash */
.splash-bg{background:#080608;height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:0;}

/* Section label */
.slabel{color:rgba(255,255,255,0.22);font-size:10px;letter-spacing:3px;margin-bottom:10px;margin-top:14px;}

/* Comments */
.comment-item{display:flex;gap:9px;margin-bottom:10px;align-items:flex-start;}
.comment-bubble{background:rgba(255,255,255,0.05);border-radius:12px;padding:8px 12px;flex:1;border:1px solid rgba(255,255,255,0.07);}
</style>
</head>
<body>
<div class="bg-grad"></div><div class="bg-orb1"></div><div class="bg-orb2"></div>

<!-- ═══ SPLASH ═══ -->
<div class="screen active" id="sc-splash">
  <div class="splash-bg">
    <img id="rr-splash-logo" src="" style="width:90px;height:90px;border-radius:50%;border:3px solid var(--red);box-shadow:0 0 40px rgba(232,0,13,0.4);margin-bottom:22px;object-fit:cover;" onerror="this.style.display='none'"/>
    <div style="font-family:'Playfair Display',serif;font-weight:900;font-size:42px;color:#fff;letter-spacing:5px;text-shadow:0 0 40px rgba(232,0,13,0.5);">PART<span style="color:var(--red)">E</span>GEUR</div>
    <div style="color:rgba(255,255,255,0.2);font-size:11px;letter-spacing:6px;margin-top:6px;font-family:'Cormorant Garamond',serif;">by REDrock</div>
    <div style="color:rgba(255,255,255,0.12);font-size:10px;margin-top:28px;line-height:1.8;letter-spacing:0.5px;padding:0 24px;">
      BY — HH. RRM. Jhahi-Ga-Ma Bahadur<br/>MRS. Sir Lakshyarao Mendsure
    </div>
    <div style="color:#2a2a2a;font-size:11px;margin-top:20px;letter-spacing:2px;">share once · vanish forever</div>
  </div>
</div>

<!-- ═══ JOIN ═══ -->
<div class="screen" id="sc-join">
  <div style="flex:1;overflow-y:auto;padding:32px 24px;display:flex;flex-direction:column;justify-content:center;">
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
      <img id="rr-join-logo" src="" style="width:36px;height:36px;border-radius:50%;border:2px solid var(--red);box-shadow:0 0 12px rgba(232,0,13,0.4);" onerror="this.style.display='none'"/>
      <div style="font-family:'Playfair Display',serif;font-weight:900;font-size:28px;color:#fff;letter-spacing:3px;">PART<span style="color:var(--red)">E</span>GEUR</div>
    </div>
    <div style="color:rgba(255,255,255,0.18);font-size:10px;letter-spacing:5px;margin-bottom:30px;font-family:'Cormorant Garamond',serif;">by REDrock</div>

    <div style="text-align:center;margin-bottom:20px;">
      <div id="j-av" onclick="document.getElementById('j-photo-in').click()" style="width:86px;height:86px;border-radius:43px;background:rgba(232,0,13,0.1);border:3px solid rgba(232,0,13,0.5);display:flex;align-items:center;justify-content:center;color:var(--red);font-size:30px;margin:0 auto 8px;cursor:pointer;overflow:hidden;box-shadow:0 0 28px rgba(232,0,13,0.15);position:relative;">
        <span id="j-av-init">👤</span>
        <div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.55);text-align:center;font-size:10px;color:#fff;padding:3px;backdrop-filter:blur(4px);">add photo</div>
      </div>
      <input type="file" id="j-photo-in" accept="image/*" style="display:none;" onchange="handleProfilePic(event)"/>
      <div style="color:rgba(255,255,255,0.2);font-size:11px;">Profile Photo (optional)</div>
    </div>

    <input id="j-name" placeholder="Your full name" oninput="updateJoinInitial()"/>
    <div style="display:flex;gap:8px;margin-bottom:12px;">
      <button id="ct-ph" onclick="setCT('phone')" style="flex:1;padding:9px;background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;border-radius:10px;font-size:12px;">📞 Phone</button>
      <button id="ct-ad" onclick="setCT('address')" style="flex:1;padding:9px;background:rgba(255,255,255,0.06);color:#555;border-radius:10px;font-size:12px;border:1px solid rgba(255,255,255,0.1);">🏠 Address</button>
    </div>
    <input id="j-contact" placeholder="Your phone number"/>
    <div id="j-err" style="color:var(--red);font-size:12px;margin-bottom:8px;display:none;"></div>
    <button class="btn-red" onclick="doJoin()">Enter PARTEGEUR →</button>
    <div style="color:#2a2a2a;font-size:10px;text-align:center;margin-top:10px;line-height:1.7;">
      Your account is saved permanently · No password needed<br/>
      BY — HH. RRM. Jhahi-Ga-Ma Bahadur · MRS. Sir Lakshyarao Mendsure
    </div>
  </div>
</div>

<!-- ═══ MAIN APP ═══ -->
<div class="screen" id="sc-app">
  <!-- Header -->
  <div class="header">
    <div style="display:flex;align-items:center;gap:8px;">
      <img id="rr-hdr-logo" src="" style="width:30px;height:30px;border-radius:50%;border:2px solid var(--red);box-shadow:0 0 10px rgba(232,0,13,0.35);" onerror="this.style.display='none'"/>
      <div class="site-title">PART<span>E</span>GEUR</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <div id="hdr-notif" style="position:relative;cursor:pointer;" onclick="switchTab('chats')">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
        <div id="notif-badge" style="display:none;position:absolute;top:-2px;right:-2px;width:8px;height:8px;border-radius:4px;background:var(--red);"></div>
      </div>
      <div id="hdr-av" onclick="switchTab('profil')" style="cursor:pointer;"></div>
    </div>
  </div>

  <!-- Tab Content -->
  <div id="tab-home" style="flex:1;overflow-y:auto;display:none;"></div>
  <div id="tab-partager" style="flex:1;overflow-y:auto;display:none;"></div>
  <div id="tab-chats" style="flex:1;display:none;flex-direction:column;"></div>
  <div id="tab-profil" style="flex:1;overflow-y:auto;display:none;"></div>

  <!-- Bottom Nav -->
  <div class="bottom-nav">
    <button class="nav-btn active" id="nav-home" onclick="switchTab('home')">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      Home
    </button>
    <button class="nav-btn" id="nav-partager" onclick="switchTab('partager')">
      <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M12 8v4l3 3" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      Partager
    </button>
    <button class="nav-btn" id="nav-chats" onclick="switchTab('chats')" style="position:relative;">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      Chats
      <div id="chat-nav-badge" style="display:none;position:absolute;top:5px;right:calc(50% - 16px);width:7px;height:7px;border-radius:50%;background:var(--red);"></div>
    </button>
    <button class="nav-btn" id="nav-profil" onclick="switchTab('profil')">
      <svg viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" fill="none" stroke="currentColor" stroke-width="2"/><circle cx="12" cy="7" r="4" fill="none" stroke="currentColor" stroke-width="2"/></svg>
      Profil
    </button>
  </div>
</div>

<!-- ═══ CHAT SCREEN ═══ -->
<div class="screen" id="sc-chat">
  <div class="header">
    <button class="back-btn" onclick="closeChat()">‹</button>
    <div style="display:flex;align-items:center;gap:10px;">
      <div id="chat-hdr-av"></div>
      <div><div id="chat-hdr-name" style="color:#fff;font-weight:700;font-size:14px;"></div><div style="color:rgba(255,255,255,0.3);font-size:11px;">messages vanish after viewing</div></div>
    </div>
    <div></div>
  </div>
  <div class="scroll-list" id="chat-msgs" style="padding:12px;"></div>
  <div id="chat-photo-prev" class="photo-prev"><img id="cpp-img"/><button onclick="clearCP()" style="background:none;color:var(--red);font-size:18px;">✕</button></div>
  <div class="msg-row">
    <input type="file" id="chat-file-in" accept="image/*" style="display:none;" onchange="handleChatPhoto(event)"/>
    <button class="icon-btn" onclick="document.getElementById('chat-file-in').click()">📷</button>
    <input id="chat-msg-in" placeholder="Message..." onkeydown="if(event.key==='Enter')sendDM()"/>
    <button class="send-btn" onclick="sendDM()">↑</button>
  </div>
</div>

<!-- ═══ GROUP CHAT SCREEN ═══ -->
<div class="screen" id="sc-grpchat">
  <div class="header">
    <button class="back-btn" onclick="showScreen('sc-app');switchTab('chats')">‹</button>
    <div><div id="grp-hdr-name" style="color:#fff;font-weight:700;font-size:15px;"></div><div id="grp-hdr-sub" style="color:rgba(255,255,255,0.3);font-size:11px;"></div></div>
    <div></div>
  </div>
  <div class="scroll-list" id="grp-msgs" style="padding:12px;"></div>
  <div id="grp-photo-prev" class="photo-prev"><img id="gpp-img"/><button onclick="clearGP()" style="background:none;color:var(--red);font-size:18px;">✕</button></div>
  <div class="msg-row">
    <input type="file" id="grp-file-in" accept="image/*" style="display:none;" onchange="handleGrpPhoto(event)"/>
    <button class="icon-btn" onclick="document.getElementById('grp-file-in').click()">📷</button>
    <input id="grp-msg-in" placeholder="Message group..." onkeydown="if(event.key==='Enter')sendGrp()"/>
    <button class="send-btn" onclick="sendGrp()">↑</button>
  </div>
</div>

<!-- ═══ STORY VIEWER ═══ -->
<div class="sv-overlay" id="sv-overlay">
  <div style="padding:14px 16px;display:flex;align-items:center;gap:12px;background:rgba(0,0,0,0.5);backdrop-filter:blur(12px);">
    <button onclick="closeSV()" style="background:none;color:#fff;font-size:22px;padding:0;">✕</button>
    <div id="sv-av"></div>
    <div><div id="sv-name" style="color:#fff;font-weight:600;font-size:14px;"></div><div id="sv-time" style="color:rgba(255,255,255,0.4);font-size:11px;"></div></div>
  </div>
  <div style="height:3px;background:rgba(255,255,255,0.1);margin:0 14px;border-radius:2px;overflow:hidden;"><div id="sv-bar" style="height:100%;width:0%;background:var(--red);transition:width 5s linear;border-radius:2px;"></div></div>
  <div style="flex:1;display:flex;align-items:center;justify-content:center;padding:20px;flex-direction:column;gap:16px;">
    <img id="sv-img" src="" style="max-width:100%;max-height:55vh;border-radius:18px;display:none;box-shadow:0 0 60px rgba(0,0,0,0.9);"/>
    <div id="sv-txt" style="color:#fff;font-size:17px;text-align:center;line-height:1.6;padding:10px 20px;"></div>
  </div>
</div>

<!-- ═══ POST DETAIL MODAL ═══ -->
<div class="modal-bg" id="post-modal">
  <div class="modal-box">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="color:#fff;font-weight:700;font-size:15px;">Comments</div>
      <button onclick="closePostModal()" style="background:none;color:#888;font-size:20px;">✕</button>
    </div>
    <div id="post-modal-comments" style="max-height:220px;overflow-y:auto;margin-bottom:12px;"></div>
    <div style="display:flex;gap:8px;">
      <input id="comment-in" placeholder="Add a comment..." style="margin:0;flex:1;border-radius:20px;padding:10px 14px;"/>
      <button onclick="postComment()" style="background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;padding:10px 16px;font-weight:700;">↑</button>
    </div>
  </div>
</div>

<!-- ═══ ADD STORY MODAL ═══ -->
<div class="modal-bg" id="story-modal">
  <div class="modal-box">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="color:#fff;font-weight:700;font-size:15px;">📖 Add Story</div>
      <button onclick="closeStoryModal()" style="background:none;color:#888;font-size:20px;">✕</button>
    </div>
    <div id="sm-photo-prev" style="display:none;text-align:center;margin-bottom:10px;">
      <img id="sm-prev-img" style="max-height:140px;border-radius:12px;"/>
      <button onclick="clearSP()" style="display:block;margin:6px auto 0;background:none;color:var(--red);font-size:12px;">✕ Remove</button>
    </div>
    <textarea id="sm-text" placeholder="What's on your mind? (optional)"></textarea>
    <input type="file" id="sm-file" accept="image/*" style="display:none;" onchange="handleStoryPhoto(event)"/>
    <button onclick="document.getElementById('sm-file').click()" class="btn-ghost" style="margin-bottom:10px;border-radius:12px;">📷 Add Photo</button>
    <button class="btn-red" onclick="postStory()">Post Story · vanishes in 48h</button>
  </div>
</div>

<!-- ═══ ADD POST MODAL ═══ -->
<div class="modal-bg" id="post-add-modal">
  <div class="modal-box">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <div style="color:#fff;font-weight:700;font-size:15px;">✨ New Post</div>
      <button onclick="closePostAddModal()" style="background:none;color:#888;font-size:20px;">✕</button>
    </div>
    <div id="pm-photo-prev" style="display:none;text-align:center;margin-bottom:10px;">
      <img id="pm-prev-img" style="max-height:160px;border-radius:12px;width:100%;object-fit:cover;"/>
      <button onclick="clearPP()" style="display:block;margin:6px auto 0;background:none;color:var(--red);font-size:12px;">✕ Remove</button>
    </div>
    <input type="file" id="pm-file" accept="image/*" style="display:none;" onchange="handlePostPhoto(event)"/>
    <button onclick="document.getElementById('pm-file').click()" class="btn-ghost" style="margin-bottom:10px;border-radius:12px;">📷 Add Photo</button>
    <textarea id="pm-caption" placeholder="Write a caption..."></textarea>
    <button class="btn-red" onclick="submitPost()">Share Post</button>
  </div>
</div>

<script>
const socket = io();
let CU = null, chatTarget = null, curGroup = null;
let CT = 'phone', chatPic = null, grpPic = null, profilePic = null, storyPic = null, postPic = null;
let poll = null, allUsers = [], curPostId = null;
const RR_LOGO_URL = '/redrock-logo';

// Load REDrock logo
function loadLogo() {
  fetch(RR_LOGO_URL).then(r => r.blob()).then(blob => {
    const url = URL.createObjectURL(blob);
    ['rr-splash-logo','rr-join-logo','rr-hdr-logo'].forEach(id => {
      const el = document.getElementById(id);
      if(el) el.src = url;
    });
  }).catch(()=>{});
}
loadLogo();

// ── UTILS ──────────────────────────────────────────
function avHTML(user, size=38) {
  const r = size/2;
  if(user && user.photo) return `<img src="${user.photo}" class="av" style="width:${size}px;height:${size}px;"/>`;
  const fs = Math.floor(size*0.38);
  return `<div class="av-placeholder" style="width:${size}px;height:${size}px;font-size:${fs}px;">${user?user.name[0].toUpperCase():'?'}</div>`;
}

function timeAgo(ts) {
  const d = Date.now()-ts;
  if(d<60000) return 'just now';
  if(d<3600000) return Math.floor(d/60000)+'m';
  if(d<86400000) return Math.floor(d/3600000)+'h';
  return Math.floor(d/86400000)+'d';
}

function resizeImg(file, maxPx, quality, cb) {
  const reader = new FileReader();
  reader.onload = ev => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement('canvas');
      const ratio = Math.min(maxPx/img.width, maxPx/img.height, 1);
      canvas.width = img.width*ratio; canvas.height = img.height*ratio;
      canvas.getContext('2d').drawImage(img,0,0,canvas.width,canvas.height);
      cb(canvas.toDataURL('image/jpeg', quality));
    };
    img.src = ev.target.result;
  };
  reader.readAsDataURL(file);
}

function showScreen(id) {
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  document.getElementById(id).classList.add('active');
}

function stopPoll() { if(poll){clearInterval(poll);poll=null;} }

// ── JOIN ───────────────────────────────────────────
function updateJoinInitial() {
  if(profilePic) return;
  const n = document.getElementById('j-name').value.trim();
  document.getElementById('j-av-init').textContent = n?n[0].toUpperCase():'👤';
}

function handleProfilePic(e) {
  const file = e.target.files[0]; if(!file) return;
  resizeImg(file, 200, 0.7, d => {
    profilePic = d;
    document.getElementById('j-av').innerHTML = `<img src="${d}" style="width:86px;height:86px;object-fit:cover;border-radius:43px;"/><div style="position:absolute;bottom:0;left:0;right:0;background:rgba(0,0,0,0.5);text-align:center;font-size:10px;color:#fff;padding:3px;">change</div>`;
  });
}

function setCT(t) {
  CT = t;
  document.getElementById('ct-ph').style.background = t==='phone'?'linear-gradient(135deg,var(--red),var(--red2))':'rgba(255,255,255,0.06)';
  document.getElementById('ct-ph').style.color = t==='phone'?'#fff':'#555';
  document.getElementById('ct-ad').style.background = t==='address'?'linear-gradient(135deg,var(--red),var(--red2))':'rgba(255,255,255,0.06)';
  document.getElementById('ct-ad').style.color = t==='address'?'#fff':'#555';
  document.getElementById('j-contact').placeholder = t==='phone'?'Your phone number':'Your home address';
}

function showErr(id, msg) {
  const el = document.getElementById(id);
  el.textContent = msg; el.style.display='block';
  setTimeout(()=>el.style.display='none',3000);
}

function doJoin() {
  const name = document.getElementById('j-name').value.trim();
  const contact = document.getElementById('j-contact').value.trim();
  if(!name) return showErr('j-err','Enter your name');
  if(!contact) return showErr('j-err','Enter phone or address');
  fetch('/api/join',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name,contact,contactType:CT,photo:profilePic})})
  .then(r=>r.json()).then(d=>{
    if(d.user){
      CU = d.user;
      localStorage.setItem('partegeur_uid', CU.id);
      socket.emit('join_user',{userId:CU.id});
      initApp();
    }
  });
}

// ── INIT ───────────────────────────────────────────
function initApp() {
  showScreen('sc-app');
  document.getElementById('hdr-av').innerHTML = avHTML(CU,30);
  switchTab('home');
  setInterval(refreshBadges, 5000);
}

function refreshBadges() {
  if(!CU) return;
  fetch('/api/unread/'+CU.id).then(r=>r.json()).then(d=>{
    const b = document.getElementById('chat-nav-badge');
    const nb = document.getElementById('notif-badge');
    if(d.count>0){b.style.display='block';nb.style.display='block';}
    else{b.style.display='none';nb.style.display='none';}
  });
}

// ── TABS ───────────────────────────────────────────
let activeTab = 'home';
function switchTab(tab) {
  activeTab = tab;
  ['home','partager','chats','profil'].forEach(t=>{
    document.getElementById('tab-'+t).style.display='none';
    document.getElementById('nav-'+t).classList.remove('active');
  });
  document.getElementById('tab-'+tab).style.display = tab==='chats'?'flex':'block';
  document.getElementById('nav-'+tab).classList.add('active');
  stopPoll();
  if(tab==='home') loadFeed();
  if(tab==='partager') loadPartager();
  if(tab==='chats') loadChatsTab();
  if(tab==='profil') loadProfil();
}

// ── HOME FEED ──────────────────────────────────────
function loadFeed() {
  fetch('/api/posts').then(r=>r.json()).then(d=>{
    const tab = document.getElementById('tab-home');
    let html = `<div style="padding:12px 14px 4px;display:flex;justify-content:space-between;align-items:center;">
      <div style="color:rgba(255,255,255,0.5);font-size:12px;letter-spacing:2px;">FEED</div>
      <button onclick="openPostAddModal()" style="background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;padding:7px 14px;font-size:12px;font-weight:600;box-shadow:0 2px 12px rgba(232,0,13,0.3);">+ Post</button>
    </div><div style="padding:8px 12px;">`;
    if(!d.posts.length) {
      html += '<div style="text-align:center;color:#333;margin-top:60px;font-size:14px;">No posts yet.<br/><span style="color:var(--red)">Be the first to post!</span></div>';
    } else {
      d.posts.slice().reverse().forEach(p=>{
        const u = {name:p.userName,photo:p.userPhoto||null};
        const liked = p.likes && p.likes.includes(CU.id);
        html += `<div class="post-card">
          <div class="post-header">
            ${avHTML(u,38)}
            <div style="flex:1;">
              <div style="color:#fff;font-weight:600;font-size:14px;">${p.userName}</div>
              <div style="color:rgba(255,255,255,0.3);font-size:11px;">${timeAgo(p.ts)}</div>
            </div>
          </div>
          ${p.photo?`<img class="post-img" src="${p.photo}"/>`:''}
          ${p.caption?`<div class="post-caption">${p.caption}</div>`:''}
          <div class="post-actions">
            <button class="post-action-btn ${liked?'liked':''}" onclick="likePost('${p.id}')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="${liked?'var(--red)':'none'}" stroke="${liked?'var(--red)':'currentColor'}" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              ${(p.likes||[]).length}
            </button>
            <button class="post-action-btn" onclick="openPostModal('${p.id}')">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              ${(p.comments||[]).length}
            </button>
          </div>
        </div>`;
      });
    }
    html += '</div>';
    tab.innerHTML = html;
  });
}

function likePost(pid) {
  fetch('/api/posts/like',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({postId:pid,userId:CU.id})})
  .then(()=>loadFeed());
}

function openPostModal(pid) {
  curPostId = pid;
  fetch('/api/posts').then(r=>r.json()).then(d=>{
    const post = d.posts.find(p=>p.id===pid);
    if(!post) return;
    const comments = post.comments||[];
    document.getElementById('post-modal-comments').innerHTML = comments.length
      ? comments.map(c=>`<div class="comment-item">${avHTML({name:c.userName,photo:c.userPhoto||null},30)}<div class="comment-bubble"><div style="color:var(--red);font-size:11px;font-weight:600;">${c.userName}</div><div style="color:rgba(255,255,255,0.8);font-size:13px;margin-top:2px;">${c.text}</div></div></div>`).join('')
      : '<div style="color:#333;font-size:13px;text-align:center;padding:20px;">No comments yet. Be first!</div>';
    document.getElementById('post-modal').classList.add('open');
  });
}

function closePostModal(){document.getElementById('post-modal').classList.remove('open');}

function postComment() {
  const text = document.getElementById('comment-in').value.trim();
  if(!text||!curPostId) return;
  fetch('/api/posts/comment',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({postId:curPostId,userId:CU.id,userName:CU.name,userPhoto:CU.photo||null,text})})
  .then(()=>{document.getElementById('comment-in').value='';openPostModal(curPostId);});
}

// Post add modal
function openPostAddModal(){document.getElementById('post-add-modal').classList.add('open');}
function closePostAddModal(){document.getElementById('post-add-modal').classList.remove('open');postPic=null;document.getElementById('pm-caption').value='';document.getElementById('pm-photo-prev').style.display='none';}
function handlePostPhoto(e){const f=e.target.files[0];if(!f)return;resizeImg(f,900,0.75,d=>{postPic=d;document.getElementById('pm-prev-img').src=d;document.getElementById('pm-photo-prev').style.display='block';});}
function clearPP(){postPic=null;document.getElementById('pm-photo-prev').style.display='none';}
function submitPost(){
  const cap=document.getElementById('pm-caption').value.trim();
  if(!cap&&!postPic) return;
  fetch('/api/posts/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:CU.id,userName:CU.name,userPhoto:CU.photo||null,caption:cap,photo:postPic})})
  .then(()=>{closePostAddModal();loadFeed();});
}

// ── PARTAGER (STORIES) ────────────────────────────
function loadPartager() {
  fetch('/api/stories').then(r=>r.json()).then(d=>{
    const tab = document.getElementById('tab-partager');
    let html = `<div style="padding:14px 14px 4px;display:flex;justify-content:space-between;align-items:center;">
      <div style="font-family:'Playfair Display',serif;font-size:18px;color:#fff;letter-spacing:2px;">PART<span style="color:var(--red)">A</span>GER</div>
      <button onclick="openStoryModal()" style="background:linear-gradient(135deg,var(--red),var(--red2));color:#fff;padding:7px 14px;font-size:12px;font-weight:600;">+ Story</button>
    </div>
    <div style="color:rgba(255,255,255,0.2);font-size:10px;padding:2px 14px 12px;letter-spacing:2px;">STORIES · VANISH IN 48H</div>
    <div style="padding:0 12px;display:flex;flex-wrap:wrap;gap:10px;">`;
    if(!d.stories.length) {
      html += '<div style="text-align:center;color:#333;margin:60px auto;font-size:14px;width:100%;">No stories yet.<br/><span style="color:var(--red)">Be the first to share!</span></div>';
    } else {
      d.stories.forEach(s=>{
        const hoursLeft = Math.ceil((48*3600*1000-(Date.now()-s.ts))/3600000);
        html += `<div onclick='viewStory(${JSON.stringify(s).replace(/'/g,"&#39;")})' style="width:calc(50% - 5px);height:220px;border-radius:18px;overflow:hidden;position:relative;cursor:pointer;border:2px solid rgba(232,0,13,0.35);background:rgba(232,0,13,0.06);">
          ${s.photo?`<img src="${s.photo}" style="width:100%;height:100%;object-fit:cover;"/>`:
            `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;padding:16px;"><div style="color:rgba(255,255,255,0.8);font-size:15px;text-align:center;line-height:1.5;">${s.text||''}</div></div>`}
          <div style="position:absolute;inset:0;background:linear-gradient(to bottom,rgba(0,0,0,0.3) 0%,transparent 35%,transparent 55%,rgba(0,0,0,0.75) 100%);"></div>
          <div style="position:absolute;top:10px;left:50%;transform:translateX(-50%);width:46px;height:46px;border-radius:23px;border:2px solid var(--red);overflow:hidden;box-shadow:0 0 14px rgba(232,0,13,0.5);">
            ${s.userPhoto?`<img src="${s.userPhoto}" style="width:100%;height:100%;object-fit:cover;"/>`:`<div style="width:100%;height:100%;background:rgba(232,0,13,0.15);display:flex;align-items:center;justify-content:center;color:var(--red);font-weight:700;font-size:18px;">${s.userName[0].toUpperCase()}</div>`}
          </div>
          <div style="position:absolute;bottom:0;left:0;right:0;padding:10px;">
            <div style="color:#fff;font-weight:600;font-size:12px;">${s.userName}</div>
            <div style="color:rgba(255,255,255,0.5);font-size:10px;">${hoursLeft}h left</div>
          </div>
        </div>`;
      });
    }
    html += '</div>';
    tab.innerHTML = html;
  });
}

function openStoryModal(){document.getElementById('story-modal').classList.add('open');}
function closeStoryModal(){document.getElementById('story-modal').classList.remove('open');storyPic=null;document.getElementById('sm-text').value='';document.getElementById('sm-photo-prev').style.display='none';}
function handleStoryPhoto(e){const f=e.target.files[0];if(!f)return;resizeImg(f,800,0.75,d=>{storyPic=d;document.getElementById('sm-prev-img').src=d;document.getElementById('sm-photo-prev').style.display='block';});}
function clearSP(){storyPic=null;document.getElementById('sm-photo-prev').style.display='none';}
function postStory(){
  const text=document.getElementById('sm-text').value.trim();
  if(!text&&!storyPic) return;
  fetch('/api/stories/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({userId:CU.id,userName:CU.name,userPhoto:CU.photo||null,text,photo:storyPic})})
  .then(()=>{closeStoryModal();loadPartager();});
}

function viewStory(s){
  if(typeof s==='string') s=JSON.parse(s);
  const ov=document.getElementById('sv-overlay');
  ov.classList.add('open');
  document.getElementById('sv-name').textContent=s.userName;
  document.getElementById('sv-av').innerHTML=avHTML({name:s.userName,photo:s.userPhoto||null},38);
  const h=Math.ceil((48*3600*1000-(Date.now()-s.ts))/3600000);
  document.getElementById('sv-time').textContent=h+'h remaining';
  const img=document.getElementById('sv-img');
  if(s.photo){img.src=s.photo;img.style.display='block';}else img.style.display='none';
  document.getElementById('sv-txt').textContent=s.text||'';
  const bar=document.getElementById('sv-bar');
  bar.style.width='0%';
  setTimeout(()=>bar.style.width='100%',100);
}
function closeSV(){document.getElementById('sv-overlay').classList.remove('open');}

// ── CHATS TAB ──────────────────────────────────────
function loadChatsTab() {
  const tab = document.getElementById('tab-chats');
  tab.innerHTML = `
    <div style="padding:12px 14px 8px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0;">
      <div style="color:rgba(255,255,255,0.5);font-size:12px;letter-spacing:2px;">MESSAGES & PEOPLE</div>
    </div>
    <div class="search-box" style="flex-shrink:0;"><div class="search-wrap"><span class="search-icon">🔍</span><input id="people-search" placeholder="Search people by name or phone..." oninput="filterPpl()" style="margin:0;"/></div></div>
    <div style="flex:1;overflow-y:auto;" id="chats-content"></div>
    <div style="padding:10px 14px;flex-shrink:0;display:flex;gap:8px;">
      <button onclick="openCreateGroup()" style="flex:1;padding:11px;background:rgba(255,255,255,0.06);color:#888;border:1px solid rgba(255,255,255,0.1);border-radius:12px;font-size:13px;">👥 New Group</button>
    </div>`;
  loadChatsContent();
}

function loadChatsContent(filter='') {
  Promise.all([
    fetch('/api/users').then(r=>r.json()),
    fetch('/api/messages/conversations/'+CU.id).then(r=>r.json()),
    fetch('/api/groups').then(r=>r.json())
  ]).then(([ud, cd, gd]) => {
    allUsers = ud.users;
    const box = document.getElementById('chats-content');
    if(!box) return;
    let html = '';

    // Recent convos
    const convos = cd.conversations||[];
    if(convos.length) {
      html += '<div class="slabel" style="padding:0 14px;">RECENT</div>';
      convos.forEach(c=>{
        const last = c.messages[c.messages.length-1];
        const unread = c.messages.filter(m=>m.toId===CU.id&&!m.viewed).length;
        if(filter && !c.user.name.toLowerCase().includes(filter) && !c.user.contact.toLowerCase().includes(filter)) return;
        html += `<div class="card-tap" onclick='openDM(${JSON.stringify(c.user).replace(/'/g,"&#39;")})' style="margin:0 12px 8px;border-radius:16px;background:rgba(255,255,255,0.04);border:1px solid ${unread?'rgba(232,0,13,0.35)':'rgba(255,255,255,0.08)'};">
          ${avHTML(c.user,42)}
          <div style="flex:1;min-width:0;">
            <div style="color:#fff;font-weight:600;">${c.user.name}</div>
            <div style="color:rgba(255,255,255,0.3);font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${last.type==='photo'?'📷 Photo':(last.text||'').substring(0,28)+'...'}</div>
          </div>
          ${unread?`<div class="badge">${unread}</div>`:'<div style="color:#333;">›</div>'}
        </div>`;
      });
    }

    // Groups
    const myGroups = (gd.groups||[]).filter(g=>g.members.includes(CU.id));
    if(myGroups.length) {
      html += '<div class="slabel" style="padding:0 14px;">GROUPS</div>';
      myGroups.forEach(g=>{
        html += `<div class="card-tap" onclick='openGrp(${JSON.stringify(g).replace(/'/g,"&#39;")})' style="margin:0 12px 8px;border-radius:16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
          <div style="width:42px;height:42px;border-radius:21px;background:rgba(232,0,13,0.1);border:2px solid rgba(232,0,13,0.3);display:flex;align-items:center;justify-content:center;font-size:20px;">👥</div>
          <div style="flex:1;"><div style="color:#fff;font-weight:600;">${g.name}</div><div style="color:rgba(255,255,255,0.3);font-size:12px;">${g.members.length} members</div></div>
          <div style="color:#333;">›</div>
        </div>`;
      });
    }

    // All people
    const others = allUsers.filter(u=>u.id!==CU.id && (!filter || u.name.toLowerCase().includes(filter) || (u.contact||'').toLowerCase().includes(filter)));
    html += '<div class="slabel" style="padding:0 14px;">FIND PEOPLE</div>';
    if(!others.length) {
      html += '<div style="text-align:center;color:#333;font-size:13px;padding:20px;">No people found.</div>';
    } else {
      others.forEach(u=>{
        html += `<div class="card-tap" onclick='openDM(${JSON.stringify(u).replace(/'/g,"&#39;")})' style="margin:0 12px 8px;border-radius:16px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
          ${avHTML(u,42)}
          <div style="flex:1;"><div style="color:#fff;font-weight:600;">${u.name}</div><div style="color:rgba(255,255,255,0.3);font-size:12px;">${u.contactType==='phone'?'📞':'🏠'} ${u.contact}</div></div>
          <div style="color:#333;">›</div>
        </div>`;
      });
    }
    box.innerHTML = html;
  });
}

function filterPpl() {
  const q = (document.getElementById('people-search')||{}).value||'';
  loadChatsContent(q.trim().toLowerCase());
}

// ── DM ─────────────────────────────────────────────
function openDM(u) {
  if(typeof u==='string') u=JSON.parse(u);
  chatTarget=u;
  document.getElementById('chat-hdr-name').textContent=u.name;
  document.getElementById('chat-hdr-av').innerHTML=avHTML(u,38);
  showScreen('sc-chat');
  stopPoll(); loadDMs(); poll=setInterval(loadDMs,2000);
}

function closeChat() {
  stopPoll();
  showScreen('sc-app');
  switchTab('chats');
}

function loadDMs() {
  if(!chatTarget||!CU) return;
  fetch(`/api/messages/dm/${CU.id}/${chatTarget.id}`).then(r=>r.json()).then(d=>{
    const box=document.getElementById('chat-msgs');
    if(!d.messages.length){box.innerHTML='<div style="text-align:center;color:#333;margin-top:40px;font-size:13px;">Start chatting!<br/><span style="color:var(--red);font-size:11px;">Messages vanish once seen.</span></div>';return;}
    box.innerHTML=d.messages.map(m=>{
      const mine=m.fromId===CU.id;
      const content=m.type==='photo'&&m.photo?`<img src="${m.photo}" style="max-width:180px;border-radius:10px;"/>`:`<div>${m.text}</div>`;
      const av=!mine?`<div style="align-self:flex-end;">${avHTML(chatTarget,26)}</div>`:'';
      return `<div class="bubble-wrap ${mine?'mine':''}">${av}<div class="bubble ${mine?'mine':'theirs'}">${content}<div class="btime">${timeAgo(m.ts)}${mine?' · '+(m.viewed?'seen 👁':'✓'):''}</div></div></div>`;
    }).join('');
    box.scrollTop=box.scrollHeight;
  });
}

function sendDM() {
  const text=document.getElementById('chat-msg-in').value.trim();
  if(!text&&!chatPic) return;
  fetch('/api/messages/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({fromId:CU.id,fromName:CU.name,fromPhoto:CU.photo||null,toId:chatTarget.id,text,type:chatPic?'photo':'text',photo:chatPic})})
  .then(()=>{document.getElementById('chat-msg-in').value='';chatPic=null;document.getElementById('chat-photo-prev').style.display='none';loadDMs();});
}

function handleChatPhoto(e){resizeImg(e.target.files[0],900,0.8,d=>{chatPic=d;document.getElementById('cpp-img').src=d;document.getElementById('chat-photo-prev').style.display='flex';});}
function clearCP(){chatPic=null;document.getElementById('chat-photo-prev').style.display='none';}

// ── GROUPS ─────────────────────────────────────────
function openCreateGroup() {
  const name=prompt('Group name:');
  if(!name) return;
  fetch('/api/groups/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name.trim(),createdBy:CU.id})})
  .then(()=>loadChatsContent());
}

function openGrp(g) {
  if(typeof g==='string') g=JSON.parse(g);
  curGroup=g;
  document.getElementById('grp-hdr-name').textContent=g.name;
  document.getElementById('grp-hdr-sub').textContent=g.members.length+' members';
  showScreen('sc-grpchat');
  stopPoll(); loadGrpMsgs(); poll=setInterval(loadGrpMsgs,2000);
}

function loadGrpMsgs() {
  if(!curGroup) return;
  fetch('/api/messages/group/'+curGroup.id).then(r=>r.json()).then(d=>{
    const box=document.getElementById('grp-msgs');
    if(!d.messages.length){box.innerHTML='<div style="text-align:center;color:#333;margin-top:40px;font-size:13px;">Group created! Start chatting.</div>';return;}
    box.innerHTML=d.messages.map(m=>{
      const mine=m.fromId===CU.id;
      const content=m.type==='photo'&&m.photo?`<img src="${m.photo}" style="max-width:180px;border-radius:10px;"/>`:`<div>${m.text}</div>`;
      const sv={name:m.fromName,photo:m.fromPhoto||null};
      const av=!mine?`<div style="align-self:flex-end;">${avHTML(sv,26)}</div>`:'';
      return `<div class="bubble-wrap ${mine?'mine':''}">${av}<div>${!mine?`<div style="color:var(--red);font-size:11px;margin-bottom:3px;margin-left:4px;">${m.fromName}</div>`:''}<div class="bubble ${mine?'mine':'theirs'}">${content}<div class="btime">${timeAgo(m.ts)}</div></div></div></div>`;
    }).join('');
    box.scrollTop=box.scrollHeight;
  });
}

function sendGrp() {
  const text=document.getElementById('grp-msg-in').value.trim();
  if(!text&&!grpPic) return;
  fetch('/api/messages/send',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({fromId:CU.id,fromName:CU.name,fromPhoto:CU.photo||null,groupId:curGroup.id,text,type:grpPic?'photo':'text',photo:grpPic})})
  .then(()=>{document.getElementById('grp-msg-in').value='';grpPic=null;document.getElementById('grp-photo-prev').style.display='none';loadGrpMsgs();});
}

function handleGrpPhoto(e){resizeImg(e.target.files[0],900,0.8,d=>{grpPic=d;document.getElementById('gpp-img').src=d;document.getElementById('grp-photo-prev').style.display='flex';});}
function clearGP(){grpPic=null;document.getElementById('grp-photo-prev').style.display='none';}

// ── PROFIL ─────────────────────────────────────────
function loadProfil() {
  fetch('/api/posts').then(r=>r.json()).then(d=>{
    const myPosts=d.posts.filter(p=>p.userId===CU.id);
    const tab=document.getElementById('tab-profil');
    tab.innerHTML=`
      <div class="profile-cover"></div>
      <div style="text-align:center;margin-top:-36px;padding-bottom:12px;">
        <div style="width:72px;height:72px;border-radius:36px;border:3px solid var(--red);overflow:hidden;margin:0 auto;box-shadow:0 0 24px rgba(232,0,13,0.3);">
          ${CU.photo?`<img src="${CU.photo}" style="width:100%;height:100%;object-fit:cover;"/>`:`<div style="width:100%;height:100%;background:rgba(232,0,13,0.12);display:flex;align-items:center;justify-content:center;color:var(--red);font-weight:700;font-size:26px;">${CU.name[0].toUpperCase()}</div>`}
        </div>
        <div style="font-family:'Playfair Display',serif;font-size:20px;color:#fff;margin-top:10px;">${CU.name}</div>
        <div style="color:rgba(255,255,255,0.3);font-size:12px;margin-top:3px;">${CU.contactType==='phone'?'📞':'🏠'} ${CU.contact}</div>
        <div style="display:flex;justify-content:center;gap:28px;margin-top:14px;">
          <div style="text-align:center;"><div style="color:#fff;font-weight:700;font-size:20px;">${myPosts.length}</div><div style="color:rgba(255,255,255,0.3);font-size:11px;">Posts</div></div>
          <div style="text-align:center;"><div style="color:#fff;font-weight:700;font-size:20px;">${myPosts.reduce((a,p)=>(p.likes||[]).length+a,0)}</div><div style="color:rgba(255,255,255,0.3);font-size:11px;">Likes</div></div>
          <div style="text-align:center;"><div style="color:#fff;font-weight:700;font-size:20px;">${myPosts.reduce((a,p)=>(p.comments||[]).length+a,0)}</div><div style="color:rgba(255,255,255,0.3);font-size:11px;">Comments</div></div>
        </div>
      </div>
      <div style="height:1px;background:rgba(255,255,255,0.07);margin:0 14px 14px;"></div>
      <div style="padding:0 12px;">
        <div class="slabel">MY POSTS</div>
        ${!myPosts.length?'<div style="text-align:center;color:#333;font-size:13px;padding:30px;">No posts yet.</div>':
          myPosts.slice().reverse().map(p=>`<div class="post-card">
            ${p.photo?`<img class="post-img" src="${p.photo}"/>`:''}
            ${p.caption?`<div class="post-caption">${p.caption}</div>`:''}
            <div class="post-actions">
              <div style="color:rgba(255,255,255,0.3);font-size:12px;padding:0 0 4px;">❤️ ${(p.likes||[]).length} · 💬 ${(p.comments||[]).length} · ${timeAgo(p.ts)}</div>
            </div>
          </div>`).join('')}
      </div>`;
  });
}

// ── SOCKET ─────────────────────────────────────────
socket.on('new_message',()=>{
  refreshBadges();
  if(document.getElementById('sc-chat').classList.contains('active')) loadDMs();
  if(document.getElementById('sc-grpchat').classList.contains('active')) loadGrpMsgs();
});
socket.on('new_post',()=>{ if(activeTab==='home') loadFeed(); });
socket.on('new_story',()=>{ if(activeTab==='partager') loadPartager(); });

// ── BOOT ───────────────────────────────────────────
setTimeout(async ()=>{
  const savedId = localStorage.getItem('partegeur_uid');
  if(savedId) {
    const res = await fetch('/api/user/'+savedId);
    const d = await res.json();
    if(d.user) {
      CU = d.user;
      socket.emit('join_user',{userId:CU.id});
      initApp();
      return;
    }
  }
  showScreen('sc-join');
}, 2000);
</script>
</body>
</html>'''

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/redrock-logo')
def redrock_logo():
    # Serve the REDrock logo from the uploaded file if available
    logo_path = 'redrock_logo.jpg'
    if os.path.exists(logo_path):
        with open(logo_path,'rb') as f:
            data = f.read()
        from flask import Response
        return Response(data, mimetype='image/jpeg')
    # Return a placeholder SVG
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r="48" fill="#1a0005" stroke="#e8000d" stroke-width="2"/>
      <text x="50" y="58" font-size="36" text-anchor="middle" fill="#e8000d" font-family="Georgia,serif" font-weight="bold">R</text>
    </svg>'''
    from flask import Response
    return Response(svg, mimetype='image/svg+xml')

@app.route('/manifest.json')
def manifest():
    return jsonify({"name":"PARTEGEUR","short_name":"PARTEGEUR","description":"Share once. Vanish forever.","start_url":"/","display":"standalone","background_color":"#080608","theme_color":"#e8000d","icons":[{"src":"/redrock-logo","sizes":"192x192","type":"image/png"}]})

@app.route('/api/join', methods=['POST'])
def join():
    data = request.json
    name = data.get('name','').strip()
    existing = next((u for u in users.values() if u['name'].lower()==name.lower()), None)
    if existing:
        if data.get('photo'): existing['photo']=data.get('photo')
        save_data()
        return jsonify({'user':existing})
    user = {'id':str(uuid.uuid4()),'name':name,'contact':data.get('contact',''),'contactType':data.get('contactType','phone'),'photo':data.get('photo',None),'joinedAt':int(time.time()*1000)}
    users[user['id']] = user
    save_data()
    socketio.emit('user_joined', user)
    return jsonify({'user':user})

@app.route('/api/user/<uid>')
def get_user(uid):
    u = users.get(uid)
    return jsonify({'user':u})

@app.route('/api/users')
def get_users(): return jsonify({'users':list(users.values())})

@app.route('/api/unread/<uid>')
def get_unread(uid):
    count = sum(1 for m in messages if m.get('toId')==uid and not m.get('viewed') and not m.get('groupId'))
    return jsonify({'count':count})

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    data = request.json
    msg = {'id':str(uuid.uuid4()),'fromId':data.get('fromId'),'fromName':data.get('fromName'),'fromPhoto':data.get('fromPhoto'),'toId':data.get('toId'),'groupId':data.get('groupId'),'text':data.get('text',''),'type':data.get('type','text'),'photo':data.get('photo'),'viewed':False,'ts':int(time.time()*1000)}
    messages.append(msg)
    socketio.emit('new_message',{'msgId':msg['id']})
    return jsonify({'ok':True})

@app.route('/api/messages/dm/<u1>/<u2>')
def get_dm(u1,u2):
    conv=[m for m in messages if not m.get('groupId') and ((m.get('fromId')==u1 and m.get('toId')==u2) or (m.get('fromId')==u2 and m.get('toId')==u1))]
    for m in conv:
        if m.get('toId')==u1 and not m.get('viewed'): m['viewed']=True
    return jsonify({'messages':conv})

@app.route('/api/messages/group/<gid>')
def get_group_messages(gid):
    return jsonify({'messages':[m for m in messages if m.get('groupId')==gid]})

@app.route('/api/messages/conversations/<uid>')
def get_conversations(uid):
    convs={}
    for m in messages:
        if m.get('groupId'): continue
        if m.get('fromId')==uid or m.get('toId')==uid:
            oid=m.get('toId') if m.get('fromId')==uid else m.get('fromId')
            if oid not in convs: convs[oid]=[]
            convs[oid].append(m)
    return jsonify({'conversations':[{'user':users[uid2],'messages':ml} for uid2,ml in convs.items() if uid2 in users]})

@app.route('/api/groups')
def get_groups(): return jsonify({'groups':list(groups.values())})

@app.route('/api/groups/create', methods=['POST'])
def create_group():
    data=request.json
    g={'id':str(uuid.uuid4()),'name':data.get('name'),'createdBy':data.get('createdBy'),'members':[data.get('createdBy')],'ts':int(time.time()*1000)}
    groups[g['id']]=g; save_data()
    return jsonify({'group':g})

@app.route('/api/groups/join', methods=['POST'])
def join_group():
    data=request.json
    g=groups.get(data.get('groupId'))
    if g and data.get('userId') not in g['members']:
        g['members'].append(data.get('userId')); save_data()
    return jsonify({'ok':True})

@app.route('/api/stories')
def get_stories():
    now=int(time.time()*1000)
    return jsonify({'stories':[s for s in stories if now-s['ts']<48*3600*1000]})

@app.route('/api/stories/post', methods=['POST'])
def post_story():
    data=request.json
    s={'id':str(uuid.uuid4()),'userId':data.get('userId'),'userName':data.get('userName'),'userPhoto':data.get('userPhoto'),'text':data.get('text',''),'photo':data.get('photo'),'ts':int(time.time()*1000)}
    stories.append(s); save_data()
    socketio.emit('new_story',s)
    return jsonify({'ok':True})

@app.route('/api/posts')
def get_posts(): return jsonify({'posts':posts})

@app.route('/api/posts/create', methods=['POST'])
def create_post():
    data=request.json
    p={'id':str(uuid.uuid4()),'userId':data.get('userId'),'userName':data.get('userName'),'userPhoto':data.get('userPhoto'),'caption':data.get('caption',''),'photo':data.get('photo'),'likes':[],'comments':[],'ts':int(time.time()*1000)}
    posts.append(p); save_data()
    socketio.emit('new_post',p)
    return jsonify({'ok':True})

@app.route('/api/posts/like', methods=['POST'])
def like_post():
    data=request.json
    p=next((x for x in posts if x['id']==data.get('postId')),None)
    if p:
        uid=data.get('userId')
        if uid in p['likes']: p['likes'].remove(uid)
        else: p['likes'].append(uid)
        save_data()
    return jsonify({'ok':True})

@app.route('/api/posts/comment', methods=['POST'])
def comment_post():
    data=request.json
    p=next((x for x in posts if x['id']==data.get('postId')),None)
    if p:
        c={'id':str(uuid.uuid4()),'userId':data.get('userId'),'userName':data.get('userName'),'userPhoto':data.get('userPhoto'),'text':data.get('text'),'ts':int(time.time()*1000)}
        p['comments'].append(c); save_data()
    return jsonify({'ok':True})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin','*')
    response.headers.add('Access-Control-Allow-Headers','Content-Type')
    response.headers.add('Access-Control-Allow-Methods','GET,POST,OPTIONS')
    return response

@socketio.on('join_user')
def on_join(data): join_room(data.get('userId'))

if __name__=='__main__':
    print("\n🔴 PARTEGEUR by REDrock — Full App")
    socketio.run(app,host='0.0.0.0',port=5000,debug=False)
