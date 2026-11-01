(() => {
  function qs(sel, root=document) { 
    return root.querySelector(sel); 
  }

  function qsa(sel, root=document) { 
    return Array.from(root.querySelectorAll(sel)); 
  }

  // 🔹 Toast notification (non-blocking, styled)
  function toast(msg, type="info") {
    let box = document.getElementById("toastBox");
    if (!box) {
      box = document.createElement("div");
      box.id = "toastBox";
      box.style.position = "fixed";
      box.style.top = "1rem";
      box.style.right = "1rem";
      box.style.zIndex = "2000";
      document.body.appendChild(box);
    }

    const el = document.createElement("div");
    el.textContent = msg;
    el.style.background = type === "error" ? "#ff4d4f" : "#4caf50";
    el.style.color = "white";
    el.style.padding = "0.6rem 1rem";
    el.style.marginTop = "0.5rem";
    el.style.borderRadius = "6px";
    el.style.boxShadow = "0 2px 6px rgba(0,0,0,0.2)";
    el.style.fontSize = "0.9rem";
    el.style.transition = "opacity 0.3s ease";

    box.appendChild(el);

    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 300);
    }, 3000);
  }

  // 🔹 setHTML that accepts selector or element
  function setHTML(target, html) {
    let el = target;
    if (typeof target === "string") {
      el = document.querySelector(target);
    }
    if (el) el.innerHTML = html;
  }

  function on(el, ev, fn) { 
    el.addEventListener(ev, fn); 
  }

  window.ui = { qs, qsa, toast, setHTML, on };
  console.log("ui.js loaded");
})();
