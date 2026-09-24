<script>
  import { onMount } from 'svelte';
  import { api, toLocalInput, fromLocalInput } from '../lib/api.js';
  import { user } from '../lib/auth.js';

  let rows = [];
  let vats = [];
  let error = '';
  let form = {
    handoverBy: '',
    successor: '',
    handedAt: toLocalInput(new Date().toISOString()),
    dyeingVatCount: 0,
    notes: '',
  };
  let editing = null;

  $: pendingCount = rows.filter((r) => !r.confirmedAt).length;

  async function load() {
    error = '';
    try {
      [rows, vats] = await Promise.all([api('/shift-handovers'), api('/vats')]);
      if (!editing) {
        form = {
          ...form,
          handoverBy: form.handoverBy || $user?.displayName || '',
          dyeingVatCount: vats.filter((v) => v.status === 'dyeing').length,
        };
      }
    } catch (e) {
      error = e.message;
    }
  }

  onMount(load);

  function canConfirm(row) {
    return (
      $user &&
      ($user.role === 'admin' ||
        $user.displayName === row.successor ||
        $user.username === row.successor)
    );
  }

  async function save() {
    error = '';
    try {
      const body = {
        handoverBy: form.handoverBy.trim(),
        successor: form.successor.trim(),
        handedAt: fromLocalInput(form.handedAt),
        dyeingVatCount: Number(form.dyeingVatCount),
        notes: form.notes.trim() || null,
      };
      if (editing) {
        await api(`/shift-handovers/${editing}`, { method: 'PUT', body: JSON.stringify(body) });
      } else {
        await api('/shift-handovers', { method: 'POST', body: JSON.stringify(body) });
      }
      editing = null;
      form = {
        handoverBy: $user?.displayName || '',
        successor: '',
        handedAt: toLocalInput(new Date().toISOString()),
        dyeingVatCount: vats.filter((v) => v.status === 'dyeing').length,
        notes: '',
      };
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  function startEdit(row) {
    editing = row.id;
    form = {
      handoverBy: row.handoverBy,
      successor: row.successor,
      handedAt: toLocalInput(row.handedAt),
      dyeingVatCount: row.dyeingVatCount,
      notes: row.notes || '',
    };
  }

  async function confirmRow(row) {
    error = '';
    try {
      await api(`/shift-handovers/${row.id}/confirm`, {
        method: 'POST',
        body: JSON.stringify({ confirmedAt: new Date().toISOString() }),
      });
      await load();
    } catch (e) {
      error = e.message;
    }
  }

  async function remove(id) {
    if (!confirm('确认删除该交接班条？')) return;
    error = '';
    try {
      await api(`/shift-handovers/${id}`, { method: 'DELETE' });
      await load();
    } catch (e) {
      error = e.message;
    }
  }
</script>

<h1 class="page-title">夜班交接</h1>
<p class="page-sub">交班登记后处于待接状态；接班人本人或主管确认接班前，全场暂停新建染程与色牢度抽检。</p>

{#if pendingCount > 0}
  <div class="panel pending-banner">
    有 {pendingCount} 条交接班待接：全场已暂停新建染程与色牢度抽检，接班确认后自动恢复。
  </div>
{/if}

<div class="panel" style="margin-bottom:1rem;">
  <div class="form-grid">
    <label>交班人 <input bind:value={form.handoverBy} /></label>
    <label>接班人 <input bind:value={form.successor} /></label>
    <label>交班时刻 <input type="datetime-local" bind:value={form.handedAt} /></label>
    <label
      >在染缸数快照
      <input type="number" min="0" step="1" bind:value={form.dyeingVatCount} />
    </label>
    <label>备注 <input bind:value={form.notes} /></label>
  </div>
  <div class="toolbar">
    <button class="btn" type="button" on:click={save}>{editing ? '保存修改' : '新建交接班'}</button>
    {#if editing}
      <button class="btn ghost" type="button" on:click={() => (editing = null)}>取消</button>
    {/if}
  </div>
  {#if error}<p class="err">{error}</p>{/if}
</div>

<div class="panel">
  <table>
    <thead>
      <tr>
        <th>ID</th>
        <th>交班人</th>
        <th>接班人</th>
        <th>交班时刻</th>
        <th>确认时刻</th>
        <th>在染缸数</th>
        <th>状态</th>
        <th>备注</th>
        <th></th>
      </tr>
    </thead>
    <tbody>
      {#each rows as row}
        <tr>
          <td>{row.id}</td>
          <td>{row.handoverBy}</td>
          <td>{row.successor}</td>
          <td>{new Date(row.handedAt).toLocaleString()}</td>
          <td>{row.confirmedAt ? new Date(row.confirmedAt).toLocaleString() : '—'}</td>
          <td>{row.dyeingVatCount}</td>
          <td>
            {#if row.confirmedAt}
              <span class="badge ready">已接</span>
            {:else}
              <span class="badge drain">待接</span>
            {/if}
          </td>
          <td>{row.notes || '—'}</td>
          <td class="row-actions">
            {#if !row.confirmedAt && canConfirm(row)}
              <button class="btn small" type="button" on:click={() => confirmRow(row)}>确认接班</button>
            {/if}
            <button class="btn ghost small" type="button" on:click={() => startEdit(row)}>编辑</button>
            <button class="btn danger small" type="button" on:click={() => remove(row.id)}>删除</button>
          </td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .pending-banner {
    border-color: rgba(224, 168, 74, 0.55);
    color: var(--warn);
    font-size: 0.9rem;
    margin-bottom: 1rem;
  }
</style>
