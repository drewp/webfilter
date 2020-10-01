<script>
  export let mac;
  export let doc;
  const disabled = mac == "0c:fe:45:db:33:9e";
  let current = {};
  let buttons = [
    { label: "open", mode: "open", filter: null },
    { label: "proxy-open", mode: "mitmproxy", filter: "open" },
    { label: "proxy-filtered", mode: "mitmproxy", filter: "filtered" },
    { label: "drop", mode: "drop", filter: null },
  ];
  buttons.forEach((bt) => {
    bt.visible = !doc.host.allowedModes || doc.host.allowedModes.indexOf(bt.mode) != -1;
  });
  $: {
    current = { mode: (doc.routing || {}).mode, filter: (doc.routing || {}).mitmproxyFilter };
  }
  const allowModeButton = (w) => !doc.host.allowedModes || doc.host.allowedModes.indexOf(w) != -1;

  const setMode = async (mode, mitmproxyFilter) => {
    const params = new URLSearchParams();
    params.append("mac", mac);
    params.append("mode", mode);
    params.append("filter", mitmproxyFilter || "");
    return await fetch("modeSet?" + params.toString(), {
      method: "PUT",
    });
  };
</script>

<style>
  button {
    min-width: 7em;
    min-height: 5em;
  }
  .current {
    outline: 3px solid orange;
    background: #e6c393;
  }
</style>

<tr>
  <td><span title={mac}>{doc.host.name || mac}</span></td>
  {#each buttons as bt}
    <td>
      {#if bt.visible}
        <button
          {disabled}
          class:current={bt.mode == current.mode && ((!bt.filter && !current.filter) || bt.filter == current.filter)}
          on:click={() => setMode(bt.mode, bt.filter)}>{bt.label}</button>
      {/if}
    </td>
  {/each}
</tr>
