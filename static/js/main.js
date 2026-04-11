const QUESTIONS = [
  { key:"business_vs_market",        text:"1. Би market timing (зах зээл таах) биш, business analysis (бизнес шинжилгээ) хийж байна уу?",            cat:"Thinking",    lo:"Market timing",       hi:"Business analysis",  hardFail:null, redFlag:4 },
  { key:"anchoring",                 text:"2. Би худалдаж авсан үнэдээ уягдаагүй байна уу? (Anchoring bias — анхны үнэд хэт баригдах алдаа)",        cat:"Temperament", lo:"Маш их уягдсан",      hi:"Уягдаагүй",          hardFail:null, redFlag:4 },
  { key:"growth_assumption",         text:"3. Миний growth assumption (өсөлтийн төсөөлөл) бодитой, хэт өөдрөг биш үү?",                              cat:"Valuation",   lo:"Хэт өөдрөг",          hi:"Бодитой",            hardFail:null, redFlag:4 },
  { key:"leverage_and_concentration",text:"4. Leverage болон hidden leverage (хэт төвлөрөл) байхгүй юу?",                                            cat:"Risk",        lo:"Их leverage",         hi:"Leverage байхгүй",   hardFail:2,    redFlag:4 },
  { key:"big_picture",               text:"5. Би detail-д живээгүй, big picture-ээ алдаагүй юу?",                                                    cat:"Thinking",    lo:"Big picture алдсан",  hi:"Тодорхой харж байна",hardFail:null, redFlag:4 },
  { key:"complexity",                text:"6. Би энэ хувьцааг авах/барих/зарах шалтгаанаа энгийнээр, бүрэн ойлгож байна уу?",                                          cat:"Thinking",    lo:"Маш төвөгтэй",        hi:"Энгийн",             hardFail:null, redFlag:4 },
  { key:"self_limiting",             text:"7. Би өөрийгөө unnecessary хязгаарлаагүй, жинхэнэ боломжийг хаагаагүй юу?",                              cat:"Opportunity", lo:"Хязгаарласан",        hi:"Чөлөөтэй",           hardFail:null, redFlag:3 },
  { key:"fresh_start",               text:"8. Хэрэв өнөөдөр 0-ээс эхэлсэн бол би энэ хувьцааг одоо авах байсан уу? (Fresh start test)",             cat:"Decision",    lo:"Авахгүй байсан",      hi:"Тодорхой авна",      hardFail:2,    redFlag:4 },
  { key:"ego",                       text:"9. Энэ decision миний ego (өөрийгөө зөв гэж батлах хүсэл)-г хамгаалаагүй юу?",                           cat:"Temperament", lo:"Ego давамгайлж байна",hi:"Ego байхгүй",        hardFail:null, redFlag:4 },
  { key:"survival",                  text:"10. Worst-case scenario-д би survive чадах уу?",                                                          cat:"Risk",        lo:"Survive хийхгүй",    hi:"Мэдээж survive",     hardFail:3,    redFlag:4 },
];

let current = 0;
let answers = {};
let timerInterval = null;

function startTimer() {
  const t0 = Date.now();
  timerInterval = setInterval(() => {
    const e = Math.floor((Date.now() - t0) / 1000);
    const m = String(Math.floor(e / 60)).padStart(2,'0');
    const s = String(e % 60).padStart(2,'0');
    document.getElementById('timer').textContent = m+':'+s;
  }, 1000);
}

function renderQ() {
  const q = QUESTIONS[current];
  const val = answers[q.key] !== undefined ? answers[q.key] : 5;

  document.getElementById('qNum').textContent = String(current+1).padStart(2,'0');
  document.getElementById('qCat').textContent = q.cat;
  document.getElementById('qText').textContent = q.text;
  document.getElementById('sliderLo').textContent = q.lo;
  document.getElementById('sliderHi').textContent = q.hi;

  const hfEl = document.getElementById('qHardFail');
  if (q.hardFail !== null) {
    hfEl.textContent = '⚠ Hard fail: ' + q.hardFail + ' ба түүнээс бага оноо → AUTO NO-GO';
    hfEl.style.display = 'block';
  } else {
    hfEl.style.display = 'none';
  }

  const slider = document.getElementById('slider');
  slider.value = val;
  document.getElementById('scoreNum').textContent = val;
  slider.oninput = function() {
    document.getElementById('scoreNum').textContent = this.value;
    answers[q.key] = parseInt(this.value);
  };

  document.getElementById('progressFill').style.width = ((current+1)/10*100)+'%';
  document.getElementById('btnBack').disabled = current === 0;
  document.getElementById('btnNext').textContent = current === 9 ? 'Үр дүн →' : 'Дараах →';
}

