import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:net';
import { checkPorts } from './dev-ports.mjs';

test('reports an occupied port and releases earlier reservations', async () => {
  const occupied = createServer();
  await new Promise(resolve => occupied.listen(0, '127.0.0.1', resolve));
  try {
    await assert.rejects(checkPorts([0, occupied.address().port]), /EADDRINUSE/);
  } finally {
    await new Promise(resolve => occupied.close(resolve));
  }
});

test('free ports are released after checking', async () => {
  await checkPorts([0, 0]);
});
