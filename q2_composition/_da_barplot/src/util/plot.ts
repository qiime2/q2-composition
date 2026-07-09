import * as d3 from "d3";
import { type ViewRecord } from "./features.svelte";

const DEFAULT_MARGIN = 120;
const LABEL_ELLIPSIS = "…";
const LABEL_FONT_SIZE = 12;
const LABEL_OFFSET = 8;
const LABEL_OVERFLOW_PADDING = 4;

type PlotDimensions = {
    svgWidth: number;
    svgHeight: number;
    margin: number;
    leftMargin: number;
    rightMargin: number;
    plotWidth: number;
    plotHeight: number;
    barHeight: number;
    barPadding: number;
};

export class DivergingBarplot {
    data: ViewRecord[] = [];
    dimensions = {} as PlotDimensions;
    xScale: d3.ScaleLinear<number, number> = d3.scaleLinear();
    yScale: d3.ScaleBand<any> = d3.scaleBand();
    xAxis: d3.Selection<any, any, any, any> = d3.selection();
    yAxis: d3.Selection<any, any, any, any> = d3.selection();
    showFullLabels = false;

    /**
     */
    init(data: ViewRecord[]) {
        this.data = data;
        this.dimensions = this.createDimensions();
        this.xScale = this.createXScale();
        this.yScale = this.createYScale();
        this.xAxis = this.createXAxis();
        this.yAxis = this.createYAxis();
    }

    getSvg(): d3.Selection<SVGSVGElement, unknown, HTMLElement, any> {
        const svg = d3.select<SVGSVGElement, unknown>(
            "#barplot-svg-container svg",
        );
        if (svg.empty()) {
            throw new Error(`Svg element not found.`);
        }

        return svg;
    }

    getContainerWidth(): number {
        const containerWidth = document
            .querySelector("#barplot-svg-container")
            ?.getBoundingClientRect().width;

        return (
            containerWidth || this.getSvg().node()!.getBoundingClientRect().width
        );
    }

    downloadSVG() {
        const svgElem = this.getSvg().node()!;

        svgElem.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        const svgData = new XMLSerializer().serializeToString(svgElem as Node);

        const blob = new Blob([svgData], {
            type: "image/svg+xml;charset=utf-8",
        });
        const url = URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "da-barplot.svg";
        a.click();

        URL.revokeObjectURL(url);
    }

    setShowFullLabels(showFullLabels: boolean) {
        this.showFullLabels = showFullLabels;

        if (this.data.length > 0) {
            this.drawPlot(false);
        }
    }

    /**
     */
    createDimensions(): PlotDimensions {
        const containerWidth = this.getContainerWidth();
        const numFeatures = this.data.length;

        const margin = this.dimensions.margin ?? DEFAULT_MARGIN;
        const barHeight = this.dimensions.barHeight ?? 20;
        const barPadding = this.dimensions.barPadding ?? 1.25;

        const plotHeight = numFeatures * barHeight * barPadding;
        const plotWidth = Math.max(containerWidth - 2 * margin, 1);
        const svgWidth = plotWidth + 2 * margin;

        return {
            svgWidth: svgWidth,
            svgHeight: plotHeight + 2 * margin,
            margin,
            leftMargin: margin,
            rightMargin: margin,
            plotWidth,
            plotHeight,
            barHeight,
            barPadding,
        };
    }

    /**
     * Updates the plotted data and redraws the plot if the data is non-empty,
     * otherwise hides the plot.
     */
    updateData(data: ViewRecord[]) {
        this.data = data;
        if (data.length > 0) {
            this.showPlot();
            this.drawPlot(true);
        } else {
            this.hidePlot();
        }
    }

    /**
     */
    increaseBarThickness() {
        this.dimensions.barHeight *= 1.1;
        this.drawPlot(true);
    }

    /**
     */
    decreaseBarThickness() {
        this.dimensions.barHeight *= 0.9;
        this.drawPlot(true);
    }

