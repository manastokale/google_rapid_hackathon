import { cpSync, existsSync, rmSync } from 'node:fs'
import { resolve } from 'node:path'

const rootDist = resolve('dist')
const frontendDist = resolve('frontend', 'dist')

if (!existsSync(frontendDist)) {
  throw new Error(`Missing frontend build output: ${frontendDist}`)
}

rmSync(rootDist, { force: true, recursive: true })
cpSync(frontendDist, rootDist, { recursive: true })
