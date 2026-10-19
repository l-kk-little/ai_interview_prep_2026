// Run the actual navigation helper against a tiny DOM stub, without a browser.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../viewer/app.js'), 'utf8');
const sandbox = {
  window: {A2_DOCS: [{path: 'DEPENDENCIES.md'}], location: {href: 'file:///clone/agentic_prep/viewer/index.html'}},
  document: {getElementById() { return {}; }}, URL
};
// Export the real helper before boot; rendering is outside this focused test.
vm.runInNewContext(source.split('  /* ---------- boot ---------- */')[0] +
  'globalThis.intercept = interceptMdLinks; })();', sandbox);
function link(href, from) {
  const a = {href, getAttribute() {return href;}, addEventListener(name, fn) {this.handler = fn;}};
  sandbox.intercept({querySelectorAll() {return [a];}}, from);
  return a;
}
assert.equal(typeof link('../DEPENDENCIES.md', '03_gaps/rag.md').handler, 'function');
assert.equal(link('../../online_resource/1p3a-openai.md', '03_gaps/rag.md').href,
  'file:///clone/online_resource/1p3a-openai.md');
assert.equal(link('../1acre3points_crawl/practice/anthropic/agent_tool_use/agent.py', '07_labs_guide.md').href,
  'file:///clone/1acre3points_crawl/practice/anthropic/agent_tool_use/agent.py');
assert.equal(link('https://example.test', 'README.md').target, '_blank');
assert.equal(link('#local', 'README.md').href, '#local');
console.log('PASS: 5 viewer link checks');
