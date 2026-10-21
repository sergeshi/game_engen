import assert from 'node:assert/strict';
import test from 'node:test';
import { createHistoryStore, createPerformanceMonitor } from '../legacy_web/performance_tools.js';

test('history keeps bounded snapshots and skips duplicate states', () => {
  const history = createHistoryStore(2);
  assert.equal(history.push({ n: 1 }), true);
  assert.equal(history.push({ n: 1 }), false);
  assert.equal(history.push({ n: 2 }), true);
  assert.equal(history.push({ n: 3 }), true);
  assert.equal(history.size, 2);
  assert.deepEqual(history.undo({ n: 4 }), { n: 2 });
  assert.deepEqual(history.redo({ n: 2 }), { n: 4 });
});

test('undo and redo transfer current state between stacks', () => {
  const history = createHistoryStore(5);
  history.push({ objects: [{ id: 'a' }] });
  history.push({ objects: [{ id: 'a' }, { id: 'b' }] });
  assert.deepEqual(history.undo({ objects: [{ id: 'a' }, { id: 'b' }, { id: 'c' }] }), { objects: [{ id: 'a' }] });
  assert.deepEqual(history.redo({ objects: [{ id: 'a' }] }), { objects: [{ id: 'a' }, { id: 'b' }, { id: 'c' }] });
});

test('performance monitor records durations and resets', () => {
  const monitor = createPerformanceMonitor({ sampleWindow: 3 });
  assert.equal(monitor.measure('unit', () => 42), 42);
  monitor.measure('unit', () => 'ok');
  const report = monitor.report();
  assert.equal(report.unit.count, 2);
  assert.ok(report.unit.avgMs >= 0);
  assert.ok(report.unit.p95Ms >= 0);
  monitor.clear();
  assert.deepEqual(monitor.report(), {});
});
