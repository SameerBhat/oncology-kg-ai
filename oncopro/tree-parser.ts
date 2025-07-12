import sax from "sax";
import { MongoClient, ObjectId } from "mongodb";
import * as cheerio from "cheerio";
import Papa from "papaparse";
import * as fs from "node:fs";

export interface User {
  id: string;
  name: string;
  phone?: string | null;

  active?: boolean | null;
  createdBy?: (string | null) | User;
  updatedBy?: (string | null) | User;
  updatedAt: string;
  createdAt: string;
  email: string;
  resetPasswordToken?: string | null;
  resetPasswordExpiration?: string | null;
  salt?: string | null;
  hash?: string | null;
  loginAttempts?: number | null;
  lockUntil?: string | null;
  password?: string | null;
}
export interface Icon {
  id: string;
  title?: string | null;
  description?: string | null;
  icon?: string | null;
  createdBy?: (string | null) | User;
  updatedBy?: (string | null) | User;
  updatedAt: string;
  createdAt: string;
}
// import { Icon, NodeCategory as PayloadCategory } from "../src/payload-types";
export interface PayloadCategory {
  id: string;
  title?: string | null;
  description?: string | null;
  category_key?: string | null;
  comments?: string | null;
  color?: string | null;
  backgroundColor?: string | null;
  border?: string | null;
  createdBy?: (string | null) | User;
  updatedBy?: (string | null) | User;
  updatedAt: string;
  createdAt: string;
}
/* ────────────────────────────────────────────────────────────────
 * Configuration
 * ────────────────────────────────────────────────────────────────*/
const MONGO_URI = process.env.DATABASE_URI || "mongodb://localhost:27017";
const DATABASE = process.env.EMBEDDING_MODEL || "jina";

const NODES_COLLECTION = "nodes";
const CATS_COLLECTION = "node_categories";
const ICONS_COLLECTION = "icons";

/* ────────────────────────────────────────────────────────────────
 * Helper interfaces
 * ────────────────────────────────────────────────────────────────*/

/** CSV attribute key/value pairs attached to a node */
export interface AttributeArrayInterface {
  key: string;
  value: string;
}

/**
 * Raw parse-time context (before DB insert)
 */
interface NodeContext {
  _id: ObjectId;
  freemindID: string;
  parentFreemindID: string | null;
  text: string | null;
  richContent: string;
  richText: string;
  notes: string;
  nodeBgColor: string | null;
  links: string[];
  font?: Record<string, any>;
  icons?: string[];
  cloud?: Record<string, any>;
  parentID?: ObjectId | null;
  ancestors?: ObjectId[];
  linkedNodes?: ObjectId[];
  attributes?: AttributeArrayInterface[];
}

/**
 * Mongo document for a **category**.
 * `_id` replaces Payload’s `id`, and we drop createdBy/updatedBy
 * to avoid importing the whole `User` type tree.
 */
export interface NodeCategoryDoc
  extends Omit<PayloadCategory, "id" | "createdBy" | "updatedBy"> {
  _id: ObjectId;
}

export interface NodeDocForInsert {
  _id: ObjectId;
  nodeid?: string;
  parentID: ObjectId | null;
  ancestors: ObjectId[];
  isRoot: boolean;
  linkedNodes: ObjectId[];
  children: ObjectId[];
  text: string;
  richContent: string;
  richText: string;
  notes: string;
  links: string[];
  font: Record<string, any>;
  cloud: Record<string, any>;
  attributes: AttributeArrayInterface[];
  category: ObjectId | null;
  icons: ObjectId[];
  createdAt: string;
  updatedAt: string;
}

/* ────────────────────────────────────────────────────────────────
 * MAIN
 * ────────────────────────────────────────────────────────────────*/
