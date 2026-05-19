<script lang="ts">
    import { onMount } from "svelte";
    import SelectedTaxon from "./SelectedTaxon.svelte";
    import TaxonomyFilter from "./TaxonomyFilter.svelte";
    import TaxonomyFilterList from "./TaxonomyFilterList.svelte";
    import { TaxonomyPlot, TaxonomyFilters } from "../util/taxonomy.svelte";

    const { rootTaxon } = $props();

    let taxonomyPlot: TaxonomyPlot | null = $state(null);
    let taxonomyFilters: TaxonomyFilters | null = $state(null);

    onMount(() => {
        taxonomyPlot = new TaxonomyPlot(rootTaxon);
        taxonomyPlot.render(rootTaxon);

        taxonomyFilters = new TaxonomyFilters(taxonomyPlot.root.data);
    });
</script>

<div id="container" class='grid grid-rows-subgrid row-span-2'>
    <div id="taxonomy-svg-container" class='grid grid-rows-subgrid bg-white rounded'>
        <svg></svg>
    </div>
    <div id="sidebar" class='grid grid-cols-3 gap-1'>
        <SelectedTaxon {taxonomyPlot} {taxonomyFilters} />
        <TaxonomyFilter {taxonomyPlot} {taxonomyFilters} />
        <TaxonomyFilterList {taxonomyPlot} {taxonomyFilters} />
    </div>
</div>

<style>
    svg {
        width: 100%;
        height: 100%;
    }
</style>
