import { tsv } from "d3-fetch";
import * as d3 from "d3";

type PlotDimensions = {
    margin: number;
    nodeWidth: number;
    nodeHeight: number;
    boxHeight: number;
    boxWidth: number;
};

export class TaxonomyPlot {
    dimensions: PlotDimensions;
    root: d3.HierarchyNode<TaxonomyNode>;
    treeLayout: d3.TreeLayout<any>;
    link: d3.Link<any, any, any>;

    selectedTaxon: TaxonomyNode | null = $state(null);
    hideFiltered: boolean = false;

    constructor(root: d3.HierarchyNode<TaxonomyNode>) {
        this.root = root;
        this.initTree(this.root);

        this.dimensions = this.getDimensions();
        this.treeLayout = this.createTreeLayout();
        this.link = this.createLinkGenerator();

        this.initSvg();
    }

    initTree(root: d3.HierarchyNode<TaxonomyNode>) {
        root.descendants().forEach((node, i) => {
            node._children = node.children;
            node.id = i;
            node.children = null;
            node.expand = false;
            node.keep = false;
            node.match = false;
        });
    }

    getSvgDimensions() {
        const svg = d3.select("#taxonomy-svg-container svg");

        if (svg.empty()) {
            throw new Error("No svg element found.");
        }

        const svgRect = (svg.node() as any).getBoundingClientRect();

        return { width: svgRect.width, height: svgRect.height };
    }

    getDimensions() {
        const margin = 25;

        const { width: svgWidth, height: svgHeight } = this.getSvgDimensions();

        const taxonomyDepth = this.root.height;
        const nodeWidth = 225;
        const nodeHeight = 30;

        const dimensions: PlotDimensions = {
            margin: margin,
            nodeHeight: nodeHeight,
            nodeWidth: nodeWidth,
            boxWidth: 0.8 * nodeWidth,
            boxHeight: 0.8 * nodeHeight,
        };

        return dimensions;
    }

    createTreeLayout(): d3.TreeLayout<any> {
        const treeLayout = d3
            .tree()
            .nodeSize([this.dimensions.nodeHeight, this.dimensions.nodeWidth]);

        return treeLayout;
    }

    createLinkGenerator(): d3.Link<any, any, any> {
        return d3
            .linkHorizontal()
            .x((d) => d.y)
            .y((d) => d.x);
    }

    initSvg() {
        const svg = d3.select("#taxonomy-svg-container svg");

        // create groups for nodes and links
        const zoomContainer = svg.append("g");
        zoomContainer.append("g").attr("class", "link-group");
        zoomContainer.append("g").attr("class", "node-group");

        // set svg view box
        const { width: svgWidth, height: svgHeight } = this.getSvgDimensions();

        svg.attr("viewBox", [
            -this.dimensions.margin,
            -svgHeight / 2,
            svgWidth,
            svgHeight,
        ]);

        // make svg zoomable & pannable
        const zoom = d3
            .zoom()
            .scaleExtent([0.4, 2])
            .on("zoom", (event) => {
                zoomContainer.attr("transform", event.transform);
            });

        svg.call(zoom).on("dblclick.zoom", null);
    }

    addSelectHandlers() {
        d3.selectAll(".taxonomy-node").on("click", (event, d) => {
            this.selectedTaxon = d.data;
        });
    }

    addExpandHandlers() {
        d3.selectAll(".expand-button").on("click", (event, d) => {
            d.expand = !d.expand;
            this.render(d);

            event.stopPropagation();
        });
    }

    addKeepHandlers() {
        d3.selectAll(".keep-button").on("click", (event, d) => {
            d.keep = !d.keep;

            const fillColor = d.keep ? "orange" : "lightgray";
            d3.select(event.currentTarget)
                .select("rect")
                .attr("fill", fillColor);

            this.render(d);

            event.stopPropagation();
        });
    }

