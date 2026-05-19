export type Top5Column =
  | { key: string; header: string; kind: 'text'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'link'; idKey: string; path: string; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'badge'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'criticality'; headerAlign?: 'left' | 'right' }
  | { key: string; header: string; kind: 'missionPriority'; headerAlign?: 'left' | 'right' }

export type Top5CardIcon = 'location' | 'gear' | 'building'
