<script lang="ts">
    import { slide } from "svelte/transition";
    import features from "../util/features.svelte";
    import plot from "../util/plot";
    import ControlContainer from "./ControlContainer.svelte";

    let filterInfo = $state({
        slice: "",
        relationship: "",
        value: "",
    });

    let filters = $state([]);

    let errorMessage = $state("");

    function addFilter() {
        // handle errors
        if (!filterInfo.slice) {
            errorMessage = "Please enter an input for slice.";
            return;
        }
        if (!filterInfo.relationship) {
            errorMessage = "Please enter an input for the relationship.";
            return;
        }
        filterInfo.value = filterInfo.value.trim();
        if (!filterInfo.value) {
            errorMessage = "Please enter an input for the value.";
            return;
        }

        const valueAsNumber = parseFloat(filterInfo.value);
        if (isNaN(valueAsNumber)) {
            errorMessage = "Please enter a valid number.";
            return;
        }

        // add filter to FeatureRecords instance
        features.addFilter(
            filterInfo.slice,
            filterInfo.relationship,
            valueAsNumber,
        );
        filters = features.filters;

        // rerender the viewed features and the plot
        features.render();
        plot.updateData(features.view);

        // clear local state
        errorMessage = "";
        filterInfo = {
            slice: "",
            relationship: "",
            value: "",
        };
    }

    function getSymbol(relationship: string) {
        if (relationship == "gt") return ">";
        if (relationship == "ge") return ">=";
        if (relationship == "lt") return "<";
        if (relationship == "le") return "<=";
    }

    function remove(slice: string, relationship: string, value: number) {
        return () => {
            features.removeFilter(slice, relationship, value);
            filters = features.filters;
            features.render();
            plot.updateData(features.view);
        };
    }
</script>

<ControlContainer title="Filters:">
    <div
        class="grid grid-cols-[auto_1fr] gap-2 place-items-baseline"
        transition:slide={{ duration: 200 }}
    >
        <div class="grid grid-cols-subgrid col-span-2">
            <label for="slice" class="col-end-1">Statistic:</label>
            <select
                name="slice"
                id="slice"
                class="bg-white border-gray-300 border rounded px-2 py-1 grow col-start-2 w-full"
                bind:value={filterInfo.slice}
            >
                <option value="lfc">lfc (log fold change)</option>
                <option value="se">se (standard error)</option>
                <option value="p">p-value</option>
                <option value="q">adjusted p-value (q)</option>
            </select>
        </div>
        <div class="grid grid-cols-subgrid col-span-2">
            <label for="relationship">Relationship:</label>
            <select
                name="relationship"
                id="relationship"
                class="bg-white border-gray-300 border rounded px-2 py-1 grow col-start-2 w-full"
                bind:value={filterInfo.relationship}
            >
                <option value="gt">greater than</option>
                <option value="ge">greater than/equal</option>
                <option value="lt">less than</option>
                <option value="le">less than/equal</option>
            </select>
        </div>
        <div class="grid grid-cols-subgrid col-span-2">
            <label for="value">Value:</label>
            <input
                type="text"
                id="value"
                name="value"
                class="bg-white border-gray-300 border rounded px-2 py-1 grow col-start-2 w-full"
                bind:value={filterInfo.value}
            />
        </div>

        <button onclick={addFilter}>Apply</button>

        {#if errorMessage}
            <p class="error-message" transition:slide>{errorMessage}</p>
        {/if}
    </div>
</ControlContainer>

{#if filters.length}
    <div class="bg-gray-100 px-1 py-0.5 rounded">
        {#each filters as filter}
            <div class="filter">
                <p>
                    {filter.slice}
                    {getSymbol(filter.relationship)}
                    {filter.value}
                </p>

                <button
                    onclick={remove(
                        filter.slice,
                        filter.relationship,
                        filter.value,
                    )}
                >
                    Remove
                </button>
            </div>
        {/each}
    </div>
{/if}

<style>
    .error-message {
        color: red;
    }
</style>