    /**
     */
    getXDomain(): [number, number] {
        // get min and max lfc +- se values
        const lfc_minus_se = this.data.map((f) => f.lfc - f.se);
        const lfc_plus_se = this.data.map((f) => f.lfc + f.se);

        let [min, max] = d3.extent([...lfc_minus_se, ...lfc_plus_se]);

        if (min == undefined || max == undefined) {
            throw new Error("Unable to find min/max of feature lfcs.");
        }

        // calculate scale range
        const scaleMargin = 0.25;
        if (min < 0) {
            min = (1 + scaleMargin) * min;
        } else {
            min = -scaleMargin * max;
        }

        if (max > 0) {
            max = (1 + scaleMargin) * max;
        } else {
            max = -scaleMargin * min;
        }

        return [min, max];
    }

    /**
     */
    getXRange() {
        return [
            this.dimensions.leftMargin,
            this.dimensions.leftMargin + this.dimensions.plotWidth,
        ];
    }

    /**
     */
    createXScale(): d3.ScaleLinear<number, number> {
        const domain = this.getXDomain();
        const range = this.getXRange();
        const scale = d3.scaleLinear().domain(domain).range(range);

        return scale;
    }

    /**
     */
    getYDomain(): string[] {
        return d3.range(0, this.data.length).map((i) => String(i));
    }

    /**
     */
    getYRange() {
        return [
            this.dimensions.margin,
            this.dimensions.margin + this.dimensions.plotHeight,
        ];
    }

    /**
     */
    createYScale(): d3.ScaleBand<any> {
        const domain = this.getYDomain();
        const range = this.getYRange();
        const scale = d3.scaleBand().domain(domain).range(range);

        return scale;
    }

    /**
     */
    getXAxisTranslation() {
        const translation = this.dimensions.margin + this.dimensions.plotHeight;
        return `translate(0, ${translation})`;
    }

    /**
     */
    getYAxisTranslation() {
        return `translate(${this.xScale(0)}, 0)`;
    }

    /**
     */
    createXAxis(): d3.Selection<any, any, any, any> {
        let axis = d3
            .select("#barplot-svg-container svg")
            .append("g")
            .attr("class", "x-axis")
            .attr("transform", this.getXAxisTranslation())
            .call(d3.axisBottom(this.xScale));

        axis.selectAll("text").attr("font-size", "14px");

        axis.append("text")
            .text("LFC (Log Fold Change)")
            .attr("fill", "black")
            .attr("font-size", "18px")
            .attr("id", "xaxis-label")
            .attr(
                "x",
                this.dimensions.leftMargin + this.dimensions.plotWidth / 2,
            )
            .attr("y", 60);

        return axis;
    }

    /**
     */
    createYAxis(): d3.Selection<any, any, any, any> {
        let axis = d3
            .select("#barplot-svg-container svg")
            .append("g")
            .attr("class", "y-axis")
            .attr("transform", this.getYAxisTranslation())
            .call(
                d3
                    .axisLeft(this.yScale)
                    .tickSize(0)
                    .tickFormat("" as any),
            );

        return axis;
    }

    /**
     */
    addHoverHandlers() {
        // event handlers
        const handleMouseover = (e: any, d: any) => {
            const tooltipData = [
                `feature ID: ${d.featureId}`,
                `classification: ${d.classification}`,
                `lfc: ${d.lfc}`,
                `se: ${d.se}`,
                `p-value: ${d.p}`,
                `q-value: ${d.q}`,
            ];

            d3.select(".tooltip")
                .style("display", "unset")
                .style("left", `${e.clientX + 25}px`)
                .style("top", `${e.clientY - 10}px`)
                .selectAll("p")
                .data(tooltipData)
                .join("p")
                .text((d, i) => tooltipData[i])
                .style("margin", "2px")
                .style("box-shadow", "none");

            d3.select(".tooltip")
                .transition()
                .duration(200)
                .style("opacity", 1);
        };

        const handleMousemove = (e: any, d: any) => {
            d3.select(".tooltip")
                .style("left", `${e.clientX + 25}px`)
                .style("top", `${e.clientY - 10}px`);
        };

        const handleMouseout = (e: any, d: any) => {
            d3.select(".tooltip")
                .transition()
                .duration(200)
                .style("opacity", 0)
                .end()
                .then(() => {
                    d3.select(".tooltip").style("display", "none");
                });
        };

        // create tooltip
        d3.select("body")
            .selectAll(".tooltip")
            .data([1])
            .join("div")
            .attr("class", "tooltip")
            .style("background-color", "#f0edef")
            .style("padding", "10px")
            .style("border-radius", "10px")
            .style("position", "absolute")
            .style("box-shadow", "1px 1px 2px gray")
            .style("display", "none")
            .style("opacity", 0);

        // register event handlers
        this.getSvg()
            .selectAll("rect, .error-bar")
            .on("mouseover", handleMouseover)
            .on("mousemove", handleMousemove)
            .on("mouseout", handleMouseout);
    }

