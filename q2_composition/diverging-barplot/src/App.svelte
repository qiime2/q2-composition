<script lang="ts">
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

    const featuresPromise = taxonomyPromise.then((rootTaxon) => {
        if (rootTaxon == null) {
            return parseAllSlices(slicesPath, features, null);
        } else {
            features.rootTaxon = rootTaxon.data;
            return parseAllSlices(slicesPath, features, rootTaxon.data);
        }
    });
</script>

<div class="grid lg:grid-cols-[.45fr_.55fr] lg:grid-rows-[1fr_auto] lg:h-dvh gap-1 p-1 bg-gray-300">
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
        <Taxonomy {rootTaxon} />
    {:catch error}
        <p>An error occurred: {error.message}</p>
    {/await}
</div>