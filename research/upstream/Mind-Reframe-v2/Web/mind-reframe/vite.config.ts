import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Thêm đoạn này vào để cho phép ngrok truy cập
    allowedHosts: true, 
    // Hoặc nếu 'true' bị báo lỗi đỏ (ở bản cũ), dùng dòng dưới:
    // host: true,
  },
})