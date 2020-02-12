export { StreamedGraph } from "streamed-graph";
import {
  LitElement,
  html,
  customElement,
  property,
  unsafeCSS
} from "lit-element";
import style from "./style.styl";
import { VersionedGraph } from "streamed-graph";
import {
  DataFactory,
  QuadCallback,
  Quad_Subject,
  Quad,
  N3Store,
  NamedNode
} from "n3";
const { namedNode } = DataFactory;
import { Moment, Duration } from "moment";
import moment from "moment";
import { getStringValue } from "streamed-graph";
const RDF = {
  type: namedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
};
const EV = {
  desc: namedNode("http://projects.bigasterisk.com/room/desc")
};
const DCTERMS = {
  created: namedNode("http://purl.org/dc/terms/created"),
}

interface DisplayRow {
  time: number; // ms
  prettyTime: string;
  iconUrl: string | undefined;
  desc: string;
}

@customElement("timebank-report")
export class TimebankReport extends LitElement {
  static get styles() {
    return unsafeCSS(style);
  }

  @property({ type: Object })
  graph!: VersionedGraph;

  // this has got to go
  @property({ type: String }) graphSelector: string = "streamed-graph";

  @property({ type: Array }) rows: DisplayRow[] = [];

  connectedCallback() {
    super.connectedCallback();
    const graphEl = this.parentElement!.ownerDocument!.querySelector(
      this.graphSelector
    );
    if (!graphEl) {
      return;
    }
    (graphEl.addEventListener as any)(
      "graph-changed",
      this.onGraphVersionChanged.bind(this)
    );
  }

  onGraphVersionChanged(ev: CustomEvent) {
    if (ev.detail && ev.detail.graph) {
      this.graph = ev.detail.graph as VersionedGraph;
      this.onGraphChange(this.graph.store as any);
    }
  }

  onGraphChange(graph: N3Store) {
    const subjs = this.graph.store.getSubjects(
      RDF.type,
      namedNode("http://projects.bigasterisk.com/room/Activity"),
      null
    );

    this.rows = [];
    const store = this.graph.store;
    subjs.forEach((subj: Quad_Subject) => {
      this.rows.push({
        time: 0,
        prettyTime: getStringValue(store, subj as NamedNode, DCTERMS.created),
        iconUrl: '',
        desc: getStringValue(store, subj as NamedNode, EV.desc)
      });
    });

    this.rows.sort((a, b) => {
      return a.time - b.time;
    });
  }

  render() {
    const renderRow = (row: DisplayRow) => {
      return html`
        <tr>
          <td>t=${row.prettyTime}</td>
          <td>
            <img src="${row.iconUrl}" class="eventIcon" />
            ${row.desc}
          </td>
        </tr>
      `;
    };
    return html`
      <div>
        Latest activity
        <table>
          <tr>
            <th>time</th>
            <th></th>
          </tr>
          ${this.rows.map(renderRow)}
        </table>
      </div>
    `;
  }
}
