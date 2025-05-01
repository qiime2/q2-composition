import { vi, describe, test, assert } from "vitest";
import { readFileSync } from "fs";
import { FeatureRecords } from "../src/util/features";
import {
    getColumnField,
    parseJSONLFeatureRecord,
    parseSlice,
    parseAllSlices,
} from "../src/util/parse";

// mock d3.text
async function mockedText(slice: string): Promise<string> {
    return readFileSync(slice, "utf-8");
}
vi.mock("d3-fetch", () => {
    return { text: vi.fn(mockedText) };
});

describe("getColumnField()", () => {
    const lfcText = readFileSync("tests/data/output-format/lfc.jsonl", "utf-8");
    const header = JSON.parse(lfcText.split("\n")[0]);

    test("column name is present", () => {
        const column = "body-site::left palm";
        const exp = {
            name: "body-site::left palm",
            type: null,
            missing: false,
            title: "",
            description: "",
            extra: {
                variable: "body-site",
                level: "left palm",
                reference: "gut",
            },
        };

        assert.deepEqual(getColumnField(column, header), exp);
    });

    test("column name not present", () => {
        const column = "waldo";

        assert.throws(
            () => getColumnField(column, header),
            "Column waldo not found in JSONL header.",
        );
    });
});

describe("parseJSONLFeatureRecord()", () => {
    const lfcText = readFileSync("tests/data/output-format/lfc.jsonl", "utf-8");
    const jsonRecords = lfcText
        .split("\n")
        .filter((line) => line.trim() !== "")
        .map((line) => JSON.parse(line));

    const header = jsonRecords[0];
    const jsonRecord = jsonRecords[1];
    const sliceName = "lfc";

    const obs = parseJSONLFeatureRecord(jsonRecord, header, sliceName);

    test("parses feature id", () => {
        assert.equal(obs.featureId, "4b5eeb300368260019c1fbc7a3c718fc");
    });

    test("parses correct number of variables", () => {
        assert.equal(obs.variables.size, 5);
    });

    test("parses categorical columns", () => {
        const variables = Array.from(obs.variables.values());
        const bodySiteVariables = variables.filter(
            (v) => v.name == "body-site",
        );
        assert.equal(bodySiteVariables.length, 3);

        const levels = bodySiteVariables.map((v) => v.level);
        assert.sameMembers(levels, ["right palm", "left palm", "tongue"]);

        const references = bodySiteVariables.map((v) => v.reference);
        assert.sameMembers(references, ["gut", "gut", "gut"]);
    });

    test("parses numerical columns", () => {
        const variables = Array.from(obs.variables.values());
        const nonCategoricalVariables = variables.filter(
            (v) => !Object.hasOwn(v, "reference"),
        );
        assert.equal(nonCategoricalVariables.length, 2);

        const yearVariable = nonCategoricalVariables.find(
            (v) => v.name == "year",
        );
        assert.deepEqual(yearVariable, {
            name: "year",
            lfc: 189.6871124062,
        });
    });
});

describe("parseSlice()", async () => {
    const sliceFilepath = "tests/data/output-format/lfc.jsonl";
    const featureRecords = new FeatureRecords();
    await parseSlice(sliceFilepath, featureRecords);

    test("correct number of features", () => {
        assert.equal(featureRecords.records.length, 8);
    });

    test("slice parsed correctly", () => {
        const feature = featureRecords.getFeature(
            "fe30ff0f71a38a39cf1717ec2be3a2fc",
        );

        assert.equal(
            feature!.getVariableSlice("body-site", "lfc", "left palm"),
            113.4173262332,
        );

        assert.equal(feature!.getVariableSlice("year", "lfc"), 181.01108921);

        const variable = feature!.getVariable("body-site", "right palm");
        assert.isOk(variable!.lfc);
        assert.isNotOk(variable!.q);
        assert.isNotOk(variable!.p);
        assert.isNotOk(variable!.se);
    });
});

describe("parseAllSlices()", async () => {
    const sliceDirPath = "tests/data/output-format";
    const featureRecords = new FeatureRecords();
    await parseAllSlices(sliceDirPath, featureRecords);

    test("correct number of features", () => {
        assert.equal(featureRecords.records.length, 8);
    });

    test("all slices parsed", () => {
        for (let featureRecord of featureRecords.records) {
            for (let variable of featureRecord.variables.values()) {
                for (let prop of ["lfc", "se", "p", "q"]) {
                    assert.property(variable, prop);
                    assert.isDefined(variable[prop]);
                }
            }
        }
    });

    test("structure and contents of arbitrary feature", () => {
        const id = "1d2e5f3444ca750c85302ceee2473331";
        const feature = featureRecords.getFeature(id);

        assert.equal(
            feature!.getVariableSlice("body-site", "lfc", "left palm"),
            86.9453579935,
        );

        assert.equal(feature!.getVariableSlice("year", "se"), 0.0030650395);

        assert.property(
            feature!.getVariable("body-site", "tongue"),
            "reference",
        );
    });
});