// @ts-ignore
async function main() {
  const [, , mmPath, csvPath] = process.argv;
  if (!mmPath) {
    console.error(
      "Usage: ts-node sax-parser-import-tree.ts <mindmap.mm> [color-map.csv]"
    );
    process.exit(1);
  }

  const colorMap =
    csvPath && fs.existsSync(csvPath)
      ? await loadCategoryColorMap(csvPath)
      : {};

  const { nodes, colors, uniqueIcons } = await parseXmlFile(mmPath);

  const parentToChildren = new Map<string, ObjectId[]>();
  nodes.forEach((node) => {
    if (node.parentID) {
      const key = node.parentID.toHexString();
      if (!parentToChildren.has(key)) parentToChildren.set(key, []);
      parentToChildren.get(key)!.push(node._id);
    }
  });

  await storeInMongo(nodes, colors, colorMap, parentToChildren);
  console.log(
    `Unique icons (${uniqueIcons.size}): ${[...uniqueIcons].join(", ")}`
  );
  console.log("✔︎ Import complete");
}

function parseXmlFile(filePath: string): Promise<{
  nodes: NodeContext[];
  colors: Set<string>;
  uniqueIcons: Set<string>;
}> {
  return new Promise((resolve, reject) => {
    const nodes: NodeContext[] = [];
    const seenColors = new Set<string>();
    const linkPairs: { source: string; dest: string }[] = [];
    const uniqueIcons = new Set<string>();

    const S = {
      rootID: null as string | null,
      stack: [] as NodeContext[],
      captureRich: false,
      richBuffer: "",
      captureNote: false,
      noteBuffer: "",
    };
    const parser = sax.createStream(true);

    parser.on("opentag", (tag) => {
      switch (tag.name) {
        case "node": {
          const fmID =
            tag.attributes.ID || `auto_${new ObjectId().toHexString()}`;
          const bg = tag.attributes.BACKGROUND_COLOR || null;
          const text = tag.attributes.TEXT || null;
          const links = tag.attributes.LINK ? [tag.attributes.LINK] : [];

          if (!S.rootID) S.rootID = fmID;
          if (bg) seenColors.add(bg);

          const parent = S.stack.at(-1) || null;
          const parentID = parent ? parent._id : null;
          const ancestors = parent
            ? [...(parent.ancestors || []), parent._id].slice(-20)
            : [];

          const ctx: NodeContext = {
            _id: new ObjectId(),
            freemindID: fmID,
            parentFreemindID: parent ? parent.freemindID : null,
            text,
            richContent: "",
            richText: "",
            notes: "",
            nodeBgColor: bg,
            links,
            parentID,
            ancestors,
          };

          S.stack.push(ctx);
          break;
        }
        case "richcontent":
          if (tag.attributes.TYPE === "NODE") {
            S.captureRich = true;
            S.richBuffer = "";
          } else if (tag.attributes.TYPE === "NOTE") {
            S.captureNote = true;
            S.noteBuffer = "";
          }
          break;
        case "linktarget":
          linkPairs.push({
            source: tag.attributes.SOURCE,
            dest: tag.attributes.DESTINATION,
          });
          break;
        default:
          if (S.captureRich) {
            S.richBuffer += `<${tag.name}${Object.entries(tag.attributes)
              .map(([k, v]) => ` ${k}="${v}"`)
              .join("")}>`;
          } else if (tag.name === "font" && S.stack.length) {
            S.stack.at(-1)!.font = {
              bold: tag.attributes.BOLD === "true",
              italic: tag.attributes.ITALIC === "true",
              name: tag.attributes.NAME,
              size: Number(tag.attributes.SIZE),
            };
          } else if (tag.name === "icon" && S.stack.length) {
            const curr = S.stack.at(-1)!;
            curr.icons = curr.icons || [];
            curr.icons.push(tag.attributes.BUILTIN);
            uniqueIcons.add(tag.attributes.BUILTIN);
          } else if (tag.name === "cloud" && S.stack.length) {
            S.stack.at(-1)!.cloud = { color: tag.attributes.COLOR };
          } else if (tag.name === "attribute" && S.stack.length) {
            const curr = S.stack.at(-1)!;
            curr.attributes = curr.attributes || [];
            curr.attributes.push({
              key: tag.attributes.NAME,
              value: tag.attributes.VALUE ?? "",
            });
          }
      }
    });

    parser.on("text", (txt) => {
      if (S.captureRich) S.richBuffer += txt;
      else if (S.captureNote) S.noteBuffer += txt;
    });

    parser.on("closetag", (tag) => {
      if (tag === "richcontent") {
        const node = S.stack.at(-1);
        if (!node) return;

        if (S.captureRich) {
          const $ = cheerio.load(S.richBuffer, { xmlMode: true });
          node.richContent = $.root().html()?.replace(/\s+/g, " ").trim() || "";
          node.richText = $("body").text()?.replace(/\s+/g, " ").trim() || "";
          S.captureRich = false;
        } else if (S.captureNote) {
          node.notes = S.noteBuffer.replace(/\s+/g, " ").trim();
          S.captureNote = false;
        }
      } else if (S.captureRich) {
        S.richBuffer += `</${tag}>`;
      } else if (S.captureNote) {
        S.noteBuffer += `</${tag}>`;
      } else if (tag === "node") {
        const finished = S.stack.pop();
        if (finished) nodes.push(finished);
      }
    });

    parser.on("error", reject);

    parser.on("end", () => {
      const byFM = new Map<string, NodeContext>();
      nodes.forEach((n) => byFM.set(n.freemindID, n));

      linkPairs.forEach(({ source, dest }) => {
        const src = byFM.get(source);
        const dst = byFM.get(dest);
        if (src && dst) (src.linkedNodes ||= []).push(dst._id);
      });

      resolve({ nodes, colors: seenColors, uniqueIcons });
    });

    fs.createReadStream(filePath).pipe(parser);
  });
}

