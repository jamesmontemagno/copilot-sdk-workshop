'use strict';

const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { getLanguage } = require('../language-registry.js');
const {
    firstLessonUrl,
    homeUrl,
    lessonUrl,
    resolveLanguage
} = require('../language-navigation.js');
const { preprocessLanguageDirectives } = require('../markdown-language-preprocessor.js');

const preprocess = (markdown, languageId) =>
    preprocessLanguageDirectives(markdown, languageId, getLanguage);

assert.equal(
    preprocess('Shared\n:::language dotnet\n.NET only\n:::\n:::language python\nPython only\n:::\nEnd', 'dotnet'),
    'Shared\n.NET only\nEnd'
);
assert.equal(
    preprocess('Shared\n:::language dotnet\n.NET only\n:::\n:::language python\nPython only\n:::\nEnd', 'python'),
    'Shared\nPython only\nEnd'
);
assert.throws(
    () => preprocess(':::language dotnet\n:::language python\n:::\n:::', 'dotnet'),
    /cannot be nested/
);
assert.throws(() => preprocess(':::language unknown\n:::', 'dotnet'), /unknown language/);
assert.throws(() => preprocess(':::language dotnet\nUnclosed', 'dotnet'), /not closed/);
assert.throws(() => preprocess(':::', 'dotnet'), /closing directive has no open/);
assert.throws(() => preprocess(':::unexpected', 'dotnet'), /expected :::language/);

assert.equal(lessonUrl('04-mcp-safety', 'rust'), '?step=04-mcp-safety&lang=rust');
assert.equal(lessonUrl('04-mcp-safety'), '?step=04-mcp-safety');
assert.equal(firstLessonUrl('java'), 'workshop/step.html?step=00-preflight&lang=java');
assert.equal(firstLessonUrl('python', 'museum'), 'workshop/step.html?step=museum-00-preflight&lang=python');
assert.equal(homeUrl('python'), '../index.html?lang=python');
assert.equal(homeUrl('python', 'museum'), '../index.html?lang=python&workshop=museum');
assert.equal(homeUrl(), '../index.html');
assert.equal(resolveLanguage('?lang=go', 'rust', getLanguage).id, 'go');
assert.equal(resolveLanguage('', 'rust', getLanguage).id, 'rust');
assert.equal(resolveLanguage('?lang=unknown', 'rust', getLanguage), null);

const lessonViewer = readFileSync(join(__dirname, '..', 'workshop', 'step.html'), 'utf8');
assert.match(lessonViewer, /id: 'museum-05-lifecycle'/);
assert.match(lessonViewer, /file: 'workshop\/museum-05-lifecycle\.md'/);
assert.match(
    lessonViewer,
    /'museum-05-lifecycle-tests': 'museum-05-lifecycle'/,
);

console.log('Workshop language directive and navigation tests passed.');
