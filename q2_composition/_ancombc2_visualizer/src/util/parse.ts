import { text } from "d3-fetch";

import {
    FeatureRecords,
    FeatureRecord,
    type VariableRecord,
} from "./features.svelte";

import { TaxonomyNode } from "./taxonomy.svelte";

type JSONLHeaderField = {
    name: string;
    type: string | null;
    missing: boolean;
    title: string;
    description: string;
    extra: Record<string, any>;
};
type JSONLHeader = {
    doctype: object;
    direction: string;
    style: string;
    fields: JSONLHeaderField[];
};
type JSONLFeatureRecord = {
    taxon: string;
} & Record<string, number>;

/**
 * Parses slice data from the ANCOMBC2 output format that resides inside of the
 * visualization artifact. Side-effects `featureRecords` by adding/updating
 * parsed features.
 */
export async function parseAllSlices(
    slicesDir: string,
    featureRecords: FeatureRecords,
    rootTaxon: TaxonomyNode | null = null,
): Promise<any> {
    const slices = ["lfc", "p", "q", "se"];
    for (let slice of slices) {
        const sliceFilepath = `${slicesDir}/${slice}.jsonl`;
        await parseSlice(sliceFilepath, featureRecords, rootTaxon);
    }

    return Promise.resolve();
}

/**
 * Parses a JSONL slice into `FeatureRecord`s and adds them to `featureRecords`.
 */
export async function parseSlice(
    sliceFilepath: string,
    featureRecords: FeatureRecords,
    rootTaxon: TaxonomyNode | null,
): Promise<undefined> {
    // open file, convert to json
    const textData: string = await text(sliceFilepath);
    const jsonRecords: any = textData
        .split("\n")
        .filter((line) => line.trim() != "")
        .map((line) => JSON.parse(line));

    // parse header and check if empty
    if (jsonRecords.length < 1) {
        const msg = `The ${sliceFilepath} slice is empty.`;
        throw new Error(msg);
    } else if (jsonRecords.length === 1) {
        const msg = `The ${sliceFilepath} slice has a header but no records.`;
        throw new Error(msg);
    }
    const header: JSONLHeader = jsonRecords.shift()!;

    // parse each remaining line into a feature record
    const jsonFeatureRecords: JSONLFeatureRecord[] = jsonRecords;
    const sliceName = sliceFilepath.split("/").pop()!.replace(".jsonl", "");

    jsonFeatureRecords.forEach((record) => {
        const feature = parseJSONLFeatureRecord(
            record,
            header,
            sliceName,
            rootTaxon,
        );
        featureRecords.addFeature(feature);
    });
}

/**
 * Parses a feature record line from a JSONL slice into a `FeatureRecord`
 * object.
 */
export function parseJSONLFeatureRecord(
    jsonRecord: JSONLFeatureRecord,
    header: JSONLHeader,
    slice: string,
    rootTaxon: TaxonomyNode | null,
): FeatureRecord {
    const taxonNode = rootTaxon?.findTaxonById(jsonRecord.taxon);

    const featureRecord = new FeatureRecord(jsonRecord.taxon, taxonNode);

    for (let column of Object.keys(jsonRecord)) {
        if (column == "taxon") continue;

        const value = jsonRecord[column];

        const headerField = getColumnField(column, header);

        let variable: VariableRecord;
        if (headerField.extra.reference) {
            variable = featureRecord.createVariable(
                headerField.extra.variable,
                slice,
                value,
                headerField.extra.level,
                headerField.extra.reference,
            );
        } else {
            variable = featureRecord.createVariable(column, slice, value);
        }

        featureRecord.addVariable(variable);
    }

    return featureRecord;
}

/**
 * Retrieves the header field entry for the `column` column.
 */
export function getColumnField(
    column: string,
    header: JSONLHeader,
): JSONLHeaderField {
    const columnFields: JSONLHeaderField[] = header.fields.filter((field) => {
        return field.name === column;
    });

    if (columnFields.length > 1) {
        const msg = `Duplicate name '${column}' found in JSONL header.`;
        throw new Error(msg);
    } else if (!columnFields.length) {
        const msg = `Column ${column} not found in JSONL header.`;
        throw new Error(msg);
    }

    return columnFields.shift()!;
}
