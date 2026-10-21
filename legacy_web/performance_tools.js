// Lightweight, renderer-independent performance and history utilities.
// Kept separate so the editor can evolve without coupling tests to Three.js.
export function createPerformanceMonitor({sampleWindow = 120} = {}) {
  const samples = new Map();
  function measure(name, fn) {
    const start = performance.now();
    try { return fn(); }
    finally {
      const elapsed = performance.now() - start;
      let list = samples.get(name);
      if (!list) samples.set(name, list = []);
      list.push(elapsed);
      if (list.length > sampleWindow) list.shift();
    }
  }
  function report() {
    const out = {};
    for (const [name, values] of samples) {
      const sorted = [...values].sort((a, b) => a - b);
      const sum = values.reduce((a, b) => a + b, 0);
      out[name] = {
        count: values.length,
        avgMs: Number((sum / values.length).toFixed(3)),
        p95Ms: Number((sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * .95))] || 0).toFixed(3)),
        maxMs: Number(Math.max(...values).toFixed(3))
      };
    }
    return out;
  }
  function clear() { samples.clear(); }
  return { measure, report, clear };
}

// Snapshot history is deliberately JSON-compatible because scene data is the
// current persistence contract. This centralizes limits and undo semantics;
// a future entity-patch implementation can replace this store without changing UI.
export function createHistoryStore(limit = 40) {
  let past = [];
  let future = [];
  const clone = value => JSON.parse(JSON.stringify(value));
  function push(state) {
    const snapshot = JSON.stringify(state);
    if (past[past.length - 1] === snapshot) return false;
    past.push(snapshot);
    if (past.length > limit) past.shift();
    future = [];
    return true;
  }
  function undo(current) {
    if (!past.length) return null;
    future.push(JSON.stringify(current));
    return JSON.parse(past.pop());
  }
  function redo(current) {
    if (!future.length) return null;
    past.push(JSON.stringify(current));
    if (past.length > limit) past.shift();
    return JSON.parse(future.pop());
  }
  function reset() { past = []; future = []; }
  return {
    push, undo, redo, reset,
    get past() { return past; },
    get future() { return future; },
    get size() { return past.length; }
  };
}
