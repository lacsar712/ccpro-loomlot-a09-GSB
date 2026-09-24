<script>
  import Router, { replace } from 'svelte-spa-router';
  import { wrap } from 'svelte-spa-router/wrap';
  import { get } from 'svelte/store';
  import { onDestroy } from 'svelte';
  import { token } from './lib/auth.js';
  import { refreshPendingHandovers } from './lib/handover.js';
  import ProcessBar from './components/ProcessBar.svelte';
  import Login from './routes/Login.svelte';
  import Dashboard from './routes/Dashboard.svelte';
  import DyeHouses from './routes/DyeHouses.svelte';
  import Vats from './routes/Vats.svelte';
  import DyeLots from './routes/DyeLots.svelte';
  import FastnessChecks from './routes/FastnessChecks.svelte';
  import NightHandovers from './routes/NightHandovers.svelte';

  const requireAuth = () => !!get(token);

  const routes = {
    '/login': Login,
    '/': wrap({ component: Dashboard, conditions: [requireAuth] }),
    '/houses': wrap({ component: DyeHouses, conditions: [requireAuth] }),
    '/vats': wrap({ component: Vats, conditions: [requireAuth] }),
    '/lots': wrap({ component: DyeLots, conditions: [requireAuth] }),
    '/checks': wrap({ component: FastnessChecks, conditions: [requireAuth] }),
    '/handovers': wrap({ component: NightHandovers, conditions: [requireAuth] }),
  };

  function onConditionsFailed() {
    replace('/login');
  }

  let pendingTimer = null;

  $: if ($token && !pendingTimer) {
    refreshPendingHandovers();
    pendingTimer = setInterval(refreshPendingHandovers, 30000);
  } else if (!$token && pendingTimer) {
    clearInterval(pendingTimer);
    pendingTimer = null;
  }

  onDestroy(() => {
    if (pendingTimer) clearInterval(pendingTimer);
  });
</script>

{#if $token}
  <div class="shell">
    <ProcessBar />
    <main class="main">
      <Router {routes} on:conditionsFailed={onConditionsFailed} />
    </main>
  </div>
{:else}
  <Router {routes} on:conditionsFailed={onConditionsFailed} />
{/if}

<style>
  .shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .main {
    flex: 1;
    padding: 1.5rem 1.75rem 2.5rem;
    max-width: 1180px;
    width: 100%;
    margin: 0 auto;
  }
</style>
