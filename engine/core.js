/**
 * GAME ENGEN core — serializable project model, validation, dialogue VM and collision helpers.
 * Deliberately independent of Three.js so the editor can later share this model with a C# runtime.
 */
export const FORMAT = 'game-engen-project';
export const VERSION = 2;
export const clone = value => JSON.parse(JSON.stringify(value));

export function normalizeProject(input = {}) {
  const p = clone(input);
  p.format = FORMAT;
  p.version = VERSION;
  p.settings ||= { grid: true, snap: true, units: 'meters' };
  p.objects = Array.isArray(p.objects) ? p.objects : [];
  p.materials = Array.isArray(p.materials) ? p.materials : [];
  p.lights = Array.isArray(p.lights) ? p.lights : [];
  p.dialogs = Array.isArray(p.dialogs) ? p.dialogs : [];
  p.variables = p.variables && typeof p.variables === 'object' ? p.variables : {};
  p.flags = p.flags && typeof p.flags === 'object' ? p.flags : {};
  p.assets = Array.isArray(p.assets) ? p.assets : [];
  p.triggers = Array.isArray(p.triggers) ? p.triggers : [];
  p.journal = Array.isArray(p.journal) ? p.journal : [];
  return p;
}

export function validateProject(project) {
  const p = normalizeProject(project), issues = [];
  const issue = (severity, code, path, message) => issues.push({ severity, code, path, message });
  const unique = (items, path) => {
    const seen = new Set();
    items.forEach((item, i) => {
      if (!item.id) issue('error', 'missing-id', path + '[' + i + '].id', 'Object has no stable ID.');
      else if (seen.has(item.id)) issue('error', 'duplicate-id', path + '[' + i + '].id', 'Duplicate ID: ' + item.id);
      else seen.add(item.id);
    });
    return seen;
  };
  const objectIds = unique(p.objects, 'objects'), materialIds = unique(p.materials, 'materials');
  const lightIds = unique(p.lights, 'lights'), dialogIds = unique(p.dialogs, 'dialogs');
  unique(p.assets, 'assets'); unique(p.triggers, 'triggers');
  p.objects.forEach((o, i) => {
    const path = 'objects[' + i + ']';
    for (const k of ['position', 'rotation', 'scale']) {
      if (!Array.isArray(o[k]) || o[k].length !== 3 || o[k].some(n => !Number.isFinite(n)))
        issue('error', 'invalid-transform', path + '.' + k, 'Expected three finite numeric values.');
    }
    if (o.scale?.some(n => n <= 0)) issue('error', 'invalid-scale', path + '.scale', 'Scale values must be greater than zero.');
    if (o.materialId && !materialIds.has(o.materialId)) issue('warning', 'missing-material', path + '.materialId', 'Material reference does not resolve.');
  });
  p.lights.forEach((l, i) => {
    if (!Array.isArray(l.position) || l.position.length !== 3 || l.position.some(n => !Number.isFinite(n)))
      issue('error', 'invalid-light-position', 'lights[' + i + '].position', 'Expected three finite numeric values.');
    if (!Number.isFinite(l.intensity) || l.intensity < 0) issue('error', 'invalid-light-intensity', 'lights[' + i + '].intensity', 'Intensity must be a non-negative number.');
  });
  const starts = p.dialogs.filter(d => d.id === 'start' || d.start === true);
  if (p.dialogs.length && starts.length === 0) issue('warning', 'missing-dialogue-start', 'dialogs', 'No start node is marked; runtime will use the first node.');
  p.dialogs.forEach((d, i) => {
    const path = 'dialogs[' + i + ']';
    if (!Array.isArray(d.choices)) issue('error', 'invalid-choices', path + '.choices', 'Choices must be an array.');
    (d.choices || []).forEach((c, j) => {
      if (!dialogIds.has(c.to)) issue('error', 'broken-dialogue-link', path + '.choices[' + j + '].to', 'Target node "' + c.to + '" does not exist.');
      if (c.condition && !isSupportedExpression(c.condition)) issue('warning', 'unknown-condition', path + '.choices[' + j + '].condition', 'Condition is not in the supported expression subset.');
      if (c.effect && !isSupportedExpression(c.effect, true)) issue('warning', 'unknown-effect', path + '.choices[' + j + '].effect', 'Effect is not in the supported assignment subset.');
    });
  });
  p.triggers.forEach((t, i) => {
    if (t.dialogueId && !dialogIds.has(t.dialogueId)) issue('error', 'broken-trigger-dialogue', 'triggers[' + i + '].dialogueId', 'Trigger dialogue target does not exist.');
    if (t.objectId && !objectIds.has(t.objectId)) issue('warning', 'broken-trigger-object', 'triggers[' + i + '].objectId', 'Trigger object reference does not exist.');
  });
  p.lights.forEach((l, i) => { if (l.objectId && !objectIds.has(l.objectId)) issue('warning', 'broken-light-object', 'lights[' + i + '].objectId', 'Attached object does not exist.'); });
  return { valid: !issues.some(i => i.severity === 'error'), errors: issues.filter(i => i.severity === 'error').length, warnings: issues.filter(i => i.severity === 'warning').length, issues };
}

