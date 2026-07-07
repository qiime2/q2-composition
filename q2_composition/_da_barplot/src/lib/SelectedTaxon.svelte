<script lang="ts">
    import { slide } from "svelte/transition";
    import features from "../util/features.svelte";
    import plot from "../util/plot";
    import ControlContainer from "./ControlContainer.svelte";

    const { taxonomyPlot, taxonomyFilters } = $props();

    let filtered = $state(false);
    $effect(() => {
        taxonomyFilters?.filters;

        if (taxonomyPlot != null && taxonomyPlot.selectedTaxon != null) {
            filtered = taxonomyPlot.selectedTaxon.filtered;
        }
    });

    const name = $derived(
        taxonomyPlot.selectedTaxon ? taxonomyPlot.selectedTaxon.name : "",
    );
    const featureCount = $derived(
        taxonomyPlot.selectedTaxon?.getFeatureCount() ?? "",
    );
    const subtreeCount = $derived(
        taxonomyPlot.selectedTaxon?.getSubtreeFeatureCount() ?? "",
    );
    const featurePercent = $derived(
        Math.round(
            (featureCount / taxonomyPlot.selectedTaxon?.getTreeFeatureCount()) *
                10_000,
        ) / 100,
    );
    const subtreePercent = $derived(
        Math.round(
            (subtreeCount / taxonomyPlot.selectedTaxon?.getTreeFeatureCount()) *
                10_000,
        ) / 100,
    );

    let searchString: string = $state("");
    let searchError: string = $state("");

    function handleSearch(event: KeyboardEvent) {
        if (event.key != "Enter") return;
        if (searchString == "") return;

        searchString = searchString.trim();

        const matches = taxonomyPlot.root.data.findTaxa(searchString);

        if (matches.length == 0) {
            searchError = "No matches found!";
            return;
        }
        if (matches.length > 10) {
            searchError = "More than 10 matches! Try a more specific search.";
            return;
        }

        searchError = "";

        taxonomyPlot.selectedTaxon = matches[0];

        for (let match of matches) {
            match.searchMatch = true;
        }
        taxonomyPlot.render(taxonomyPlot.root);
    }

    function clearSearch() {
        searchString = "";
        searchError = "";
        taxonomyPlot.root.data.clearSearchMatches();
        taxonomyPlot.render(taxonomyPlot.root);
    }

    function handleFilter() {
        if (filtered) {
            taxonomyFilters.addIndividualFilter(taxonomyPlot.selectedTaxon);
        } else {
            taxonomyFilters.removeIndividualFilter(taxonomyPlot.selectedTaxon);
        }

        taxonomyFilters.applyFilters();
        taxonomyPlot.render(taxonomyPlot.root);

        features.render();
        plot.updateData(features.view);
    }
</script>

<ControlContainer title="Taxon Info:">
    <div class="flex justify-between mb-2 gap-2">
        <input
            type="text"
            name="taxon"
            class="bg-white border-gray-300 border rounded px-2 py-1 w-full"
            placeholder="Search..."
            bind:value={searchString}
            onkeydown={handleSearch}
        />
        <button
            onclick={clearSearch}
            class="bg-purple-400 px-4 py-0.5 rounded text-white">Clear</button
        >
    </div>
    {#if searchError != ""}
        <div id="search-error" transition:slide>
            <p>{searchError}</p>
        </div>
    {/if}
    <div class="toggle">
        <input
            type="checkbox"
            id="taxon-filter"
            name="taxon-filter"
            bind:checked={filtered}
            onchange={handleFilter}
        />
        <label for="taxon-filter">Filter taxon</label>
    </div>
    <hr class="my-2 border-gray-400" />
    {#if taxonomyPlot?.selectedTaxon == undefined}
        {#if searchError == ""}
            <p>Click on a taxon name for more information.</p>
        {/if}
    {:else}
        <p><b>Name:</b> {name}</p>
        <p>
            <b>Features classified to taxon:</b>
            {featureCount} ({featurePercent}%)
        </p>
        <p>
            <b>Features classified to subtree:</b>
            {subtreeCount} ({subtreePercent}%)
        </p>
    {/if}
</ControlContainer>

<style>
    #search-error {
        background-color: #fca9a9;
        border-radius: 5px;
        padding: 3px;
        max-width: 90%;
    }
</style>