async function loadCategoryColorMap(csvPath: string): Promise<
  Record<
    string,
    {
      title: string;
      category_key: string;
      comments: string;
      finalColor: string;
    }
  >
> {
  return new Promise((resolve, reject) => {
    const mapping: Record<
      string,
      {
        title: string;
        category_key: string;
        comments: string;
        finalColor: string;
      }
    > = {};
    Papa.parse(fs.readFileSync(csvPath, "utf8"), {
      header: true,
      skipEmptyLines: true,
      complete: ({ data }) => {
        data.forEach((row: any) => {
          if (!row.color_code) return;
          mapping[row.color_code] = {
            title: row.category_name ? `${row.category_name}` : `Auto-Category`,
            category_key: row.category_key || "",
            comments: row.comments || "",
            finalColor: row.color_code_final || row.color_code,
          };
        });
        resolve(mapping);
      },
      error: reject,
    });
  });
}

async function storeInMongo(
  parsed: NodeContext[],
  colors: Set<string>,
  colorMap: Record<
    string,
    {
      title: string;
      category_key: string;
      comments: string;
      finalColor: string;
    }
  >,
  parentToChildren: Map<string, ObjectId[]>
) {
  const client = new MongoClient(MONGO_URI);
  await client.connect();
  const db = client.db(DATABASE);

  const nodesCol = db.collection<NodeDocForInsert>(NODES_COLLECTION);
  const catsCol = db.collection<NodeCategoryDoc>(CATS_COLLECTION);
  const iconsCol = db.collection<Partial<Icon>>(ICONS_COLLECTION);

  await Promise.all([nodesCol.deleteMany({}), catsCol.deleteMany({})]);

  const nowISO = new Date().toISOString();

  const catCache = new Map<string, ObjectId>();
  const color2Cat = new Map<string, ObjectId>();
  const catDocs: NodeCategoryDoc[] = [];

  for (const color of colors) {
    const colorIndex = Array.from(colors).indexOf(color);
    const csv = colorMap[color] ?? {
      title: `Auto-Category-${colorIndex + 1}`,
      category_key: "",
      comments: "",
      finalColor: color,
    };
    const key = csv.category_key || csv.title;
    if (catCache.has(key)) {
      color2Cat.set(color, catCache.get(key)!);
      continue;
    }
    const _id = new ObjectId();
    const doc: NodeCategoryDoc = {
      _id,
      title: csv.title,
      category_key: key,
      description: "Auto-generated category",
      comments: csv.comments,
      color,
      backgroundColor: contrastColor(color, true),
      border: contrastColor(color, false),
      createdAt: nowISO,
      updatedAt: nowISO,
    };
    catCache.set(key, _id);
    color2Cat.set(color, _id);
    catDocs.push(doc);
  }

  if (catDocs.length) await catsCol.insertMany(catDocs);

  const iconNames = Array.from(new Set(parsed.flatMap((n) => n.icons || [])));
  const existing = await iconsCol.find({ icon: { $in: iconNames } }).toArray();
  const iconMap = new Map<string, ObjectId>();
  existing.forEach((ic) => {
    if (ic.icon && ic._id) iconMap.set(ic.icon.toString(), ic._id);
  });

  const nodeDocs: NodeDocForInsert[] = parsed.map((n) => {
    const catID =
      n.nodeBgColor && color2Cat.has(n.nodeBgColor)
        ? color2Cat.get(colorMap[n.nodeBgColor]?.finalColor ?? n.nodeBgColor) ||
          null
        : null;

    const iconIDs = (n.icons || [])
      .map((name) => iconMap.get(name))
      .filter(Boolean) as ObjectId[];
    const childIDs = [
      ...(parentToChildren.get(n._id.toHexString()) || []),
      ...(n.linkedNodes || []),
    ];

    return {
      _id: n._id,
      nodeid: n.freemindID,
      parentID: n.parentID || null,
      ancestors: n.ancestors || [],
      isRoot: !n.parentID,
      linkedNodes: n.linkedNodes ?? [],
      children: childIDs,
      text: n.text?.trim() || "",
      richContent: n.richContent,
      richText: n.text?.trim() ? "" : n.richText,
      notes: n.notes,
      links: n.links,
      font: n.font || {},
      cloud: n.cloud || {},
      attributes: n.attributes || [],
      category: catID,
      icons: iconIDs,
      createdAt: nowISO,
      updatedAt: nowISO,
    };
  });

  if (nodeDocs.length) await nodesCol.insertMany(nodeDocs);
  await client.close();
}