    drawButton(
        selection: d3.Selection<any, any, any, any>,
        type: "expand" | "keep",
    ) {
        let xTranslation;
        let className;
        let letter;
        if (type == "expand") {
            xTranslation = this.dimensions.boxWidth - this.dimensions.boxHeight;
            className = "expand-button";
            letter = "E";
        } else if (type == "keep") {
            xTranslation =
                this.dimensions.boxWidth - 2 * this.dimensions.boxHeight;
            className = "keep-button";
            letter = "K";
        } else {
            throw new Error("Unrecognized button type.");
        }

        const button = selection
            .append("g")
            .attr("class", className)
            .attr("transform", `translate(${xTranslation}, 2)`);

        button
            .append("rect")
            .attr("width", this.dimensions.boxHeight - 4)
            .attr("height", this.dimensions.boxHeight - 4)
            .attr("fill", "lightgray");

        if (type == "keep") {
            button
                .selectAll("rect")
                .attr("fill", (d) => (d.keep ? "orange" : "lightgray"));
        }

        button
            .append("text")
            .text(letter)
            .attr("x", this.dimensions.boxHeight / 2 - 2)
            .attr("y", this.dimensions.boxHeight / 2 - 2)
            .attr("dominant-baseline", "middle")
            .attr("text-anchor", "middle")
            .attr("font-size", 14)
            .attr("dy", 2);
    }

    drawNodes(
        nodes: d3.HierarchyNode<TaxonomyNode>[],
        source: d3.HierarchyNode<TaxonomyNode>,
    ) {
        const updateSelection = d3
            .select(".node-group")
            .selectAll(".taxonomy-node")
            .data(nodes, (d) => d.id);

        // create entering node groups
        const enterSelection = updateSelection
            .enter()
            .append("g")
            .attr("class", "taxonomy-node")
            .attr("cursor", "pointer")
            .attr("transform", (d) => `translate(${source.y0}, ${source.x0})`)
            .attr("stroke-opacity", 1)
            .attr("fill-opacity", 1);

        // taxon names
        enterSelection
            .append("text")
            .text((d) => {
                if (d.data.name.length > 18) {
                    return d.data.name.slice(0, 15) + "...";
                }
                return d.data.name;
            })
            .attr("dx", 10)
            .attr("y", this.dimensions.boxHeight / 2)
            .attr("dominant-baseline", "middle")
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", 5)
            .attr("stroke", "white")
            .attr("paint-order", "stroke")
            .attr("font-weight", "bold")
            .attr("font-size", 13);

        // draw taxon boxes
        enterSelection
            .append("rect")
            .attr("class", "taxon-box")
            .attr("height", this.dimensions.boxHeight)
            .attr("width", this.dimensions.boxWidth)
            .attr("fill", (d) => {
                if (d.data.searchMatch) return "green";
                if (d.data.filtered) return "red";
                return "white";
            })
            .attr("stroke", "gray")
            .attr("stroke-width", 2)
            .attr("rx", 2)
            .attr("ry", 2)
            .attr("stroke-opacity", 1)
            .attr("fill-opacity", (d) => {
                if (d.data.searchMatch || d.data.filtered) {
                    return 0.2;
                }
                return 0;
            });

        // left circle
        enterSelection
            .append("circle")
            .attr("cx", 0)
            .attr("cy", this.dimensions.boxHeight / 2)
            .attr("r", 3)
            .attr("fill", "#555");

        // right circle; visible only if node has children
        enterSelection
            .append("circle")
            .attr("class", "right-circle")
            .attr("cx", this.dimensions.boxWidth)
            .attr("cy", this.dimensions.boxHeight / 2)
            .attr("r", (d) => {
                let kept = d._children;
                if (this.hideFiltered) {
                    kept = d._children?.filter((n) => !n.data.filtered);
                }
                if (kept && kept.length > 0) {
                    return 3;
                }
                return 0;
            })
            .attr("fill", "#555");

        updateSelection.selectAll(".right-circle").attr("r", (d) => {
            let kept = d._children;
            if (this.hideFiltered) {
                kept = d._children?.filter((n) => !n.data.filtered);
            }
            if (kept && kept.length > 0) {
                return 3;
            }
            return 0;
        });

        // color search matches
        updateSelection
            .selectAll(".taxon-box")
            .attr("fill", (d) => {
                if (d.data.searchMatch) return "green";
                if (d.data.filtered) return "red";
                return "white";
            })
            .attr("fill-opacity", (d) => {
                if (d.data.searchMatch || d.data.filtered) {
                    return 0.2;
                }
                return 0;
            });

        this.drawButton(enterSelection, "expand");
        this.drawButton(enterSelection, "keep");

        // add click event handlers
        this.addSelectHandlers();
        this.addExpandHandlers();
        this.addKeepHandlers();

        // color buttons
        updateSelection
            .merge(enterSelection)
            .selectAll(".expand-button")
            .select("rect")
            .attr("fill", (d) => {
                if (d.children && d.children.length == d._children.length) {
                    return "lightblue";
                } else {
                    return "lightgray";
                }
            });

        updateSelection
            .merge(enterSelection)
            .selectAll(".keep-button")
            .select("rect")
            .attr("fill", (d) => (d.keep ? "orange" : "lightgray"));

        // transition all nodes to their new positions
        updateSelection
            .merge(enterSelection)
            .transition()
            .duration(200)
            .attr("transform", (d) => `translate(${d.y}, ${d.x})`)
            .attr("fill-opacity", 1)
            .attr("stroke-opacity", 1);

        // transition exiting nodes to parents' new positions
        updateSelection
            .exit()
            .transition()
            .duration(200)
            .remove()
            .attr("transform", (d) => `translate(${source.y}, ${source.x})`)
            .attr("fill-opacity", 0)
            .attr("stroke-opacity", 0);
    }

