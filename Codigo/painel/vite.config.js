import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Painel do TCC (4.6.1): app estatico, servido pela Vercel, consumindo a
// interface REST que roda na VM. Em desenvolvimento, VITE_API_URL aponta
// para o uvicorn local.
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