function contrastColor(hex: string, light = true): string {
  const norm = normalizeHex(hex);
  if (!norm) return light ? "#f3f4f6" : "#6b7280";
  return light ? lighten(norm, 0.8) : darken(norm, 0.3);
}
function normalizeHex(h: string): string | null {
  h = h.replace("#", "");
  if (h.length === 3)
    h = h
      .split("")
      .map((c) => c + c)
      .join("");
  return /^[0-9a-fA-F]{6}$/.test(h) ? h.toLowerCase() : null;
}
function hex2rgb(h: string) {
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  };
}
function rgb2hex(r: number, g: number, b: number) {
  return (
    "#" +
    [r, g, b]
      .map((x) => {
        const h = x.toString(16);
        return h.length === 1 ? "0" + h : h;
      })
      .join("")
  );
}
function lighten(hex: string, f: number) {
  const { r, g, b } = hex2rgb(hex);
  return rgb2hex(
    Math.min(255, Math.round(r + (255 - r) * f)),
    Math.min(255, Math.round(g + (255 - g) * f)),
    Math.min(255, Math.round(b + (255 - b) * f))
  );
}
function darken(hex: string, f: number) {
  const { r, g, b } = hex2rgb(hex);
  return rgb2hex(
    Math.round(r * (1 - f)),
    Math.round(g * (1 - f)),
    Math.round(b * (1 - f))
  );
}

main().catch((err) => {
  console.error("❌  Unhandled error:", err);
  process.exit(1);
});