    /**
     */
    drawErrorBar(path: d3.Path, d: ViewRecord, i: number): d3.Path {
        // calculate error bar layout
        const startX = this.xScale(d.lfc)!;
        const startY =
            this.yScale(i.toString())! + this.dimensions.barHeight / 2;

        const errorBarRight = this.xScale(d.lfc + d.se);
        const errorBarLeft = startX - (errorBarRight - startX);
        const errorBarTop = startY + 0.25 * this.dimensions.barHeight;
        const errorBarBottom = startY - 0.25 * this.dimensions.barHeight;

        // draw error bar
        path.moveTo(errorBarRight, errorBarTop);
        path.lineTo(errorBarRight, errorBarBottom);
        path.moveTo(errorBarRight, startY);
        path.lineTo(errorBarLeft, startY);
        path.moveTo(errorBarLeft, errorBarTop);
        path.lineTo(errorBarLeft, errorBarBottom);

        return path;
    }

    getLabelText(d: ViewRecord, full = this.showFullLabels): string {
        if (full && d.classification && d.classification != "N/A") {
            return `(${d.featureId.slice(0, 6)}) ${d.classification}`;
        }

        return d.shortClassification ? d.shortClassification : d.featureId;
    }

    getLabelX(d: ViewRecord): number {
        if (d.lfc > 0) {
            return Math.min(this.xScale(d.lfc - d.se), this.xScale(0));
        }

        return Math.max(this.xScale(d.lfc + d.se), this.xScale(0));
    }

    getLabelDx(d: ViewRecord): number {
        return d.lfc > 0 ? -LABEL_OFFSET : LABEL_OFFSET;
    }

    getAvailableLabelWidth(d: ViewRecord): number {
        const labelEdge = this.getLabelX(d) + this.getLabelDx(d);

        return d.lfc > 0
            ? Math.max(labelEdge - LABEL_OVERFLOW_PADDING, 0)
            : Math.max(
                  this.dimensions.svgWidth - labelEdge - LABEL_OVERFLOW_PADDING,
                  0,
              );
    }

    getTextLength(label: d3.Selection<any, any, any, any>): number {
        const node = label.node();
        if (!node) return 0;

        try {
            return node.getComputedTextLength();
        } catch {
            return (node.textContent ?? "").length * LABEL_FONT_SIZE * 0.6;
        }
    }

    /**
     * Returns the longest prefix of `fullLabel` that fits within `maxWidth`
     * after appending an ellipsis.
     *
     * SVG text does not support CSS-style single-line ellipsis, and character
     * count is not a reliable proxy for rendered width because glyphs have
     * different widths. This temporarily writes candidate strings into the
     * label element so their actual rendered length can be measured. The
     * binary search keeps the number of DOM measurements low while finding the
     * longest prefix that fits.
     */
    ellipsizeLabel(
        label: d3.Selection<any, any, any, any>,
        fullLabel: string,
        maxWidth: number,
    ): string {
        if (maxWidth <= 0) return "";

        label.text(fullLabel);
        if (this.getTextLength(label) <= maxWidth) {
            return fullLabel;
        }

        label.text(LABEL_ELLIPSIS);
        if (this.getTextLength(label) > maxWidth) {
            return "";
        }

        let low = 0;
        let high = fullLabel.length;

        while (low < high) {
            const midpoint = Math.ceil((low + high) / 2);
            label.text(`${fullLabel.slice(0, midpoint)}${LABEL_ELLIPSIS}`);

            if (this.getTextLength(label) <= maxWidth) {
                low = midpoint;
            } else {
                high = midpoint - 1;
            }
        }

        return `${fullLabel.slice(0, low)}${LABEL_ELLIPSIS}`;
    }

