<script lang="ts">
    let { children, title } = $props();
</script>

<div class="w-full rounded bg-gray-50">
    <h3 class="font-bold bg-purple-100 rounded-t px-4 py-1">{title}</h3>
    <div class="px-4 py-2 max-h-64 overflow-auto">{@render children()}</div>
</div>