    drawLinks(
        links: d3.HierarchyLink<TaxonomyNode>[],
        source: d3.HierarchyNode<TaxonomyNode>,
    ) {
        const updateSelection = d3
            .select(".link-group")
            .selectAll(".taxonomy-link")
            .data(links, (d) => d.target.id);

        // create entering link paths
        const enterSelection = updateSelection
            .enter()
            .append("path")
            .attr("class", "taxonomy-link")
            .attr("fill", "none")
            .attr("stroke", "#555")
            .attr("stroke-opacity", 0.5)
            .attr("stroke-width", 1.5)
            .attr("d", (d) => {
                const parentOld = { x: source.x0, y: source.y0 };
                return this.link({ source: parentOld, target: parentOld });
            });

        // transition all links to their new shapes
        updateSelection
            .merge(enterSelection)
            .transition()
            .duration(200)
            .attr("d", (d) => {
                const sourceX = d.source.x! + this.dimensions.boxHeight / 2;
                const targetX = d.target.x! + this.dimensions.boxHeight / 2;

                const sourceY = d.source.y! + this.dimensions.boxWidth;
                const targetY = d.target.y!;

                const positions = {
                    source: { x: sourceX, y: sourceY },
                    target: { x: targetX, y: targetY },
                };
                return this.link(positions);
            });

        // transition exiting links to parent's new position
        updateSelection
            .exit()
            .transition()
            .duration(200)
            .remove()
            .attr("d", (d) => {
                const parentNew = { x: source.x, y: source.y };
                return this.link({ source: parentNew, target: parentNew });
            });
    }

    assignChildren(node: d3.HierarchyNode<TaxonomyNode>): boolean {
        let keptDescendant = node.keep || node.data.searchMatch;

        if (this.hideFiltered && node.data.filtered) {
            return false;
        }

        // leaf
        if (!node._children) {
            return keptDescendant;
        }

        node.children = [];
        for (let child of node._children) {
            if (this.assignChildren(child)) {
                node.children.push(child);
                keptDescendant = true;
            }
        }

        if (node.expand) {
            node.children = node._children;
            if (this.hideFiltered) {
                node.children = node.children.filter((n) => !n.data.filtered);
            }
        }

        if (node.children!.length == 0) {
            node.children = undefined;
        }

        return keptDescendant;
    }

