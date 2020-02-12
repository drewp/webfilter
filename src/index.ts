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
  desc: namedNode("http://projects.bigasterisk.com/room/desc"),
  thumbnailUrl: namedNode("http://projects.bigasterisk.com/room/thumbnailUrl"),
  link: namedNode("http://projects.bigasterisk.com/room/link")
};
const DCTERMS = {
  created: namedNode("http://purl.org/dc/terms/created"),
  creator: namedNode("http://purl.org/dc/terms/creator"),
}

interface DisplayRow {
  time: number; // ms
  creator: string;
  prettyTime: string;
  thumbnailUrl: string | undefined;
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
      const t = getStringValue(store, subj as NamedNode, DCTERMS.created);
      this.rows.push({
        time: +new Date(t),
        prettyTime: t,
        thumbnailUrl: getStringValue(store, subj as NamedNode, EV.thumbnailUrl),
        desc: getStringValue(store, subj as NamedNode, EV.desc),
        creator: getStringValue(store, subj as NamedNode, DCTERMS.creator)
      });
      const link = getStringValue(store, subj as NamedNode, EV.link);
      if (link) {
        this.rows[this.rows.length-1].desc += ' ' + link;
      }
    });

    this.rows.sort((a, b) => {
      return b.time - a.time;
    });
  }

  render() {
    const renderRow = (row: DisplayRow) => {
      return html`
        <tr>
        <td class="time">${row.prettyTime}</td>
        <td class="time">${row.creator}</td>
          <td>
            [${row.thumbnailUrl}]<img src="${row.thumbnailUrl}" class="eventIcon" />
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
            <th>host</th>
            <th></th>
          </tr>
          ${this.rows.map(renderRow)}
        </table>
      </div>
    `;
  }
}
