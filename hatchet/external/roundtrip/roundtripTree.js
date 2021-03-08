//d3.v4
(function (element) {
    require(['https://d3js.org/d3.v4.min.js'], function (d3) {
        var cleanTree = argList[0].replace(/'/g, '"');

        var forestData = JSON.parse(cleanTree);

        var rootNodeNames = [];
        var numberOfTrees = forestData.length;
        // Get the metric_column names
        var metricColumns = d3.keys(forestData[0].metrics);
        // pick the first metric listed to color the nodes
        var selectedMetric = metricColumns[0];

        forestMetrics = [];
        forestMinMax = {};
        for (var i = 0; i < numberOfTrees; i++) {
            var thisTree = forestData[i];

            // Get tree names for the display select options
            rootNodeNames.push(thisTree.frame.name);

            var thisTreeMetrics = {};
            // init the min/max for all trees' metricColumns

            for (var j = 0; j < metricColumns.length; j++) {
                thisTreeMetrics[metricColumns[j]] = {};
                thisTreeMetrics[metricColumns[j]]["min"] = Number.MAX_VALUE;
                thisTreeMetrics[metricColumns[j]]["max"] = 0;
            }

            forestMetrics.push(thisTreeMetrics);
        }
        for (var j = 0; j < metricColumns.length; j++) {
            forestMinMax[metricColumns[j]] = {};
            forestMinMax[metricColumns[j]]["min"] = Number.MAX_VALUE;
            forestMinMax[metricColumns[j]]["max"] = 0;
        }

        rootNodeNames.push("Show all trees");

        // ************** Generate the tree diagram  *****************
        var margin = {top: 20, right: 20, bottom: 80, left: 20},
                treeHeight = 300,
                width = element.clientWidth - margin.right - margin.left,
                height = treeHeight * (numberOfTrees + 1),
                gOffset = [{x: margin.left, y: margin.top}]; //keep track of translations to know absolute position

        d3.select(element).append('label').attr('for', 'metricSelect').text('Color by:');
        var metricInput = d3.select(element).append("select") //element
                .attr("id", "metricSelect")
                .selectAll('option')
                .data(metricColumns)
                .enter()
                .append('option')
                .text(d => d)
                .attr('value', d => d);
        document.getElementById("metricSelect").style.margin = "10px 10px 10px 0px";

        d3.select(element).append('label').style('margin', '0 0 0 10px').attr('for', 'treeRootSelect').text(' Display:');
        var treeRootInput = d3.select(element).append("select") //element
                .attr("id", "treeRootSelect")
                .selectAll('option')
                .data(rootNodeNames)
                .enter()
                .append('option')
                .attr('selected', d => d.name == 'Show all trees' ? true : false)
                .text(d => d)
                .attr('value', (d, i) => i + "|" + d);
        document.getElementById("treeRootSelect").style.margin = "10px 10px 10px 10px";

        var tooltip = d3.select(element).append("div")
                .attr('id', 'tooltip')
                .style('position', 'absolute')
                .style('top', '5px')
                .style('right', '15px')
                .style('padding', '5px')
                .style('border-radius', '5px')
                .style('background', '#ccc')
                .style('color', 'black')
                .style('font-size', '14px')
                .style('font-family', 'monospace')
                .html('<p>Click a node or "Select nodes" to see more info</p>');

        var svg = d3.select(element).append("svg") //element
                .attr("width", width + margin.right + margin.left)
                .attr("height", height + margin.top + margin.bottom);

        var brushOn = 1;
        var colorScheme = 1; //default=1 : invert=-1
        var button = svg.append('g')
                .attr('id', 'selectButton')
                .append('rect')
                .attr('width', '80px')
                .attr('height', '15px')
                .attr('x', 0).attr('y', 0).attr('rx', 5)
                .style('fill', '#ccc')
                .on('click', function () {
                    brushOn = -1 * brushOn;
                    activateBrush(brushOn);
                });
        d3.select(element).select('#selectButton').append('text')
                .attr("x", 3)
                .attr("y", 12)
                .text('Select nodes')
                .attr("font-family", "sans-serif")
                .attr("font-size", "12px")
                .attr('cursor', 'pointer')
                .on('click', function () {
                    brushOn = -1 * brushOn;
                    activateBrush(brushOn);
                });
        var colorButton = svg.append('g')
                .attr('id', 'colorButton')
                .append('rect')
                .attr('width', '90px')
                .attr('height', '15px')
                .attr('x', 90).attr('y', 0).attr('rx', 5)
                .style('fill', '#ccc');
        d3.select(element).select('#colorButton').append('text')
                .attr("x", 93)
                .attr("y", 12)
                .text('Colors: default')
                .attr("font-family", "sans-serif")
                .attr("font-size", "12px")
                .attr('cursor', 'pointer')
                .on('click', function () {
                    colorScheme = -1 * colorScheme;
                    var curMetric = d3.select(element).select('#metricSelect').property('value');
                    var curLegend = d3.select(element).select('#unifyLegends').text();
                    d3.select(element).selectAll(".circleNode")
                            .transition()
                            .duration(duration)
                            .style('fill', function (d) {
                                if (curLegend == 'Legends: unified') {
                                    return colorScale(d.data.metrics[curMetric], -1);
                                }
                                return colorScale(d.data.metrics[curMetric], d.treeIndex);
                            })
                            .style('stroke', 'black');

                    //Update each individual legend to inverted scale
                    for (var treeIndex = 0; treeIndex < numberOfTrees; treeIndex++) {
                        if (curLegend == 'Legends: unified') {
                            setColorLegend(-1);
                        } else {
                            setColorLegend(treeIndex);
                        }
                    }
                });
        var unifyLegends = svg.append('g')
                .attr('id', 'unifyLegends')
                .append('rect')
                .attr('width', '100px')
                .attr('height', '15px')
                .attr('x', 190)
                .attr('y', 0)
                .attr('rx', 5)
                .style('fill', '#ccc');
        d3.select(element).select('#unifyLegends').append('text')
                .attr("x", 195)
                .attr("y", 12)
                .text('Legends: unified')
                .attr("font-family", "sans-serif")
                .attr("font-size", "12px")
                .attr('cursor', 'pointer')
                .on('click', function () {
                    var curMetric = d3.select(element).select('#metricSelect').property('value');
                    var sameLegend = true;
                    if (d3.select(this).text() == 'Legends: unified') {
                        d3.select(this).text('Legends: indiv.');
                        sameLegend = false;
                        for (var treeIndex = 0; treeIndex < numberOfTrees; treeIndex++) {
                            setColorLegend(treeIndex);
                        }
                    } else {
                        d3.select(this).text('Legends: unified');
                        sameLegend = true;
                        setColorLegend(-1);
                    }

                    d3.select(element).selectAll(".circleNode")
                            .transition()
                            .duration(duration)
                            .style("fill", function (d) {
                                return sameLegend ? colorScale(d.data.metrics[curMetric], -1) : colorScale(d.data.metrics[curMetric], d.treeIndex);
                            })
                            .style("stroke", 'black');
                });


        var mainG = svg.append("g")
                .attr('id', "mainG")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var treemap = d3.tree().size([(treeHeight), width - margin.left]);

        var maxHeight = 0;
        // Find the tallest tree for layout purposes (used to set a uniform spreadFactor)
        for (var treeIndex = 0; treeIndex < forestData.length; treeIndex++) {
            currentTreeData = forestData[treeIndex];
            currentRoot = d3.hierarchy(currentTreeData, d => d.children);

            currentRoot.x0 = height;
            currentRoot.y0 = margin.left;

            var currentTreeMap = treemap(currentRoot);
            if (currentTreeMap.height > maxHeight) {
                maxHeight = currentTreeMap.height;
            }
        }

        // Add a group and tree for each forestData[i]
        for (var treeIndex = 0; treeIndex < forestData.length; treeIndex++) {
            currentTreeData = forestData[treeIndex];
            currentRoot = d3.hierarchy(currentTreeData, d => d.children);
            currentRoot.x0 = height;
            currentRoot.y0 = margin.left;

            var currentTreeMap = treemap(currentRoot);
            var newg = mainG.append("g")
                    .attr('class', 'group ' + treeIndex)
                    .attr("transform", "translate(" + margin.left + "," + (treeHeight * treeIndex + margin.top) + ")");

            currentTreeMap.descendants().forEach(function (d) {
                for (var i = 0; i < metricColumns.length; i++) {
                    var tempMetric = metricColumns[i];
                    if (d.data.metrics[tempMetric] > forestMetrics[treeIndex][tempMetric].max) {
                        forestMetrics[treeIndex][tempMetric].max = d.data.metrics[tempMetric];
                    }
                    if (d.data.metrics[tempMetric] < forestMetrics[treeIndex][tempMetric].min) {
                        forestMetrics[treeIndex][tempMetric].min = d.data.metrics[tempMetric];
                    }
                    if (d.data.metrics[tempMetric] > forestMinMax[tempMetric].max) {
                        forestMinMax[tempMetric].max = d.data.metrics[tempMetric];
                    }
                    if (d.data.metrics[tempMetric] < forestMinMax[tempMetric].min) {
                        forestMinMax[tempMetric].min = d.data.metrics[tempMetric];
                    }
                }
            });

            addColorLegendRects(newg);

            update(currentRoot, currentTreeMap, newg);
            newg.style("display", "inline-block");
        } //end for-loop "add tree"

        // Global min/max are the last entry of forestMetrics;
        forestMetrics.push(forestMinMax);

        var i = 0,
                duration = 750;

        // Helper function for determining which nodes are in brush
        function rectContains(selection, points) {
            if (selection) {
                var isBrushed = selection[0][0] <= points.yMainG && selection[1][0] >= points.yMainG && // Check X coordinate
                        selection[0][1] <= points.xMainG && selection[1][1] >= points.xMainG  // And Y coordinate
                //Remember points are at (y,x)
                return isBrushed;
            }
        }

        function highlightNodes(brushedNodes) {
            if (brushedNodes.length == 0) {
                d3.select(element).selectAll("circle")
                        .style("stroke", 'black')
                        .style("stroke-width", "1px");
                return;
            }
            brushedNodes.transition()
                    .duration(duration / 100)
                    .style("stroke", "black")
                    .style("stroke-width", "4px");
        }

        function activateBrush(brushOn) {
            if (brushOn > 0) {
                //Turn brush off
                d3.select(element).select("#selectButton rect")
                        .style("fill", "#ccc")
                        .attr('cursor', 'pointer');
                d3.select(element).select("#selectButton text")
                        .style("fill", "black")
                        .attr('cursor', 'pointer');
                d3.selectAll('.brush').remove();
                brushOn = -brushOn;
            } else {
                d3.select(element).select("#selectButton rect")
                        .style("fill", "black")
                        .attr('cursor', 'pointer');
                d3.select(element).select("#selectButton text")
                        .style("fill", "white")
                        .attr('cursor', 'pointer');
                var brush = d3.brush()
                        .extent([[0, 0], [2 * width, 2 * (height + margin.top + margin.bottom)]])
                        .on('brush', brushmove)
                        .on('end', brushend);

                const gBrush = mainG.append('g')
                        .attr('class', 'brush')
                        .call(brush);
                brushOn = -brushOn;
            }
        }

        function setColors(treeIndex) {
            var invertColors = [['#edf8e9', '#c7e9c0', '#a1d99b', '#74c476', '#31a354', '#006d2c'], //green
                ['#fee5d9', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26', '#a50f15'], //red
                ['#eff3ff', '#c6dbef', '#9ecae1', '#6baed6', '#3182bd', '#08519c'], //blue
                ['#f2f0f7', '#dadaeb', '#bcbddc', '#9e9ac8', '#756bb1', '#54278f'], //purple
                ['#feedde', '#fdd0a2', '#fdae6b', '#fd8d3c', '#e6550d', '#a63603'], //orange
                ['#f7f7f7', '#d9d9d9', '#bdbdbd', '#969696', '#636363', '#252525']];  //black
            var regularColors = [['#006d2c', '#31a354', '#74c476', '#a1d99b', '#c7e9c0', '#edf8e9'], //green
                ['#a50f15', '#de2d26', '#fb6a4a', '#fc9272', '#fcbba1', '#fee5d9'], //red
                ['#08519c', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#eff3ff'], //blue
                ['#54278f', '#756bb1', '#9e9ac8', '#bcbddc', '#dadaeb', '#f2f0f7'], //purple
                ['#a63603', '#e6550d', '#fd8d3c', '#fdae6b', '#fdd0a2', '#feedde'], //orange
                ['#252525', '#636363', '#969696', '#bdbdbd', '#d9d9d9', '#f7f7f7']]; //black

            var allTreesColors = ['#d73027', '#fc8d59', '#fee090', '#e0f3f8', '#91bfdb', '#4575b4'];
            var invertedAllTrees = ['#4575b4', '#91bfdb', '#e0f3f8', '#fee090', '#fc8d59', '#d73027', ]

            var colorSchemeUsed;
            if (treeIndex == -1) { //all trees are displayed
                if (colorScheme == 1) {
                    d3.select(element).select('#colorButton text')
                            .text('Colors: default');
                    colorSchemeUsed = allTreesColors;
                } else {
                    d3.select(element).select('#colorButton text')
                            .text('Colors: inverted');
                    colorSchemeUsed = invertedAllTrees;
                }
            } else { //single tree is displayed
                if (colorScheme == 1) {
                    d3.select(element).select('#colorButton text')
                            .text('Colors: default');
                    colorSchemeUsed = regularColors[treeIndex];
                } else {
                    d3.select(element).select('#colorButton text')
                            .text('Colors: inverted');
                    colorSchemeUsed = invertColors[treeIndex];
                }
            }
            return colorSchemeUsed;
        }

        function addColorLegendRects(thisG) {
            var treeIndex = thisG.attr("class").split(" ")[1];

            const legendGroups = thisG.selectAll("g")
                    .data([0, 1, 2, 3, 4, 5])
                    .enter()
                    .append('g')
                    .attr('class', 'legend legend' + treeIndex)
                    .attr('transform', (d, i) => {
                        const y = 18 * i;
                        return "translate(-20, " + y + ")";
                    });
            const legendRects = legendGroups.append('rect')
                    .attr('class', 'legend legend' + treeIndex)
                    .attr('x', 0)
                    .attr('y', 0)
                    .attr('height', 15)
                    .attr('width', 10)
                    .style('stroke', 'black');
            const legendText = legendGroups.append('text')
                    .attr('class', 'legend legend' + treeIndex)
                    .attr('x', 12)
                    .attr('y', 13)
                    .text("0.0 - 0.0")
                    .style('font-family', 'monospace')
                    .style('font-size', '12px');
        }

        function setColorLegend(treeIndex) {
            var curMetric = d3.select(element).select('#metricSelect').property('value');
            if (d3.select(element).select('#unifyLegends').text() == 'Legends: unified') {
                treeIndex = -1;
            }
            if (treeIndex == -1) { //unified color legend

                var metric_range = forestMinMax[curMetric].max - forestMinMax[curMetric].min;
                var colorScaleDomain = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1].map(function (x) {
                    return x * metric_range + forestMinMax[curMetric].min;
                });

                var colorSchemeUsed = setColors(treeIndex);
                var legendClass = ".legend";

            } else {
                var metric_range = forestMetrics[treeIndex][curMetric].max - forestMetrics[treeIndex][curMetric].min;
                var colorScaleDomain = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1].map(function (x) {
                    return x * metric_range + forestMetrics[treeIndex][curMetric].min;
                });

                var colorSchemeUsed = setColors(treeIndex);
                var legendClass = '.legend' + treeIndex;
            }
            d3.select(element).selectAll(legendClass + ' rect')
                    .transition()
                    .duration(duration)
                    .attr('fill', function (d, i) {
                        return colorSchemeUsed[d];
                    })
                    .attr('stroke', 'black');
            d3.select(element).selectAll(legendClass + ' text')
                    .text((d, i) => {
                        return colorScaleDomain[6 - d - 1] + ' - ' + colorScaleDomain[6 - d];
                    })
        }

        // Update colorScale with min and max
        function colorScale(nodeMetric, treeIndex) {
            var curMetric = d3.select(element).select('#metricSelect').property('value');
            if (treeIndex == -1) {
                var colorSchemeUsed = setColors(treeIndex);
                var metric_range = forestMinMax[curMetric].max - forestMinMax[curMetric].min;
                var proportion_of_total = (nodeMetric - forestMinMax[curMetric].min) / metric_range;
            } else {
                var colorSchemeUsed = setColors(treeIndex);
                var metric_range = forestMetrics[treeIndex][curMetric].max - forestMetrics[treeIndex][curMetric].min;
                var proportion_of_total = nodeMetric / 1;

                if (metric_range != 0) {
                    proportion_of_total = (nodeMetric - forestMetrics[treeIndex][curMetric].min) / metric_range;
                }
            }

            if (proportion_of_total > 0.9) {
                return colorSchemeUsed[0];
            }
            if (proportion_of_total > 0.7) {
                return colorSchemeUsed[1];
            }
            if (proportion_of_total > 0.5) {
                return colorSchemeUsed[2];
            }
            if (proportion_of_total > 0.3) {
                return colorSchemeUsed[3];
            }
            if (proportion_of_total > 0.1) {
                return colorSchemeUsed[4];
            } else {
                return colorSchemeUsed[5];
            }
        }

        d3.select(element).select('#treeRootSelect')
                .on('change', function () {
                    var rootIndex = d3.select(element).select('#treeRootSelect').property('value').split("|")[0];
                    var rootName = d3.select(element).select('#treeRootSelect').property('value').split("|")[1];
                    if (rootName == "Show all trees") {
                        d3.select(element).selectAll(".group ").attr('transform', function () {
                            var groupIndex = d3.select(this).attr("class").split(" ")[1];
                            return 'translate(' + margin.left + "," + (treeHeight * groupIndex + margin.top) + ")"
                        });

                        d3.select(element).selectAll(".group ").style("display", "inline-block");
                    } else {
                        d3.select(element).selectAll(".group ").style("display", function () {
                            var groupIndex = d3.select(this).attr("class").split(" ")[1];
                            if (groupIndex == rootIndex) {
                                // Move this displayed tree to the top
                                d3.select(this).attr('transform', 'translate(' + margin.left + "," + margin.top + ")");
                                return "inline-block";
                            } else {
                                // Return the other trees back to their original spots
                                d3.select(this).attr('transform', 'translate(' + margin.left + "," + (treeHeight * groupIndex + margin.top) + ")");
                                return "none";
                            }
                        });
                    }
                });

        function update(source, treeData, g) {
            var curMetric = d3.select(element).select('#metricSelect').property('value');
            var treeIndex = g.attr("class").split(" ")[1];
            if (d3.select(element).select('#unifyLegends').text() == 'Legends: unified') {
                setColorLegend(-1);
            } else {
                setColorLegend(treeIndex);
            }

            // Compute the new tree layout
            var nodes = treeData.descendants();
            var links = treeData.descendants().slice(1);

            spreadFactor = width / (maxHeight + 1);
            legendOffset = 30;
            // Normalize for fixed-depth.
            nodes.forEach(function (d) {
                d.x = d.x + legendOffset;
                d.y = d.depth * spreadFactor;
                d.treeIndex = treeIndex;
            });

            // Update the nodes…
            var node = g.selectAll("g.node")
                    .data(nodes, function (d) {
                        return d.id || (d.id = ++i);
                    });

            // Enter any new nodes at the parent's previous position.
            nodeEnter = node.enter().append('g')
                    .attr('class', 'node')
                    .attr("transform", function (d) {
                        return "translate(" + source.y0 + "," + source.x0 + ")";
                    })
                    .on("click", click)
                    .on('dblclick', function (d) {
                        doubleclick(d, treeData, g);
                    });

            nodeEnter.append("circle")
                    .attr('class', 'circleNode')
                    .attr("r", 1e-6)
                    .style("fill", function (d) {
                        if (d3.select(element).select('#unifyLegends').text() == 'Legends: unified') {
                            return colorScale(d.data.metrics[curMetric], -1);
                        }
                        return colorScale(d.data.metrics[curMetric], d.treeIndex);
                    })
                    .style('stroke-width', '1px')
                    .style('stroke', 'black');

            nodeEnter.append("text")
                    .attr("x", function (d) {
                        return d.children || d._children ? -13 : 13;
                    })
                    .attr("dy", ".75em")
                    .attr("text-anchor", function (d) {
                        return d.children || d._children ? "end" : "start";
                    })
                    .text(function (d) {
                        return d.data.name;
                    })
                    .attr('transform', 'rotate( -15)')
                    .style("stroke-width", "3px")
                    .style("font", "12px monospace");

            //UPDATE
            var nodeUpdate = nodeEnter.merge(node);

            // Transition nodes to their new position.
            nodeUpdate.transition()
                    .duration(duration)
                    .attr("transform", function (d) {
                        return "translate(" + d.y + "," + d.x + ")";
                    });

            nodeUpdate.select('circle.circleNode')
                    .attr("r", 10)
                    .style('fill', function (d) {
                        if (d3.select(element).select('#unifyLegends').text() == 'Legends: unified') {
                            return colorScale(d.data.metrics[curMetric], -1);
                        }
                        return colorScale(d.data.metrics[curMetric], d.treeIndex);
                    })
                    .style('stroke', 'black')
                    .style("stroke-dasharray", function (d) {
                        return d._children ? '4' : '0';
                    }) //lightblue
                    .style('stroke-width', d => d._children ? '6px' : '1px')
                    .attr('cursor', 'pointer');

            // Transition exiting nodes to the parent's new position.
            var nodeExit = node.exit().transition()
                    .duration(duration)
                    .attr("transform", function (d) {
                        return "translate(" + source.y + "," + source.x + ")";
                    })
                    .remove();

            nodeExit.select("circle")
                    .attr("r", 1e-6);

            nodeExit.select("text")
                    .style("fill-opacity", 1);

            /******** Links ********/
            // Creates a curved (diagonal) path from parent to the child nodes
            function diagonal(s, d) {
                path = `M ${s.y} ${s.x}
          C ${(s.y + d.y) / 2} ${s.x},
          ${(s.y + d.y) / 2} ${d.x},
          ${d.y} ${d.x}`

                return path
            }

            // Update the links…
            var link = g.selectAll("path.link")
                    .data(links, function (d) {
                        return d.id;
                    });

            // Enter any new links at the parent's previous position.
            var linkEnter = link.enter().insert("path", "g")
                    .attr("class", "link")
                    .attr("d", function (d) {
                        var o = {x: source.x0, y: source.y0};
                        return diagonal(o, o);
                    })
                    .attr('fill', 'none')
                    .attr('stroke', '#ccc')
                    .attr('stroke-width', '2px');

            var linkUpdate = linkEnter.merge(link);

            // Transition links to their new position.
            linkUpdate.transition()
                    .duration(duration)
                    .attr("d", function (d) {
                        return diagonal(d, d.parent);
                    });

            // Transition exiting nodes to the parent's new position.
            var linkExit = link.exit().transition()
                    .duration(duration)
                    .attr("d", function (d) {
                        var o = {x: source.x, y: source.y};
                        return diagonal(o, o);
                    })
                    .remove();

            // Stash the old positions for transition and
            // stash absolute positions (absolute in mainG)
            nodes.forEach(function (d) {
                d.x0 = d.x;
                d.y0 = d.y;

                // Store the overall position based on group
                d.xMainG = d.x + treeHeight * treeIndex + margin.top;
                d.yMainG = d.y + margin.left;

            });
        }

        //When metricSelect is changed (metric_col)
        d3.select(element).select('#metricSelect')
                .on('change', function () {
                    changeMetric();
                });

        // To pretty print the node data as a IPython table
        function printNodeData(nodeList) {
            var nodeStr = '<table><tr><td>name</td>';
            var numNodes = nodeList.length;
            //lay the nodes out in a table
            for (var i = 0; i < metricColumns.length; i++) {
                nodeStr += '<td>' + metricColumns[i] + '</td>';
            }
            nodeStr += '</tr>';
            for (var i = 0; i < numNodes; i++) {
                for (var j = 0; j < metricColumns.length; j++) {
                    if (j == 0) {
                        nodeStr += '<tr><td>' + nodeList[i].data.frame.name + '</td><td>' + nodeList[i].data.metrics[metricColumns[j]] + '</td><td>';
                    }
                    else if (j == metricColumns.length - 1) {
                        nodeStr += nodeList[i].data.metrics[metricColumns[j]] + '</td></tr>';
                    }
                    else {
                        nodeStr += nodeList[i].data.metrics[metricColumns[j]];
                    }
                }
            }
            nodeStr = nodeStr + '</table>';
            return nodeStr;
        }

        jsNodeSelected = "['*']"; //default: select all nodes

        function printQuery(nodeList) {
            var leftMostNode = {depth: Number.MAX_VALUE, data: {name: 'default'}};
            var rightMostNode = {depth: 0, data: {name: 'default'}};
            var lastNode = "";
            var selectionIsAChain = false;

            for (var i = 0; i < nodeList.length; i++) {
                if (nodeList[i].depth < leftMostNode.depth) {
                    leftMostNode = nodeList[i];
                }
                if (nodeList[i].depth > rightMostNode.depth) {
                    rightMostNode = nodeList[i];
                }
                if ((i > 1) && (nodeList[i].x == nodeList[i-1].x)) {
                    selectionIsAChain = true;
                }
                else {
                    selectionIsAChain = false;
                }
            }

            //do some evaluation for other subtrees
            // we could generate python code that does this
            var queryStr = "['<no query generated>']";
            if ((nodeList.length > 1) && (selectionIsAChain)) {
                // This query is for chains
                queryStr = "[{'name': '" + leftMostNode.data.frame.name + "'}, '*', {'name': '" + rightMostNode.data.frame.name + "'}]";
            }
            else if (nodeList.length > 1) {
                // This query is for subtrees
                queryStr = "[{'name': '" + leftMostNode.data.frame.name + "'}, '*', {'depth': '<= " + rightMostNode.depth + "' }]";
            }
            else {
                //Single node query
                queryStr = "[{'name': '" + leftMostNode.data.frame.name + "'}]";
            }

            return queryStr;
        }

        function updateTooltip(nodeList) {
            d3.select(element).selectAll("#tooltip text").remove();
            var tipText = printNodeData(nodeList);
            var longestName = 0;
            nodeList.forEach(function (d) {
                var nodeData = d.data.frame.name + ': ' + d.data.metrics.time + 's (' + d.data.metrics["time (inc)"] + 's inc)';
                if (nodeData.length > longestName) {
                    longestName = nodeData.length;
                }
            });

            d3.select(element).select('#tooltip')
                    .html(tipText);
        }

        function click(d) {
            updateTooltip([d]);
            jsNodeSelected = printQuery([d]);

            var selectedData = d;
            d3.select(element).selectAll('.circleNode')
                .style('stroke', function (e) {
                    if (e == selectedData)
                        return 'black';
                    else {
                        var curMetric = d3.select(element).select('#metricSelect').property('value');
                        return e._children ? "#89c3e0" : 'black';
                    }
                })
                .style('stroke-width', e => e == selectedData ? '4px' : '1px');
        }

        // Toggle children on doubleclick.
        function doubleclick(d, treeData, g) {
            if (d.children) {
                d._children = d.children;
                d.children = null;
            } else {
                d.children = d._children;
                d._children = null;
            }
            update(d, treeData, g);
        }

        function changeMetric(allMin, allMax) {
            var curMetric = d3.select(element).select('#metricSelect').property('value');
            var nodes = d3.select(element).selectAll(".circleNode");

            for (var treeIndex = 0; treeIndex < numberOfTrees; treeIndex++) {
                setColorLegend(treeIndex);

                d3.select(element).selectAll(".group ").selectAll(".circleNode")
                        .transition()
                        .duration(duration)
                        .style("fill", function (d) {
                            if (d3.select(element).select('#unifyLegends').text() == 'Legends: unified') {
                                return colorScale(d.data.metrics[curMetric], -1);
                            }
                            return colorScale(d.data.metrics[curMetric], d.treeIndex);
                        })
                        .style("stroke", 'black');
            }
        }

        function brushmove() {
            const {selection} = d3.event;

            if (!selection) {
                highlightNodes([]);
                return;
            }
            // Slow, unoptimized
            const brushedNodes = d3.select(element).selectAll(".circleNode")
                    .filter(d => rectContains(selection, d));

            const brushedData = [];
            brushedNodes.each(d => brushedData.push(d));

            highlightNodes(brushedNodes);
        }

        function brushend() {
            const {selection} = d3.event;

            if (!selection) {
                highlightNodes([]);
                return;
            }
            // Slow, unoptimized
            const brushedNodes = d3.select(element).selectAll(".circleNode")
                    .filter(d => rectContains(selection, d));

            const brushedData = [];
            brushedNodes.each(d => brushedData.push(d));

            updateTooltip(brushedData);

            jsNodeSelected = printQuery(brushedData);
       }
    });
})(element);