const IDENT = '[a-zA-Z_$][\\w.$]*';
const VALUE = String.raw`(?:true|false|null|-?\d+(?:\.\d+)?|"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')`;
export function isSupportedExpression(expression, assignment = false) {
  const s = String(expression || '').trim();
  if (!s) return true;
  if (assignment) return new RegExp('^' + IDENT + '\\s*=\\s*' + VALUE + '$').test(s);
  return new RegExp('^(?:' + IDENT + '|skill\\(' + IDENT + '\\)\\s*(?:>=|<=|==|!=|>|<)\\s*-?\\d+(?:\\.\\d+)?|' + IDENT + '\\s*(?:==|!=|>=|<=|>|<)\\s*' + VALUE + '|chance\\(\\s*\\d+(?:\\.\\d+)?\\s*\\))$').test(s);
}

function parseValue(raw) {
  const s = raw.trim();
  if (s === 'true') return true;
  if (s === 'false') return false;
  if (s === 'null') return null;
  if (/^-?\\d+(?:\\.\\d+)?$/.test(s)) return Number(s);
  if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
    try { return s[0] === '"' ? JSON.parse(s) : s.slice(1, -1).replace(/\\'/g, "'").replace(/\\\\\\\\/g, '\\'); } catch { return s.slice(1, -1); }
  }
  return s;
}
function readPath(path, state) {
  return path.split('.').reduce((v, k) => v == null ? undefined : v[k], { flags: state.flags, vars: state.variables, variables: state.variables, skills: state.skills, ...state.variables });
}
function compare(a, op, b) {
  switch (op) { case '==': return a === b; case '!=': return a !== b; case '>': return Number(a) > Number(b); case '<': return Number(a) < Number(b); case '>=': return Number(a) >= Number(b); case '<=': return Number(a) <= Number(b); default: return false; }
}
export function evaluateCondition(expression, state, rng = Math.random) {
  const s = String(expression || '').trim();
  if (!s) return true;
  let m = s.match(/^chance\\(\\s*(\\d+(?:\\.\\d+)?)\\s*\\)$/);
  if (m) return rng() * 100 < Math.max(0, Math.min(100, Number(m[1])));
  m = s.match(/^skill\\(([^)]+)\\)\\s*(>=|<=|==|!=|>|<)\\s*(-?\\d+(?:\\.\\d+)?)$/);
  if (m) return compare(state.skills[m[1].trim()] ?? 0, m[2], Number(m[3]));
  m = s.match(/^('(?:[^'\\\\]|\\.)*'|"(?:[^"\\\\]|\\.)*"|-?\\d+(?:\\.\\d+)?|true|false|null)\\s*(==|!=|>=|<=|>|<)\\s*(.+)$/);
  if (m) return compare(parseValue(m[1]), m[2], readPath(m[3].trim(), state));
  m = s.match(/^([\\w.$]+)\\s*(==|!=|>=|<=|>|<)\\s*(.+)$/);
  if (m) return compare(readPath(m[1], state), m[2], parseValue(m[3]));
  return Boolean(readPath(s, state));
}
export function applyEffect(expression, state) {
  const s = String(expression || '').trim();
  const m = s.match(/^([a-zA-Z_$][\\w.$]*)\\s*=\\s*(.+)$/);
  if (!m) return false;
  const path = m[1].split('.'), key = path.pop();
  let target = path[0] === 'flags' ? state.flags : path[0] === 'vars' || path[0] === 'variables' ? state.variables : state.variables;
  if (path[0] === 'flags' || path[0] === 'vars' || path[0] === 'variables') path.shift();
  for (const part of path) { target[part] ||= {}; target = target[part]; }
  target[key] = parseValue(m[2]);
  return true;
}

