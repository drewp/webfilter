import svelte from "rollup-plugin-svelte";

import resolve from "@rollup/plugin-node-resolve";
import commonjs from "@rollup/plugin-commonjs";
export default {
  input: "main.js",
  output: {
    sourcemap: false,
    format: "iife",
    name: "app",
    file: "build/bundle.js",
  },
  plugins: [
    svelte({
      dev: true,
      css: function (css) {
        console.log(css.code); // the concatenated CSS
        console.log(css.map); // a sourcemap

        // creates `main.css` and `main.css.map`
        // using a falsy name will default to the bundle name
        // — pass `false` as the second argument if you don't want the sourcemap
        css.write("main.css");
      },
    }),
    resolve({
      browser: true,
      dedupe: ["svelte"],
    }),
    commonjs(),
  ],
};