function goNext() {
  const q = QUESTIONS[current];
  if (answers[q.key] === undefined) answers[q.key] = 5;
  if (current < 9) { current++; renderQ(); }
  else submitScores();
}

function goBack() {
  if (current > 0) { current--; renderQ(); }
}

async function submitScores() {
  const payload = {};
  QUESTIONS.forEach(q => { payload[q.key] = answers[q.key] !== undefined ? answers[q.key] : 5; });
  const res = await fetch('/score', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({answers: payload}),
  });
  showResult(await res.json());
}

function showResult(data) {
  document.getElementById('quizView').classList.add('hidden');
  document.getElementById('resultView').classList.remove('hidden');
  clearInterval(timerInterval);

  document.getElementById('resScore').textContent = data.score;
  const offset = 326.7 - (data.score / 100) * 326.7;
  setTimeout(() => { document.getElementById('ringFill').style.strokeDashoffset = offset; }, 100);

  const badge = document.getElementById('verdictBadge');
  badge.textContent = data.decision;
  const cls = data.decision === 'STRONG BUY / ADD' ? 'badge-go'
    : data.decision === 'SMALL POSITION / WATCHLIST' ? 'badge-watch'
    : data.decision === 'HOLD / NEED MORE WORK' ? 'badge-hold'
    : 'badge-nogo';
  badge.className = 'verdict-badge ' + cls;
  document.getElementById('verdictInterp').textContent = data.interpretation;

  // Hard fails
  const hfWrap = document.getElementById('hardFailWrap');
  if (data.hard_fails && data.hard_fails.length) {
    hfWrap.innerHTML = '<h3 class="section-heading">Hard fail triggers</h3>' +
      data.hard_fails.map(k => `<div class="hardfail-item">${k.replace(/_/g,' ')}</div>`).join('');
    hfWrap.style.display = 'block';
  } else {
    hfWrap.style.display = 'none';
  }

  // Category breakdown
  let catHtml = '';
  for (const [cat, val] of Object.entries(data.category_breakdown)) {
    catHtml += `<div class="cat-row">
      <span class="cat-label">${cat}</span>
      <div class="cat-bar-track"><div class="cat-bar-fill" style="width:${val}%"></div></div>
      <span class="cat-score-val">${val}/100</span>
    </div>`;
  }
  document.getElementById('catBreakdown').innerHTML = catHtml;

  // Red flags
  let flagHtml = '';
  if (data.red_flags.length) {
    data.red_flags.forEach(f => { flagHtml += `<div class="flag-item">${f}</div>`; });
  } else {
    flagHtml = '<div class="no-flags">Red flag байхгүй</div>';
  }
  document.getElementById('flagsWrap').innerHTML = flagHtml;

  // Action
  document.getElementById('sizingBox').textContent = data.action;

  // Q scores
  let qsHtml = '';
  for (const [key, val] of Object.entries(data.normalized_scores)) {
    const q = QUESTIONS.find(q => q.key === key);
    const isHardFail = data.hard_fails && data.hard_fails.includes(key);
    qsHtml += `<div class="qs-item ${isHardFail ? 'qs-hardfail' : ''}">
      <span class="qs-key">${key.replace(/_/g,' ')}</span>
      <span class="qs-val">${val}/10</span>
    </div>`;
  }
  document.getElementById('qScoresGrid').innerHTML = qsHtml;
}

function restart() {
  current = 0;
  answers = {};
  document.getElementById('resultView').classList.add('hidden');
  document.getElementById('quizView').classList.remove('hidden');
  startTimer();
  renderQ();
}

startTimer();
renderQ();
