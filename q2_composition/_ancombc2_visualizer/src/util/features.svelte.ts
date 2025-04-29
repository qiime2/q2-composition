import { TaxonomyNode } from "./taxonomy.svelte";

export type VariableRecord = {
    name: string;
    lfc?: number;
    p?: number;
    q?: number;
    se?: number;
    level?: string;
    reference?: string;
} & Record<string, number | string>;

export class FeatureRecord {
    featureId: string;
    classification?: string;
    shortClassification?: string;
    variables: Map<string, VariableRecord> = new Map();

    constructor(featureId: string, taxonomyNode?: TaxonomyNode) {
        this.featureId = featureId;

        this.classification = taxonomyNode?.getFullTaxonString();
        if (taxonomyNode) {
            const nonAnonymousName = taxonomyNode.getNonAnonymousTaxonString();
            this.shortClassification = `(${featureId.slice(0, 6)}) ${nonAnonymousName}`;
        }
    }

    /**
     * Returns the variable with `variableName` and `level` or undefined if
     * none is found.
     */
    getVariable(
        variableName: string,
        level: string | undefined = undefined,
    ): VariableRecord | undefined {
        if (level) {
            return this.variables.get(`${variableName}::${level}`);
        }

        return this.variables.get(variableName);
    }

    /**
     * Creates a VariableRecord from primitives.
     */
    createVariable(
        variableName: string,
        slice: string,
        value: number,
        level: string | undefined = undefined,
        reference: string | undefined = undefined,
    ): VariableRecord {
        let variable = {
            name: variableName,
            [slice]: value,
        };
        if (level && reference) {
            variable.level = level;
            variable.reference = reference;
        }

        return variable;
    }

    /**
     * Adds a new variable to the set of feature variables. If a matching
     * variable is already present then updates that variable with the any new
     * slice properties from `variable`.
     */
    addVariable(variable: VariableRecord): undefined {
        let matchingVariable = this.getVariable(variable.name, variable.level);

        let newVariable: VariableRecord;
        if (!matchingVariable) {
            newVariable = variable;
        } else {
            newVariable = {
                ...matchingVariable,
                ...variable,
            };
        }

        if (newVariable.level) {
            this.variables.set(
                `${newVariable.name}::${newVariable.level}`,
                newVariable,
            );
        } else {
            this.variables.set(newVariable.name, newVariable);
        }
    }

    /**
     * Returns the slice value for some variable. Errors if the variable or
     * slice is not found.
     */
    getVariableSlice(
        variableName: string,
        slice: string,
        level: string | undefined = undefined,
    ): number {
        const variable = this.getVariable(variableName, level);

        if (!variable) {
            throw new Error(`The ${variable} variable was not found.`);
        }
        if (!Object.hasOwn(variable, slice)) {
            throw new Error(`The ${variable} variable has no ${slice} slice.`);
        }

        return variable[slice] as number;
    }
}

export type ViewRecord = {
    featureId: string;
    lfc: number;
    se: number;
    p: number;
    q: number;
    classification: string;
    shortClassification: string;
};

type Filter = {
    (record: FeatureRecord): boolean;
    slice: string;
    relationship: string;
    value: number;
};

export class FeatureRecords {
    records: FeatureRecord[] = [];

    rootTaxon: TaxonomyNode | null = null;
    hideFiltered: boolean = false;
    showOnlyKept: boolean = false;

    view: ViewRecord[] = [];
    viewVariable: string = $state("");
    viewVariableLevel: string = $state("");

    filters: Filter[] = [];

    /**
     * Returns an arbitrary variable record, useful for initializing the
     * barplot.
     */
    getInitialVariable(): VariableRecord {
        return this.getAllVariables()[0];
    }

    /*
     * Return the feature with id `featureId`, or undefined if not found.
     */
    getFeature(featureId: string): FeatureRecord | undefined {
        return this.records.find((r) => r.featureId == featureId);
    }

