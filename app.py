from flask import Flask, render_template_string # type: ignore
import webbrowser
import threading

app = Flask(__name__)

# HTML (el mismo que te hice antes pero embebido en Python)
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Rodrierr – Buscador</title>
  <style>
    :root {
      --bg: #ffffff;
      --text: #202124;
      --accent: #4285f4;
      --border: #dadce0;
      --shadow: rgba(0,0,0,.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;
      display: grid;
      place-items: start center;
      min-height: 100dvh;
      padding: 48px 16px;
    }
    .logo {
      font-size: clamp(28px, 6vw, 56px);
      font-weight: 800;
      letter-spacing: .5px;
      margin: 24px 0 12px;
      user-select: none;
    }
    .logo .r { color: #ea4335; }
    .logo .o { color: #fbbc05; }
    .logo .d { color: #4285f4; }
    .logo .i { color: #34a853; }
    .logo .e { color: #ea4335; }
    .logo .rr { color: #fbbc05; }

    .search-card { width: min(720px, 100%); }
    .searchbar {
      display: flex;
      align-items: center;
      gap: 10px;
      background: #fff;
      border: 1px solid var(--border);
      border-radius: 24px;
      padding: 10px 16px;
      box-shadow: 0 2px 10px var(--shadow);
      position: relative;
    }
    .searchbar input {
      flex: 1;
      font-size: 18px;
      border: none;
      outline: none;
      background: transparent;
      padding: 6px 2px;
    }
    .btn {
      border: none;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      padding: 10px 16px;
      border-radius: 18px;
      cursor: pointer;
    }
    .btn:active { transform: translateY(1px); }

    .suggestions { position: relative; margin-top: 6px; }
    .suggestions ul {
      list-style: none;
      margin: 0;
      padding: 6px 0;
      border: 1px solid var(--border);
      border-top: none;
      border-radius: 0 0 16px 16px;
      box-shadow: 0 8px 16px var(--shadow);
      background: #fff;
      overflow: hidden;
    }
    .suggestions li {
      padding: 10px 16px;
      cursor: pointer;
    }
    .suggestions li:hover,
    .suggestions li.active { background: #f1f3f4; }

    .history { margin-top: 18px; border-top: 1px dashed var(--border); padding-top: 12px; }
    .history-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }
    .history h3 { margin: 0; font-size: 16px; opacity: .9; }
    .history button {
      background: transparent;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 6px 10px;
      cursor: pointer;
    }
    .chips { display: flex; flex-wrap: wrap; gap: 8px; }
    .chip {
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: 16px;
      cursor: pointer;
      background: #fff;
    }
    .chip:hover { background: #f7f8f9; }
  </style>
</head>
<body>
  <main class="search-card">
    <div class="logo"><span class="r">R</span><span class="o">o</span><span class="d">d</span><span class="i">r</span><span class="e">i</span><span class="rr">err</span></div>

    <div class="searchbar">
      <input id="q" type="text" placeholder="Busca con Rodrierr..." autocomplete="off" />
      <button id="searchBtn" class="btn">Buscar</button>
    </div>

    <div class="suggestions" id="suggestions" style="display:none;">
      <ul id="suggestions-list"></ul>
    </div>

    <section class="history">
      <div class="history-header">
        <h3>Historial</h3>
        <button id="clear-history">Limpiar</button>
      </div>
      <div id="history-chips" class="chips"></div>
    </section>
  </main>

  <script>
    const BASE_SUGERENCIAS = [
      "Python","Ciberseguridad","Inteligencia Artificial",
      "Big Data","Redes de Datos","Rodrierr buscador",
      "Machine Learning","ChatGPT","Programación en Python",
      "Google vs Rodrierr","Análisis de datos","Algoritmos"
    ];
    const MAX_HISTORY = 50;
    let history = [];
    let activeIndex = -1;

    const input = document.getElementById('q');
    const searchBtn = document.getElementById('searchBtn');
    const sugWrap = document.getElementById('suggestions');
    const sugList = document.getElementById('suggestions-list');
    const chips = document.getElementById('history-chips');
    const clearBtn = document.getElementById('clear-history');

    const loadHistory = () => {
      try { history = JSON.parse(localStorage.getItem('rodrierr_history')||'[]'); }
      catch { history = []; }
    };
    const saveHistory = () => localStorage.setItem('rodrierr_history', JSON.stringify(history));

    const dedup = arr => Array.from(new Set(arr));
    const combinedPool = () => dedup([...history, ...BASE_SUGERENCIAS]);
    const filtered = t => !t ? [] : combinedPool().filter(s => s.toLowerCase().includes(t.toLowerCase())).slice(0,3);

    const renderSuggestions = items => {
      sugList.innerHTML = '';
      activeIndex = -1;
      if (!items.length) { sugWrap.style.display = 'none'; return; }
      items.forEach(text => {
        const li = document.createElement('li');
        li.textContent = text;
        li.addEventListener('mousedown', e => { e.preventDefault(); input.value = text; search(); });
        sugList.appendChild(li);
      });
      sugWrap.style.display = 'block';
    };

    const renderHistory = () => {
      chips.innerHTML = '';
      history.forEach(q => {
        const chip = document.createElement('button');
        chip.className = 'chip'; chip.textContent = q;
        chip.addEventListener('click', () => { input.value = q; search(); });
        chips.appendChild(chip);
      });
    };

    const addToHistory = q => {
      const val = q.trim(); if (!val) return;
      const i = history.indexOf(val); if (i !== -1) history.splice(i,1);
      history.unshift(val); if (history.length>MAX_HISTORY) history.pop();
      saveHistory(); renderHistory();
    };

    const search = () => {
      const q = input.value.trim(); if (!q) return;
      addToHistory(q);
      window.open('https://www.google.com/search?q='+encodeURIComponent(q), '_blank');
      renderSuggestions([]);
    };

    input.addEventListener('input', () => renderSuggestions(filtered(input.value)));
    input.addEventListener('keydown', e => {
      const items = [...sugList.querySelectorAll('li')];
      if (e.key==='ArrowDown' && items.length) { e.preventDefault(); activeIndex=(activeIndex+1)%items.length; items.forEach((el,i)=>el.classList.toggle('active',i===activeIndex)); input.value=items[activeIndex].textContent; }
      if (e.key==='ArrowUp' && items.length) { e.preventDefault(); activeIndex=(activeIndex-1+items.length)%items.length; items.forEach((el,i)=>el.classList.toggle('active',i===activeIndex)); input.value=items[activeIndex].textContent; }
      if (e.key==='Enter') { e.preventDefault(); search(); }
      if (e.key==='Escape') renderSuggestions([]);
    });
    searchBtn.addEventListener('click', search);
    clearBtn.addEventListener('click', ()=>{history=[];saveHistory();renderHistory();});
    window.addEventListener('click', e=>{ if(!e.target.closest('.searchbar') && !e.target.closest('.suggestions')) renderSuggestions([]); });

    loadHistory(); renderHistory();
  </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

def abrir_navegador():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1, abrir_navegador).start()
    app.run(debug=False)
