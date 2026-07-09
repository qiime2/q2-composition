<script lang="ts">
    import { onMount } from "svelte";
    import BarplotControls from "./BarplotControls.svelte";
    import BarplotFilters from "./BarplotFilters.svelte";
    import features from "../util/features.svelte";
    import plot from "../util/plot";

    // render features
    const initialVariable = features.getInitialVariable();
    features.viewVariable = initialVariable.name;
    if (initialVariable.level) {
        features.viewVariableLevel = initialVariable.level;
    }
    features.render();

    // draw plot once svg exists
    onMount(() => {
        plot.init(features.view);
        plot.drawPlot(false);
    });

    let referenceLevel = $derived(
        features.getVariablesWithName(features.viewVariable)[0].reference,
    );
</script>

<div class="grid grid-rows-subgrid row-span-2">
    <div id="barplot-svg-container" class="bg-white rounded overflow-scroll">
        {#if features.viewVariableLevel != ""}
            <h2 id="barplot-title" class="text-lg text-center mt-5 -mb-[60px]">
                Reference Level: {referenceLevel}
            </h2>
        {/if}
        <svg></svg>
    </div>
    <div id="sidebar" class="flex w-full min-w-0 gap-1">
        <BarplotControls />
        <BarplotFilters />
    </div>
</div>

<style>
    svg {
        min-width: 100%;
        overflow: visible;
    }
</style>
