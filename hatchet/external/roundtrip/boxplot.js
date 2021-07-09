//d3.v4
(function (element) {
    const [path, data_string] = argList;
    requirejs.config({
        baseUrl: path,
         paths: {
            d3src: 'https://d3js.org',
            lib: 'lib',
        },
        map: {
            '*': {
                'd3': 'd3src/d3.v6.min',
                'd3-utils': 'lib/d3_utils',
            }
        }
    });
    require(['d3', 'd3-utils'], (d3, d3_utils) => {
        const data = JSON.parse(data_string.replace(/'/g, '"'));

        /**
         * Sort the callsite ordering based on the attribute.
         *
         * @param {Array} callsites - Callsites as a list.
         * @param {Stirng} metric - Metric (e.g., time or time (inc))
         * @param {String} attribute - Attribute to sort by.
         */
        const sortByAttribute = (callsites, metric, attribute, boxplot_type) => {
            let items = Object.keys(callsites).map(function (key) {
                return [key, callsites[key][boxplot_type]];
            });

            items = items.sort( (first, second) => {
                return second[1][metric][attribute] - first[1][metric][attribute];
            });

            return items.reduce(function (map, obj) {
                map[obj[0]] = obj[1][metric];
                return map;
            }, {});
        }

        const callsites = Object.keys(data);

        // Selection dropdown for metrics.
        const metrics = Object.keys(data[callsites[0]]["tgt"]);
        const selected_metric = metrics[0]
        d3_utils.selectionDropDown(element, metrics, "metricSelect");

        // Selection dropdown for attributes.
        const attributes = ["min", "max", "mean", "var", "imb", "kurt", "skew"];
        const selected_attribute = "mean";
        d3_utils.selectionDropDown(element, attributes, "attributeSelect");

        const sort_callsites = sortByAttribute(data, selected_metric, selected_attribute, "tgt");

        const margin = {top: 20, right: 20, bottom: 0, left: 20},
                containerHeight = 100 * Object.keys(sort_callsites).length,
                width = element.clientWidth - margin.right - margin.left,
                height = containerHeight - margin.top - margin.bottom;

        const svgArea = d3_utils.prepareSvgArea(width, height, margin);
        const svg = d3_utils.prepareSvg(element, svgArea);
        
        let idx = 0;
        for (let [callsite, d] of Object.entries(sort_callsites)) {
            const stats = { 
                "min": d3_utils.formatRuntime(d.min),
                "max": d3_utils.formatRuntime(d.max),
                "mean": d3_utils.formatRuntime(d.mean),
                "var": d3_utils.formatRuntime(d.var),
                "imb": d3_utils.formatRuntime(d.imb),
                "kurt": d3_utils.formatRuntime(d.kurt),
                "skew": d3_utils.formatRuntime(d.skew),
            };
            
            const boxWidth = 0.6 * width;
            const xScale = d3.scaleLinear()
                .domain([d.min, d.max])
                .range([0.05 * boxWidth, boxWidth - 0.05 * boxWidth]);

            const gId = "box-" + idx;
            const gYOffset = 200;
            const g = svg.append("g")
                .attr("id", gId)
                .attr("width", boxWidth)
                .attr("transform", "translate(0, " + gYOffset * idx  + ")");
            d3_utils.drawText(element, gId, "callsite: " + callsite, 10, 0);

            let statIdx = 1;
            for( let [stat, val] of Object.entries(stats)) {
                d3_utils.drawText(element, gId, `${stat}:  ${val}`, 1.1 * boxWidth, 15, statIdx);
                statIdx += 1;
            }

            // const tooltip = element;

            // const mouseover = (data) => tooltip.render(data);
            // const mouseout = (data) => tooltip.clear();
            // const click = (data) => tooltip.render(data);

            const boxHeight = 80;
            const boxYOffset = 30;
            const fillColor = "#d9d9d9";
            const strokeColor = "#202020";
            const strokeWidth = 1;

            // Centerline
            d3_utils.drawLine(g, xScale(d.q[0]), boxYOffset + boxHeight/2, xScale(d.q[4]), boxYOffset + boxHeight/2, strokeColor);

            // Box
            const box = d3_utils.drawRect(g, {
                "class": "rect",      
                "x": xScale(d.q[1]),
                "y": boxYOffset,
                "height": boxHeight,
                "fill": fillColor,
                "width": xScale(d.q[3]) - xScale(d.q[1]),
                "stroke": strokeColor,
                "stroke-width": strokeWidth
            });

            // Markers
            d3_utils.drawLine(g, xScale(d.q[0]), boxYOffset, xScale(d.q[0]), boxYOffset + boxHeight, strokeColor);
            d3_utils.drawLine(g, xScale(d.q[4]), boxYOffset, xScale(d.q[4]), boxYOffset + boxHeight, strokeColor);

            // Outliers
            const outlierRadius = 4; 
            let outliers = []
            for (let idx = 0; idx < d.outliers["values"].length; idx += 1) {
                outliers.push({
                    x: xScale(d.outliers["values"][idx]),
					value: d.outliers["values"][idx],
					rank: d.outliers["ranks"][idx],
					// dataset: d.dataset
                })
            }
            d3_utils.drawCircle(g, outliers, outlierRadius, boxYOffset, fillColor);

            idx += 1
        }
    });
})(element);