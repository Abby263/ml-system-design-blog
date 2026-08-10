import { readFile } from 'node:fs/promises';
import { deflateSync } from 'node:zlib';
import { randomBytes, webcrypto } from 'node:crypto';

const ENDPOINT = 'https://json.excalidraw.com/api/v2/post/';
const BOARD_PATHS = process.argv.slice(2);

if (!BOARD_PATHS.length) {
  console.error('Usage: node scripts/publish-excalidraw-boards.mjs <board.excalidraw> [...]');
  process.exitCode = 1;
} else {
  const concatBuffers = (...chunks) => {
    const bytes = 4 + chunks.reduce((sum, chunk) => sum + 4 + chunk.length, 0);
    const result = Buffer.alloc(bytes);
    let cursor = 0;
    result.writeUInt32BE(1, cursor);
    cursor += 4;
    for (const chunk of chunks) {
      result.writeUInt32BE(chunk.length, cursor);
      cursor += 4;
      Buffer.from(chunk).copy(result, cursor);
      cursor += chunk.length;
    }
    return result;
  };

  const base64url = (bytes) => Buffer.from(bytes).toString('base64url');

  for (const boardPath of BOARD_PATHS) {
    const scene = JSON.parse(await readFile(boardPath, 'utf8'));
    const databaseScene = JSON.stringify({
      type: 'excalidraw',
      version: 2,
      source: 'https://excalidraw.com',
      elements: scene.elements,
      appState: scene.appState ?? {},
    }, null, 2);

    const keyBytes = randomBytes(16);
    const keyString = base64url(keyBytes);
    const cryptoKey = await webcrypto.subtle.importKey(
      'raw', keyBytes, { name: 'AES-GCM' }, false, ['encrypt'],
    );
    const iv = randomBytes(12);
    const contents = concatBuffers(
      Buffer.from('null'),
      Buffer.from(databaseScene),
    );
    const encrypted = Buffer.from(await webcrypto.subtle.encrypt(
      { name: 'AES-GCM', iv }, cryptoKey, deflateSync(contents),
    ));
    const payload = concatBuffers(
      Buffer.from(JSON.stringify({ version: 2, compression: 'pako@1', encryption: 'AES-GCM' })),
      iv,
      encrypted,
    );

    const response = await fetch(ENDPOINT, { method: 'POST', body: payload });
    if (!response.ok) throw new Error(`Excalidraw upload failed (${response.status})`);
    const result = await response.json();
    if (!result.id) throw new Error(`Excalidraw upload failed: ${JSON.stringify(result)}`);
    console.log(`${boardPath}\thttps://excalidraw.com/#json=${result.id},${keyString}`);
  }
}