    render(source: d3.HierarchyNode<TaxonomyNode>) {
        // update visible children
        this.assignChildren(this.root);

        // gather all expanded nodes and links
        const nodes = this.root.descendants().reverse();
        const links = this.root.links();

        // assign coordinates to nodes
        this.treeLayout(this.root);

        // const transition = this.resizeSvg();
        this.drawLinks(links, source);
        this.drawNodes(nodes, source);

        // store the current positions for the next render
        this.root.eachBefore((node) => {
            node.x0 = node.x;
            node.y0 = node.y;
        });
    }
}

export class TaxonomyNode {
    name: string;
    parent: TaxonomyNode | null;
    children: TaxonomyNode[];
    featureIDs: string[];
    hierarchyNode: d3.HierarchyNode<TaxonomyNode> | null;
    searchMatch: boolean = false;
    filtered: boolean = false;

    constructor(name: string, parent: TaxonomyNode | null) {
        this.name = name;
        this.parent = parent;
        this.children = [];
        this.featureIDs = [];
        this.hierarchyNode = null;
    }

    getChild(name: string): TaxonomyNode | null {
        let matchingChildren = this.children.filter((child) => {
            return child.name == name;
        });

        if (matchingChildren.length > 1) {
            throw new Error("More than one matching child found.");
        }
        if (matchingChildren.length == 0) {
            return null;
        }

        return matchingChildren[0];
    }

    getRoot(): TaxonomyNode {
        let currentNode: TaxonomyNode = this;
        while (currentNode.parent != null) {
            currentNode = currentNode.parent;
        }

        return currentNode;
    }

    getDescendants(): TaxonomyNode[] {
        const descendants: TaxonomyNode[] = [this];
        for (let child of this.children) {
            descendants.push(...child.getDescendants());
        }

        return descendants;
    }

    findTaxa(name: string): TaxonomyNode[] {
        const root = this.getRoot();
        const descendants = root.getDescendants();

        const matches = descendants.filter((descendant) => {
            const index = descendant.name
                .toLowerCase()
                .indexOf(name.toLowerCase());

            return index != -1 && !descendant.filtered;
        });

        return matches;
    }

    findTaxonById(id: string): TaxonomyNode | null {
        const descendants = this.getRoot().getDescendants();
        const matches = descendants.filter((descendant) => {
            return descendant.featureIDs.indexOf(id) != -1;
        });

        if (matches.length == 0) {
            return null;
        } else if (matches.length == 1) {
            return matches[0];
        } else {
            throw new Error(
                "More than one taxonomy node with the same feature ID.",
            );
        }
    }

    getAncestors(): TaxonomyNode[] {
        const ancestors = [];
        let currentNode: TaxonomyNode = this;
        while (currentNode.parent != null) {
            ancestors.push(currentNode);
            currentNode = currentNode.parent;
        }

        return ancestors;
    }

    getFullTaxonString(): string {
        const ancestorNames = this.getAncestors()
            .reverse()
            .map((a) => a.name);

        return ancestorNames.join(";");
    }

    /**
     * Gets the shortest taxonomy string that contains a non-anonymous level
     * label.
     *
     * Examples:
     * (...);f__family;g__genus;s__ => g__genus;s__
     * (...);o__order;f__family;g__;s__ => f__family;g__;s__
     * (...);g__genus;s__species => s__species
     */
    getNonAnonymousTaxonString(): string {
        if (this.parent == null) return "root";

        const ancestorNames = this.getAncestors()
            .reverse()
            .map((a) => a.name);

        let lastNonAnonymousIndex = null;
        for (const [index, ancestorName] of ancestorNames.entries()) {
            if (ancestorName.slice(-2) != "__") {
                lastNonAnonymousIndex = index;
            }
        }
        if (lastNonAnonymousIndex == null) lastNonAnonymousIndex = 0;

        return ancestorNames.slice(lastNonAnonymousIndex).join(";");
    }