export class DialogueRuntime {
  constructor(project, { rng = Math.random } = {}) {
    this.project = normalizeProject(project);
    this.rng = rng;
    this.state = { flags: clone(this.project.flags), variables: clone(this.project.variables), skills: clone(this.project.skills || {}), journal: clone(this.project.journal || []), visited: [], history: [] };
    this.currentId = this.project.dialogs.find(d => d.id === 'start' || d.start)?.id || this.project.dialogs[0]?.id || null;
  }
  get current() { return this.project.dialogs.find(d => d.id === this.currentId) || null; }
  availableChoices() { return (this.current?.choices || []).filter(c => evaluateCondition(c.condition, this.state, this.rng)); }
  choose(index) {
    const d = this.current, c = this.availableChoices()[index];
    if (!d || !c) return { ok: false, error: 'Choice is unavailable.' };
    this.state.history.push({ nodeId: d.id, choice: c.text, target: c.to, at: Date.now() });
    if (!this.state.visited.includes(d.id)) this.state.visited.push(d.id);
    applyEffect(c.effect, this.state);
    this.currentId = c.to;
    const next = this.current;
    if (next?.journal) this.addJournal(next.journal, next.title || next.id);
    return { ok: !!next, node: next, error: next ? null : 'Broken dialogue link: ' + c.to };
  }
  addJournal(text, title = 'Journal') {
    this.state.journal.push({ id: 'j' + this.state.journal.length + 1, title, text, at: Date.now() });
  }
  snapshot() { return clone({ currentId: this.currentId, state: this.state }); }
  restore(save) { if (!save?.state) throw new Error('Invalid runtime save.'); this.currentId = save.currentId; this.state = clone(save.state); }
}

/** Fast axis-aligned broadphase helper, in world-space min/max form. */
export function aabbIntersects(a, b) {
  return a.min[0] <= b.max[0] && a.max[0] >= b.min[0] &&
    a.min[1] <= b.max[1] && a.max[1] >= b.min[1] &&
    a.min[2] <= b.max[2] && a.max[2] >= b.min[2];
}
export function moveWithAabbCollisions(position, delta, bodyHalfExtents, obstacles) {
  const out = [...position];
  for (const axis of [0, 2, 1]) {
    out[axis] += delta[axis];
    const body = { min: out.map((v, i) => v - bodyHalfExtents[i]), max: out.map((v, i) => v + bodyHalfExtents[i]) };
    for (const obstacle of obstacles) {
      if (!aabbIntersects(body, obstacle)) continue;
      if (delta[axis] > 0) out[axis] = obstacle.min[axis] - bodyHalfExtents[axis];
      else if (delta[axis] < 0) out[axis] = obstacle.max[axis] + bodyHalfExtents[axis];
      body.min[axis] = out[axis] - bodyHalfExtents[axis]; body.max[axis] = out[axis] + bodyHalfExtents[axis];
    }
  }
  return out;
}
