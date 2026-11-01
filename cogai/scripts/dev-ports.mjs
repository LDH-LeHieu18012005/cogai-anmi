import { createServer } from 'node:net';

export async function checkPorts(ports) {
  const reservations = [];
  try {
    for (const port of ports) {
      const server = createServer();
      await new Promise((resolve, reject) => {
        server.once('error', error => {
          reject(new Error(`Cannot start CogAI: port ${port} is unavailable (${error.code}). Stop the previous CogAI terminal with Ctrl+C before retrying.`));
        });
        server.listen({ host: '127.0.0.1', port, exclusive: true }, resolve);
      });
      reservations.push(server);
    }
  } finally {
    await Promise.all(reservations.map(server => new Promise(resolve => server.close(resolve))));
  }
}
