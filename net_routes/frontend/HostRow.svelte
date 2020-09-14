<script>
  export let mac;
  export let row;
  export let disabled = false;
  let status = "";
  $: {
    const pr = fetch(`routes/${mac}`, {
      method: "PUT",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: `route=${row.route}`,
    });
    status = "sending";
    pr.then((resp) => {
      if (resp.status == 200) {
        status = "updated";
      } else {
        status = `failed (${resp.status})`;
      }
    }).catch((err) => {
      status = `failed to update: ${err.message}`;
    });
  }
</script>

<style>
  .status {
    color: gray;
    font-size: 80%;
  }
</style>

<tr>
  <td><span title={mac}>{row.host}</span></td>
  <td>
    <label> <input type="radio" bind:group={row.route} value="normal" {disabled} /> normal </label>
    <label> <input type="radio" bind:group={row.route} value="webfilter" {disabled} /> webfilter </label>
    <label> <input type="radio" bind:group={row.route} value="drop" {disabled} /> drop </label>
  </td>
  <td class="status">{status}</td>
  <td>
    {#if disabled}(This row is controlled by a calendar){/if}
  </td>
</tr>