    getLabelWidths(): number[] {
        /**
         * Add a dummy element to measure rendered label widths. Keep it outside
         * the SVG viewbox to prevent flashing while labels are being measured.
         */
        const measurer = this.getSvg()
            .append("text")
            .attr("class", "label-measurer")
            .attr("font-size", `${LABEL_FONT_SIZE}px`)
            .attr("visibility", "hidden")
            .attr("x", -9999)
            .attr("y", -9999);

        const widths = this.data.map((d) => {
            measurer.text(this.getLabelText(d));
            return this.getTextLength(measurer);
        });

        measurer.remove();

        return widths;
    }

    expandDimensionsForFullLabels() {
        const labelWidths = this.getLabelWidths();
        let extraLeftMargin = 0;
        let extraRightMargin = 0;

        this.data.forEach((d, i) => {
            const labelWidth = labelWidths[i] + LABEL_OVERFLOW_PADDING;
            const labelEdge = this.getLabelX(d) + this.getLabelDx(d);

            if (d.lfc > 0) {
                extraLeftMargin = Math.max(
                    extraLeftMargin,
                    labelWidth - labelEdge,
                );
            } else {
                extraRightMargin = Math.max(
                    extraRightMargin,
                    labelEdge + labelWidth - this.dimensions.svgWidth,
                );
            }
        });

        this.dimensions.leftMargin += Math.max(extraLeftMargin, 0);
        this.dimensions.rightMargin += Math.max(extraRightMargin, 0);
        this.dimensions.svgWidth =
            this.dimensions.leftMargin +
            this.dimensions.plotWidth +
            this.dimensions.rightMargin;
    }

