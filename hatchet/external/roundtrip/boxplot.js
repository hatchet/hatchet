// TODO: Adopt MVC pattern for this module.
(function (element) {
    const BOXPLOT_TYPES = ["tgt", "bkg"];
    const [path, visType, variableString] = cleanInputs(argList);

    // Quit if visType is not boxplot. 
    if (visType !== "boxplot") {
        console.error("Incorrect visualization type passed.")
        return;
    }

    // Setup the requireJS config to get required libraries.
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

    // --------------------------------------------------------------------------------
    // Utility functions.
    // --------------------------------------------------------------------------------
    // TODO: Move this to a common utils folder.
    function cleanInputs(strings) {
        return strings.map( (_) =>  _.replace(/'/g, '"'));
    }

    /**
     * Sort the callsite ordering based on the attribute.
     *
     * @param {Array} callsites - Callsites as a list.
     * @param {Stirng} metric - Metric (e.g., time or time (inc)).
     * @param {String} attribute - Attribute to sort by.
     * @param {String} boxplotType -  boxplot type - for options, refer BOXPLOT_TYPES.
     */
    function sortByAttribute (callsites, metric, attribute, boxplotType) {
        if (!BOXPLOT_TYPES.includes(boxplotType)) {
            console.error("Invalid boxplot type. Use either 'tgt' or 'bkg'")
        }

        // Sanity check to see if the boxplotType is present in the callsites.
        let _is_empty = false;
        Object.keys(callsites).map(function (key) {
            if(callsites[key][boxplotType] === undefined) {
                _is_empty = true;
            }
        })

        let items = Object.keys(callsites).map(function (key) {
            return [key, callsites[key][boxplotType]];
        });
        
        if(!_is_empty) {
            items = items.sort( (first, second) => {
                return second[1][metric][attribute] - first[1][metric][attribute];
            });
        }      

        return items.reduce(function (map, obj) {
            if (obj[1] !== undefined) {
                map[obj[0]] = obj[1][metric];
            } else {
                map[obj[0]] = obj[1];
            }
            return map;
        }, {});
    }

    require(['d3', 'd3-utils'], (d3, d3_utils) => {
        const data = JSON.parse(variableString);

        const callsites = Object.keys(data);
        const MODE = Object.keys(data[callsites[0]]).length == 2 ? "COMPARISON" : "NORMAL";
        
        // Assign an index to the callsites. 
        const idxToNameMap = Object.assign({}, callsites.map((callsite) => (callsite)));
        const nameToIdxMap = Object.entries(idxToNameMap).reduce((acc, [key, value]) => (acc[value] = key, acc), {})

        // Selection dropdown for metrics.
        const metrics = Object.keys(data[callsites[0]]["tgt"]);
        const selectedMetric = metrics[0]
        d3_utils.selectionDropDown(element, metrics, "metricSelect");

        // Selection dropdown for attributes.
        const attributes = ["min", "max", "mean", "var", "imb", "kurt", "skew"];
        const selectedAttribute = "mean";
        d3_utils.selectionDropDown(element, attributes, "attributeSelect");

        // Sort the callsites by the selected attribute and metric.
        const sortedTgtCallsites = sortByAttribute(data, selectedMetric, selectedAttribute, "tgt");
        const sortedBkgCallsites = sortByAttribute(data, selectedMetric, selectedAttribute, "bkg");

        // Setup VIS area.
        const margin = {top: 20, right: 20, bottom: 0, left: 20},
                containerHeight = 100 * Object.keys(callsites).length,
                width = element.clientWidth - margin.right - margin.left,
                height = containerHeight - margin.top - margin.bottom;
        const svgArea = d3_utils.prepareSvgArea(width, height, margin);
        const svg = d3_utils.prepareSvg(element, svgArea);

        visualize(sortedTgtCallsites, sortedBkgCallsites, nameToIdxMap, false);
       
        function _format(d) {
            return { 
                "min": d3_utils.formatRuntime(d.min),
                "max": d3_utils.formatRuntime(d.max),
                "mean": d3_utils.formatRuntime(d.mean),
                "var": d3_utils.formatRuntime(d.var),
                "imb": d3_utils.formatRuntime(d.imb),
                "kurt": d3_utils.formatRuntime(d.kurt),
                "skew": d3_utils.formatRuntime(d.skew),
            };
        }

        function visualizeStats (d, mode, gId, boxWidth) {
            const stats = _format(d);

            // Text fpr statistics title.
            const xOffset = mode === "tgt" ? 1.1 * boxWidth : 1.4 * boxWidth;
            const textColor = mode === "tgt" ? "#4DAF4A": "#202020";
            // d3_utils.drawText(element, gId, mode, xOffset, 15, 0, textColor);

            // Text for statistics
            let statIdx = 1;
            for( let [stat, val] of Object.entries(stats)) {
                d3_utils.drawText(element, gId, `${stat}:  ${val}`, xOffset, 15, statIdx, textColor);
                statIdx += 1;
            }
        }

        function visualizeBoxplot(g, d, type, xScale, drawCenterLine) {
            const fillColor = { 
                "tgt": "#4DAF4A",
                "bkg": "#D9D9D9"
            };
            const strokeWidth = 1;
            const boxYOffset = 30;
            const strokeColor = "#202020";
            const boxHeight = 80;

            // Centerline
            if (drawCenterLine) {
                const [min, max] = xScale.domain();
                d3_utils.drawLine(g, xScale(min), boxYOffset + boxHeight/2, xScale(max), boxYOffset + boxHeight/2, strokeColor);
            }

            // Box
            d3_utils.drawRect(g, {
                "class": "rect",      
                "x": xScale(d.q[1]),
                "y": boxYOffset,
                "height": boxHeight,
                "fill": fillColor[type],
                "width": xScale(d.q[3]) - xScale(d.q[1]),
                "stroke": strokeColor,
                "stroke-width": strokeWidth
            });

            // Markers
            const markerStrokeWidth = 3;
            d3_utils.drawLine(g, xScale(d.q[0]), boxYOffset, xScale(d.q[0]), boxYOffset + boxHeight, fillColor[type], markerStrokeWidth);
            d3_utils.drawLine(g, xScale(d.q[4]), boxYOffset, xScale(d.q[4]), boxYOffset + boxHeight, fillColor[type], markerStrokeWidth);

            // Outliers
            const outlierRadius = 4; 
            const outlierYOffset = 20;
            let outliers = []
            for (let idx = 0; idx < d.outliers["values"].length; idx += 1) {
                outliers.push({
                    x: xScale(d.outliers["values"][idx]),
                    value: d.outliers["values"][idx],
                    rank: d.outliers["ranks"][idx],
                    // dataset: d.dataset # TODO: pass dataset to differentiate.
                })
            }
            d3_utils.drawCircle(g, outliers, outlierRadius, outlierYOffset, fillColor[type]);
        }
        
        function visualize(tgtCallsites, bkgCallsites, idxMap) {
            const boxWidth = 0.6 * width;
            const allCallsites = [...new Set([...Object.keys(tgtCallsites), ...Object.keys(bkgCallsites)])];

            for (let callsite of allCallsites) {
                let tgt = null;
                if (callsite in tgtCallsites) {
                    tgt = tgtCallsites[callsite];
                }

                let bkg = null;
                if (callsite in bkgCallsites) {
                    bkg = bkgCallsites[callsite];
                }

                // Set the min and max for xScale.
                let min = 0, max = 0;
                if (bkg === undefined) {
                    min = tgt.min;
                    max = tgt.max;
                } else {
                    min = Math.min(tgt.min, bkg.min);
                    max = Math.max(tgt.max, bkg.max);
                }
                const xScale = d3.scaleLinear()
                        .domain([min, max])
                        .range([0.05 * boxWidth, boxWidth - 0.05 * boxWidth]);

                // Set up a g container
                const idx = idxMap[callsite];
                const gId = "box-" + idx;
                const gYOffset = 200;
                const g = svg.append("g")
                    .attr("id", gId)
                    .attr("width", boxWidth)
                    .attr("transform", "translate(0, " + gYOffset * idx  + ")");

                const axisOffset = gYOffset * 0.6;
                d3_utils.drawXAxis(g, xScale, 5, d3_utils.formatRuntime, 0, axisOffset, "black");

                // Text for callsite name.
                d3_utils.drawText(element, gId, "callsite: " + callsite, 0, 0);

                visualizeStats(tgt, "tgt", gId, boxWidth);
                if (bkg !== undefined) {
                    visualizeStats(bkg, "bkg", gId, boxWidth);
                }

                // const tooltip = element;
                // const mouseover = (data) => tooltip.render(data);
                // const mouseout = (data) => tooltip.clear();
                // const click = (data) => tooltip.render(data);

                visualizeBoxplot(g, tgt, "tgt", xScale, true);
                if (bkg !== undefined) {
                    visualizeBoxplot(g, bkg, "bkg", xScale, false);
                }
            }
        }

    });
})(element);