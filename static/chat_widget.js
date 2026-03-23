/**
 * TriggersAPI Chat Widget
 * Self-initializing floating chatbot widget.
 * Include via <script src="/static/chat_widget.js"></script>
 */
(function () {
  'use strict';

  // ─── Constants ────────────────────────────────────────────────────────────
  const COLORS = {
    primary:     '#FF4F00',
    primaryDark: '#a93100',
    bg:          '#f8f9fa',
    text:        '#1a1a1a',
    white:       '#ffffff',
    gray100:     '#f3f4f6',
    gray200:     '#e5e7eb',
    gray400:     '#9ca3af',
    gray700:     '#374151',
  };

  const WELCOME_MESSAGE =
    "Hi! I'm the TriggersAPI assistant. I can help you with event ingestion, " +
    'delivery setup, subscriptions, and debugging. What would you like to know?';

  const STORAGE_KEY_MODEL = 'triggersapi_selectedModel';

  // ─── State ────────────────────────────────────────────────────────────────
  let isOpen          = false;
  let isWaiting       = false;
  let conversationHistory = [];   // [{role, content}]
  let selectedModel   = localStorage.getItem(STORAGE_KEY_MODEL) || '';
  let sessionId       = _uuid();
  let hasNewResponse  = false;
  let welcomeShown    = false;

  // ─── Helpers ──────────────────────────────────────────────────────────────
  function _uuid() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
      const r = (Math.random() * 16) | 0;
      return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
  }

  function _el(tag, attrs, children) {
    const el = document.createElement(tag);
    if (attrs) {
      Object.entries(attrs).forEach(([k, v]) => {
        if (k === 'style' && typeof v === 'object') {
          Object.assign(el.style, v);
        } else if (k.startsWith('data-')) {
          el.setAttribute(k, v);
        } else if (k === 'className') {
          el.className = v;
        } else {
          el[k] = v;
        }
      });
    }
    if (children) {
      (Array.isArray(children) ? children : [children]).forEach(c => {
        if (c == null) return;
        el.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
      });
    }
    return el;
  }

  // ─── Markdown-lite renderer ───────────────────────────────────────────────
  function renderMarkdown(text) {
    const container = document.createDocumentFragment();

    // Split by code blocks first
    const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    function processInline(raw) {
      // bold, inline code, bullet lists, line breaks
      const lines = raw.split('\n');
      const frag = document.createDocumentFragment();

      lines.forEach((line, i) => {
        // Bullet list
        const bulletMatch = line.match(/^[\s]*[-*+]\s+(.*)$/);
        if (bulletMatch) {
          const li = _el('div', {
            style: {
              display: 'flex',
              alignItems: 'flex-start',
              gap: '6px',
              margin: '2px 0',
            },
          });
          const dot = _el('span', { style: { flexShrink: '0', marginTop: '2px' } }, ['•']);
          const content = _el('span');
          applyInlineStyles(content, bulletMatch[1]);
          li.appendChild(dot);
          li.appendChild(content);
          frag.appendChild(li);
        } else {
          const span = _el('span');
          applyInlineStyles(span, line);
          frag.appendChild(span);
          if (i < lines.length - 1) {
            frag.appendChild(_el('br'));
          }
        }
      });

      return frag;
    }

    function applyInlineStyles(el, text) {
      // Bold: **text** or __text__
      const parts = text.split(/(\*\*[\s\S]*?\*\*|`[^`]+`)/g);
      parts.forEach(part => {
        if (part.startsWith('**') && part.endsWith('**')) {
          const b = _el('strong', {}, [part.slice(2, -2)]);
          el.appendChild(b);
        } else if (part.startsWith('`') && part.endsWith('`') && part.length > 2) {
          const code = _el('code', {
            style: {
              background: 'rgba(0,0,0,0.08)',
              padding: '1px 4px',
              borderRadius: '3px',
              fontFamily: 'monospace',
              fontSize: '0.85em',
            },
          }, [part.slice(1, -1)]);
          el.appendChild(code);
        } else {
          el.appendChild(document.createTextNode(part));
        }
      });
    }

    while ((match = codeBlockRegex.exec(text)) !== null) {
      // Text before code block
      if (match.index > lastIndex) {
        const before = text.slice(lastIndex, match.index);
        container.appendChild(processInline(before));
      }

      // Code block
      const lang    = match[1] || '';
      const code    = match[2].trimEnd();
      const wrapper = _el('div', {
        style: {
          background:   '#1e1e2e',
          borderRadius: '6px',
          margin:       '6px 0',
          overflow:     'hidden',
        },
      });
      if (lang) {
        const langLabel = _el('div', {
          style: {
            background:  '#2a2a3e',
            color:       '#a0a0b8',
            fontSize:    '0.7em',
            padding:     '3px 10px',
            fontFamily:  'monospace',
          },
        }, [lang]);
        wrapper.appendChild(langLabel);
      }
      const pre = _el('pre', {
        style: {
          color:      '#cdd6f4',
          fontSize:   '0.8em',
          padding:    '10px 12px',
          margin:     '0',
          overflowX:  'auto',
          fontFamily: 'monospace',
          lineHeight: '1.5',
        },
      }, [code]);
      wrapper.appendChild(pre);
      container.appendChild(wrapper);

      lastIndex = match.index + match[0].length;
    }

    // Remaining text after last code block
    if (lastIndex < text.length) {
      container.appendChild(processInline(text.slice(lastIndex)));
    }

    return container;
  }

  // ─── CSS injection ────────────────────────────────────────────────────────
  function injectStyles() {
    const css = `
      @keyframes tapi-bounce {
        0%,100% { transform: translateY(0);   }
        25%      { transform: translateY(-10px); }
        50%      { transform: translateY(0);   }
        75%      { transform: translateY(-5px); }
      }
      @keyframes tapi-slideUp {
        from { opacity: 0; transform: translateY(20px) scale(0.97); }
        to   { opacity: 1; transform: translateY(0)   scale(1);     }
      }
      @keyframes tapi-fadeIn {
        from { opacity: 0; transform: translateY(6px); }
        to   { opacity: 1; transform: translateY(0);   }
      }
      @keyframes tapi-dot {
        0%,80%,100% { transform: scale(0); opacity: 0.4; }
        40%          { transform: scale(1); opacity: 1;   }
      }
      @keyframes tapi-pulse-dot {
        0%,100% { transform: scale(1);   opacity: 1; }
        50%     { transform: scale(1.3); opacity: 0.7; }
      }

      #tapi-btn {
        position:    fixed;
        bottom:      24px;
        right:       24px;
        z-index:     9999;
        width:       56px;
        height:      56px;
        border-radius: 50%;
        background:  linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark});
        border:      none;
        cursor:      pointer;
        display:     flex;
        align-items: center;
        justify-content: center;
        box-shadow:  0 4px 20px rgba(255,79,0,0.45);
        transition:  transform 0.18s ease, box-shadow 0.18s ease;
        outline:     none;
      }
      #tapi-btn:hover {
        transform:  scale(1.08);
        box-shadow: 0 6px 28px rgba(255,79,0,0.55);
      }
      #tapi-btn:active {
        transform: scale(0.95);
      }
      #tapi-btn.tapi-bounce {
        animation: tapi-bounce 0.9s ease 0.4s 3;
      }
      #tapi-btn .tapi-notif-dot {
        position:     absolute;
        top:          4px;
        right:        4px;
        width:        11px;
        height:       11px;
        border-radius: 50%;
        background:   #fbbf24;
        border:       2px solid white;
        animation:    tapi-pulse-dot 1.4s ease infinite;
      }

      #tapi-panel {
        position:      fixed;
        bottom:        90px;
        right:         24px;
        z-index:       9998;
        width:         400px;
        height:        560px;
        background:    ${COLORS.white};
        border-radius: 16px;
        box-shadow:    0 20px 60px rgba(0,0,0,0.18), 0 4px 16px rgba(0,0,0,0.1);
        display:       flex;
        flex-direction: column;
        overflow:      hidden;
        animation:     tapi-slideUp 0.28s cubic-bezier(0.34,1.56,0.64,1) both;
      }

      @media (max-width: 639px) {
        #tapi-panel {
          width:         100vw;
          height:        100vh;
          bottom:        0;
          right:         0;
          border-radius: 0;
        }
        #tapi-btn {
          bottom: 16px;
          right:  16px;
        }
      }

      /* Header */
      #tapi-header {
        display:         flex;
        align-items:     center;
        gap:             10px;
        padding:         14px 16px;
        background:      linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark});
        flex-shrink:     0;
      }
      #tapi-header-icon {
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif;
        font-size:   24px;
        color:       white;
        font-style:  normal;
        line-height: 1;
        user-select: none;
      }
      #tapi-title {
        flex:        1;
        font-family: Manrope, 'Segoe UI', sans-serif;
        font-weight: 700;
        font-size:   0.95rem;
        color:       white;
        letter-spacing: 0.01em;
      }
      #tapi-model-select {
        font-family:  Inter, 'Segoe UI', sans-serif;
        font-size:    0.72rem;
        background:   rgba(255,255,255,0.18);
        color:        white;
        border:       1px solid rgba(255,255,255,0.3);
        border-radius: 6px;
        padding:      4px 6px;
        cursor:       pointer;
        outline:      none;
        max-width:    140px;
        transition:   background 0.15s;
      }
      #tapi-model-select:hover {
        background: rgba(255,255,255,0.28);
      }
      #tapi-model-select option {
        background: ${COLORS.primaryDark};
        color:      white;
      }
      #tapi-close-btn {
        background:  transparent;
        border:      none;
        cursor:      pointer;
        color:       rgba(255,255,255,0.85);
        font-size:   20px;
        line-height: 1;
        padding:     4px;
        border-radius: 50%;
        display:     flex;
        align-items: center;
        justify-content: center;
        width:       30px;
        height:      30px;
        transition:  background 0.15s, color 0.15s;
        font-family: 'Material Symbols Rounded', 'Material Icons', sans-serif;
        font-style:  normal;
        user-select: none;
      }
      #tapi-close-btn:hover {
        background: rgba(255,255,255,0.2);
        color:      white;
      }

      /* Messages */
      #tapi-messages {
        flex:        1;
        overflow-y:  auto;
        padding:     16px;
        display:     flex;
        flex-direction: column;
        gap:         10px;
        scroll-behavior: smooth;
      }
      #tapi-messages::-webkit-scrollbar {
        width: 5px;
      }
      #tapi-messages::-webkit-scrollbar-track {
        background: transparent;
      }
      #tapi-messages::-webkit-scrollbar-thumb {
        background:    ${COLORS.gray200};
        border-radius: 10px;
      }

      .tapi-msg {
        display:        flex;
        flex-direction: column;
        max-width:      80%;
        animation:      tapi-fadeIn 0.22s ease both;
      }
      .tapi-msg.user {
        align-self:  flex-end;
        align-items: flex-end;
      }
      .tapi-msg.bot {
        align-self:  flex-start;
        align-items: flex-start;
      }
      .tapi-bubble {
        padding:       10px 14px;
        border-radius: 14px;
        font-family:   Inter, 'Segoe UI', sans-serif;
        font-size:     0.875rem;
        line-height:   1.55;
        word-break:    break-word;
      }
      .tapi-msg.user .tapi-bubble {
        background:   ${COLORS.primary};
        color:        white;
        border-bottom-right-radius: 4px;
      }
      .tapi-msg.bot .tapi-bubble {
        background:   ${COLORS.gray100};
        color:        ${COLORS.text};
        border-bottom-left-radius: 4px;
      }
      .tapi-msg-meta {
        font-family: Inter, 'Segoe UI', sans-serif;
        font-size:   0.68rem;
        color:       ${COLORS.gray400};
        margin-top:  4px;
        padding:     0 4px;
      }

      /* Typing indicator */
      #tapi-typing {
        display:        flex;
        align-items:    center;
        gap:            5px;
        padding:        10px 14px;
        background:     ${COLORS.gray100};
        border-radius:  14px;
        border-bottom-left-radius: 4px;
        align-self:     flex-start;
        animation:      tapi-fadeIn 0.22s ease both;
      }
      .tapi-typing-dot {
        width:         7px;
        height:        7px;
        border-radius: 50%;
        background:    ${COLORS.gray400};
        animation:     tapi-dot 1.2s ease infinite;
      }
      .tapi-typing-dot:nth-child(2) { animation-delay: 0.2s; }
      .tapi-typing-dot:nth-child(3) { animation-delay: 0.4s; }

      /* Input area */
      #tapi-input-area {
        display:      flex;
        align-items:  flex-end;
        gap:          8px;
        padding:      12px 14px;
        border-top:   1px solid ${COLORS.gray200};
        background:   white;
        flex-shrink:  0;
      }
      #tapi-input {
        flex:          1;
        resize:        none;
        border:        1.5px solid ${COLORS.gray200};
        border-radius: 10px;
        padding:       9px 12px;
        font-family:   Inter, 'Segoe UI', sans-serif;
        font-size:     0.875rem;
        color:         ${COLORS.text};
        outline:       none;
        max-height:    120px;
        min-height:    40px;
        line-height:   1.5;
        transition:    border-color 0.18s;
        background:    ${COLORS.bg};
      }
      #tapi-input:focus {
        border-color: ${COLORS.primary};
        background:   white;
      }
      #tapi-input::placeholder {
        color: ${COLORS.gray400};
      }
      #tapi-input:disabled {
        opacity: 0.6;
        cursor:  not-allowed;
      }
      #tapi-send-btn {
        width:         40px;
        height:        40px;
        border-radius: 10px;
        background:    linear-gradient(135deg, ${COLORS.primary}, ${COLORS.primaryDark});
        border:        none;
        cursor:        pointer;
        display:       flex;
        align-items:   center;
        justify-content: center;
        flex-shrink:   0;
        transition:    transform 0.15s, box-shadow 0.15s, opacity 0.15s;
        box-shadow:    0 2px 10px rgba(255,79,0,0.35);
      }
      #tapi-send-btn:hover:not(:disabled) {
        transform:  scale(1.07);
        box-shadow: 0 4px 14px rgba(255,79,0,0.5);
      }
      #tapi-send-btn:active:not(:disabled) {
        transform: scale(0.94);
      }
      #tapi-send-btn:disabled {
        opacity: 0.5;
        cursor:  not-allowed;
      }
      #tapi-send-btn svg {
        pointer-events: none;
      }
    `;

    const style = _el('style', { id: 'tapi-styles' }, [css]);
    document.head.appendChild(style);
  }

  // ─── Build DOM ────────────────────────────────────────────────────────────
  let $btn, $panel, $messages, $input, $sendBtn, $modelSelect, $notifDot;

  function buildDOM() {
    // ── Floating button ──
    $notifDot = _el('span', { className: 'tapi-notif-dot', style: { display: 'none' } });

    const btnIcon = _el('span', {
      style: {
        fontFamily: "'Material Symbols Rounded','Material Icons',sans-serif",
        fontStyle:  'normal',
        fontSize:   '26px',
        color:      'white',
        lineHeight: '1',
        userSelect: 'none',
        // Fallback for when Material Symbols not loaded: use SVG below
      },
    }, ['chat_bubble']);

    // SVG fallback icon (always rendered, hidden behind font icon via overlap)
    const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svgIcon.setAttribute('width', '26');
    svgIcon.setAttribute('height', '26');
    svgIcon.setAttribute('viewBox', '0 0 24 24');
    svgIcon.setAttribute('fill', 'white');
    const path1 = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path1.setAttribute('d', 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z');
    svgIcon.appendChild(path1);

    // Wrap both icons; the font icon will render if font loads, SVG as backup
    const iconWrap = _el('span', {
      style: {
        position: 'relative',
        display:  'flex',
        alignItems: 'center',
        justifyContent: 'center',
      },
    });
    // Only append SVG if Material Symbols likely not loaded
    iconWrap.appendChild(svgIcon);

    $btn = _el('button', { id: 'tapi-btn', 'aria-label': 'Open chat', type: 'button' }, [
      iconWrap,
      $notifDot,
    ]);

    // ── Panel ──
    // Header
    const headerIcon = _el('span', { id: 'tapi-header-icon' }, ['smart_toy']);
    const headerIconSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    headerIconSvg.setAttribute('width', '22');
    headerIconSvg.setAttribute('height', '22');
    headerIconSvg.setAttribute('viewBox', '0 0 24 24');
    headerIconSvg.setAttribute('fill', 'white');
    const botPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    botPath.setAttribute('d',
      'M20 9V7c0-1.1-.9-2-2-2h-3V3c0-.55-.45-1-1-1h-4c-.55 0-1 .45-1 1v2H6C4.9 5 4 5.9 4 7v2c-1.1 0-2 .9-2 2v4c0 1.1.9 2 2 2v2c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2v-2c1.1 0 2-.9 2-2v-4c0-1.1-.9-2-2-2zm-9 9H7v-2h4v2zm6 0h-4v-2h4v2zM9 13c-.83 0-1.5-.67-1.5-1.5S8.17 10 9 10s1.5.67 1.5 1.5S9.83 13 9 13zm6 0c-.83 0-1.5-.67-1.5-1.5S14.17 10 15 10s1.5.67 1.5 1.5S15.83 13 15 13z');
    headerIconSvg.appendChild(botPath);

    const headerLeft = _el('div', {
      style: {
        display:     'flex',
        alignItems:  'center',
        gap:         '8px',
        flex:        '1',
        minWidth:    '0',
      },
    }, [headerIconSvg, _el('span', { id: 'tapi-title' }, ['TriggersAPI Assistant'])]);

    $modelSelect = _el('select', { id: 'tapi-model-select', 'aria-label': 'Select model' });

    const closeBtn = _el('button', {
      id:          'tapi-close-btn',
      type:        'button',
      'aria-label': 'Close chat',
    }, ['close']);
    // SVG close fallback
    const closeSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    closeSvg.setAttribute('width', '18');
    closeSvg.setAttribute('height', '18');
    closeSvg.setAttribute('viewBox', '0 0 24 24');
    closeSvg.setAttribute('fill', 'currentColor');
    const closePath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    closePath.setAttribute('d',
      'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z');
    closeSvg.appendChild(closePath);

    const header = _el('div', { id: 'tapi-header' }, [headerLeft, $modelSelect, closeBtn]);

    // Messages area
    $messages = _el('div', { id: 'tapi-messages', role: 'log', 'aria-live': 'polite' });

    // Input area
    $input = _el('textarea', {
      id:          'tapi-input',
      rows:        1,
      placeholder: 'Ask about TriggersAPI...',
      'aria-label': 'Message input',
    });

    const sendSvg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    sendSvg.setAttribute('width', '18');
    sendSvg.setAttribute('height', '18');
    sendSvg.setAttribute('viewBox', '0 0 24 24');
    sendSvg.setAttribute('fill', 'white');
    const sendPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    sendPath.setAttribute('d', 'M2.01 21L23 12 2.01 3 2 10l15 2-15 2z');
    sendSvg.appendChild(sendPath);

    $sendBtn = _el('button', {
      id:          'tapi-send-btn',
      type:        'button',
      'aria-label': 'Send message',
    }, [sendSvg]);

    const inputArea = _el('div', { id: 'tapi-input-area' }, [$input, $sendBtn]);

    $panel = _el('div', {
      id:   'tapi-panel',
      role: 'dialog',
      'aria-label': 'TriggersAPI chat panel',
    }, [header, $messages, inputArea]);
    $panel.style.display = 'none';

    document.body.appendChild($btn);
    document.body.appendChild($panel);

    // Close button uses SVG since font icon may not load
    closeBtn.textContent = '';
    closeBtn.appendChild(closeSvg);
  }

  // ─── Typing indicator ─────────────────────────────────────────────────────
  let $typingEl = null;

  function showTyping() {
    if ($typingEl) return;
    $typingEl = _el('div', { id: 'tapi-typing', role: 'status', 'aria-label': 'Thinking' }, [
      _el('span', { className: 'tapi-typing-dot' }),
      _el('span', { className: 'tapi-typing-dot' }),
      _el('span', { className: 'tapi-typing-dot' }),
    ]);
    $messages.appendChild($typingEl);
    scrollBottom();
  }

  function hideTyping() {
    if ($typingEl) {
      $typingEl.remove();
      $typingEl = null;
    }
  }

  // ─── Message rendering ────────────────────────────────────────────────────
  function appendMessage(role, content, meta) {
    const bubble = _el('div', { className: 'tapi-bubble' });

    if (role === 'user') {
      bubble.textContent = content;
    } else {
      bubble.appendChild(renderMarkdown(content));
    }

    const msgEl = _el('div', { className: `tapi-msg ${role}` }, [bubble]);

    if (meta) {
      const metaEl = _el('div', { className: 'tapi-msg-meta' }, [meta]);
      msgEl.appendChild(metaEl);
    }

    $messages.appendChild(msgEl);
    scrollBottom();
    return msgEl;
  }

  function scrollBottom() {
    requestAnimationFrame(() => {
      $messages.scrollTop = $messages.scrollHeight;
    });
  }

  // ─── Model selector ───────────────────────────────────────────────────────
  async function loadModels() {
    try {
      const res  = await fetch('/api/v1/chat/models');
      const data = await res.json();

      // Support various response shapes: array of strings, array of {id,name} objects, {models:[...]}
      let models = Array.isArray(data) ? data : (data.models || data.data || []);

      $modelSelect.innerHTML = '';

      if (models.length === 0) {
        const opt = _el('option', { value: '' }, ['Default']);
        $modelSelect.appendChild(opt);
        return;
      }

      models.forEach(m => {
        const id    = typeof m === 'string' ? m : (m.id || m.name || m.model || String(m));
        const label = typeof m === 'string' ? m : (m.name || m.id || String(m));
        const opt   = _el('option', { value: id }, [label]);
        if (id === selectedModel) opt.selected = true;
        $modelSelect.appendChild(opt);
      });

      // If saved model not in list, default to first
      if (!selectedModel || !models.find(m =>
        (typeof m === 'string' ? m : (m.id || m.name || '')) === selectedModel)
      ) {
        const first = models[0];
        selectedModel = typeof first === 'string' ? first : (first.id || first.name || '');
        $modelSelect.value = selectedModel;
        localStorage.setItem(STORAGE_KEY_MODEL, selectedModel);
      }
    } catch (e) {
      // Silently fail — keep select empty or with a placeholder
      const opt = _el('option', { value: '' }, ['Default']);
      $modelSelect.innerHTML = '';
      $modelSelect.appendChild(opt);
    }
  }

  // ─── API call ─────────────────────────────────────────────────────────────
  async function sendMessage(userText) {
    if (!userText.trim() || isWaiting) return;

    isWaiting = true;
    $input.disabled    = true;
    $sendBtn.disabled  = true;

    // Add user message to history and UI
    conversationHistory.push({ role: 'user', content: userText });
    appendMessage('user', userText);

    showTyping();

    try {
      const body = {
        messages:   conversationHistory,
        model:      selectedModel || undefined,
        session_id: sessionId,
      };

      const res = await fetch('/api/v1/chat', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`Server error: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();

      // Support various response shapes
      const assistantText =
        data.message ||
        data.content  ||
        data.response ||
        (data.choices && data.choices[0]?.message?.content) ||
        (data.choices && data.choices[0]?.text) ||
        'Sorry, I received an unexpected response format.';

      const tokenInfo = data.usage
        ? `${data.model || selectedModel || 'model'} · ${data.usage.total_tokens ?? ''} tokens`
        : (data.model || selectedModel || null);

      hideTyping();
      conversationHistory.push({ role: 'assistant', content: assistantText });
      appendMessage('bot', assistantText, tokenInfo);

      // Show notification dot if panel is closed
      if (!isOpen) {
        hasNewResponse = true;
        $notifDot.style.display = 'block';
      }
    } catch (err) {
      hideTyping();
      appendMessage('bot',
        `**Error:** ${err.message}\n\nPlease try again or check your connection.`);
    } finally {
      isWaiting         = false;
      $input.disabled   = false;
      $sendBtn.disabled = false;
      $input.focus();
    }
  }

  // ─── Panel open / close ───────────────────────────────────────────────────
  function openPanel() {
    isOpen              = true;
    hasNewResponse      = false;
    $notifDot.style.display = 'none';

    $panel.style.display = 'flex';
    // Re-trigger animation
    $panel.style.animation = 'none';
    void $panel.offsetWidth; // reflow
    $panel.style.animation = '';

    $btn.setAttribute('aria-expanded', 'true');

    if (!welcomeShown) {
      welcomeShown = true;
      appendMessage('bot', WELCOME_MESSAGE);
    }

    loadModels();
    scrollBottom();

    setTimeout(() => $input.focus(), 120);
  }

  function closePanel() {
    isOpen = false;
    $panel.style.display = 'none';
    $btn.setAttribute('aria-expanded', 'false');
  }

  function togglePanel() {
    isOpen ? closePanel() : openPanel();
  }

  // ─── Input auto-resize ────────────────────────────────────────────────────
  function autoResize() {
    $input.style.height = 'auto';
    $input.style.height = Math.min($input.scrollHeight, 120) + 'px';
  }

  // ─── Event listeners ──────────────────────────────────────────────────────
  function bindEvents() {
    $btn.addEventListener('click', togglePanel);

    document.getElementById('tapi-close-btn').addEventListener('click', closePanel);

    $modelSelect.addEventListener('change', () => {
      selectedModel = $modelSelect.value;
      localStorage.setItem(STORAGE_KEY_MODEL, selectedModel);
    });

    $input.addEventListener('input', autoResize);

    $input.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const text = $input.value.trim();
        if (text) {
          $input.value = '';
          autoResize();
          sendMessage(text);
        }
      }
    });

    $sendBtn.addEventListener('click', () => {
      const text = $input.value.trim();
      if (text) {
        $input.value = '';
        autoResize();
        sendMessage(text);
      }
    });

    // Close on backdrop click (mobile full-screen: not applicable, but nice on desktop)
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && isOpen) closePanel();
    });
  }

  // ─── Bounce animation ─────────────────────────────────────────────────────
  function startBounce() {
    $btn.classList.add('tapi-bounce');
    $btn.addEventListener('animationend', () => {
      $btn.classList.remove('tapi-bounce');
    }, { once: true });
  }

  // ─── Init ─────────────────────────────────────────────────────────────────
  function init() {
    if (document.getElementById('tapi-btn')) return; // already initialized

    injectStyles();
    buildDOM();
    bindEvents();

    // Start bounce after a short delay
    setTimeout(startBounce, 600);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
