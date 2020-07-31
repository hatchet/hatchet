//d3.v4
// brushing help: https://peterbeshai.com/blog/2016-12-03-brushing-in-scatterplots-with-d3-and-quadtrees/
(function(element) {
    require(['https://d3js.org/d3.v4.min.js'], function(d3) {
    for (var i=0; i < argList.length; i++) {
    //         console.log("arg:",argList[i]);
    //         console.log(typeof argList[i]);
    }

    var cleanTree =  argList[0].replace(/'/g, '"');
    
    var forestData = JSON.parse(cleanTree);
    var treeData = forestData[0];
    var rootNodeNames = [];
        
    for (var i=0; i<forestData.length; i++){
        rootNodeNames.push(forestData[i].name);
    }
    rootNodeNames.push("Show all trees");
     
    
    // Get the metric_column names
    var metricColumns = d3.keys(treeData.metrics);
    
 
    // ************** Generate the tree diagram  *****************
    var margin = {top: 20, right: 20, bottom: 80, left: 40},
    width = window.innerWidth - margin.right - margin.left,
    height = 1000 - margin.top - margin.bottom,
    spreadFactor = 100;
    
    var selectedMetric = metricColumns[0];
        
    var metricInput = d3.select(element).append("select")
        .attr("id", "metricSelect")
        .selectAll('option')
        .data(metricColumns)
        .enter()
        .append('option')
        .text(d => d)
        .attr('value', d => d);
   
    var treeRootInput = d3.select(element).append("select")
        .attr("id", "treeRootSelect")
        .selectAll('option')
        .data(rootNodeNames)
        .enter()
        .append('option')
        .text(d => d)
        .attr('value', (d,i) => i+"|"+d);
        
    var svg = d3.select(element).append("svg") 
        .attr("width", width + margin.right + margin.left)
        .attr("height", height + margin.top + margin.bottom);
        
    var tooltip = svg.append("g")
              .attr("id", "tooltip")
              .append("rect")
              .attr("width", spreadFactor)
              .attr("height", "20px")
              .attr("x", 200)
              .attr("y", 12)
              .style("fill", "white");   
        
     const legendGroups = svg.selectAll("g")
         .data([0,1,2,3,4,5,6])
         .enter()
         .append('g')
         .attr('class', 'legend')
         .attr('transform', (d,i)=>{
             const y = 18*i;
             return "translate(" + [0, y] + ")";
         });
     const legendRects = legendGroups.append('rect')
         .attr('class', 'legend')
         .attr('x', 0)
         .attr('y', 0)
         .attr('height', 15)
         .attr('width', 10)
         .attr('fill', 'white');
    const legendText = legendGroups.append('text')
         .attr('class', 'legend')
         .attr('x', 12)
         .attr('y', 13)
         .text("0.0 - 0.0")
         .style('font-family', 'monospace')
         .style('font-size', '12px');
     
        
     var brushOn = 1;
     var colorScheme = 1; //default=1 : invert=-1
     var button = svg.append('g')
         .attr('id', 'selectButton')
         .append('rect')
         .attr('width', '80px')
         .attr('height', '15px')
         .attr('x', 0)
         .attr('y', 0)
         .attr('rx', 5)
         .style('fill', '#ccc')
         .on('click', function() {
           brushOn = -1 * brushOn;
           activateBrush(brushOn);
         });
      d3.select('#selectButton').append('text')
         .attr("x", 3)
         .attr("y", 12)
         .text('Select nodes')
         .attr("font-family", "sans-serif")
         .attr("font-size", "12px")
         .attr('cursor', 'pointer')
         .on('click', function() {
           brushOn = -1 * brushOn;
           activateBrush(brushOn);
         });
     var colorButton = svg.append('g')
         .attr('id', 'colorButton')
         .append('rect')
         .attr('width', '90px')
         .attr('height', '15px')
         .attr('x', 90)
         .attr('y', 0)
         .attr('rx', 5)
         .style('fill', '#ccc');
      d3.select('#colorButton').append('text')
         .attr("x", 93)
         .attr("y", 12)
         .text('Colors: default')
         .attr("font-family", "sans-serif")
         .attr("font-size", "12px")
         .attr('cursor', 'pointer')
         .on('click', function() {
             colorScheme = -1 * colorScheme;
             var curMetric = d3.select('#metricSelect').property('value');
             d3.selectAll(".circleNode")
               .transition()
               .duration(duration)
               .style("fill", function(d){ 
                 return colorScale(d.data.metrics[curMetric]);})
               .style("stroke", function(d){ 
                 return colorScale(d.data.metrics[curMetric]);})
              setColorLegend(curMetric);
         });
//         var highlightButton = svg.append('g')
//          .attr('id', 'highlightButton')
//          .append('rect')
//          .attr('width', '90px')
//          .attr('height', '15px')
//          .attr('x', 190)
//          .attr('y', 0)
//          .attr('rx', 5)
//          .style('fill', '#ccc');
//       d3.select('#highlightButton').append('text')
//          .attr("x", 195)
//          .attr("y", 12)
//          .text('Highlight: ON')
//          .attr("font-family", "sans-serif")
//          .attr("font-size", "12px")
//          .attr('cursor', 'pointer')
//          .on('click', function() {
//              console.log("clicked highlight text",d3.selectAll('.node text'));
//               d3.selectAll('.node text')
//               .transition()
//               .duration(duration/100)
//               .style('fill', 'magenta'); //#949494
//          });

        
    var mainG = svg.append("g")
        .attr('id', "mainG")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var g = mainG.append("g")
        .attr('id', 'group0')
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        
    var i = 0,
        duration = 750,
        root;

    allMax = {};
    allMin = {};
    // init the min/max for all metricColumns
    for (var i=0; i<metricColumns.length; i++){
        
        allMin[metricColumns[i]] = Number.MAX_VALUE;
        allMax[metricColumns[i]] = 0;
    }

    // Helper function for determining which nodes are in brush
    function rectContains(selection, points) {
      if (selection) {
          var isBrushed = selection[0][0] <= points.y && selection[1][0] >= points.y && // Check X coordinate
            selection[0][1] <= points.x && selection[1][1] >= points.x  // And Y coordinate
          //Remember points are at (y,x)
          return isBrushed;
      }
    }

    function highlightNodes(brushedNodes) {
      if (brushedNodes.length == 0) {
          d3.selectAll("circle")
          .style("fill", function(d){  
              var curMetric = d3.select('#metricSelect').property('value');
              colorScale(d.data.metrics[curMetric]);})
          return;
      }
      brushedNodes.transition()
        .duration(duration/100)
        .style("fill", "#89c3e0"); //lightblue "#89c3e0"

    }

    function activateBrush(brushOn) {
      
      if (brushOn > 0) {
          //Turn brush off
          d3.select("#selectButton rect")
              .style("fill", "#ccc")
              .attr('cursor', 'pointer');
          d3.select("#selectButton text")
              .style("fill", "black")
              .attr('cursor', 'pointer');
          d3.selectAll('.brush').remove();
          brushOn = -brushOn;
      }
      else{
        d3.select("#selectButton rect")
            .style("fill", "black")
            .attr('cursor', 'pointer');
        d3.select("#selectButton text")
            .style("fill", "white")
            .attr('cursor', 'pointer');
        var brush = d3.brush()
          .extent([[-20, -20], [2*height, 2*width]])
          .on("brush end", brushmove);
          
        const gBrush = mainG.append('g')
          .attr('class', 'brush')
          .call(brush);
        brushOn = -brushOn;
      }
    }
        
    
    function setColors() {
        //var gyrColors = ["#005f00","#ffd700","#d70000"]; //old hatchet
        var invertColors = ["#005f00", "#00af00", "#00ff00", "#ffd900", "#ff8800", "#ff0000"];
        var regularColors = ["#ff0000", "#ff8800", "#ffd900","#00ff00",  "#00af00", "#005f00"]; //hatchet 2.0
        
        var colorSchemeUsed;
        if (colorScheme == 1) {
            d3.select('#colorButton text')
            .text('Colors: default');
            colorSchemeUsed = regularColors;
        }
        else {
            d3.select('#colorButton text')
            .text('Colors: inverted');
            colorSchemeUsed = invertColors;
        }
        return colorSchemeUsed;
    }
        
    function setColorLegend() {
        var curMetric = d3.select('#metricSelect').property('value');
        var metric_range = allMax[curMetric] - allMin[curMetric];
        var colorScaleDomain = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1].map(function(x){ return x*metric_range + allMin[curMetric]; });
        var colorSchemeUsed = setColors();
        
        d3.selectAll('.legend rect')
            .transition()
            .duration(duration)
            .attr('fill', function(d, i){
                return colorSchemeUsed[i];
            });
        d3.selectAll('.legend text')
            .text((d,i) => {return colorScaleDomain[6-i-1]+' - '+colorScaleDomain[6-i]; })
    } 
        
    // Update colorScale with min and max
    function colorScale(nodeMetric) {
        var curMetric = d3.select('#metricSelect').property('value');
        var colorSchemeUsed = setColors();
        var metric_range = allMax[curMetric] - allMin[curMetric];
        var proportion_of_total = nodeMetric/1;
        
        if (metric_range != 0){
            proportion_of_total = (nodeMetric - allMin[curMetric])/metric_range;
        }
//         return colorSchemeUsed;
        if (proportion_of_total > 0.9) { return colorSchemeUsed[0]; }
        if (proportion_of_total > 0.7) { return colorSchemeUsed[1]; }
        if (proportion_of_total > 0.5) { return colorSchemeUsed[2]; }
        if (proportion_of_total > 0.3) { return colorSchemeUsed[3]; }
        if (proportion_of_total > 0.1) { return colorSchemeUsed[4]; }
        else { return colorSchemeUsed[5]; }
    }
    var treemap = d3.tree().size([(height/2)-margin.top-margin.bottom, width-margin.left-margin.right]);

    d3.select('#treeRootSelect')
        .on('change', function() {
        
        var currentTreeRoot = d3.select("#treeRootSelect").property('value').split("|")[0];
        currentTreeRoot = parseInt(currentTreeRoot);
        if (d3.select("#treeRootSelect").property('value').includes("Show all trees")) {
            // Display all the trees 
            treeData0 = forestData[0];
            treeData1 = forestData[1];
            root0 = d3.hierarchy(treeData0, function(d) { return d.children; });
            root0.x0 = height / 2;
            root0.y0 = 0;
            root1 = d3.hierarchy(treeData1, function(d) { return d.children; });
            root1.x0 = height / 2;
            root1.y0 = 0;
                // Assigns the x and y position for the nodes
            var treeMap0 = treemap(root0);
            var treeMap1 = treemap(root1);
            var newg = mainG.append("g")
                .attr('id', 'group1')
              .attr("transform", "translate(" + margin.left + "," + (height/2) + ")");
            update(root0, treeMap0, g);
            update(root1, treeMap1, newg);
            
        }
        else {
            treeData = forestData[currentTreeRoot];
            console.log("root int", currentTreeRoot, treeData);
            root = d3.hierarchy(treeData, function(d) { return d.children; });
            root.x0 = height / 2;
            root.y0 = 0;

            var treeMap = treemap(root);

            treeMap.descendants().forEach(function(d){
                for (var i=0; i<metricColumns.length; i++){
                    var tempMetric = metricColumns[i];
                    if (d.data.metrics[tempMetric] > allMax[tempMetric]) {
                        allMax[tempMetric] = d.data.metrics[tempMetric];
                    }
                    if (d.data.metrics[tempMetric] < allMin[tempMetric]) {
                        allMin[tempMetric] = d.data.metrics[tempMetric];
                    }
                }

            });

            update(root, treeMap, g);
        }
        
    });
        
    
    
    // Assigns parent, children, height, depth
    root = d3.hierarchy(treeData, function(d) { return d.children; });
    root.x0 = height / 2;
    root.y0 = 0;

    var treeDataInit = treemap(root);
    
    treeDataInit.descendants().forEach(function(d){
        for (var i=0; i<metricColumns.length; i++){
            var tempMetric = metricColumns[i];
            if (d.data.metrics[tempMetric] > allMax[tempMetric]) {
                allMax[tempMetric] = d.data.metrics[tempMetric];
            }
            if (d.data.metrics[tempMetric] < allMin[tempMetric]) {
                allMin[tempMetric] = d.data.metrics[tempMetric];
            }
        }
        
    });
   
    update(root, treeDataInit, g);


    //d3.select(self.frameElement).style("height", "500px");
    //cleanUp(); //katy

    function update(source, treeData, g) {
    
    console.log("source", source, "treeData", treeData);
    var curMetric = d3.select('#metricSelect').property('value');
    setColorLegend();   

    // Compute the new tree layout
    var nodes = treeData.descendants();
    var links = treeData.descendants().slice(1);

    // Normalize for fixed-depth.
    nodes.forEach(function(d) { d.y = d.depth * spreadFactor; });

    const quadtree = d3.quadtree() //TODO optimize 
    .x(d => d.x + margin.left)
    .y(d => d.y + margin.top)
    .addAll(nodes);

    // Update the nodes…
    var node = g.selectAll("g.node")
    .data(nodes, function(d) { return d.id || (d.id = ++i); });

    // Enter any new nodes at the parent's previous position.
    nodeEnter = node.enter().append('g')
    .attr('class', 'node')
    .attr("transform", function(d) { return "translate(" + source.y0 + "," + source.x0 + ")"; })
    .on("click", click)
    .on('dblclick', doubleclick);

    nodeEnter.append("circle")
        .attr('class', 'circleNode')
        .attr("r", 1e-6)
        .style("fill", function(d){ 
        return colorScale(d.data.metrics[curMetric]);});

    nodeEnter.append("text")
        .attr("x", function(d) { return d.children || d._children ? -13 : 13; })
        .attr("dy", ".75em")
        .attr("text-anchor", function(d) { return d.children || d._children ? "end" : "start"; })
        .text(function(d) { return d.data.name; })
        .style("stroke-width", "3px")
        .style("font", "12px monospace");

    //UPDATE
    var nodeUpdate = nodeEnter.merge(node);

    // Transition nodes to their new position.
    nodeUpdate.transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + d.y + "," + d.x + ")"; });

        
    nodeUpdate.select('circle.circleNode')
        .attr("r", 10)
        .style('fill', function(d){
        return colorScale(d.data.metrics[curMetric]); })
        .style("stroke", function(d) { 
        return d._children ? "#89c3e0" : colorScale(d.data.metrics[curMetric]); }) //lightblue
        .style('stroke-width', '3px')
        .attr('cursor', 'pointer');


    // Transition exiting nodes to the parent's new position.
    var nodeExit = node.exit().transition()
        .duration(duration)
        .attr("transform", function(d) { return "translate(" + source.y + "," + source.x + ")"; })
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
    .data(links, function(d) { return d.id; });

    // Enter any new links at the parent's previous position.
    var linkEnter = link.enter().insert("path", "g")
        .attr("class", "link")
        .attr("d", function(d) {
            var o = {x: source.x0, y: source.y0};
            return diagonal(o,o);
        })
        .attr('fill', 'none')
        .attr('stroke', '#ccc')
        .attr('stroke-width', '2px');

    var linkUpdate = linkEnter.merge(link);

    // Transition links to their new position.
    linkUpdate.transition()
        .duration(duration)
        .attr("d", function(d){ return diagonal(d, d.parent); });

    // Transition exiting nodes to the parent's new position.
    var linkExit = link.exit().transition()
        .duration(duration)
        .attr("d", function(d) {
        var o = {x: source.x, y: source.y};
        return diagonal(o,o);
        })
        .remove();

    // Stash the old positions for transition.
    nodes.forEach(function(d) {
        d.x0 = d.x;
        d.y0 = d.y;
        });
    }
    
    //When metricSelect is changed (metric_col)
    d3.select('#metricSelect')
        .on('change', function() {
        changeMetric(allMin, allMax, this.value);
    });
        
    // To pretty print the node data
    function printNodeData(nodeList) {
      var nodeStr = '';

      for (var i=0; i<nodeList.length; i++) {
        nodeStr = nodeStr + nodeList[i].data.name + ': ' + nodeList[i].data.metrics.time + 's (' + nodeList[i].data.metrics["time (inc)"]+'s inc)';
      }
      return nodeStr;
    }
        
    jsNodeSelected = 'Alert: no node(s) selected';
        
    function printQuery(nodeList) {
       
        var leftMostNode = { depth: Number.MAX_VALUE, data: {name : 'default'}};
        var lastNode = "";
        for (var i=0; i<nodeList.length; i++){
            console.log(nodeList[i].data.name);
            if (nodeList[i].depth < leftMostNode.depth) {
                leftMostNode = nodeList[i];
            }
            
        }
        var queryStr = "<no query generated>";
        if (nodeList.length > 1) {
            // This way is for subtrees?
            queryStr = "query = [{'name': '" +leftMostNode.data.name +"'},'*'}]"; 
        }
        else {
            //Single node query
            queryStr = "query = [{'name': '"+leftMostNode.data.name+"'}]";
        }

        return queryStr;
    }
        
    function updateTooltip(nodeList) {
        d3.selectAll("#tooltip text").remove();
        
        var tipText = printNodeData(nodeList);
        var textLength = tipText.length;
        var textLength = tipText.split(' |')[0].length;
        var textHeight = tipText.split(' |').length;
        d3.select("#tooltip rect")
            .transition()
            .duration(duration/100)
            .attr("width", textLength*10);

        var tooltip = d3.select('#tooltip')
        .append("text")
        .attr('x', 200)
        .attr('y', 12)
        .text(tipText)
        .attr('font-family', 'monospace')
        .attr('font-size', '15px');
        
    }

    function click(d) {
        updateTooltip([d]);
        jsNodeSelected = printQuery([d]);
        
        d3.select(this).select('.circleNode').style('stroke', '#aaa');
        var selectedData = d;
        d3.selectAll('.circleNode').style('stroke', function(d){
            if (d == selectedData) return '#aaa';
            else { 
                var curMetric = d3.select('#metricSelect').property('value');
                return d._children ? "#89c3e0" : colorScale(d.data.metrics[curMetric]);}
        });
        console.log("jsNodeSelected",jsNodeSelected);
        //update(d);
    }    
        
    // Toggle children on doubleclick.
    function doubleclick(d) {
        if (d.children) {
              d._children = d.children;
              d.children = null;
          } else {
              d.children = d._children;
              d._children = null;
          }
        update(d);
    }
    
    // Helper function for determining which nodes are in brush
    function rectContains(selection, points) {
        if (selection) {
            isBrushed = selection[0][0] <= points.y && selection[1][0] >= points.y && // Check X coordinate
              selection[0][1] <= points.x && selection[1][1] >= points.x  // And Y coordinate
            //Remember points are at (y,x)
            return isBrushed;
        }
    }

    function highlightNodes(brushedNodes) {
        if (brushedNodes.length == 0) {
            d3.selectAll("circle")
            .style("stroke", function(d){ 
                var curMetric = d3.select('#metricSelect').property('value');
                return colorScale(d.data.metrics[curMetric]);})
            .style("stroke-width", "3px");
            return;
        }
        brushedNodes.transition()
          .duration(duration/100)
          .style("stroke", "#aaa")
          .style("stroke-width", "4px");

    }

    function changeMetric(allMin, allMax) {
        var curMetric = d3.select('#metricSelect').property('value');
        maxtime = allMax[curMetric];
        mintime = allMin[curMetric];
        var nodes = d3.selectAll(".circleNode");
        
        setColorLegend();
        
        d3.selectAll(".circleNode")
               .transition()
               .duration(duration)
               .style("fill", function(d){ 
                  return colorScale(d.data.metrics[curMetric]);
                })
               .style("stroke", function(d){ 
                  return colorScale(d.data.metrics[curMetric]);
                });
       
    }

    function brushmove() {
        const { selection } = d3.event;

        if (!selection) {
            highlightNodes([]);
        return;
        }
        // Slow, unoptimized
        const brushedNodes = d3.selectAll("circle")
        .filter(d => rectContains(selection, d));

        const brushedData = [];
        brushedNodes.each(d => brushedData.push(d));
      
        highlightNodes(brushedNodes);
        updateTooltip(brushedData);
        jsNodeSelected = printQuery(brushedData);
        console.log("jsNodeSelected", jsNodeSelected);
        /* Optimized: https://peterbeshai.com/blog/2016-12-03-brushing-in-scatterplots-with-d3-and-quadtrees/*/

    }
        
      
  })
})(element);











