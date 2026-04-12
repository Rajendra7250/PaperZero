// ─── Signature Pad ────────────────────────────────────────────────────────────
let sigDataMap = {}; // store state per canvas ID

function initSignaturePad() {
  const canvases = [document.getElementById("sigCanvas"), document.getElementById("sigCanvasReq")];
  
  canvases.forEach(canvas => {
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    sigDataMap[canvas.id] = { ctx, drawing: false, hasData: false };

    const styleCtx = () => {
      ctx.strokeStyle = "#1a472a";
      ctx.lineWidth   = 2.5;
      ctx.lineCap     = "round";
      ctx.lineJoin    = "round";
    };
    styleCtx();

    // Use ResizeObserver to reliably tie canvas resolution to its CSS box size whenever it becomes visible
    const observer = new ResizeObserver(() => {
      if (canvas.offsetWidth > 0 && canvas.width !== canvas.offsetWidth) {
        // Only resize if it actually changed to prevent wiping ongoing drawings needlessly
        const oldData = canvas.width > 0 ? ctx.getImageData(0, 0, canvas.width, canvas.height) : null;
        canvas.width  = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight || 250;
        styleCtx();
        if (oldData) ctx.putImageData(oldData, 0, 0);
      }
    });
    observer.observe(canvas);

    // Mouse events
    canvas.addEventListener("mousedown",  (e) => startDraw(canvas, e));
    canvas.addEventListener("mousemove",  (e) => draw(canvas, e));
    canvas.addEventListener("mouseup",    ()  => stopDraw(canvas));
    canvas.addEventListener("mouseleave", ()  => stopDraw(canvas));

    // Touch events
    canvas.addEventListener("touchstart", (e) => { e.preventDefault(); startDraw(canvas, e.touches[0]); }, { passive: false });
    canvas.addEventListener("touchmove",  (e) => { e.preventDefault(); draw(canvas, e.touches[0]); },      { passive: false });
    canvas.addEventListener("touchend",   ()  => stopDraw(canvas));
  });
}

function getPos(canvas, e) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width  / rect.width || 1;
  const scaleY = canvas.height / rect.height || 1;
  return [(e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY];
}

function startDraw(canvas, e) {
  const state = sigDataMap[canvas.id];
  state.drawing = true;
  state.ctx.beginPath();
  state.ctx.moveTo(...getPos(canvas, e));
}

function draw(canvas, e) {
  const state = sigDataMap[canvas.id];
  if (!state.drawing) return;
  state.ctx.lineTo(...getPos(canvas, e));
  state.ctx.stroke();
  state.hasData = true;
  
  const statusEl = document.getElementById(canvas.id === "sigCanvas" ? "sigStatus" : "sigStatusReq");
  if (statusEl) statusEl.textContent = "Signature captured ✓";
}

function stopDraw(canvas) {
  const state = sigDataMap[canvas.id];
  if (state) state.drawing = false;
}

function clearSignature() {
  _clearSig("sigCanvas", "sigStatus");
}

function clearSignatureReq() {
  _clearSig("sigCanvasReq", "sigStatusReq");
}

function _clearSig(canvasId, statusId) {
  const state = sigDataMap[canvasId];
  if (!state || !state.ctx) return;
  state.ctx.clearRect(0, 0, state.ctx.canvas.width, state.ctx.canvas.height);
  state.hasData = false;
  const statusEl = document.getElementById(statusId);
  if (statusEl) statusEl.textContent = "Draw your signature above";
}

function hasSignature(isReq = false) {
  const id = isReq ? "sigCanvasReq" : "sigCanvas";
  return sigDataMap[id] ? sigDataMap[id].hasData : false;
}
