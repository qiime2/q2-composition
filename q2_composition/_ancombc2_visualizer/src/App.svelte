<script lang="ts">
    import { tick } from "svelte";
    import Barplot from "./lib/Barplot.svelte";
    import Taxonomy from "./lib/Taxonomy.svelte";
    import { parseAllSlices } from "./util/parse";
    import features from "./util/features.svelte";
    import { parseTaxonomy } from "./util/taxonomy.svelte";

    const taxonomyPath = "taxonomy.tsv";
    const slicesPath = "slices";

    const fetchPromise = fetch(taxonomyPath);

    const taxonomyPromise = fetchPromise.then((response) => {
        if (response.ok) {
            return parseTaxonomy(taxonomyPath);
        } else {
            return Promise.resolve(null);
        }
    });

    let hideTaxonomy = $state(false);

    const featuresPromise = taxonomyPromise.then(async (rootTaxon) => {
        if (rootTaxon == null) {
            hideTaxonomy = true;
            await tick();

            return parseAllSlices(slicesPath, features, null);
        } else {
            features.rootTaxon = rootTaxon.data;
            return parseAllSlices(slicesPath, features, rootTaxon.data);
        }
    });
</script>

<div
    class="grid lg:grid-rows-[1fr_auto] lg:h-dvh gap-1 p-1 bg-gray-300"
    class:lg:grid-cols-1={hideTaxonomy}
    class:max-w-4xl={hideTaxonomy}
    class:lg:mx-auto={hideTaxonomy}
    class:lg:grid-cols-[.45fr_.55fr]={!hideTaxonomy}
>
    {#await featuresPromise}
        <p>Parsing slices...</p>
    {:then features}
        <Barplot />
    {:catch error}
        <p>An error occurred: {error.message}</p>
    {/await}

    {#await taxonomyPromise}
        <p>Parsing taxonomy...</p>
    {:then rootTaxon}
        {#if rootTaxon}
            <Taxonomy {rootTaxon} />
        {/if}
    {:catch error}
        <p>An error occurred: {error.message}</p>
    {/await}
</div>
