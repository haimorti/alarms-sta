from __future__ import annotations

import json

from html import escape
from typing import Any


def _status_badge(status: dict[str, Any]) -> str:
    state = str(status.get("state", "quiet"))
    title = escape(str(status.get("title", "אין התרעה פעילה כרגע")))
    return f'<div class="status-pill status-{state}">{title}</div>'


def _timeline_items(active_events: list[dict[str, Any]]) -> str:
    return "".join(
        f"<li><span>{escape(str(event['normalized_type']))}</span><strong>#{event['id']}</strong><time>{escape(str(event['started_at']))}</time></li>"
        for event in active_events[:6]
    ) or '<li class="empty-row">אין כרגע אירועים פעילים במאגר.</li>'


def render_home_page(health: dict[str, Any], active_events: list[dict[str, Any]]) -> str:
    has_active = bool(active_events)
    timeline = _timeline_items(active_events)
    app_state = {"state": "warning", "title": "יש התרעה פעילה כלשהי"} if has_active else {"state": "quiet", "title": "אין התרעה פעילה כרגע"}
    initial_payload = json.dumps({"health": health, "active_events": active_events}, ensure_ascii=False)
    return f"""
    <html lang="he" dir="rtl">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Alarms STA</title>
      <style>
        :root {{ color-scheme: light; --card:#fffdf9; --ink:#1f2937; --muted:#6b7280; --line:#e8ded0; --brand:#185adb; --brand-soft:#e8f0ff; --warn:#b45309; --warn-soft:#fff3df; --alarm:#b42318; --alarm-soft:#feeceb; --ok:#166534; --ok-soft:#eaf8ee; }}
        * {{ box-sizing:border-box; }} body {{ margin:0; font-family:Arial,"Noto Sans Hebrew",sans-serif; background:linear-gradient(180deg,#fbf8f3 0%,#f4efe8 100%); color:var(--ink); }}
        .shell {{ max-width:1100px; margin:0 auto; padding:32px 20px 56px; }} .hero {{ display:grid; grid-template-columns:2fr 1fr; gap:20px; align-items:stretch; }}
        .card {{ background:var(--card); border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 10px 30px rgba(15,23,42,.05); }}
        h1 {{ margin:0 0 12px; font-size:40px; line-height:1.1; }} h2 {{ margin:0 0 14px; font-size:22px; }} p {{ margin:0; line-height:1.7; color:var(--muted); }}
        .status-pill {{ display:inline-flex; align-items:center; border-radius:999px; padding:10px 14px; font-size:14px; font-weight:700; margin-bottom:16px; }} .status-warning {{ background:var(--warn-soft); color:var(--warn); }} .status-quiet,.status-ended {{ background:var(--ok-soft); color:var(--ok); }} .status-alarm {{ background:var(--alarm-soft); color:var(--alarm); }}
        .update-clock {{ display:flex; align-items:center; gap:8px; margin-bottom:14px; color:var(--muted); font-size:14px; }} .update-clock strong {{ color:var(--ink); font-size:16px; }}
        .hero-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:14px; margin-top:20px; }} .metric {{ padding:16px; border-radius:18px; background:#faf7f2; border:1px solid var(--line); }} .metric strong {{ display:block; font-size:26px; margin-top:6px; }}
        .search {{ display:flex; flex-direction:column; gap:12px; }} input {{ width:100%; padding:14px 16px; font-size:16px; border-radius:16px; border:1px solid var(--line); background:white; }}
        .hint {{ font-size:13px; color:var(--muted); }} .actions a {{ display:inline-flex; margin-top:8px; color:var(--brand); text-decoration:none; font-weight:700; }}
        .grid {{ display:grid; grid-template-columns:1.2fr .8fr; gap:20px; margin-top:20px; }} ul {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:10px; }} li {{ display:flex; justify-content:space-between; gap:12px; padding:14px 16px; border-radius:16px; background:#fcfaf7; border:1px solid var(--line); }} li span, li time {{ color:var(--muted); font-size:14px; }} .empty-row {{ justify-content:flex-start; color:var(--muted); }} .recent-chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }} .chip {{ border:none; background:var(--brand-soft); color:var(--brand); padding:10px 12px; border-radius:999px; cursor:pointer; }}
        @media (max-width: 860px) {{ .hero,.grid,.hero-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:32px; }} }}
      </style>
    </head>
    <body>
      <main class="shell">
        <section class="hero">
          <div class="card">
            {_status_badge(app_state)}
            <div class="update-clock">🕒 <span>שעת עדכון אחרונה</span><strong id="last-updated-clock">—</strong></div>
            <h1>מערכת התרעות עם הסתברות יישובית.</h1>
            <p>המסך מתעדכן אוטומטית כל 3 שניות. המשתמש מקבל תמונת מצב ברורה: שקט, התראה מוקדמת, אזעקה בפועל או סיום אירוע.</p>
            <div class="hero-grid">
              <div class="metric"><span>Raw events</span><strong id="raw-events-count">{escape(str(health.get('raw_events', 0)))}</strong></div>
              <div class="metric"><span>Normalized events</span><strong id="normalized-events-count">{escape(str(health.get('normalized_events', 0)))}</strong></div>
              <div class="metric"><span>Last fetch</span><strong id="last-fetch-metric" style="font-size:18px">{escape(str(health.get('last_fetch_at') or 'טרם התקבל'))}</strong></div>
            </div>
          </div>
          <div class="card search">
            <h2>בחירת יישוב</h2>
            <p>חיפוש חופשי בעברית, כולל מקפים, רווחים ותתי-אזורים.</p>
            <input id="settlement-search" placeholder="לדוגמה: נתניה - מזרח / חוות יאיר" autocomplete="off" />
            <div class="hint">לחיצה על Enter תפתח את מסך התוצאה של היישוב.</div>
            <div class="recent-chips" id="recent-settlements"></div>
            <div class="actions"><a href="/settlements/search?q=נתניה">API לחיפוש יישובים</a></div>
          </div>
        </section>
        <section class="grid">
          <div class="card">
            <h2>אירועים אחרונים</h2>
            <ul id="active-events-timeline">{timeline}</ul>
          </div>
          <div class="card">
            <h2>מה המשתמש יראה</h2>
            <ul>
              <li><strong>שקט</strong><span>אין התרעה פעילה כרגע</span></li>
              <li><strong>התראה</strong><span>צפויות להתקבל התרעות</span></li>
              <li><strong>אזעקה</strong><span>צבע אדום</span></li>
              <li><strong>סיום</strong><span>האירוע הסתיים</span></li>
            </ul>
          </div>
        </section>
      </main>
      <script>
        const initialPayload = {initial_payload};
        const input = document.getElementById('settlement-search');
        const recentsRoot = document.getElementById('recent-settlements');
        const storageKey = 'alarms-sta-recent-settlements';
        const readRecents = () => {{ try {{ return JSON.parse(localStorage.getItem(storageKey) || '[]'); }} catch (error) {{ return []; }} }};
        const writeRecents = (value) => localStorage.setItem(storageKey, JSON.stringify(value.slice(0, 6)));
        const formatClock = (value) => new Date(value).toLocaleTimeString('he-IL', {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
        const openSettlement = (value) => {{
          if (!value.trim()) return;
          const recents = [value.trim(), ...readRecents().filter(item => item !== value.trim())];
          writeRecents(recents);
          window.location.href = `/probability/current?settlement=${{encodeURIComponent(value.trim())}}&format=html`;
        }};
        const renderRecents = () => {{
          const recents = readRecents();
          recentsRoot.innerHTML = recents.map(item => `<button class="chip" type="button">${{item}}</button>`).join('');
          recentsRoot.querySelectorAll('button').forEach((button) => button.addEventListener('click', () => openSettlement(button.textContent || '')));
        }};
        const statusRoot = document.querySelector('.hero .card');
        const rawEventsCount = document.getElementById('raw-events-count');
        const normalizedEventsCount = document.getElementById('normalized-events-count');
        const lastFetchMetric = document.getElementById('last-fetch-metric');
        const lastUpdatedClock = document.getElementById('last-updated-clock');
        const timelineRoot = document.getElementById('active-events-timeline');
        const renderStatusBadge = (hasActive) => {{
          const title = hasActive ? 'יש התרעה פעילה כלשהי' : 'אין התרעה פעילה כרגע';
          const stateClass = hasActive ? 'status-warning' : 'status-quiet';
          const badge = statusRoot.querySelector('.status-pill');
          badge.className = `status-pill ${{stateClass}}`;
          badge.textContent = title;
        }};
        const renderTimeline = (events) => {{
          timelineRoot.innerHTML = events.length
            ? events.slice(0, 6).map((event) => `<li><span>${{event.normalized_type}}</span><strong>#${{event.id}}</strong><time>${{event.started_at}}</time></li>`).join('')
            : '<li class="empty-row">אין כרגע אירועים פעילים במאגר.</li>';
        }};
        const markRefreshTime = (value = new Date().toISOString()) => {{
          lastUpdatedClock.textContent = formatClock(value);
        }};
        const applyHomePayload = (payload) => {{
          const health = payload.health || {{}};
          const events = payload.active_events || [];
          rawEventsCount.textContent = String(health.raw_events ?? '0');
          normalizedEventsCount.textContent = String(health.normalized_events ?? '0');
          lastFetchMetric.textContent = health.last_fetch_at || 'טרם התקבל';
          renderStatusBadge(events.length > 0);
          renderTimeline(events);
          markRefreshTime();
        }};
        const pollHomePage = async () => {{
          try {{
            const [healthResponse, activeEventsResponse] = await Promise.all([fetch('/health'), fetch('/events/active')]);
            if (!healthResponse.ok || !activeEventsResponse.ok) return;
            const [health, activeEvents] = await Promise.all([healthResponse.json(), activeEventsResponse.json()]);
            applyHomePayload({{ health, active_events: activeEvents }});
          }} catch (error) {{
            console.warn('Failed to refresh home page', error);
          }}
        }};
        input.addEventListener('keydown', (event) => {{ if (event.key === 'Enter') openSettlement(input.value); }});
        applyHomePayload(initialPayload);
        renderRecents();
        window.setInterval(pollHomePage, 3000);
      </script>
    </body></html>
    """
