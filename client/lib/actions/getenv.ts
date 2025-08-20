'use server'

export async function getEnv(env: string) {
  const value = process.env[env]
  return value
}
