<script lang="ts">
    import features from "../util/features.svelte";
    import plot from "../util/plot";
    import ControlContainer from "./ControlContainer.svelte";

    const variables = features.getAllVariables();
    const uniqueVariableNames = Array.from(
        new Set(variables.map((v) => v.name)),
    );

    let levelNames = $derived<(string | undefined)[]>(
        features
            .getVariablesWithName(features.viewVariable)
            .map((v) => v.level),
    );
    let showLevel = $derived(levelNames.length > 1);

    function handleNameChange() {
        const variables = features.getVariablesWithName(features.viewVariable);

        if (variables.length == 1) {
            // variable not categorical
            features.viewVariableLevel = "";

            features.render();
            plot.updateData(features.view);
        }
    }

    function handleLevelChange() {
        // update features and render
        features.render();
        plot.updateData(features.view);
    }

    let showFullLabels = $state(false);

    function handleShowFullLabelsChange() {
        plot.setShowFullLabels(showFullLabels);
    }
</script>

<ControlContainer title="Model Variable and Level:">
    <div
        class="grid gap-x-2 gap-y-2 grid-cols-[auto_1fr] place-items-baseline"
    >
        <div class="grid grid-cols-subgrid col-span-2">
            <label for="variable" class="col-end-1">Name:</label>
            <select
                name="variable"
                id="variable"
                bind:value={features.viewVariable}
                class="bg-white border-gray-300 border rounded px-2 py-1 grow col-start-2 w-full"
                onchange={handleNameChange}
            >
                {#each uniqueVariableNames as name}
                    <option value={name}>{name}</option>
                {/each}
            </select>
        </div>
        <div class="grid grid-cols-subgrid col-span-2">
            <label for="level" class="col-end-1">Level:</label>
            <select
                name="level"
                id="level"
                bind:value={features.viewVariableLevel}
                class="bg-white border-gray-300 border rounded px-2 py-1 grow col-start-2 w-full"
                onchange={handleLevelChange}
                disabled={!showLevel}
            >
                {#each levelNames as name}
                    <option value={name}>{name}</option>
                {/each}
            </select>
        </div>
        <div class="flex items-center gap-4 col-span-2">
            <p class="col-end-1">Bar Thickness:</p>
            <button
                onclick={() => plot.decreaseBarThickness()}>-</button
            >
            <button
                onclick={() => plot.increaseBarThickness()}>+</button
            >
        </div>
        <div class="flex items-center gap-2 col-span-2">
            <input
                type="checkbox"
                id="show-full-labels"
                bind:checked={showFullLabels}
                onchange={handleShowFullLabelsChange}
            />
            <label for="show-full-labels">Show full labels</label>
        </div>
        <div class="col-span-2">
            <button onclick={() => plot.downloadSVG()}>
                Download SVG
            </button>
        </div>
    </div>
</ControlContainer>
