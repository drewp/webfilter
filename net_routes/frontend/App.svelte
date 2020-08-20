<script>
  import HostRow from "./HostRow.svelte";

  let routes = (async () => {
    return (await fetch("routes")).json();
  })();

  const sorted = (m) => {
    const entries = Object.entries(m);
    entries.sort((ent1, ent2) => (ent1[1].host > ent2[1].host ? 1 : -1));
    return entries;
  };
</script>

<main>
  <h1>Edit network routes:</h1>
  {#await routes}
    <p>loading data...</p>
  {:then m}
    <table>
      <tr>
        <td>host</td>
        <td>filter?</td>
        <td />
      </tr>
      {#each sorted(m) as [mac, row]}
        <HostRow {mac} {row} />
      {/each}
    </table>
  {:catch error}
    <p>fetch failed: {error.message}</p>
  {/await}
</main>
