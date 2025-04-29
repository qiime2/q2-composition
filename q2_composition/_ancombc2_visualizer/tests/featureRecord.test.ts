import { describe, test, assert } from "vitest";
import { FeatureRecord, FeatureRecords } from "../src/util/features";

describe("FeatureRecord class", () => {
    const feature = new FeatureRecord("abc123");

    feature.addVariable(
        feature.createVariable("body-site", "lfc", 2.2, "tongue", "gut"),
    );
    feature.addVariable(
        feature.createVariable("body-site", "lfc", -0.3, "left palm", "gut"),
    );
    feature.addVariable(
        feature.createVariable("body-site", "p", 0.05, "left palm", "gut"),
    );

    test("addVariable()", () => {
        assert.equal(feature.variables.size, 2);
    });

    test("getVariable()", () => {
        let obs = feature.getVariable("body-site", "tongue");
        let exp = {
            name: "body-site",
            lfc: 2.2,
            level: "tongue",
            reference: "gut",
        };
        assert.deepEqual(obs, exp);

        obs = feature.getVariable("body-site", "left palm");
        exp = {
            name: "body-site",
            lfc: -0.3,
            p: 0.05,
            level: "left palm",
            reference: "gut",
        };
        assert.deepEqual(obs, exp);
    });

    test("getVariableSlice()", () => {
        let obs = feature.getVariableSlice("body-site", "lfc", "tongue");
        let exp = 2.2;
        assert.equal(obs, exp);

        obs = feature.getVariableSlice("body-site", "p", "left palm");
        exp = 0.05;
        assert.equal(obs, exp);
    });
});

describe("FeatureRecords class", () => {
    const features = new FeatureRecords();

    const feature1 = new FeatureRecord("abc123");
    feature1.addVariable(
        feature1.createVariable("body-site", "lfc", 2.2, "tongue", "gut"),
    );
    feature1.addVariable(
        feature1.createVariable("body-site", "lfc", -0.3, "left palm", "gut"),
    );

    features.addFeature(feature1);

    test("addFeature()", () => {
        assert.equal(features.records.length, 1);
    });

    const feature2 = new FeatureRecord("abc123");
    feature2.addVariable(
        feature2.createVariable("body-site", "p", 0.05, "left palm", "gut"),
    );
    features.addFeature(feature2);

    test("addFeature() matching feature", () => {
        assert.equal(features.records.length, 1);

        assert.equal(features.records[0].variables.size, 2);
    });

    test("addFeature() merges features", () => {
        assert.equal(features.records.length, 1);

        const feature = features.getFeature("abc123");

        const lfc = feature!.getVariableSlice("body-site", "lfc", "left palm");
        assert.equal(lfc, -0.3);

        const p = feature!.getVariableSlice("body-site", "p", "left palm");
        assert.equal(p, 0.05);
    });
});
