<script>
  import { onMount } from 'svelte';
  import { api, toLocalInput, fromLocalInput } from '../lib/api.js';
  import { user } from '../lib/auth.js';
  import { pendingHandovers } from '../lib/handover.js';

  let users = [];
  let rows = [];
  let loaded = false;
  let error = '';
  let form = {
    handoverById: '',
    takeoverById: '',
    handedAt: toLocalInput(new Date().toISOString()),
    notes: '',
  };

  async function load() {
    error = '';
    try {
      [users, rows] = await Promise.all([
        api('/auth/users'),
        api('/night-handovers'),
      ]);
      loaded = true;
      if (!form.handoverById && users.length) {
        const me = users.find((u) => u.username === $user?.username);
        const other = users.find((u) => u.id !== me?.id) || users[0];
        form.handoverById = String((me || users[0]).id);
        form.takeoverById = String(other.id);
      }
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  $: pendingRows = rows.filter((r) => r.isPending);
  $: pendingCount = pendingRows.length;
  $: if (loaded) pendingHandovers.set(pendingCount);

  function userLabel(id) {
    const u = users.find((x) => x.id === id);
    if (!u) return `#${id}`;
    return u.role === 'admin' ? `${u.displayName}（主管）` : u.displayName;
  }

  function canConfirm(row) {
    return $user && (row.takeoverById === $user.id || $user.role === 'admin');
  }

  async function createHandover() {
    error = '';
    if (!form.handoverById || !form.takeoverById) {
      error = '请选择交班人与接班人';
      return;
    }
    if (form.handoverById === form.takeoverById) {
      error = '交班人与接班人不得相同';
      return;
    }
    try {
      await api('/night-handovers', {
        method: 'POST',
        body: JSON.stringify({
          handoverById: Number(form.handoverById),
          takeoverById: Number(form.takeoverById),
          handedAt: fromLocalInput(form.handedAt),
          notes: form.notes.trim() || null,
        }),
      });
      form.notes = '';
      form.handedAt = toLocalInput(new Date().toISOString());
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function confirmRow(row) {
    if (!confirm('确认完成接班？确认后全场恢复新建染程与色牢度抽检。')) return;
    error = '';
    try {
      await api(`/night-handovers/${row.id}/confirm`, {
        method: 'POST',
        body: JSON.stringify({}),
      });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">夜班交接</h1>
<p class="page-sub">交班条未经接班确认即为「待接」；存在待接条时全场禁止新建染程与色牢度抽检。</p>

{#if pendingCount > 0}
  <div class="lock-banner">
    ⚠ 当前 <strong>{pendingCount}</strong> 条夜班交接待接班确认，全场已禁止新建染程与色牢度抽检；
    接班人本人或主管确认后自动恢复。
  </div>
{/if}

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label
      >交班人
      <select bind:value={form.handoverById}>
        {#each users as u}
          <option value={String(u.id)}>{u.displayName} · {u.username}</option>
        {/each}
      </select>
    </label>
    <label
      >接班人
      <select bind:value={form.takeoverById}>
        {#each users as u}
          <option value={String(u.id)}>{u.displayName} · {u.username}</option>
        {/each}
      </select>
    </label>
    <label>交班时刻 <input type="datetime-local" bind:value={form.handedAt} /></label>
    <label>备注 <input bind:value={form.notes} placeholder="在缸情况、温度、注意事项" /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={createHandover}>新建夜班交接条</button>
    <span class="snapshot-hint">在染缸数快照由系统按交班时刻自动写入</span>
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel">
  <div class="list-head">
    <h2 class="list-title">交接记录</h2>
    <span class="pending-tag">待接 {pendingCount} 条</span>
  </div>
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>状态</th>
        <th>交班人</th>
        <th>接班人</th>
        <th>交班时刻</th>
        <th>接班确认时刻</th>
        <th>在染缸数快照</th>
        <th>备注</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr class:row-pending={row.isPending}>
          <td>{row.id}</td>
          <td>
            {#if row.isPending}
              <span class="badge pending">待接</span>
            {:else}
              <span class="badge done">已确认</span>
            {/if}
          </td>
          <td>{row.handoverByName || userLabel(row.handoverById)}</td>
          <td>{row.takeoverByName || userLabel(row.takeoverById)}</td>
          <td>{new Date(row.handedAt).toLocaleString()}</td>
          <td>{row.confirmedAt ? new Date(row.confirmedAt).toLocaleString() : '—'}</td>
          <td>{row.activeVatCount}</td>
          <td>{row.notes || '—'}</td>
          <td class="row-actions">
            {#if row.isPending}
              {#if canConfirm(row)}
                <button class="btn small" type="button" on:click={() => confirmRow(row)}>接班确认</button>
              {:else}
                <span class="wait-hint">待 {row.takeoverByName || userLabel(row.takeoverById)} 确认</span>
              {/if}
            {/if}
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .lock-banner {
    margin-bottom: 1rem;
    padding: 0.8rem 1rem;
    border: 1px solid rgba(224, 168, 74, 0.6);
    background: rgba(224, 168, 74, 0.14);
    color: var(--warn);
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .snapshot-hint {
    font-size: 0.78rem;
    color: var(--indigo-mist);
  }

  .list-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
  }

  .list-title {
    font-size: 1.05rem;
    margin: 0;
    letter-spacing: 0.04em;
  }

  .pending-tag {
    font-size: 0.8rem;
    color: var(--warn);
    border: 1px solid rgba(224, 168, 74, 0.5);
    border-radius: 999px;
    padding: 0.1rem 0.65rem;
  }

  .row-pending {
    background: rgba(224, 168, 74, 0.07);
  }

  .badge {
    display: inline-block;
    padding: 0.08rem 0.55rem;
    border-radius: 999px;
    font-size: 0.78rem;
  }

  .badge.pending {
    color: var(--warn);
    border: 1px solid rgba(224, 168, 74, 0.6);
  }

  .badge.done {
    color: var(--ok);
    border: 1px solid rgba(76, 175, 130, 0.6);
  }

  .wait-hint {
    font-size: 0.75rem;
    color: var(--indigo-mist);
    white-space: nowrap;
  }
</style>
