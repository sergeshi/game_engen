import { normalizeProject, validateProject, DialogueRuntime, aabbIntersects, moveWithAabbCollisions } from '../engine/core.js';
import assert from 'node:assert/strict';
import test from 'node:test';

const base = normalizeProject({
  objects: [{id:'box', name:'Box', type:'Box', position:[0,0,0], rotation:[0,0,0], scale:[1,1,1], materialId:'mat'}],
  materials: [{id:'mat',name:'Concrete'}],
  dialogs: [
    {id:'start',start:true,title:'Start',text:'Check your skill.',choices:[
      {text:'Pass',to:'success',condition:'skill(psyche) >= 3',effect:'flags.passed = true'},
      {text:'Luck',to:'success',condition:'chance(100)',effect:'vars.rolls = 1'}
    ]},
    {id:'success',title:'Success',text:'Done.',journal:'Added to journal.',choices:[]}
  ],
  skills: {psyche:4}
});
test('project validation accepts valid scene and catches broken links', () => { assert.equal(validateProject(base).valid, true); const broken = structuredClone(base); broken.dialogs[0].choices[0].to='missing'; assert.equal(validateProject(broken).valid, false); });
test('dialogue conditions, effects, journal and saves', () => { const runtime = new DialogueRuntime(base, {rng:()=>0});
assert.equal(runtime.availableChoices().length, 2);
assert.equal(runtime.choose(0).ok, true);
assert.equal(runtime.state.flags.passed, true);
assert.equal(runtime.state.journal.length, 1);
const save = runtime.snapshot();
const other = new DialogueRuntime(base);
other.restore(save);
assert.equal(other.currentId, 'success'); });
test('AABB collision helpers', () => { assert.equal(aabbIntersects({min:[0,0,0],max:[1,1,1]},{min:[.5,.5,.5],max:[2,2,2]}),true);
assert.deepEqual(moveWithAabbCollisions([0,0,0],[2,0,0],[.5,.5,.5],[{min:[1,-2,-2],max:[2,2,2]}]),[.5,0,0]); });
