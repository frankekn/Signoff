import { spawn } from 'node:child_process'
import { createRequire } from 'node:module'
import fs from 'node:fs/promises'

const repo = '/Users/termtek/Github/Signoff'
const textPath = `${repo}/.omo/evidence/task-5-signoff-ui-flow-post-fix-proof-ui.txt`
const screenshotPath = `${repo}/.omo/evidence/task-5-signoff-ui-flow-post-fix-proof-ui.png`

const serverCode = String.raw`
import json
import sys
import threading

from signoff.web import create_server
from tests.support import RepoFixture

fx = RepoFixture()
fx.lock()
iteration_dir = fx.passing_evidence(final=True)
fx.fill_roast(iteration_dir)
fx.runtime.roast()
fx.runtime.finish("done")

server = create_server(fx.project, host="127.0.0.1", port=0)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
host, port = server.server_address[:2]
print(json.dumps({"base": f"http://{host}:{port}", "missionId": fx.mission_id}), flush=True)
try:
    sys.stdin.read()
finally:
    server.shutdown()
    server.server_close()
    thread.join(timeout=3)
    fx.close()
`

function waitForLine(proc) {
  return new Promise((resolve, reject) => {
    let buffer = ''
    proc.stdout.on('data', (chunk) => {
      buffer += chunk.toString()
      const newline = buffer.indexOf('\n')
      if (newline >= 0) {
        resolve(buffer.slice(0, newline))
      }
    })
    proc.once('exit', (code) => reject(new Error(`server exited before ready: ${code ?? 'signal'}`)))
  })
}

const server = spawn('python3', ['-u', '-c', serverCode], {
  cwd: repo,
  env: { ...process.env, PYTHONPATH: 'src' },
  stdio: ['pipe', 'pipe', 'pipe'],
})

const vite = spawn('npm', ['--workspace', '@signoff/web', 'run', 'dev', '--', '--host', '127.0.0.1', '--port', '5174', '--strictPort'], {
  cwd: repo,
  stdio: ['ignore', 'pipe', 'pipe'],
})

const cleanup = async () => {
  server.stdin.end()
  vite.kill('SIGTERM')
}

try {
  const { chromium } = createRequire('/tmp/signoff-pw-qa/package.json')('playwright')
  const ready = JSON.parse(await waitForLine(server))
  await new Promise((resolve) => setTimeout(resolve, 1500))

  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } })
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url())
    const response = await page.request.fetch(`${ready.base}${url.pathname}${url.search}`, {
      method: route.request().method(),
      headers: route.request().headers(),
      postData: route.request().postData() ?? undefined,
    })
    await route.fulfill({ response })
  })
  await page.goto('http://127.0.0.1:5174/', { waitUntil: 'networkidle' })
  const proofText = await page.locator('.proof-card').innerText()
  await page.screenshot({ path: screenshotPath, fullPage: true })
  await browser.close()

  const expectedPath = `.signoff/missions/${ready.missionId}/FINAL_RECEIPT.json`
  const pass = proofText.includes(expectedPath)
  const report = [
    'scenario: post-fix readable proof final receipt path browser assertion',
    'surface: browser UI DOM and screenshot',
    'invocation: node .omo/evidence/task-5-signoff-ui-flow-post-fix-proof-ui.mjs with playwright resolved from /tmp/signoff-pw-qa/node_modules',
    `app: http://127.0.0.1:5174/`,
    `api: ${ready.base} routed from browser /api requests`,
    `expectedFinalReceiptPath: ${expectedPath}`,
    `binaryObservable: .proof-card ${pass ? 'contains' : 'does not contain'} expectedFinalReceiptPath`,
    `screenshot: ${screenshotPath}`,
    `result: ${pass ? 'PASS' : 'FAIL'}`,
    '',
    'READABLE PROOF',
    proofText,
    '',
  ].join('\n')
  await fs.writeFile(textPath, report)
  if (!pass) {
    throw new Error(report)
  }
} finally {
  await cleanup()
}