    getFeatureCount(): number {
        return this.featureIDs.length;
    }

    getSubtreeFeatureCount(): number {
        let subtreeCount = this.getFeatureCount();

        for (let child of this.children) {
            subtreeCount += child.getSubtreeFeatureCount();
        }

        return subtreeCount;
    }

    getTreeFeatureCount(): number {
        return this.getRoot().getSubtreeFeatureCount();
    }

    clearSearchMatches() {
        this.getRoot()
            .getDescendants()
            .forEach((n) => {
                n.searchMatch = false;
            });
    }
}

export class TaxonomyFilters {
    filters: ((node: TaxonomyNode) => boolean)[] = $state([]);
    taxonomyRoot: TaxonomyNode;

    constructor(taxonomyRoot: TaxonomyNode) {
        this.filters = [];
        this.taxonomyRoot = taxonomyRoot;
    }

    addFeatureCountFilter(featureCount: number) {
        const filter = (node: TaxonomyNode) => {
            return node.getSubtreeFeatureCount() < featureCount;
        };

        filter.type = "feature-count";
        filter.value = featureCount;

        this.filters = [...this.filters, filter];
    }

    removeFeatureCountFilter(value: number) {
        this.filters = this.filters.filter((f) => {
            if (f.type != "feature-count") return true;

            return !(f.value == value);
        });
    }

    addIndividualFilter(filterNode: TaxonomyNode) {
        const filter = (node: TaxonomyNode) => {
            return node == filterNode;
        };

        filter.type = "individual";
        filter.node = filterNode;

        this.filters = [...this.filters, filter];
    }

    removeIndividualFilter(filterNode: TaxonomyNode) {
        this.filters = this.filters.filter((f) => {
            if (f.type != "individual") return true;

            return !(f.node == filterNode);
        });
    }

    applyFilters() {
        const nodes = this.taxonomyRoot.getDescendants();

        nodes.forEach((node) => (node.filtered = false));

        nodes.forEach((node) => {
            for (let filter of this.filters) {
                node.filtered = filter(node);
                if (node.filtered) return;
            }
        });
    }
}

/**
 * Parses a taxonomy.tsv file into a d3.hierarchy.
 */
export async function parseTaxonomy(
    taxonomyFilepath: string,
): Promise<d3.HierarchyNode<TaxonomyNode>> {
    const taxonomyRecords = await tsv(taxonomyFilepath);

    const root = new TaxonomyNode("root", null);

    for (let taxonRecord of taxonomyRecords) {
        const levelNames = taxonRecord["Taxon"]
            .split(";")
            .filter((n) => n != "");
        const featureId = taxonRecord["Feature ID"];

        let parentNode = root;
        for (let [levelIndex, levelName] of levelNames.entries()) {
            const currentNode = new TaxonomyNode(levelName, parentNode);

            // if this is the last level then it has a feature ID
            if (levelIndex == levelNames.length - 1) {
                currentNode.featureIDs.push(featureId);
            }

            // merge with matching child if one exists
            const matchingChild = parentNode.getChild(levelName);
            if (matchingChild) {
                matchingChild.featureIDs.push(...currentNode.featureIDs);
                parentNode = matchingChild;
            } else {
                parentNode.children.push(currentNode);
                parentNode = currentNode;
            }
        }
    }

    const hierarchyRoot = d3.hierarchy(root);

    // create back references from TaxonomyNodes to d3 nodes
    hierarchyRoot.eachBefore((node) => {
        node.data.hierarchyNode = node;
    });

    return hierarchyRoot;
}
