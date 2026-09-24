import { writable } from 'svelte/store';
import { api } from './api.js';

// 全场待接夜班交接条数；>0 时锁定新建染程与色牢度抽检
export const pendingHandovers = writable(0);

export async function refreshPendingHandovers() {
  try {
    const r = await api('/night-handovers/pending-count');
    pendingHandovers.set(r.pendingCount || 0);
  } catch {
    // 拉取失败不阻断页面，等下次刷新
  }
}
