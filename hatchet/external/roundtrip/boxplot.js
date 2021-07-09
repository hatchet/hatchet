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
                'd3-color': 'd3src/d3-color.v1.min',
                'd3-interpolate': 'd3src/d3-interpolate.v1.min',
                'd3-scale-chromatic': 'd3src/d3-scale-chromatic.v1.min',
                'd3-utils': 'lib/d3_utils',
            }
        }
    });
    require(['d3', 'd3-utils'], function (d3, d3_utils) {
        const data = JSON.parse(data_string.replace(/'/g, '"'));

        const margin = {top: 20, right: 20, bottom: 80, left: 20},
                containerHeight = 400,
                width = element.clientWidth - margin.right - margin.left,
                height = containerHeight - margin.top - margin.bottom;

        const svgArea = d3_utils.prepareSvgArea(width, height, margin);
        const svg = d3_utils.prepareSvg(element, svgArea);

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
        console.log(sort_callsites);
        
        let stats = {};
        let boxplot = {};
        for (let callsite in sort_callsites) {
            d = sort_callsites[callsite];

            // Set the dictionaries for metadata information. 
            stats[callsite] = { 
                "min": d3_utils.formatRuntime(d["min"]),
                "max": d3_utils.formatRuntime(d["max"]),
                "mean": d3_utils.formatRuntime(d["mean"]),
                "var": d3_utils.formatRuntime(d["var"]),
                "imb": d3_utils.formatRuntime(d["imb"]),
                "kurt": d3_utils.formatRuntime(d["kurt"]),
                "skew": d3_utils.formatRuntime(d["skew"]),
            };
            
            // Set the data for the boxplot.
            boxplot[callsite] = {"q": d["q"], "outliers": d["outliers"]};
        }
    })
})(element);