    /**
     */
    drawPlot(transition: boolean) {
        this.dimensions = this.createDimensions();

        // update scales
        const xDomain = this.getXDomain();
        const xRange = this.getXRange();
        const yDomain = this.getYDomain();
        const yRange = this.getYRange();

        this.xScale.domain(xDomain).range(xRange);
        this.yScale.domain(yDomain).range(yRange);

        if (this.showFullLabels) {
            this.expandDimensionsForFullLabels();
            this.xScale.range(this.getXRange());
        }

        this.getSvg()
            .attr("width", this.dimensions.svgWidth)
            .attr("height", this.dimensions.svgHeight)
            .style("width", `${this.dimensions.svgWidth}px`);

        const drawXAxis = (axis: any) => {
            axis.attr("transform", this.getXAxisTranslation()).call(
                d3.axisBottom(this.xScale),
            );
        };

        const drawYAxis = (axis: any) => {
            axis.attr("transform", this.getYAxisTranslation()).call(
                d3.axisLeft(this.yScale).tickSize(0).tickFormat("" as any),
            );
        };

        if (transition) {
            drawXAxis(this.xAxis.transition().duration(500));
            drawYAxis(this.yAxis.transition().duration(500));
        } else {
            drawXAxis(this.xAxis);
            drawYAxis(this.yAxis);
        }

        this.xAxis.selectAll("text").attr("font-size", "14px");
        this.xAxis
            .select("#xaxis-label")
            .attr("font-size", "18px")
            .attr(
                "x",
                this.dimensions.leftMargin + this.dimensions.plotWidth / 2,
            );

        // draw bars
        let barSelection = this.getSvg()
            .selectAll("rect")
            .data(this.data)
            .join("rect");

        const drawBars = (selection: any) => {
            selection
                .attr("x", (d: ViewRecord) =>
                    d.lfc > 0 ? this.xScale(0) : this.xScale(d.lfc),
                )
                .attr("y", (_d: ViewRecord, i: number) =>
                    this.yScale(String(i)),
                )
                .attr("width", (d: ViewRecord) =>
                    Math.abs(this.xScale(d.lfc) - this.xScale(0)),
                )
                .attr("height", this.dimensions.barHeight)
                .attr("fill", (d: ViewRecord) => (d.lfc > 0 ? "green" : "red"));
        };

        if (transition) {
            barSelection.transition().duration(400).call(drawBars.bind(this));
        } else {
            barSelection.call(drawBars.bind(this));
        }

        // draw error bars
        let errorBarSelection = this.getSvg()
            .selectAll(".error-bar")
            .data(this.data)
            .join("path")
            .attr("class", "error-bar");

        const drawErrorBars = (selection: any) => {
            selection
                .attr("d", (d: ViewRecord, i: number) =>
                    this.drawErrorBar(d3.path(), d, i).toString(),
                )
                .attr("stroke", "black")
                .attr("stroke-width", "2px");
        };

        if (transition) {
            errorBarSelection
                .transition()
                .duration(400)
                .call(drawErrorBars.bind(this));
        } else {
            errorBarSelection.call(drawErrorBars.bind(this));
        }

        // draw labels
        let labelSelection = this.getSvg()
            .selectAll(".label")
            .data(this.data)
            .join("text")
            .attr("class", "label");

        const drawLabels = (selection: any) => {
            selection
                .attr("x", (d: ViewRecord) => this.getLabelX(d))
                .attr(
                    "y",
                    (_d: ViewRecord, i: number) =>
                        (this.yScale(String(i)) ?? 0) +
                        this.yScale.bandwidth() / 2,
                )
                .attr("text-anchor", (d: ViewRecord) =>
                    d.lfc > 0 ? "end" : "start",
                )
                .attr("dx", (d: ViewRecord) => this.getLabelDx(d))
                .attr("dy", "1px")
                .attr("font-size", `${LABEL_FONT_SIZE}px`)
                .attr("fill", "#474747")
                .each((d: ViewRecord, i: number, nodes: SVGTextElement[]) => {
                    const label = d3.select(nodes[i] as SVGTextElement);
                    const labelText = this.getLabelText(d);
                    const fullLabelText = this.getLabelText(d, true);
                    const displayLabel = this.showFullLabels
                        ? labelText
                        : this.ellipsizeLabel(
                              label,
                              labelText,
                              this.getAvailableLabelWidth(d),
                          );

                    label.text(displayLabel);
                    label
                        .selectAll("title")
                        .data([fullLabelText])
                        .join("title")
                        .text(fullLabelText);
                });
        };

        labelSelection.call(drawLabels.bind(this));

        // attach hover event listeners
        this.addHoverHandlers();
    }

    /**
     */
    hidePlot() {
        // gray-out the plot
        this.getSvg()
            .append("rect")
            .attr("class", "hider")
            .attr("width", this.dimensions.svgWidth)
            .attr("height", this.dimensions.svgHeight)
            .attr("fill", "gray")
            .attr("opacity", 0.9);

        // add error message
        this.getSvg()
            .append("rect")
            .attr("class", "hider-text-box")
            .attr("x", 0.3 * this.dimensions.svgWidth)
            .attr("y", 0.4 * this.dimensions.svgHeight)
            .attr("width", 0.4 * this.dimensions.svgWidth)
            .attr("height", 0.2 * this.dimensions.svgHeight)
            .attr("fill", "white");

        this.getSvg()
            .append("text")
            .attr("class", "hider-text")
            .text("Oops! All features were filtered.")
            .attr("x", this.dimensions.svgWidth / 2)
            .attr("y", this.dimensions.svgHeight / 2)
            .attr("dominant-baseline", "middle")
            .attr("text-anchor", "middle")
            .attr("font-size", "18px");
    }

    /**
     */
    showPlot() {
        this.getSvg()
            .selectAll(".hider, .hider-text, .hider-text-box")
            .remove();
    }
}

const plot = new DivergingBarplot();
export default plot;
