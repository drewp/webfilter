export { StreamedGraph } from "streamed-graph";
import {
  LitElement,
  html,
  TemplateResult,
  customElement,
  property,
  unsafeCSS,
} from "lit-element";
import style from "./style.styl";
import { VersionedGraph } from "streamed-graph";
import { Quad, DataFactory, Quad_Subject, N3Store, NamedNode } from "n3";
const { namedNode } = DataFactory;
import { Moment, Duration } from "moment";
import moment from "moment";
import { getStringValue } from "streamed-graph";

// move upstream somewhere
function Namespace(prefix: string): { [key: string]: NamedNode } {
  return new Proxy(
    {},
    {
      get(target: object, name: string) {
        return namedNode(prefix + name);
      },
    }
  );
}

const RDF = Namespace("http://www.w3.org/1999/02/22-rdf-syntax-ns#");
const EV = Namespace("http://projects.bigasterisk.com/room/");
const DCTERMS = Namespace("http://purl.org/dc/terms/");

interface DisplayRow {
  time: Moment;
  creator: string;
  prettyTime: string;
  thumbnailUrl: string | undefined;
  uri: NamedNode;
}

const userFromMac = (mac: string) => {
  if (mac == "7c:b0:c2:83:31:0f") return "ari laptop";
  if (!mac) {
    mac = "unknown";
  }
  return `(todo: ${mac})`;
};

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
    const subjs = this.graph.store.getSubjects(RDF.type, EV.Activity, null);

    this.rows = [];
    const store = this.graph.store;
    subjs.forEach((subj: Quad_Subject) => {
      const t = moment(
        getStringValue(store, subj as NamedNode, DCTERMS.created)
      );
      const uri = subj as NamedNode;
      this.rows.push({
        uri: uri,
        time: t,
        prettyTime: t.format("YYYY-MM-DD ddd HH:mm:ss"),
        thumbnailUrl: getStringValue(store, uri, EV.thumbnailUrl),
        creator: userFromMac(getStringValue(store, uri, DCTERMS.creator)),
      });
    });

    this.rows.sort((a, b) => {
      return b.time.valueOf() - a.time.valueOf();
    });
  }

  render() {
    const renderRow = (row: DisplayRow) => {
      const store = this.graph.store;

      const contents: Array<TemplateResult> = [];
      const gather = (q: Quad) => {
        if (
          q.predicate.equals(RDF.type) ||
          q.predicate.equals(EV.thumbnailUrl) ||
          q.predicate.equals(DCTERMS.created) ||
          q.predicate.equals(DCTERMS.creator)
        ) {
          // already in a header column (except some types)
        } else {
          if (q.predicate.equals(EV.desc)) {
            contents.push(
              html`
                <span class="chatLine">${q.object.value}</span>
              `
            );
          } else if (q.predicate.equals(EV.link)) {
            contents.push(
              html`
                <a href="${q.object.value}" class="requested"
                  >${q.object.value}</a
                >
              `
            );
          } else if (q.predicate.equals(EV.viewUrl)) {
            const thumb = getStringValue(store, row.uri, EV.videoThumbnailUrl);
            contents.push(
              html`
                View <a href="${q.object.value}">${q.object.value}</a>
                <img class="ytThumb" src="${thumb}" />
              `
            );
          } else if (q.predicate.equals(EV.videoThumbnailUrl)) {
            //  pass
          } else if (q.predicate.equals(EV.currentTime)) {
            const duration = Math.round(
              parseFloat(getStringValue(store, row.uri, EV.videoDuration))
            );
            contents.push(
              html`
                Watched ${Math.round(parseFloat(q.object.value))} of ${duration}
                seconds
              `
            );
          } else if (q.predicate.equals(EV.videoDuration)) {
            // pass
          } else if (q.predicate.equals(EV.searchQuery)) {
              contents.push(html`Search for <pre>${q.object.value}</pre>`);
          } else {
            contents.push(
              html`
                ${q.predicate.value} => ${q.object.value};
              `
            );
          }
        }
      };
      store.forEach(gather, row.uri, null, null, null);
      let rowClasses = "";
      if (moment().diff(row.time) < 2 /*hr*/ * 60 * 60 * 1000) {
        rowClasses += " recent";
      }
      return html`
        <tr class="${rowClasses}">
          <td class="created">${row.prettyTime}</td>
          <td class="creator">${row.creator}</td>
          <td>
            <img class="rowIcon" src="${row.thumbnailUrl}" />
          </td>
          <td>
            ${contents}
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
            <th></th>
          </tr>
          ${this.rows.map(renderRow)}
        </table>
      </div>
    `;
  }
}
