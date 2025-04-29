import * as d3 from "d3";
import { type ViewRecord } from "./features.svelte";

type PlotDimensions = {
    svgWidth: number;
    svgHeight: number;
    margin: number;
    plotWidth: number;
    plotHeight: number;
    barHeight: number;
    barPadding: number;
};

export class DivergingBarplot {
    data: ViewRecord[] = [];
    dimensions: PlotDimensions = {};
    xScale: d3.ScaleLinear<number, number> = d3.scaleLinear();
    yScale: d3.ScaleBand<any> = d3.scaleBand();
    xAxis: d3.Selection<any, any, any, any> = d3.selection();
    yAxis: d3.Selection<any, any, any, any> = d3.selection();

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

    /**
     */
    createDimensions(): PlotDimensions {
        const svg = d3.select("svg");
        let svgWidth: number;
        if (!svg.empty()) {
            svgWidth = svg.node()!.getBoundingClientRect().width;
        } else {
            throw new Error(`Svg element not found.`);
        }

        const numFeatures = this.data.length;

        const barHeight = 20;
        const barPadding = 1.25;

        const plotHeight = numFeatures * barHeight * barPadding;

        const margin = 120;
        const plotWidth = svgWidth - 2 * margin;

        return {
            svgWidth: svgWidth,
            svgHeight: plotHeight + 2 * margin,
            margin,
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
    updatePlotHeight() {
        this.dimensions.plotHeight =
            this.data.length *
            this.dimensions.barHeight *
            this.dimensions.barPadding;
        this.dimensions.svgHeight =
            this.dimensions.plotHeight + 2 * this.dimensions.margin;
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
        // get min and max lfc values
        let [min, max] = d3.extent(this.data.map((f) => f.lfc));

        if (!min || !max) {
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
            this.dimensions.margin,
            this.dimensions.margin + this.dimensions.plotWidth,
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
            .select("svg")
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
            .attr("x", "50%")
            .attr("y", 60);

        return axis;
    }

    /**
     */
    createYAxis(): d3.Selection<any, any, any, any> {
        let axis = d3
            .select("svg")
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
        d3.select("svg")
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

    /**
     */
    drawPlot(transition: boolean) {
        const sizeSvg = () => {
            let svg = d3
                .select("svg")
                .attr("width", this.dimensions.svgWidth)
                .attr("height", this.dimensions.svgHeight);
        };

        if (!transition) {
            sizeSvg();
        }

        if (transition) {
            // update plot height
            this.updatePlotHeight();

            // update scales
            const xDomain = this.getXDomain();
            const xRange = this.getXRange();
            const yDomain = this.getYDomain();
            const yRange = this.getYRange();

            this.xScale.domain(xDomain).range(xRange);
            this.yScale.domain(yDomain).range(yRange);

            // resize svg
            sizeSvg();

            // transition axes
            this.xAxis
                .transition()
                .duration(500)
                .attr("transform", this.getXAxisTranslation())
                .call(d3.axisBottom(this.xScale));

            this.xAxis.selectAll("text").attr("font-size", "14px");
            this.xAxis.select("#xaxis-label").attr("font-size", "18px");

            this.yAxis
                .transition()
                .duration(500)
                .attr("transform", this.getYAxisTranslation())
                .call(
                    d3
                        .axisLeft(this.yScale)
                        .tickSize(0)
                        .tickFormat("" as any),
                );
        }

        // draw bars
        let barSelection = d3
            .select("svg")
            .selectAll("rect")
            .data(this.data)
            .join("rect");

        const drawBars = (selection: any) => {
            selection
                .attr("x", (d) =>
                    d.lfc > 0 ? this.xScale(0) : this.xScale(d.lfc),
                )
                .attr("y", (d, i) => this.yScale(String(i)))
                .attr("width", (d) =>
                    Math.abs(this.xScale(d.lfc) - this.xScale(0)),
                )
                .attr("height", this.dimensions.barHeight)
                .attr("fill", (d) => (d.lfc > 0 ? "green" : "red"));
        };

        if (transition) {
            barSelection.transition().duration(400).call(drawBars.bind(this));
        } else {
            barSelection.call(drawBars.bind(this));
        }

        // draw error bars
        let errorBarSelection = d3
            .select("svg")
            .selectAll(".error-bar")
            .data(this.data)
            .join("path")
            .attr("class", "error-bar");

        const drawErrorBars = (selection: any) => {
            selection
                .attr("d", (d, i) =>
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
        let labelSelection = d3
            .select("svg")
            .selectAll(".label")
            .data(this.data)
            .join("text")
            .attr("class", "label");

        const drawLabels = (selection: any) => {
            selection
                .text((d) =>
                    d.shortClassification ? d.shortClassification : d.featureId,
                )
                .attr("x", this.xScale(0))
                .attr(
                    "y",
                    (d, i) =>
                        this.yScale(String(i)) + this.yScale.bandwidth() / 2,
                )
                .attr("text-anchor", (d) => (d.lfc > 0 ? "end" : "start"))
                .attr("dx", (d) => (d.lfc > 0 ? -8 : 8))
                .attr("font-size", "12px")
                .attr("fill", "#474747");
        };

        if (transition) {
            labelSelection
                .transition()
                .duration(400)
                .call(drawLabels.bind(this));
        } else {
            labelSelection.call(drawLabels.bind(this));
        }

        // attach hover event listeners
        this.addHoverHandlers();
    }

    /**
     */
    hidePlot() {
        // gray-out the plot
        d3.select("svg")
            .append("rect")
            .attr("class", "hider")
            .attr("width", this.dimensions.svgWidth)
            .attr("height", this.dimensions.svgHeight)
            .attr("fill", "gray")
            .attr("opacity", 0.9);

        // add error message
        d3.select("svg")
            .append("rect")
            .attr("class", "hider-text-box")
            .attr("x", 0.3 * this.dimensions.svgWidth)
            .attr("y", 0.4 * this.dimensions.svgHeight)
            .attr("width", 0.4 * this.dimensions.svgWidth)
            .attr("height", 0.2 * this.dimensions.svgHeight)
            .attr("fill", "white");

        d3.select("svg")
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
        d3.selectAll(".hider, .hider-text, .hider-text-box").remove();
    }
}

const plot = new DivergingBarplot();
export default plot;
