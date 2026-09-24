<script>
  import { onMount } from 'svelte';
  import { link } from 'svelte-spa-router';
  import { api } from '../lib/api.js';
  import { pendingHandovers } from '../lib/handover.js';

  let stats = null;
  let error = '';

  onMount(async () => {
    try {
      stats = await api('/dashboard/stats');
      pendingHandovers.set(stats.nightHandoverPendingCount || 0);
    } catch (e) {
      error = e.message;
    }
  });
</script>

<h1 class="page-title">工艺总览</h1>
<p class="page-sub">按染坊 → 染缸 → 染程 → 色牢度推进；顶部步骤条可跳转各工序。</p>

{#if error}
  <p class="err">{error}</p>
{/if}

{#if $pendingHandovers > 0}
  <div class="lock-banner">
    ⚠ 现有 <strong>{$pendingHandovers}</strong> 条夜班交接待接班确认，全场禁止新建染程与色牢度抽检。
    <a class="banner-link" href="/handovers" use:link>前往处理 →</a>
  </div>
{/if}

{#if stats}
  <div class="grid-stats">
    <div class="stat" class:stat-warn={$pendingHandovers > 0}>
      <div class="n">{$pendingHandovers}</div>
      <div class="l">夜班交接待接</div>
    </div>
    <div class="stat">
      <div class="n">{stats.dyeHouseTotal}</div>
      <div class="l">染坊</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatReadyCount}</div>
      <div class="l">就绪染缸</div>
    </div>
    <div class="stat">
      <div class="n">{stats.vatDyeingCount}</div>
      <div class="l">染色中</div>
    </div>
    <div class="stat">
      <div class="n">{stats.lotsLast7d}</div>
      <div class="l">近 7 日染程</div>
    </div>
    <div class="stat">
      <div class="n">{stats.checksLast24h}</div>
      <div class="l">近 24 时抽检</div>
    </div>
  </div>
{/if}

<div class="panel">
  <p style="margin:0 0 0.75rem;color:var(--indigo-mist);font-size:0.9rem;">
    业务约束：仅当染缸为 <strong>ready</strong> 或 <strong>dyeing</strong> 时可新建染程；新建后染缸自动变为 dyeing。排液可用染缸「完成排液」动作。
    存在<strong>夜班交接待接</strong>条时，全场禁止新建染程与色牢度抽检，接班确认后恢复。
  </p>
  <div class="toolbar">
    <a class="btn" href="/houses" use:link>进入染坊</a>
    <a class="btn ghost" href="/vats" use:link>管理染缸</a>
    <a class="btn ghost" href="/lots" use:link>登记染程</a>
    <a class="btn ghost" href="/checks" use:link>色牢度抽检</a>
    <a class="btn ghost" href="/handovers" use:link>夜班交接</a>
  </div>
</div>

<style>
  .lock-banner {
    margin-bottom: 1.1rem;
    padding: 0.8rem 1rem;
    border: 1px solid rgba(224, 168, 74, 0.6);
    background: rgba(224, 168, 74, 0.14);
    color: var(--warn);
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .banner-link {
    margin-left: 0.5rem;
    color: white;
    text-decoration: underline;
    white-space: nowrap;
  }

  .stat-warn {
    border-color: rgba(224, 168, 74, 0.7);
    box-shadow: 0 0 0 1px rgba(224, 168, 74, 0.35);
  }

  .stat-warn .n {
    color: var(--warn);
  }
</style>