def render_settlement_page(payload: dict[str, Any]) -> str:
    settlement = payload.get("settlement", {})
    snapshot = payload.get("snapshot", {})
    risk_window = payload.get("risk_window", {}) or {}
    status = payload.get("status", {"state": "quiet", "title": "אין התרעה פעילה כרגע"})
    refreshed_at = escape(str(payload.get("refreshed_at") or ""))
    last_fetch_at = escape(str(payload.get("last_fetch_at") or "טרם התקבל"))
    if not snapshot:
        return f"""
        <html lang="he" dir="rtl"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
        <meta http-equiv="refresh" content="3" />
        <style>body{{font-family:Arial,'Noto Sans Hebrew',sans-serif;background:#f6f3ee;color:#1f2937;padding:24px}} .card{{max-width:760px;margin:0 auto;background:#fffdf9;border:1px solid #e8ded0;border-radius:24px;padding:24px}} .update-clock{{display:flex;align-items:center;gap:8px;margin-bottom:14px;color:#6b7280;font-size:14px}} .update-clock strong{{color:#1f2937}}</style></head>
        <body><div class="card">{_status_badge(status)}<div class="update-clock">🕒 <span>שעת עדכון אחרונה</span><strong>{refreshed_at}</strong></div><div class="update-clock"><span>Last fetch</span><strong>{last_fetch_at}</strong></div><h1>{escape(str(settlement.get('name_he', 'Unknown')))}</h1><p>{escape(str(payload.get('message', 'No probability snapshot available')))}</p></div></body></html>"""

    def component(title: str, score: Any, label: Any, explanation: Any, confidence: Any, weighted: bool = False) -> str:
        extra_class = ' weighted' if weighted else ''
        return (
            f'<article class="score-card{extra_class}"><span>{escape(title)}</span><strong>{escape(str(score))}</strong>'
            f'<em>{escape(str(label))}</em><p>{escape(str(explanation))}</p><small>Confidence: {escape(str(confidence))}</small></article>'
        )

    return f"""
    <html lang="he" dir="rtl">
    <head><meta charset="utf-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/><meta http-equiv="refresh" content="3" /><title>{escape(str(settlement.get('name_he')))}</title>
    <style>
      :root {{ --card:#fffdf9; --line:#e8ded0; --ink:#1f2937; --muted:#6b7280; --brand:#185adb; }}
      * {{ box-sizing:border-box; }} body {{ margin:0; font-family:Arial,"Noto Sans Hebrew",sans-serif; background:linear-gradient(180deg,#fbf8f3 0%,#f4efe8 100%); color:var(--ink); }}
      .shell {{ max-width:1100px; margin:0 auto; padding:32px 20px 56px; }} .card {{ background:var(--card); border:1px solid var(--line); border-radius:24px; padding:24px; box-shadow:0 10px 30px rgba(15,23,42,.05); }}
      .hero {{ display:grid; grid-template-columns:1.35fr .65fr; gap:20px; }} h1 {{ margin:0 0 10px; font-size:42px; }} p {{ color:var(--muted); line-height:1.7; }}
      .score-grid {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin-top:20px; }} .score-card {{ border:1px solid var(--line); border-radius:20px; padding:18px; background:#fcfaf7; }} .score-card strong {{ display:block; margin-top:8px; font-size:38px; line-height:1; }} .score-card em {{ display:inline-block; margin-top:10px; color:var(--brand); font-style:normal; font-weight:700; }} .score-card p {{ min-height:78px; }} .score-card small {{ color:var(--muted); }} .score-card.weighted {{ background:linear-gradient(180deg,#edf3ff 0%,#f7fbff 100%); border-color:#cadeff; }}
      .facts {{ display:grid; grid-template-columns:repeat(2,1fr); gap:14px; margin-top:20px; }} .fact {{ padding:16px; border:1px solid var(--line); border-radius:18px; background:#fcfaf7; }} .list {{ display:flex; flex-direction:column; gap:12px; }} .list .fact strong {{ display:block; margin-bottom:8px; }} .back {{ color:var(--brand); text-decoration:none; font-weight:700; }}
      .status-pill {{ display:inline-flex; align-items:center; border-radius:999px; padding:10px 14px; font-size:14px; font-weight:700; margin-bottom:16px; }} .status-warning {{ background:#fff3df; color:#b45309; }} .status-quiet,.status-ended {{ background:#eaf8ee; color:#166534; }} .status-alarm {{ background:#feeceb; color:#b42318; }}
      .update-clock {{ display:flex; align-items:center; gap:8px; margin-bottom:12px; color:var(--muted); font-size:14px; }} .update-clock strong {{ color:var(--ink); font-size:16px; }}
      @media (max-width: 860px) {{ .hero,.score-grid,.facts {{ grid-template-columns:1fr; }} h1 {{ font-size:32px; }} }}
    </style></head>
    <body><main class="shell">
      <a class="back" href="/">← חזרה למסך הראשי</a>
      <section class="hero">
        <div class="card">
          {_status_badge(status)}
          <div class="update-clock">🕒 <span>שעת עדכון אחרונה</span><strong>{refreshed_at}</strong></div>
          <div class="update-clock"><span>Last fetch</span><strong>{last_fetch_at}</strong></div>
          <h1>{escape(str(settlement.get('name_he')))}</h1>
          <p>העמוד מתרענן אוטומטית כל 3 שניות, ולכן כאשר תופיע התרעה חדשה או יתעדכנו הנתונים של היישוב — התצוגה תתעדכן לבד.</p>
          <div class="facts">
            <div class="fact"><strong>היישוב נכלל כרגע באירוע</strong><span>כן — נמצא בהתראה המוקדמת הפעילה</span></div>
            <div class="fact"><strong>שלב אזור ההתרעה</strong><span>{escape(str(risk_window.get('phase_label', 'current_estimate')))}</span></div>
            <div class="fact"><strong>התרעת אזעקה בפועל</strong><span>{'כן' if payload.get('latest_alarm') else 'טרם זוהתה אזעקה תואמת'}</span></div>
            <div class="fact"><strong>Confidence סופי</strong><span>{escape(str(snapshot.get('weighted_confidence_label')))} ({escape(str(snapshot.get('weighted_confidence')))})</span></div>
          </div>
        </div>
        <div class="card list">
          <div class="fact"><strong>הסבר קצר</strong><span>{escape(str(snapshot.get('weighted_explanation')))}</span></div>
          <div class="fact"><strong>מה זה אומר בפועל</strong><span>הציון המרחבי משקף התאמה לאזור ההתרעה, הציון ההיסטורי משקף דפוסי עבר, והציון המשוקלל נותן החלטה סופית קריאה למשתמש.</span></div>
        </div>
      </section>
      <section class="score-grid">
        {component('Spatial score', snapshot.get('spatial_score'), snapshot.get('spatial_label'), snapshot.get('spatial_explanation'), snapshot.get('spatial_confidence'))}
        {component('Historical score', snapshot.get('historical_score'), snapshot.get('historical_label'), snapshot.get('historical_explanation'), snapshot.get('historical_confidence'))}
        {component('Weighted score', snapshot.get('weighted_score'), snapshot.get('weighted_label'), snapshot.get('weighted_explanation'), snapshot.get('weighted_confidence'), weighted=True)}
      </section>
    </main></body></html>
    """


def render_event_page(payload: dict[str, Any]) -> str:
    if not payload:
        return "<html><body><p>Event not found.</p></body></html>"
    locations = "".join(f"<li>{escape(str(loc['location_name_raw']))}</li>" for loc in payload.get("locations", [])) or "<li>No locations</li>"
    return f"""
    <html><body>
      <h1>Event {payload.get('id')}</h1>
      <p>Type: {escape(str(payload.get('normalized_type')))}</p>
      <p>Started at: {escape(str(payload.get('started_at')))}</p>
      <h2>Locations</h2>
      <ul>{locations}</ul>
    </body></html>
    """
