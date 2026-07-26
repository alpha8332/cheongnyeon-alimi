import { create } from 'zustand';

interface AppState {
  // 추후 백엔드/기능 협의 후 전역 상태 추가 예정
}

export const useAppStore = create<AppState>(() => ({}));