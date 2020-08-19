<script>
  export let mac;
  export let row;
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

<tr>
  <td>{row.host}</td>
  <td>{mac}</td>
  <td>
    <label><input type="radio" bind:group={row.route} value="normal"/> normal</label>
    <label><input type="radio" bind:group={row.route} value="webfilter"/> webfilter</label>
    <label><input type="radio" bind:group={row.route} value="drop"/> drop</label>
  </td>
  <td>{status}</td>
</tr>
