import { ref, computed } from 'vue'
import { getMe, loginUser, registerUser } from './api.js'

const token = ref(localStorage.getItem('agentready_token') || null)
const user = ref(null)

export const isLoggedIn = computed(() => !!token.value && !!user.value)
export const isPro = computed(() => user.value?.plan === 'pro')

export async function initAuth() {
  if (!token.value) return
  try {
    const data = await getMe()
    user.value = data
  } catch {
    token.value = null
    user.value = null
    localStorage.removeItem('agentready_token')
  }
}

export async function login(email, password) {
  const data = await loginUser(email, password)
  token.value = data.token
  user.value = data.user
  localStorage.setItem('agentready_token', data.token)
  return data
}

export async function register(email, password) {
  const data = await registerUser(email, password)
  token.value = data.token
  user.value = data.user
  localStorage.setItem('agentready_token', data.token)
  return data
}

export function logout() {
  token.value = null
  user.value = null
  localStorage.removeItem('agentready_token')
}

export { token, user }
