import { create } from 'zustand'

interface UIState {
  isNavExpanded: boolean
  toggleNav: () => void
  setNavExpanded: (expanded: boolean) => void
}

export const useUIStore = create<UIState>((set) => ({
  isNavExpanded: true,
  toggleNav: () => set((state) => ({ isNavExpanded: !state.isNavExpanded })),
  setNavExpanded: (expanded) => set({ isNavExpanded: expanded }),
}))
