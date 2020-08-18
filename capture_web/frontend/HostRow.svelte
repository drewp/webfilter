<script>
  export let mac;
  export let row;
  let status = "";
  $: {
    const pr = fetch(`captures/${mac}`, {
      method: "PUT",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: `capturing=${row.capturing ? "yes" : ""}`,
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
    <input type="checkbox" bind:checked={row.capturing} />
  </td>
  <td>{status}</td>
</tr>