    /**
     * Adds a new feature. If a matching feature is already present then
     * merges that feature's variables with those from `feature`.
     */
    addFeature(feature: FeatureRecord): undefined {
        let matchingFeature = this.getFeature(feature.featureId);

        if (!matchingFeature) {
            this.records.push(feature);
        } else {
            Array.from(feature.variables.values()).forEach((v) =>
                matchingFeature.addVariable(v),
            );
        }
    }

    /**
     * Adds a user-specified filter to the set of filters applied to the
     * data. The filter function is annotated with each of this functions
     * arguments for display in the UI.
     */
    addFilter(slice: string, relationship: string, value: number) {
        const filter = (record: FeatureRecord) => {
            const variableValue = record.getVariableSlice(
                this.viewVariable,
                slice,
                this.viewVariableLevel,
            );

            if (relationship == "gt") return !(variableValue > value);
            if (relationship == "ge") return !(variableValue >= value);
            if (relationship == "lt") return !(variableValue < value);
            if (relationship == "le") return !(variableValue <= value);

            throw new Error(`Unexpected relationship ${relationship}.`);
        };

        // annotate function with its defining characteristics
        filter.slice = slice;
        filter.relationship = relationship;
        filter.value = value;

        this.filters.push(filter);
    }

    /**
     * Removes a filter by index.
     */
    removeFilter(slice: string, relationship: string, value: number) {
        this.filters = this.filters.filter((f) => {
            return !(
                f.slice == slice &&
                f.relationship == relationship &&
                f.value == value
            );
        });
    }

    /**
     * Returns all variable records in the feature dataset. Accessing only the
     * first feature record is sufficient because all features have the same
     * set of variable records. Removes the intercept variable record.
     */
    getAllVariables(): VariableRecord[] {
        const variables = Array.from(this.records[0].variables.values());
        return variables.filter((v) => v.name != "(Intercept)");
    }

    /**
     */
    getVariablesWithName(variableName: string): VariableRecord[] {
        const variables = this.getAllVariables();
        return variables.filter((v) => v.name == variableName);
    }

    /**
     * Renders the `view` by applying all existing filters, sorting features
     * by decreasing lfc value, and extracting the slice values for the current
     * `viewVariable`.
     */
    render() {
        let filtered: FeatureRecord[] = [];

        // apply taxonomyFilters if present
        if (this.hideFiltered || this.showOnlyKept) {
            for (let record of this.records) {
                const node = this.rootTaxon.findTaxonById(record.featureId);
                if (node == null) {
                    throw new Error(
                        `Could not find taxon with id ${record.featureId}`,
                    );
                }

                if (this.hideFiltered && !node.filtered) {
                    filtered.push(record);
                } else if (this.showOnlyKept && node.hierarchyNode.keep) {
                    filtered.push(record);
                }
            }
        } else {
            filtered = this.records;
        }

        // apply slice filters
        for (let f of Object.values(this.filters)) {
            filtered = filtered.filter(f);
        }

        // map to view records by only selecting from variable of interest
        let viewRecords: ViewRecord[] = filtered.map((record) => {
            const variable = record.getVariable(
                this.viewVariable,
                this.viewVariableLevel,
            );

            if (!variable) {
                throw new Error(
                    `Could not find variable ${this.viewVariable}.`,
                );
            }

            let classification = record.classification;
            if (classification == null) classification = "N/A";

            return {
                featureId: record.featureId,
                lfc: variable.lfc!,
                se: variable.se!,
                p: variable.p!,
                q: variable.q!,
                classification,
                shortClassification: record.shortClassification,
            };
        });

        // filter null lfc values
        viewRecords = viewRecords.filter((r) => r.lfc != null);

        // sort view records by decreasing lfc
        viewRecords = viewRecords.sort((r1, r2) => r2.lfc - r1.lfc);

        // update state
        this.view = viewRecords;
    }
}

// global state
let features = new FeatureRecords();
export default features;
