import { vi, describe, test, assert } from "vitest";
import { readFileSync } from "fs";
import { TaxonomyNode, parseTaxonomy } from "../src/util/taxonomy";
import * as d3 from "d3";

// mock d3.tsv
async function mockedTsv(slice: string): Promise<object[]> {
    const textData = readFileSync(slice, "utf-8");
    let lines = textData.split("\n").filter((l) => l.trim() != "");

    // drop header
    lines = lines.slice(1);

    let data: object[] = [];
    for (let line of lines) {
        const values = line.split("\t");
        const record = {
            "Feature ID": values[0],
            Taxon: values[1],
        };
        data.push(record);
    }

    return data;
}
vi.mock("d3-fetch", () => {
    return { tsv: vi.fn(mockedTsv) };
});

describe("parseTaxonomy()", async () => {
    let root: d3.HierarchyNode<TaxonomyNode>;

    test("parses successfully", async () => {
        root = await parseTaxonomy("tests/data/taxonomy-fake.tsv");
    });

    test("has correct number of nodes", () => {
        assert.equal(root.descendants().length, 12);
    });

    test("root has correct children", () => {
        const exp = ["d1", "d2"];
        assert.deepEqual(
            root.children!.map((c) => c.data.name),
            exp,
        );
    });

    test("back references exist", () => {
        assert.equal(root.data.hierarchyNode, root);
    });
});
