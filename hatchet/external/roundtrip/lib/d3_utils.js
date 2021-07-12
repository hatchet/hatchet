define(function (require) {
  const d3 = require("d3");

  return {
    calcContainerWidth: name => +d3.select(name).style('width').slice(0, -2),
    calcContainerHeight: name => +d3.select(name).style('height').slice(0, -2),
    calcCellWidth: (width, colNames) => width / colNames.length,
    calcCellHeight: (height, rowNames) => height / rowNames.length,
    calcCellSize: (width, height, colNames, rowNames, widthMax, heightMax) => [Math.min(calcCellWidth(width, colNames), widthMax), Math.min(calcCellHeight(height, rowNames), heightMax)],
    prepareSvgArea: (windowWidth, windowHeight, margin) => {
      return {
        width: windowWidth - margin.left - margin.right,
        height: windowHeight - margin.top - margin.bottom,
        margin: margin
      }
    },
    prepareSvg: (id, svgArea) => {
      d3.select(id).selectAll('*').remove();
      const svg = d3.select(id)
        .append('svg')
        .attr('width', svgArea.width + svgArea.margin.left + svgArea.margin.right)
        .attr('height', svgArea.height + svgArea.margin.top + svgArea.margin.bottom)
        .append('g')
        .attr('transform',
          'translate(' + svgArea.margin.left + ',' + svgArea.margin.top + ')');

      return svg;
    },
    initSvgInfo: (targetView, margin) => {
      const sd = targetView.svgData;
      const domId = targetView.domId;

      sd.svgArea = prepareSvgArea(
        calcContainerWidth(`#${domId}`),
        calcContainerHeight(`#${domId}`), margin || {
          top: 0,
          right: 0,
          bottom: 0,
          left: 0
        })
      sd.svg = prepareSvg(`#${domId}`, sd.svgArea);
      sd.domId = targetView.domId;
    },

    // Axes, Scaling
    genX: (data, svgArea, domain = null, scaler = d3.scaleLinear()) => {
      if (domain === null) {
        domain = d3.extent(data);
      }
      return scaler.domain(domain).range([0, svgArea.width]);
    },
    genInvX: (data, svgArea, domain = null, scaler = d3.scaleLinear()) => {
      if (domain === null) {
        domain = d3.extent(data);
      }
      return scaler.domain([0, svgArea.width]).range(domain);
    },
    genY: (data, svgArea, domain = null, scaler = d3.scaleLinear(), goUp = true) => {
      if (domain === null) {
        domain = d3.extent(data);
      }
      return goUp ?
        scaler.domain(domain).range([svgArea.height, 0]) :
        scaler.domain(domain).range([0, svgArea.height]);
    },
    genInvY: (data, svgArea, domain = null, scaler = d3.scaleLinear()) => {
      if (domain === null) {
        domain = d3.extent(data);
      }
      return scaler.domain([svgArea.height, 0]).range(domain);
    },

    // UI Components
    selectionDropDown: (element, data, id) => {
      return d3.select(element).append("select")
        .attr("id", id)
        .selectAll('option')
        .data(data)
        .enter()
        .append('option')
        .text(d => d)
        .attr('value', d => d);
    },
    

    // Formatting numbers
    formatRuntime: (val) => {
      if (val == 0) {
        return val;
      }
      let format = d3.format(".3");
      return format(val);
    },

    // SVG elements
    drawRect: (element, attrDict, click = () => { }, mouseover = () => { }, mouseout = () => { }) => {
      return element.append("rect")
        .attr("x", attrDict["x"])
        .attr("y", attrDict["y"])
        .attr("height", attrDict["height"])
        .attr("width", attrDict["width"])
        .attr("fill", attrDict["fill"])
        .attr("stroke", attrDict["stroke"])
        .attr("stroke-width", attrDict["stroke-width"])
        .on("click", click)
        .on("mouseover", mouseover)
        .on("mouseout", mouseout);
    },
    drawText: (element, forId, text, xOffset, yOffset, yOffsetIdx, textColor) => {
      return d3.select(element)
        .select('#' + forId)
        .append('text')
        .attr("x", xOffset)
        .attr("y", yOffset * yOffsetIdx)
        .attr("stroke", textColor)
        .attr('for', forId)
        .text(text);
    },
    drawLine: (element, x1, y1, x2, y2, strokeColor) => {
      return element
				.append("line")
				.attr("class", "line")
				.attr("x1", x1)
        .attr("y1", y1)
        .attr("x2", x2)
        .attr("y2", y2)
        .attr("stroke", strokeColor)
				.style("stroke-width", "1.5");
    },
    drawCircle: (element, data, radius, yOffset, fillColor, click = () => { }, mouseover = () => { }, mouseout = () => { }) => {
      return element
				.selectAll(".circle")
				.data(data)
				.join("circle")
				.attr("r", radius)
        .attr("cx", (d) => d.x)
        .attr("cy", (d) => d.y + yOffset)
				.attr("class", "circle")
				.style("fill", fillColor)
				.on("click", (d) => click(d))
				.on("mouseover", (d) => mouseover(d))
				.on("mouseout", (d) => mouseout(d));
    }
  }
});
