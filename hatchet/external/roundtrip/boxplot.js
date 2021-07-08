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

        const callsites = Object.keys(data);
        const metrics = Object.keys(data[callsites[0]]);

        console.log(callsites,  d3_utils);
        d3_utils.selectionDropDown(element, metrics, "metricSelect");
        
        // document.getElementById("metricSelect").style.margin = "10px 10px 10px 0px";

    })
})(element);