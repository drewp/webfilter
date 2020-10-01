<script>
  import HostRow from "./HostRow.svelte";

  const byMac = {};

  let macOrder = (async () => {
    const ret = await (await fetch("hosts")).json();
    const macs = ret.macs.map((row) => {
      byMac[row.mac] = { host: row };
      return row.mac;
    });

    const modeSettings = new EventSource("modeSettings");
    modeSettings.addEventListener("message", (ev) => {
      JSON.parse(ev.data).updates.forEach((upd) => {
        byMac[upd.mac].routing = upd;
      });
    });

    return macs;
  })();
</script>

<main>
  <h1>net_route_input</h1>
  {#await macOrder}
    <p>loading data...</p>
  {:then macs}
    <table>
      <tr>
        <td>host</td>
      </tr>
      {#each macs as mac}
        <HostRow {mac} doc={byMac[mac]} />
      {/each}
    </table>
  {:catch error}
    <p>fetch failed: {error.message}</p>
  {/await}
</main>
