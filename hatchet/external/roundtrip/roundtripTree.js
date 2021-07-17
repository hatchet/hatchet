//d3.v4
(function (element) {
    require(['https://d3js.org/d3.v4.min.js'], function (d3) {

        const globals = Object.freeze({
            UNIFIED: 0,
            DEFAULT: 0,
            signals: {
                CLICK: "CLICK",
                DBLCLICK: "DBLCLICK",
                BRUSH: "BRUSH",
                TOGGLEBRUSH: "TOGGLEBRUSH",
                COLLAPSE: "COLLAPSE",
                METRICCHANGE: "METRICCHANGE",
                TREECHANGE: "TREECHANGE",
                COLORCLICK: "COLORCLICK",
                LEGENDCLICK: "LEGENDCLICK",
                ZOOM: "ZOOM",
                STOREINITIALLAYOUTOFFSETS: "STORE",
                MASSPRUNE: "MASSPRUNE",
                RESETVIEW: "RESET"
            },
            layout: {
                margin: {top: 20, right: 20, bottom: 20, left: 20},
            },
            duration: 750
        });

        jsNodeSelected = "['*']";

        const makeColorManager = function(model) {
            // TODO: Move the colors to a color.js.
            const REGULAR_COLORS = [
                ['#006d2c', '#31a354', '#74c476', '#a1d99b', '#c7e9c0', '#edf8e9'], //green
                ['#a50f15', '#de2d26', '#fb6a4a', '#fc9272', '#fcbba1', '#fee5d9'], //red
                ['#08519c', '#3182bd', '#6baed6', '#9ecae1', '#c6dbef', '#eff3ff'], //blue
                ['#54278f', '#756bb1', '#9e9ac8', '#bcbddc', '#dadaeb', '#f2f0f7'], //purple
                ['#a63603', '#e6550d', '#fd8d3c', '#fdae6b', '#fdd0a2', '#feedde'], //orange
                ['#252525', '#636363', '#969696', '#bdbdbd', '#d9d9d9', '#f7f7f7']
            ];

            const CAT_COLORS = ["#3366cc", "#dc3912", "#ff9900", "#109618", "#990099", "#0099c6", "#dd4477", "#66aa00", "#b82e2e", "#316395", "#994499", "#22aa99", "#aaaa11", "#6633cc", "#e67300", "#8b0707", "#651067", "#329262", "#5574a6", "#3b3eac"];

            const _regularColors = {
                0: REGULAR_COLORS,
                1: REGULAR_COLORS.map((colorArr) => [].concat(colorArr).reverse()),
                2: CAT_COLORS,
                3: [].concat(CAT_COLORS).reverse()
            };

            const ALL_COLORS = ['#d73027', '#fc8d59', '#fee090', '#e0f3f8', '#91bfdb', '#4575b4'];

            const _allTreesColors = {
                0: ALL_COLORS,
                1: [].concat(ALL_COLORS).reverse(),
                2: CAT_COLORS,
                3: [].concat(CAT_COLORS).reverse(),
            };

            const _state = model.state;
            const _forestMinMax = model.data["forestMinMax"];
            const _forestStats = model.data["forestStats"];
            const _metricColumns = model.data["metricColumns"];
            const _attributeColumns = model.data["attributeColumns"];

            return {
                setColors: function(treeIndex) {
                    const curMetric = _state["selectedMetric"];
                    const colorScheme = _state["colorScheme"];

                    if (_metricColumns.includes(curMetric)) {
                        if (treeIndex == -1) return _allTreesColors[colorScheme];
                        else return _regularColors[colorScheme][treeIndex % REGULAR_COLORS.length];
                    } else if (_attributeColumns.includes(curMetric)) {
                        if (treeIndex == -1) return _allTreesColors[2 + colorScheme];
                        else return _regularColors[2 + colorScheme];
                    }
                },
                getLegendDomains: function(treeIndex){
                    /**
                     * Sets the min and max of the legend. 
                     * 
                     * @param {Int} treeIndex - The index of the current tree's legend being set
                     */

                    const curMetric = _state["selectedMetric"];

                    // so hacky: need to fix later
                    if (model.data["legends"][_state["legend"]].includes("Unified")) {
                        treeIndex = -1;
                    }

                    let metricMinMax;
                    if (treeIndex === -1) { //unified color legend
                        metricMinMax = _forestMinMax[curMetric]
                    } else { // individual color legend
                        metricMinMax = _forestStats[treeIndex][curMetric]
                    }

                    let colorScaleDomain;
                    if (_metricColumns.includes(curMetric)) {
                        let metricRange = metricMinMax.max - metricMinMax.min;
                        colorScaleDomain = [0, 0.1, 0.3, 0.5, 0.7, 0.9, 1].map(function(x) {
                            return x * metricRange + metricMinMax.min;
                        });
                    } else if (_attributeColumns.includes(curMetric)) {
                        colorScaleDomain = metricMinMax;
                    }

                    return colorScaleDomain;
                },
                getColorLegend: function(treeIndex) {
                    /**
                     * Gets the color scheme used for a legend, contigent on individual tree-specific schemes or one unified color scheme.
                     * 
                     * @param {Int} treeIndex - The index of the current tree's legend being set
                     */
                
                    //hacky need to fix later
                    if (model.data["legends"][_state["legend"]].includes("Unified")) {
                        treeIndex = -1;
                    }

                    return this.setColors(treeIndex);
                },
                calcColorScale: function(nodeMetric, treeIndex) {
                    var curMetric = _state["primaryMetric"];
                    var colorSchemeUsed = this.setColors(treeIndex);
                    
                    if (treeIndex == -1) {
                        var metric_range = _forestMinMax[curMetric].max - _forestMinMax[curMetric].min;
                        var proportion_of_total = (nodeMetric - _forestMinMax[curMetric].min) / metric_range;
                    } else {
                        var metric_range = _modelForestStats[treeIndex][curMetric].max - _modelForestStats[treeIndex][curMetric].min;
                        var proportion_of_total = nodeMetric / 1;
    
                        if (metric_range != 0) {
                            proportion_of_total = (nodeMetric - _modelForestStats[treeIndex][curMetric].min) / metric_range;
                        }
                    }
    
                    if (proportion_of_total > 0.9) {
                        return colorSchemeUsed[0];
                    }

                    // Decide the color scheme for the settings.
                    const colorSchemeUsed = this.setColors(treeIndex);
                    const curMetric = _state["selectedMetric"];

                    // Get the suitable data based on the Legend settings.
                    let _d;
                    if (treeIndex === -1) {
                        _d = _forestMinMax[curMetric];
                    } else {
                        _d = _forestStats[treeIndex][curMetric];
                    }

                    if (_attributeColumns.includes(curMetric)) {
                        const nodeMetric = nodeData.attributes[curMetric];
                        const indexOfMetric = _d.indexOf(nodeMetric);
                        return colorSchemeUsed[indexOfMetric];
                    } else if (_metricColumns.includes(curMetric)) {
                        const nodeMetric = nodeData.metrics[curMetric];

                        // Calculate the range of min/max.
                        const metricRange = _d.max - _d.min;

                        // Set colorMap for runtime metrics.
                        let proportion_of_total = nodeMetric / 1;

                        // If min != max, we can split the runtime into bins.
                        if (metricRange != 0) {
                            proportion_of_total = (nodeMetric - _d.min) / metricRange;
                        }

                        // TODO: Generalize to any bin size.
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
                }
            }
        }

        // This is the makeSignaller from class
        var makeSignaller = function() {
            let _subscribers = []; // Private member

            // Return the object that's created
            return {
                // Register a function with the notification system
                add: function(handlerFunction) {_subscribers.push(handlerFunction); },

                // Loop through all registered function and call them with passed
                // arguments
                notify: function(args) {
                    for (var i = 0; i < _subscribers.length; i++) {
                        _subscribers[i](args);
                    }
                }
            };
        }

        // Create an object that handles user interaction and events
        var createController = function(model) {
            var _model = model;

            return {
                // All types of events run through a central dispatch
                // function. The dispatch function decides what to do.
                dispatch: function(evt) {
                    switch(evt.type) {
                        case (globals.signals.CLICK):
                            _model.updateSelected([evt.node]);
                            break;
                        case (globals.signals.DBLCLICK):
                            _model.handleDoubleClick(evt.node,evt.tree);
                            break;
                        case(globals.signals.TOGGLEBRUSH):
                            _model.toggleBrush();
                            break;
                        case (globals.signals.BRUSH):
                            _model.setBrushedPoints(evt.selection, evt.end);
                            break;
                        case (globals.signals.METRICCHANGE):
                            _model.changeMetric(evt.newMetric, evt.source);
                            break;
                        case(globals.signals.COLORCLICK):
                            _model.changeColorScheme();
                            break;
                        case(globals.signals.TREECHANGE):
                            _model.updateActiveTrees(evt.display);
                            break;
                        case(globals.signals.LEGENDCLICK):
                            _model.updateLegends();
                            break;
                        case(globals.signals.ZOOM):
                            _model.updateNodeLocations(evt.index, evt.transformation);
                            break;
                        case(globals.signals.STOREINITIALLAYOUTOFFSETS):
                            _model.storeXOffsets(evt.index, evt.globalXOffset, evt.localXOffset);
                            break;
                        case(globals.signals.MASSPRUNE):
                            _model.pruneTree(evt.threshold);
                            break;
                        case(globals.signals.RESETVIEW):
                            _model.resetView();
                            break;
                        default:
                            console.log('Unknown event type', evt.type);
                    }
                }
            };
        }


        var createModel = function() {
            var _observers = makeSignaller();

            //initialize default data and state
            var _data = {
                            "trees":[],
                            "legends": ["Unified", "Indiv."],
                            "colors": ["Default", "Inverted"],
                            "forestData": null,
                            "rootNodeNames": [],
                            "numberOfTrees": 0,
                            "metricColumns": [],
                            "forestMinMax": [],
                            "aggregateMinMax": {},
                            "forestMetrics": [],
                            "metricLists":[]
                        };

            var _state = {
                            "selectedNodes":[], 
                            "collapsedNodes":[],
                            "primaryMetric": null,
                            "secondaryMetric": null,
                            "lastClicked": null,
                            "legend": 0,
                            "colorScheme": 0,
                            "brushOn": -1,
                            "hierarchyUpdated": true,
                            "cachedThreshold": 0,
                            "outlierThreshold": 0
                        };

            //setup model
            var cleanTree = argList[0].replace(/'/g, '"');
            var cleanTree = cleanTree.replace(/nan/g, '\"nan\"');
            var _forestData = JSON.parse(cleanTree);

            _data.hierarchy = [];
            _data.immutableHierarchy = [];
            _data.maxHeight = 0;
            _data.rootNodeNames = [];
            _data.rootNodeNames.push("Show all trees");
            _data.numberOfTrees = _forestData.length;
            _data.metricColumns = d3.keys(_forestData[0].metrics);
            
            
            for(var metric = 0; metric < _data.metricColumns.length; metric++){
                metricName = _data.metricColumns[metric];
                //remove private metric
                if(_data.metricColumns[metric][0] == '_'){
                    _data.metricColumns.splice(metric, 1);
                }
                else{
                    //setup aggregrate min max for metric
                    _data.aggregateMinMax[metricName] = {min: Number.MAX_VALUE, max: Number.MIN_VALUE};
                }
            }
            console.log(_data.aggregateMinMax);
            // pick the first metric listed to color the nodes
            _state.primaryMetric = _data.metricColumns[0];
            _state.secondaryMetric = _data.metricColumns[1];
            _state.activeTree = "Show all trees";
            _state.treeXOffsets = [];


            //Stats functions
            function _getListOfMetrics(h){
                //Gets a list of metrics with 0s removed
                // 0s in hpctoolkit are too numerous and they
                // throw off outlier calculations
                var list = [];
                
                h.each(d=>{
                    if(d.data.metrics[_state.primaryMetric] != 0){
                        list.push(d.data.metrics)
                    }
                })

                return list;
            }

            function _asc(arr){
                return arr.sort((a,b) => a[_state.primaryMetric]-b[_state.primaryMetric])
            }
            
            function _quantile(arr, q){
                const sorted = _asc(arr);
                const pos = (sorted.length - 1) * q;
                const base = Math.floor(pos);
                const rest = pos - base;
                if (sorted[base + 1] !== undefined) {
                    return sorted[base][_state.primaryMetric] + rest * (sorted[base + 1][_state.primaryMetric] - sorted[base][_state.primaryMetric]);
                } else {
                    return sorted[base][_state.primaryMetric];
                }
            }

            function _getIQR(arr){
                if(arr.length != 0){
                    var q25 = _quantile(arr, .25);
                    var q75 = _quantile(arr, .75);
                    var IQR = q75 - q25;
                    
                    return IQR;
                }
                
                return NaN;
            }

            function _setOutlierFlags(h){
                var outlierScalar = 1.5;
                var upperOutlierThreshold = Number.MAX_VALUE;
                var lowerOutlierThreshold = Number.MIN_VALUE;

                var metrics = _getListOfMetrics(h);

                var IQR = _getIQR(metrics);

                if(!isNaN(IQR)){
                    upperOutlierThreshold = _quantile(metrics, .75) + (IQR * outlierScalar);
                    lowerOutlierThreshold = _quantile(metrics, .25) - (IQR * outlierScalar);
                } 

                h.each(function(node){
                    var metric = node.data.metrics[_state.primaryMetric];
                    if(metric != 0 &&   //zeros are not interesting outliers
                       metric >= upperOutlierThreshold || 
                       metric <= lowerOutlierThreshold){
                        node.data.outlier = 1;
                    }
                    else{
                        node.data.outlier = 0;
                    }
                })

            }

            //Model support functions
            function _getAggregateMetrics(h){
                let agg = {};
                
                for(metric of _data.metricColumns){
                    if(!metric.includes("(inc)")){
                        h.sum(d=>d.metrics[metric]);
                        agg[metric] = h.value;
                    }
                    else{
                        agg[metric] = h.data.metrics[metric];
                    }
                }

                return agg;
            }


            function _visitor(root, condition){
                if(root.children){
                    var dummyHolder = null;
                    var aggregateMetrics = {};
                    for(var childNdx = root.children.length-1; childNdx >= 0; childNdx--){
                        var child = root.children[childNdx];

                        //condition where we remove child
                        if(child.value < condition){
                            if(!root._children){
                                root._children = [];
                            }

                            if(!dummyHolder){
                                dummyHolder = child.copy();
                                dummyHolder.depth = child.depth;
                                dummyHolder.height = child.height;
                                dummyHolder.children = null;
                            }

                            root._children.push(child);
                            root.children.splice(childNdx, 1);
                        }
                    }
                    
                    if (root._children && root._children.length > 0){
                        dummyHolder.data.elided = root._children;        
                        dummyHolder.data.dummy = true;
                        dummyHolder.data.aggregate = false;
                        dummyHolder.parent = root;
                        dummyHolder.data.outlier = 0;
                        root.children.push(dummyHolder);

                        //initialize the aggregrate metrics for summing
                        for(metric of _data.metricColumns){
                            aggregateMetrics[metric] = 0;
                        }

                        for(elided of dummyHolder.data.elided){
                            var aggMetsForChild = _getAggregateMetrics(elided)
                            for(metric of _data.metricColumns){
                                aggregateMetrics[metric] += aggMetsForChild[metric];
                            }
                        }

                        //get the overall min and max of aggregate metrics
                        // for scales
                        for(metric of _data.metricColumns){
                            console.log(metric, _data.aggregateMinMax[metric]);
                            if (aggregateMetrics[metric] > _data.aggregateMinMax[metric].max){
                                _data.aggregateMinMax[metric].max = aggregateMetrics[metric];
                            }
                            if(aggregateMetrics[metric] < _data.aggregateMinMax[metric].min){
                                _data.aggregateMinMax[metric].min = aggregateMetrics[metric];
                            }
                        }

                        dummyHolder.data.aggregateMetrics = aggregateMetrics;

                        if(dummyHolder.data.aggregateMetrics[_state.primaryMetric] != 0){
                            dummyHolder.data.aggregate = true;
                        }
                    }


                    for(var child of root.children){
                        _visitor(child, condition);
                    }

                    if(root.children.length == 0){
                        root.children = null;
                    }
                }
            }


            //problems with actively modifying the tree
            // may need to build a custom each
            function _pruneZerosFromTree(condition){
                for(var i = 0; i < _data.numberOfTrees; i++){
                    var h = _data.immutableHierarchy[i].copy().sum(d => d.metrics[_state.primaryMetric]);
                    if (condition != 0){   
                        _visitor(h, 1);
                    }
                    _data.hierarchy[i] = h;
                }
            }

            function _aggregateTreeData(){
                for(var i = 0; i < _data.numberOfTrees; i++){
                    var h = _data.hierarchy[i].copy().sum(d => d.outlier);
                    _visitor(h, 1);
                    _data.hierarchy[i] = h;

                }
            }

            // HELPER FUNCTION DEFINTIONS
            function _printNodeData(nodeList) {
                /**
                  * To pretty print the node data as a IPython table
                  * 
                  * @param {Array} nodeList - An array of selected nodes for formatting
                  */
                
                var nodeStr = '<table><tr><td>name</td>';
                var numNodes = nodeList.length;
                var metricColumns = _data["metricColumns"];

                //lay the nodes out in a table
                for (var i = 0; i < metricColumns.length; i++) {
                    nodeStr += '<td>' + metricColumns[i] + '</td>';
                }
                nodeStr += '</tr>';
                for (var i = 0; i < numNodes; i++) {
                    nodeStr += "<tr>"
                    for (var j = 0; j < metricColumns.length; j++) {
                        if (j == 0) {
                            nodeStr += `<td>${nodeList[i].data.frame.name}</td>`;
                        }
                        nodeStr += `<td>${nodeList[i].data.metrics[metricColumns[j]]}</td>`
                    }
                    nodeStr += '</tr>'
                }
                nodeStr = nodeStr + '</table>';
                return nodeStr;
            }

            function _printQuery(nodeList) {
                /**
                  * Prints out user selected nodes as a query string which can be used in the GraphFrame.filter() function.
                  * 
                  * @param {Array} nodeList - An array of selected nodes for formatting
                  */
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


            //Do processing required for model setup
            for (var treeIndex = 0; treeIndex < _forestData.length; treeIndex++) {
                _data.immutableHierarchy.push(d3.hierarchy(_forestData[treeIndex], d => d.children));
                _data.hierarchy.push(d3.hierarchy(_forestData[treeIndex], d => d.children));
                if (_data.immutableHierarchy[treeIndex].height > _data.maxHeight){
                    _data.maxHeight = _data.immutableHierarchy[treeIndex].height;
                }
                _setOutlierFlags(_data.immutableHierarchy[treeIndex]);
            }
            _state.lastClicked = _data.hierarchy[0];
            

            // _pruneZerosFromTree(1);
            _aggregateTreeData();

            //get the max and min metrics across the forest
            // and for each individual tree
            var _forestMetrics = [];
            var _forestMinMax = {}; 

            for (var index = 0; index < _data.numberOfTrees; index++) {
                var thisTree = _forestData[index];
                let mc = _data.metricColumns;

                // Get tree names for the display select options
                _data["rootNodeNames"].push(thisTree.frame.name);

                var thisTreeMetrics = {};

                for (var j = 0; j < mc.length; j++) {
                    thisTreeMetrics[mc[j]] = {};
                    thisTreeMetrics[mc[j]]["min"] = Number.MAX_VALUE;
                    thisTreeMetrics[mc[j]]["max"] = 0;

                    //only one run time
                    if(index == 0){
                        _forestMinMax[mc[j]] = {};
                        _forestMinMax[mc[j]]["min"] = Number.MAX_VALUE;
                        _forestMinMax[mc[j]]["max"] = 0;
                    }
                }

                _data['hierarchy'][index].each(function (d) {
                    for (var i = 0; i < mc.length; i++) {
                        var tempMetric = mc[i];
                        if (d.data.metrics[tempMetric] > thisTreeMetrics[tempMetric].max) {
                            thisTreeMetrics[tempMetric].max = d.data.metrics[tempMetric];
                        }
                        if (d.data.metrics[tempMetric] < thisTreeMetrics[tempMetric].min) {
                            thisTreeMetrics[tempMetric].min = d.data.metrics[tempMetric];
                        }
                        if (d.data.metrics[tempMetric] > _forestMinMax[tempMetric].max) {
                            _forestMinMax[tempMetric].max = d.data.metrics[tempMetric];
                        }
                        if (d.data.metrics[tempMetric] < _forestMinMax[tempMetric].min) {
                            _forestMinMax[tempMetric].min = d.data.metrics[tempMetric];
                        }
                    }
                });

                _forestMetrics.push(thisTreeMetrics);
            }
            _data.forestMetrics = _forestMetrics;

            // Global min/max are the last entry of forestMetrics;
            _data.forestMinMax = _forestMinMax;
            _data.forestMetrics.push(_forestMinMax);




            /* Class object created from call to createModel */
            return{
                data: _data,
                state: _state,
                register: function(s){
                    /**
                     * Registers a signaller (a callback function) to be run with _observers.notify()
                     * 
                     * @param {Function} s - (a callback function) to be run with _observers.notify()
                     */
                    _observers.add(s);
                },
                addTree: function(tm){
                    /**
                     * Pushes a tree into the model.
                     * 
                     * @param {Object} tm - A d3 tree constructed from a d3 hierarchy
                     */

                    _data['trees'].push(tm);
                },
                getTree: function(index){
                    /**
                     * Retrieves a tree from the model.
                     * 
                     * @param {Number} index - The index of the tree we want to get
                     */
                    return _data['trees'][index];
                },
                getNodesFromMap: function(index){
                    /**
                     * Retrieves tree nodes from the model
                     * 
                     * @param {Number} index - The index of the tree nodes we want to get
                     */
                    return _data['trees'][index].descendants();
                },
                getLinksFromMap: function(index){
                    /**
                     * Retrieves tree links from the model
                     * 
                     * @param {Number} index - The index of the tree links we want to get
                     */
                    return _data['trees'][index].descendants().slice(1);
                },
                updateNodes: function(index, f){
                    /**
                     * Updates the nodes in the model according to the passed in callback function.
                     *
                     * @param {Number} index - The index of the tree we are updating
                     * @param {Function} f - The callback function being applied to the nodes
                     */
                    f(_data['trees'][index].descendants());
                },
                updateforestStats: function(index){
                    /**
                     * Updates the local maximum and minimum metrics for a single tree in the forest. 
                     * Updates the global maximum and minimum metrics across all trees in our forest.
                     * Stores these values in the model.
                     *
                     * @param {Number} index - The index of the tree we are updating
                     */

                    var curTreeData = _forestStats[index];
                    for(let metric of  _data["metricColumns"]) {
                        // get local minimum and maximum for our current tree
                        // for each metric
                        _data['trees'][index].descendants().forEach(function (d) {
                            curTreeData[metric].max = Math.max(curTreeData[metric].max, d.data.metrics[metric]);
                            curTreeData[metric].min = Math.min(curTreeData[metric].min, d.data.metrics[metric]);
                        });

                        //Update global minimum and maximum per metric
                        _forestMinMax[metric].max = Math.max(_forestMinMax[metric].max, curTreeData[metric].max);
                        _forestMinMax[metric].min = Math.min(_forestMinMax[metric].min, curTreeData[metric].min);
                    }

                        _data["forestStats"] = _forestStats;
                        _data["forestMinMax"] = _forestMinMax;
                },
                pruneTree: function(threshold){
                    _pruneDefaultTree(threshold);

                    _state.cachedThreshold = threshold;
                    _state.hierarchyUpdated = true;

                    _observers.notify();
                },
                storeXOffsets: function(index, globalOffset, localOffset){
                    var obj = {
                        global: globalOffset,
                        local: localOffset
                    }
                },
                updateSelected: function(nodes){
                    /**
                     * Updates which nodes are "Selected" by the user in the model
                     *
                     * @param {Array} nodes - A list of selected nodes
                     */

                    _state['selectedNodes'] = nodes;
                    this.updateTooltip(nodes);

                    if(nodes.length > 0 && nodes[0]){
                        jsNodeSelected = _printQuery(nodes);
                    } else {
                        jsNodeSelected = "['*']";
                    }
                    
                    _observers.notify();
                },
                handleDoubleClick: function(d){
                    /**
                     * Handles the model functionlaity of hiding and un-hiding subtrees
                     * on double click
                     *
                     * @param {Object} d - The node which was double clicked
                     */

                    // if the node is not already collapsed
                    // keep track of collapsed nodes
                    if (! _state["collapsedNodes"].includes(d) ){
                        _state["collapsedNodes"].push(d);
                    }
                    else{
                        var index = _state["collapsedNodes"].indexOf(d);
                        _state["collapsedNodes"].splice(index, 1);
                    }

                    //this is kind of a hack for this paradigm
                    // but it updates the passed data directly
                    // and hides children nodes triggering update
                    // when view is re-rendered
                    if (d.children) {
                        d._children = d.children;
                        d.children = null;
                    } else {
                        d.children = d._children;
                        d._children = null;
                    }

                    _state["lastClicked"] = d;
                    
                    _observers.notify();
                },
                toggleBrush: function(){
                    /**
                     * Toggles the brushing functionality with a button click
                     *
                     */

                    _state["brushOn"] = -_state["brushOn"];
                    _observers.notify();
                },
                setBrushedPoints(selection, end){
                    /**
                     * Calculates which nodes are in the brushing area.
                     * 
                     * @param {Array} selection - A d3 selection matrix with svg coordinates showing the selected space
                     * @param {Boolean} end - A variable which tests if the brushing is over or not
                     *
                     */

                    var brushedNodes = [];

                    if(selection){
                        //calculate brushed points
                        for(var i = 0; i < _data["numberOfTrees"]; i++){
                            var nodes = _data['trees'][i].descendants();
                            nodes.forEach(function(d){
                                if(selection[0][0] <= d.yMainG && selection[1][0] >= d.yMainG 
                                    && selection[0][1] <= d.xMainG && selection[1][1] >= d.xMainG){
                                    brushedNodes.push(d);
                                }
                            })
                        }

                        //update if end
                        if(end){
                            //call update selected
                            this.updateSelected(brushedNodes);
                        }
                    }
                    else{
                        this.updateSelected([]);
                    }
                    
                },
                updateTooltip: function(nodes){
                    if(nodes.length > 0 && nodes[0]){
                        var longestName = 0;
                        nodes.forEach(function (d) {
                            var nodeData = d.data.frame.name + ': ' + d.data.metrics.time + 's (' + d.data.metrics["time (inc)"] + 's inc)';
                            if (nodeData.length > longestName) {
                                longestName = nodeData.length;
                            }
                        });
                        _data["tipText"] = _printNodeData(nodes);
                    } 
                    else{
                        _data["tipText"] = '<p>Click a node or "Select nodes" to see more info</p>';
                    }
                },
                changeMetric: function(newMetric, source){
                      /**
                     * Changes the currently selected metric in the model.
                     * 
                     * @param {String} newMetric - the most recently selected metric
                     *
                     */

                    if(source.includes("primary")){
                        _state.primaryMetric = newMetric;
                    } 
                    else if(source.includes("secondary")){
                        _state.secondaryMetric = newMetric;
                    }
                    
                    //need to cache last value of 
                    // _pruneDefaultTree(_state.cachedThreshold);
                    // _state.hierarchyUpdated = true;

                    _observers.notify();
                },
                changeColorScheme: function(){
                    /**
                     * Changes the current color scheme to inverse or regular. Updates the view
                     *
                     */

                    //loop through the possible color schemes
                    _state["colorScheme"] = (_state["colorScheme"] + 1) % _data["colors"].length;
                    _observers.notify();
                },
                updateLegends: function(){
                    /**
                     * Toggles between divergent or unified legends. Updates the view
                     *
                     */
                    //loop through legend configruations
                    _state["legend"] = (_state["legend"] + 1) % _data["legends"].length;
                    _observers.notify();
                },
                updateActiveTrees: function(activeTree){
                    /**
                     * Sets which tree is currently "active" in the model. Updates the view.
                     *
                     */
                    _state["activeTree"] = activeTree;
                    _observers.notify();
                },
                resetView: function(){
                    _state.resetView = true;
                    _observers.notify();
                }
            }
        }

        var createMenuView = function(elem, model){
            /**
             * View class for the menu portion of the visualization
             * 
             * @param {DOMElement} elem - The current cell of the calling jupyter notebook
             * @param {Model} model - The model object
             */

            let _observers = makeSignaller();
            var rootNodeNames = model.data["rootNodeNames"];
            var metricColumns = model.data["metricColumns"];
            const attributeColumns = model.data["attributeColumns"];
            const allColumns = metricColumns.concat(attributeColumns);
            var brushOn = model.state["brushOn"];
            var curColor = model.state["colorScheme"];
            var colors = model.data["colors"];        
            var curLegend = model.state["legend"];
            var legends = model.data["legends"];

            //initialize bounds for svg
            var width = element.clientWidth - globals.layout.margin.right - globals.layout.margin.left;
            var height = globals.treeHeight * (model.data["numberOfTrees"] + 1);

            // ----------------------------------------------
            // Create HTML interactables
            // ----------------------------------------------

            const htmlInputs = d3.select(elem).insert('div', '.canvas').attr('class','html-inputs');
            //setup scale
            var _svgButtonOffset = 0;


            function _addNewMenuButton(id, text, click){
                //refactor to remove repeated code and make it easier to add buttons
                // with a more dynamic offset from the right
                var buttonPad = 5;
                var textPad = 3;
                var button = _svg.append('g')
                    .attr('id', id)
                    .append('rect')
                    .attr('height', '15px')
                    .attr('x', _svgButtonOffset).attr('y', 0).attr('rx', 5)
                    .style('fill', '#ccc')
                    .on('click', click);

                var buttonText = d3.select(elem).select('#'+id).append('text')
                        .attr("x", _svgButtonOffset + textPad)
                        .attr("y", 12)
                        .text(text)
                        .attr("font-family", "sans-serif")
                        .attr("font-size", "12px")
                        .attr('cursor', 'pointer')
                        .on('click', click);
                
                var width = buttonText.node().getBBox().width + 2*textPad;
                    
                button.attr('width', width);

                _svgButtonOffset += width + buttonPad;
            }



            htmlInputs.append('label').attr('for', 'primaryMetricSelect').text('Color by:');
            var metricInput = htmlInputs.append("select") //element
                    .attr("id", "primaryMetricSelect")
            var metricInput = d3.select(elem).append("select") //element
                    .attr("id", "primaryMetricSelect")
                    .selectAll('option')
                    .data(metricColumns)
                    .enter()
                    .append('option')
                    .text(d => d)
                    .attr('value', d => d);
            document.getElementById("primaryMetricSelect").style.margin = "10px 10px 10px 0px";

            d3.select(elem).append('label').attr('for', 'secondaryMetricSelect').text('Radius:');
            var metricInputRadius = d3.select(elem).append("select") //element
                    .attr("id", "secondaryMetricSelect")
                    .selectAll('option')
                    .data(metricColumns)
                    .enter()
                    .append('option')
                    .attr('selected', (d,i) => i == 1 ? "selected" : null)
                    .text(d => d)
                    .attr('value', d => d);
            document.getElementById("secondaryMetricSelect").style.margin = "10px 10px 10px 0px";


            htmlInputs.append('label').style('margin', '0 0 0 10px').attr('for', 'treeRootSelect').text(' Display:');
            var treeRootInput = htmlInputs.append("select") //element
                    .attr("id", "treeRootSelect")
                    .selectAll('option')
                    .data(rootNodeNames)
                    .enter()
                    .append('option')
                    .attr('selected', d => d.includes('Show all trees') ? "selected" : null)
                    .text(d => d)
                    .attr('value', (d, i) => i + "|" + d);

            document.getElementById("treeRootSelect").style.margin = "10px 10px 10px 10px";

            d3.select(elem).select('#treeRootSelect')
                    .on('change', function () {
                        _observers.notify({
                            type: globals.signals.TREECHANGE,
                            display: this.value
                        });
                    });
            
            // ----------------------------------------------
            // Create SVG and SVG-based interactables
            // ----------------------------------------------

            
            d3.select(elem).append('label').style('margin', '0 0 0 10px').attr('for', 'test_pruning').text(' Prune Less Than:');
            d3.select(elem).append("select")
                .attr("id", "test_pruning")
                .selectAll("option")
                .data([0, 1, 60000, 100000])
                .enter()
                .append('option')
                .text(d => d)
                .attr("value", d=>(d));

            document.getElementById("test_pruning").style.margin = "10px 10px 10px 10px";


            d3.select(elem).select('#test_pruning')
                .on('change', function(){
                    _observers.notify({
                        type: globals.signals.MASSPRUNE,
                        threshold: this.value
                    });
                })


            //make an svg in the scope of our current
            // element/drawing space
            var _svg = d3.select(element).append("svg") //element
                .attr("class", "canvas")
                .attr("width", width + globals.layout.margin.right + globals.layout.margin.left)
                .attr("height", height + globals.layout.margin.top + globals.layout.margin.bottom);


            _addNewMenuButton('selectButton', 'Select nodes',  
                function () {
                    _observers.notify({
                        type: globals.signals.TOGGLEBRUSH
                    })
                });
            
            _addNewMenuButton('colorButton', 
                function(){
                    return `Colors: ${model.data["colors"][model.state["colorScheme"]]}`;
                }, 
                function () {
                    _observers.notify({
                        type: globals.signals.COLORCLICK
                    })
                });

            _addNewMenuButton('unifyLegends', 
                function(){ 
                    return `Legends: ${model.data["legends"][model.state["legend"]]}`;
                }, 
                function () {
                    _observers.notify({
                        type: globals.signals.LEGENDCLICK
                    });
                });
            
            _addNewMenuButton('resetZoom', 'Reset View', 
                function () {
                    _observers.notify({
                        type: globals.signals.RESETVIEW
                    });
                });

            var mainG = _svg.append("g")
                .attr('id', "mainG")
                .attr("transform", "translate(" + globals.layout.margin.left + "," + globals.layout.margin.top + ")");

           // ----------------------------------------------
            // Define and set d3 callbacks for changes
            // ----------------------------------------------
            var brush = d3.brush()
                    .extent([[0, 0], [2 * width, 2 * (height + globals.layout.margin.top + globals.layout.margin.bottom)]])
                    .on('brush', function(){
                        _observers.notify({
                            type: globals.signals.BRUSH,
                            selection: d3.event.selection,
                            end: false
                        })
                    })
                    .on('end', function(){
                        _observers.notify({
                            type: globals.signals.BRUSH,
                            selection: d3.event.selection,
                            end: true
                        })
                    });

            const gBrush = d3.select("#mainG").append('g')
                    .attr('class', 'brush')
                    .call(brush);
            
                
            //When metricSelect is changed (metric_col)
            d3.select(element).select('#primaryMetricSelect')
                .on('change', function () {
                    _observers.notify({
                        type: globals.signals.METRICCHANGE,
                        newMetric: this.value,
                        source: d3.select(this).attr('id')
                    })
                });

            d3.select(element).select('#secondaryMetricSelect')
                .on('change', function(){
                    _observers.notify({
                        type:globals.signals.METRICCHANGE,
                        newMetric: this.value,
                        source: d3.select(this).attr('id')
                    })
                })
            
            var brushButton = d3.select('#selectButton');
            var colorButton = d3.select('#colorButton');
            var unifyLegends = d3.select('#unifyLegends');
            var brushButtonText = brushButton.select('text');
            var colorButtonText = colorButton.select('text');
            var legendText = unifyLegends.select('text');


            

            return{
                register: function(s){
                    _observers.add(s);
                },
                render: function(){
                    brushOn = model.state["brushOn"];
                    curColor = model.state["colorScheme"];
                    colors = model.data["colors"];
                    curLegend = model.state["legend"];
                    legends = model.data["legends"];

                    //Remove brush and reset if active
                    d3.selectAll('.brush').remove();

                    //updates
                    brushButton.style("fill", function(){ 
                        if(brushOn > 0){
                            return "black";
                        }
                        else{
                            return "#ccc";
                        }
                    })
                    .attr('cursor', 'pointer');

                    brushButtonText.style("fill", function(){
                        if(brushOn > 0){
                            return "white";
                        }
                        else{
                            return "black";
                        }
                    })
                    .attr('cursor', 'pointer');


                    //add brush if there should be one
                    if(brushOn > 0){
                        d3.select("#mainG").append('g')
                            .attr('class', 'brush')
                            .call(brush);
                    } 

                    colorButtonText
                    .text(function(){
                        return `Colors: ${colors[curColor]}`;
                    })

                    legendText
                    .text(function(){
                        return `Legends: ${legends[curLegend]}`;
                    })

                    colorButton.attr('width', colorButtonText.node().getBBox().width + 10);
                    unifyLegends.attr('width', legendText.node().getBBox().width + 10);
                    
                }
            }
        }

        var createChartView = function(elem, model){
            let _observers = makeSignaller();
            var _colorManager = makeColorManager(model);
            const metricColumns = model.data["metricColumns"];
            const attributeColumns = model.data["attributeColumns"];
            var forestData = model.data["forestData"];
            var width = elem.clientWidth - globals.layout.margin.right - globals.layout.margin.left;
            var height = globals.layout.margin.top + globals.layout.margin.bottom;
            var _margin = globals.layout.margin;
            var _nodeRadius = 30;
            var treeLayoutHeights = [];


            var svg = d3.select(elem)
                        .append('svg')
                        .attr("class", "canvas")
                        .attr("width", width)
                        .attr("height", height);

            var _maxNodeRadius = 30;
            var _treeDepthScale = d3.scaleLinear().range([0,element.offsetWidth-50]).domain([0, model.data.maxHeight])
            var _nodeScale = d3.scaleLinear().range([5, _maxNodeRadius]).domain([model.data.forestMinMax[model.state.secondaryMetric].min, model.data.forestMinMax[model.state.secondaryMetric].max]);
            var _barScale = d3.scaleLinear().range([0, 25]).domain([model.data.aggregateMinMax[model.state.primaryMetric].min, model.data.aggregateMinMax[model.state.primaryMetric].max]);
            var _treeLayoutHeights = [];

            //layout variables            
            var spreadFactor = 0;
            var legendOffset = 0;
            var maxHeight = 0;
            var chartOffset = _margin.top;
            var treeOffset = 0;
            var minmax = [];
            var maxTreeCanvasHeight = 1000;

            //view specific data
            var nodes = [];
            var surrogates = [];
            var aggregates = [];
            var links = [];

            function diagonal(s, d, ti) {
                              /**
                 * Creates a curved diagonal path from parent to child nodes
                 * 
                 * @param {Object} s - parent node
                 * @param {Object} d - child node
                 * 
                 */
                var dy = _treeDepthScale(d.depth);
                var sy = _treeDepthScale(s.depth);
                var sx = _getLocalNodeX(s.x, ti);
                var dx = _getLocalNodeX(d.x, ti);
                let path = `M ${sy} ${sx}
                C ${(sy + dy) / 2} ${sx},
                ${(sy + dy) / 2} ${dx},
                ${dy} ${dx}`

                return path
            }

            function _getMinxMaxxFromTree(root){
                /**
                 * Get the minimum x value and maximum x value from a tree layout
                 * Used for calculating canvas offsets before drawing
                 * 
                 * @param {Object} root - The root node of the working tree
                 */

                var obj = {}
                var min = Infinity;
                var max = -Infinity;
                root.descendants().forEach(function(d){
                    max = Math.max(d.x, max);
                    min = Math.min(d.x, min);
                })

                obj.min = min;
                obj.max = max;

                return obj;
            }

            function _getHeightFromTree(root){
                /**
                 * Get the vertical space required to draw the tree
                 * by subtracting the min x value from the maximum
                 * 
                 * @param {Object} root - The root node of the working tree
                 */
                let minmax = _getMinxMaxxFromTree(root);
                let min = minmax["min"];
                let max = minmax["max"];

                return max - min;
            }

            // --------------------------------------------------------------
            // Initialize layout before first render
            // --------------------------------------------------------------

            var mainG = svg.append("g")
                            .attr('id', "mainG")
                            .attr("transform", "translate(" + globals.layout.margin.left + "," + 0 + ")");

            function _calcNodePositions(nodes, treeIndex){
                nodes.forEach(
                    function (d) {
                            d.x0 = _getLocalNodeX(d.x, treeIndex);
                            d.y0 = _treeDepthScale(d.depth);
                        
                            // Store the overall position based on group
                            d.xMainG = d.x0 + chartOffset;
                            d.yMainG = d.y0 + _margin.left;
                    }
                );
            }

            var mainG = svg.select("#mainG");
            var tree = d3.tree()//.size([maxTreeCanvasHeight, width - _margin.left]);
            .nodeSize([_maxNodeRadius, _maxNodeRadius]);
            

          
            var zoom = d3.zoom()
                .on("zoom", function (){
                     let zoomObj = d3.select(this).selectAll(".chart");
                     zoomObj.attr("transform", d3.event.transform);
                 })
                 .on("end", function(){
                     let zoomObj = d3.select(this).selectAll(".chart");
                     let index = zoomObj.attr("chart-id");
                     let transformation = zoomObj.node().getCTM();
     
                     nodes[index].forEach(function(d, i) {
                         // This function gets the absolute location for each point based on the relative
                         // locations of the points based on transformations
                         // the margins were being added into the .e and .f values so they have to be subtracted
                         // I think they come from the margins being added into the "main group" when it is created
                         // We can brush regardless of zoom or pan
                         // Adapted from: https://stackoverflow.com/questions/18554224/getting-screen-positions-of-d3-nodes-after-transform
                         d.yMainG = transformation.e + d.y0*transformation.d + d.x0*transformation.c - globals.layout.margin.left;
                         d.xMainG = transformation.f + d.y0*transformation.b + d.x0*transformation.a - globals.layout.margin.top;
                     });
                 });


            // Add a group and tree for each forestData[i]
            for (var treeIndex = 0; treeIndex < model.data.numberOfTrees; treeIndex++) {
                var currentRoot = tree(model.data.hierarchy[treeIndex]);
                var currentLayoutHeight = _getHeightFromTree(currentRoot);
                var currentMinMax = _getMinxMaxxFromTree(currentRoot);

                currentRoot.x0 = height;
                currentRoot.y0 = _margin.left;

                var currentTree = tree(currentRoot);

                if (currentTree.height > maxHeight) {
                    maxHeight = currentTree.height;
                }

                model.addTree(currentTree);

                treeLayoutHeights.push(_getHeightFromTree(currentRoot));
                minmax.push(_getMinxMaxxFromTree(currentRoot))
            }

            //layout variables            
            spreadFactor = width / (maxHeight + 1);

            // Add a group and tree for each tree in the current forest
            for (var treeIndex = 0; treeIndex < forestData.length; treeIndex++) {
                model.updateforestStats(treeIndex);
                
                var currentTree = model.getTree(treeIndex);
                var newg = mainG.append("g")
                        .attr('class', 'group-' + treeIndex + ' subchart')
                        .attr('tree_id', treeIndex)
                        .attr("transform", "translate(" + _margin.left + "," + chartOffset + ")");

                const legGroup = newg
                    .append('g')
                    .attr('class', 'legend-grp-' + treeIndex)
                    .attr('transform', 'translate(0, 0)');

                const legendGroups = legGroup.selectAll("g")
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

                legendOffset = legGroup.node().getBBox().height;

                //make an invisible rectangle for zooming on
                newg.append('rect')
                    .attr('height', treeLayoutHeights[treeIndex])
                    .attr('width', width)
                    .attr('fill', 'rgba(0,0,0,0)');

                //put tree itself into a group
                newg.append('g')
                    .attr('class', 'chart')
                    .attr('chart-id', treeIndex)
                    .attr('height', globals.treeHeight)
                    .attr('width', width)
                    .attr('fill', 'rgba(0,0,0,0)');

                //Create d3 zoom element and affix to each tree individually
                var zoom = d3.zoom().on("zoom", function (){
                    let zoomObj = d3.select(this).selectAll(".chart");

                    zoomObj.attr("transform", d3.event.transform);

                    //update for scale view
                    _observers.notify({
                        type: globals.signals.ZOOM,
                        index: zoomObj.attr("chart-id"),
                        transformation: zoomObj.node().getCTM()
                    })
                });

                newg.call(zoom)
                    .on("dblclick.zoom", null);
                    
                //store node and link layout data for use later
                var treeLayout = tree(model.data.hierarchy[treeIndex]);
                nodes.push(treeLayout.descendants());
                surrogates.push([]);
                aggregates.push([]);
                links.push(treeLayout.descendants().slice(1));
                
                //X value where tree should start being drawn
                treeOffset = 0 + legendOffset + _margin.top;

                //updates
                // put this on the immutable tree
                _calcNodePositions(nodes[treeIndex], treeIndex);

                newg.style("display", "inline-block");

                
                //updates
                chartOffset += treeLayoutHeights[treeIndex] + treeOffset + _margin.top;
                height += chartOffset;


                newg.call(zoom)
                    .on("dblclick.zoom", null);

            } //end for-loop "add tree"
        
              //setup Interactions
              var brush = d3.brush()
                .extent([[0, 0], [2 * width, 2 * (height + globals.layout.margin.top + globals.layout.margin.bottom)]])
                .on('brush', function(){
                })
                .on('end', function(){
                    var selection = _getSelectedNodes(d3.event.selection);
                    _observers.notify({
                        type: globals.signals.BRUSH,
                        selection: selection
                    })
                });
            
            //return object        
            return{
                register: function(s){
                    _observers.add(s);
                },
                render: function(){
                    /**
                     * Core render function for the chart portion of the view, including legends
                     * Called from the model with observers.notify
                     * 
                     */

                    chartOffset = _margin.top;
                    height = _margin.top + _margin.bottom;
                    _nodeScale.domain([0, model.data.forestMinMax[model.state.secondaryMetric].max]);

                     //add brush if there should be one
                     if(model.state.brushOn > 0){
                        d3.select("#mainG").append('g')
                            .attr('class', 'brush')
                            .call(brush);
                    } 

                    //render for any number of trees
                    for(var treeIndex = 0; treeIndex < model.data.numberOfTrees; treeIndex++){
                        //retrieve new data from model
                        let lastClicked = model.state.lastClicked;
                        var primaryMetric = model.state.primaryMetric;
                        var secondaryMetric = model.state.secondaryMetric;
                        var source = model.data.hierarchy[treeIndex];

                        //will need to optimize this redrawing
                        // by cacheing tree between calls
                        if(model.state.hierarchyUpdated == true){
                            var treeLayout = tree(source);
                            nodes[treeIndex] = treeLayout.descendants().filter(d=>{return !d.data.dummy});
                            surrogates[treeIndex] = treeLayout.descendants().filter(d=>{return (d.data.dummy && !d.data.aggregate)});
                            aggregates[treeIndex] = treeLayout.descendants().filter(d=>{return d.data.aggregate});
                            links[treeIndex] = treeLayout.descendants().slice(1);
                            _calcNodePositions(nodes[treeIndex], treeIndex);

                            console.log("Tree" + treeIndex, surrogates, aggregates);

                            //only update after last tree
                            if(treeIndex == model.data.numberOfTrees - 1){
                                model.state.hierarchyUpdated = false;
                            }
                        }

                        
                        var chart = svg.selectAll('.group-' + treeIndex);
                        var treeGroup = chart.selectAll('.chart');

                        if(model.state.resetView == true){
                            treeGroup.attr("transform", "");

                            nodes[treeIndex].forEach(
                                function (d) {
                                        // Store the overall position based on group
                                        d.xMainG = d.x0 + chartOffset;
                                        d.yMainG = d.y0 + _margin.left;
                                }
                            );

                            //only update after last tree
                            if(treeIndex == model.data.numberOfTrees - 1){
                                model.state.resetView = false;
                            }
                        }

                        // ---------------------------------------------
                        // ENTER 
                        // ---------------------------------------------
                        // Update the nodes…
                        var i = 0;
                        var node = treeGroup.selectAll("g.node")
                                .data(nodes[treeIndex], function (d) {
                                    return d.id || (d.id = ++i);
                                });
                        
                        var dummyNodes = treeGroup.selectAll("g.fakeNode")
                            .data(surrogates[treeIndex], function (d) {
                                return d.id || (d.id = ++i);
                            });

                        var aggBars = treeGroup.selectAll("g.aggBar")
                            .data(aggregates[treeIndex], function (d) {
                                return d.id || (d.id = ++i);
                            });
                        
                        // Enter any new nodes at the parent's previous position.
                        var nodeEnter = node.enter().append('g')
                                .attr('class', 'node')
                                .attr("transform", function (d) {
                                    if(!d.parent){
                                        return "translate(0,0)"
                                    }
                                    return "translate(" + d.parent.y + "," + d.parent.x + ")";
                                })
                                .on("click", function(d){

                                    console.log(d);
                                    _observers.notify({
                                        type: globals.signals.CLICK,
                                        node: d
                                    })
                                })
                                .on('dblclick', function (d) {
                                    _observers.notify({
                                        type: globals.signals.DBLCLICK,
                                        node: d,
                                        tree: treeIndex
                                    })
                                });
                                // .on("mouseover", function(d){
                                //     _observers.notify({
                                //         type: globals.signals.CLICK,
                                //         node: d
                                //     })
                                // })
                                // .on("mouseout", function(d){
                                //     _observers.notify({
                                //         type: globals.signals.CLICK,
                                //         node: null
                                //     })
                                // });


                        var dNodeEnter = dummyNodes.enter().append('g')
                            .attr('class', 'fakeNode')
                            .attr("transform", function (d) {
                                if(!d.parent){
                                    return "translate(0,0)";
                                }
                                return "translate(" + d.parent.y + "," + d.parent.x + ")";
                            })
                            .on("click", function(d){
                                console.log(d);
                                _observers.notify({
                                    type: globals.signals.CLICK,
                                    node: d
                                })
                            })
                            .on('dblclick', function (d) {
                                _observers.notify({
                                    type: globals.signals.DBLCLICK,
                                    node: d,
                                    tree: treeIndex
                                })
                            });
                        
                        var aggNodeEnter = aggBars.enter().append('g')
                            .attr('class', 'aggBar')
                            .attr("transform", function (d) {
                                if(!d.parent){
                                    return "translate(0,0)"
                                }
                                return "translate(" + d.parent.y + "," + d.parent.x + ")";
                            })
                            .on("click", function(d){
                                console.log(d);
                                _observers.notify({
                                    type: globals.signals.CLICK,
                                    node: d
                                })
                            })
                            .on('dblclick', function (d) {
                                _observers.notify({
                                    type: globals.signals.DBLCLICK,
                                    node: d,
                                    tree: treeIndex
                                })
<<<<<<< HEAD
                                .on("mouseout", function(d){
                                    _observers.notify({
                                        type: globals.signals.CLICK,
                                        node: null
                                    })
                                });

=======
                            });

                        
            
>>>>>>> Drawing bars, need to tidy up the tree after this tho.
                        nodeEnter.append("circle")
                                .attr('class', 'circleNode')
                                .attr("r", 1e-6)
                                .style("fill", function (d) {
                                    if(model.state["legend"] == globals.UNIFIED){
                                        return _colorManager.calcColorScale(d.data.metrics[primaryMetric], -1);
                                    }
                                    return _colorManager.calcColorScale(d.data.metrics[primaryMetric], treeIndex);
                                })
                                .style('stroke-width', '1px')
                                .style('stroke', 'black');
            
                        dNodeEnter.append("path")
                                .attr('class', 'dummyNode')
                                .attr("d", "M 6 2 C 6 2 5 2 5 3 S 6 4 6 4 S 7 4 7 3 S 6 2 6 2 Z M 6 3 S 6 3 6 3 Z M 8 0 C 8 0 7 0 7 1 C 7 1 7 2 8 2 C 8 2 9 2 9 1 C 9 0 8 0 8 0 M 9 5 C 9 4 8 4 8 4 S 7 4 7 5 S 8 6 8 6 S 9 6 9 5")
                                .attr("fill", "rgba(0,0,0, .4)")
                                .style("stroke-width", ".5px")
                                .style("stroke", "rgba(100,100,100)");
                        dNodeEnter.append("path")
                                .attr('class', 'dummyNode2')
                                .attr("d", "M 6 2 C 6 2 5 2 5 3 S 6 4 6 4 S 7 4 7 3 S 6 2 6 2 Z M 6 3 S 6 3 6 3 Z M 8 0 C 8 0 7 0 7 1 C 7 1 7 2 8 2 C 8 2 9 2 9 1 C 9 0 8 0 8 0 M 9 5 C 9 4 8 4 8 4 S 7 4 7 5 S 8 6 8 6 S 9 6 9 5")
                                .attr("fill", "rgba(0,0,0, .4)")
                                .style("stroke-width", ".5px")
                                .style("stroke", "rgba(100,100,100)");
                        
                        aggNodeEnter.append("rect")
                                .attr('class', 'bar')
                                .attr('height', (d) => {return _barScale(d.data.aggregateMetrics[primaryMetric]);})
                                .attr('width', 20)
                                .attr("fill", "rgba(0,0,0)")
                                .style("stroke-width", ".5px")
                                .style("stroke", "rgba(100,100,100)");

                                

                        // commenting out text for now
                        nodeEnter.append("text")
                                .attr("x", function (d) {
                                    return d.children || model.state['collapsedNodes'].includes(d) ? -13 : 13;
                                })
                                .attr("dy", ".75em")
                                .attr("text-anchor", function (d) {
                                    return d.children || model.state['collapsedNodes'].includes(d) ? "end" : "start";
                                })
                                .text(function (d) {
                                    // if(d.data.name.includes("mv2_increment")){
                                    //     return d.data.frame.name;
                                    // }
                                    if(!d.children){
                                        return d.data.name;
                                    }
                                    else if(d.children.length == 1){
                                        return "";
                                    }

                                    // else {
                                    //     return d.data.name.slice(0,10) + "...";
                                    // }
                                    return "";
                                })
                                .attr("transform", (d) => {
                                    if(d.children){
                                        return "rotate(-25)"
                                    }
                                })
                                .style("font", "12px monospace");
        
                                  // commenting out text for now
                            dNodeEnter.append("text")
                                .attr("x", function (d) {
                                    return 20;
                                })
                                .attr("dy", "2em")
                                .attr("text-anchor", function (d) {
                                    return "start";
                                })
                                .text(function (d) {
                                    if (d.data.elided.length > 1){
                                        return `Children of: ${d.parent.name}` ;
                                    } 
                                    else{
                                        return `${d.data.name} Subtree`;
                                    }
                                })
                                .style("font", "12px monospace");

                            aggNodeEnter.append("text")
                                .attr("x", function (d) {
                                    return 20;
                                })
                                .attr("dy", "1em")
                                .attr("text-anchor", function (d) {
                                    return "start";
                                })
                                .text(function (d) {
                                    if (d.data.elided.length > 1){
                                        return `Children of: ${d.parent.name}` ;
                                    } 
                                    else{
                                        return `${d.data.name} Subtree`;
                                    }
                                })
                                .style("font", "12px monospace");


                        // links
                        var link = treeGroup.selectAll("path.link")
                        .data(links[treeIndex], function (d) {
                            return d.id;
                        });
        
                        // Enter any new links at the parent's previous position.
                        var linkEnter = link.enter().insert("path", "g")
                                .attr("class", "link")
                                .attr("d", function (d) {
                                    var o = {x: nodes[0].x, y: nodes[0].y};
                                    return diagonal(o, o);
                                })
                                .attr('fill', 'none')
                                .attr('stroke', '#ccc')
                                .attr('stroke-width', '2px');

        
                        // ---------------------------------------------
                        // Updates 
                        // ---------------------------------------------
                        var nodeUpdate = nodeEnter.merge(node);
                        var dNodeUpdate = dNodeEnter.merge(dummyNodes);
                        var linkUpdate = linkEnter.merge(link);
                        var aggNodeUpdate = aggNodeEnter.merge(aggBars);
                
                        // Chart updates
                        chart
                            .transition()
                            .duration(globals.duration)
                            .attr("transform", function(){
                                if(model.state["activeTree"].includes(model.data["rootNodeNames"][treeIndex+1])){
                                    return `translate(${_margin.left}, ${_margin.top})`;
                                } 
                                else {
                                    return `translate(${_margin.left}, ${chartOffset})`;
                                }
                            })    
                            .style("display", function(){
                                if(model.state["activeTree"].includes("Show all trees")){
                                    return "inline-block";
                                } 
                                else if(model.state["activeTree"].includes(model.data["rootNodeNames"][treeIndex+1])){
                                    return "inline-block";
                                } 
                                else {
                                    return "none";
                                }
                            });

                        //legend updates
                        chart.selectAll(".legend rect")
                            .transition()
                            .duration(globals.duration)
                            .attr('fill', function (d, i) {
                                return _colorManager.getColorLegend(treeIndex)[d];
                            })
                            .attr('stroke', 'black');

                        chart.selectAll('.legend text')
                            .transition()
                            .duration(globals.duration)
                            .text((d, i) => {
                                if (metricColumns.includes(model.state["selectedMetric"])) {
                                    return _colorManager.getLegendDomains(treeIndex)[6 - d - 1] + ' - ' + _colorManager.getLegendDomains(treeIndex)[6 - d];
                                } else if (attributeColumns.includes(model.state["selectedMetric"])) {
                                    return _colorManager.getLegendDomains(treeIndex)[i];
                                }
                            });


                        // Transition links to their new position.
                        linkUpdate.transition()
                                .duration(globals.duration)
                                .attr("d", function (d) {
                                    return diagonal(d, d.parent);
                                });

            
                        // Transition normal nodes to their new position.
                        nodeUpdate
                            .transition()
                            .duration(globals.duration)
                            .attr("transform", function (d) {
                                return `translate(${_treeDepthScale(d.depth)}, ${_getLocalNodeX(d.x, treeIndex)})`;
                            });
                                
                        //update other characteristics of nodes
                        nodeUpdate
                            .select('circle.circleNode')
                            .style('stroke', function(d){
                                if (model.state['collapsedNodes'].includes(d)){
                                    return "#89c3e0";
                                }
                                else{
                                    return 'black';
                                }
                            })
                            .style("stroke-dasharray", function (d) {
                                return model.state['collapsedNodes'].includes(d) ? '4' : '0';
                            }) //lightblue
                            .style('stroke-width', function(d){
                                if (model.state['collapsedNodes'].includes(d)){
                                    return '6px';
                                } 
                                else if (model.state['selectedNodes'].includes(d)){
                                    return '4px';
                                } 
                                else {
                                    return '1px';
                                }
                            })
                            .attr('cursor', 'pointer')
                            .transition()
                            .duration(globals.duration)
                            .attr("r", 
                            function(d){
                                if (model.state['selectedNodes'].includes(d)){
                                    return _nodeScale(d.data.metrics[secondaryMetric]) + 3;
                                }
                                return _nodeScale(d.data.metrics[secondaryMetric]);
                            })
                            .style('fill', function (d) {
                                if(model.state["legend"] == globals.UNIFIED){
                                    return _colorManager.calcColorScale(d.data.metrics[primaryMetric], -1);
                                }
                                return _colorManager.calcColorScale(d.data.metrics[primaryMetric], treeIndex);

                            });
                        
                        nodeUpdate.select("text")
                            .attr("x", function (d) {
                                return d.children || model.state['collapsedNodes'].includes(d) ? -13 : 13;
                            })
                            .attr("dy", ".75em")
                            .attr("text-anchor", function (d) {
                                return d.children || model.state['collapsedNodes'].includes(d) ? "end" : "start";
                            })
                            .text(function (d) {
                                if(!d.children || d.children.length == 0){
                                    return d.data.name;
                                }
                                else if(d.children.length == 1){
                                    return "";
                                }
                                // else {
                                //     return d.data.name.slice(0,10) + "...";
                                // }
                                return "";
                            });
                        
                        dNodeUpdate
                            .selectAll(".dummyNode")
                            .attr("d", "M 6 2 C 6 2 5 2 5 3 S 6 4 6 4 S 7 4 7 3 S 6 2 6 2 Z M 6 3 S 6 3 6 3 Z M 8 0 C 8 0 7 0 7 1 C 7 1 7 2 8 2 C 8 2 9 2 9 1 C 9 0 8 0 8 0 M 9 5 C 9 4 8 4 8 4 S 7 4 7 5 S 8 6 8 6 S 9 6 9 5")
                            .attr("fill", "rgba(180,180,180)")
                            .style("stroke-width", ".5px")
                            .style("stroke", "rgba(100,100,100)")
                            .attr("transform", function (d) {
                                let scale = 3;
                                return `scale(${scale})`;
                            });
                        
                        dNodeUpdate
                            .selectAll(".dummyNode2")
                            .attr("d", "M 6 2 C 6 2 5 2 5 3 S 6 4 6 4 S 7 4 7 3 S 6 2 6 2 Z M 6 3 S 6 3 6 3 Z M 8 0 C 8 0 7 0 7 1 C 7 1 7 2 8 2 C 8 2 9 2 9 1 C 9 0 8 0 8 0 M 9 5 C 9 4 8 4 8 4 S 7 4 7 5 S 8 6 8 6 S 9 6 9 5")
                            .attr("fill", "rgba(180,180,180)")
                            .style("stroke-width", ".5px")
                            .style("stroke", "rgba(100,100,100)")
                            .attr("transform", function (d) {
                                return `translate(0, 1)`;
                            })
                            .attr("transform", function (d) {
                                let scale = 3;
                                return `scale(${scale})`;
                            });
                        
                        dNodeUpdate
                            .transition()
                            .duration(globals.duration)
                            .attr("transform", function (d) {
                                    let h = d3.select(this).select('path').node().getBBox().height;
                                    return `translate(${_treeDepthScale(d.depth)-15}, ${_getLocalNodeX(d.x, treeIndex) - (h+1)/2})`;
                            });

                        aggNodeUpdate
                            .select('rect')
                            .style('fill', function (d) {
                                if(model.state["legend"] == globals.UNIFIED){
                                    return _colorManager.calcColorScale(d.data.aggregateMetrics[primaryMetric], -1);
                                }
                                return _colorManager.calcColorScale(d.data.aggregateMetrics[primaryMetric], treeIndex);
                            })

                        aggNodeUpdate
                            .transition()
                            .duration(globals.duration)
                            .attr("transform", function (d) {
                                    let h = d3.select(this).select('rect').node().getBBox().height;
                                    let w = d3.select(this).select('rect').node().getBBox().width;
                                    return `translate(${_treeDepthScale(d.depth)-w/3}, ${_getLocalNodeX(d.x, treeIndex) - h/2})`;
                            });
                        
                                
                        // ---------------------------------------------
                        // Exit
                        // ---------------------------------------------
                        // Transition exiting nodes to the parent's new position.
                        var nodeExit = node.exit().transition()
                                .duration(globals.duration)
                                .attr("transform", function (d) {
                                    return "translate(" + lastClicked.y + "," + lastClicked.x + ")";
                                })
                                .remove();
            
                        nodeExit.select("circle")
                                .attr("r", 1e-6);
            
                        nodeExit.select("text")
                                .style("fill-opacity", 1)
                                .remove();
                        
                        var dNodeExit = dummyNodes.exit().transition()
                                .duration(globals.duration)
                                .attr("transform", function (d) {
                                    return "translate(" + lastClicked.y + "," + lastClicked.x + ")";
                                })
                                .remove();
            
                        // Transition exiting links to the parent's new position.
                        var linkExit = link.exit().transition()
                                .duration(globals.duration)
                                .attr("d", function (d) {
                                    var o = {x: source.x, y: source.y};
                                    return diagonal(o, o);
                                })
                                .remove();

                        chartOffset = treeLayoutHeights[treeIndex] + treeOffset + _margin.top;
                        height += chartOffset;
                    }                    

                    svg.attr("height", height);
                }
            }
            
        }

        var createTooltipView = function(elem, model){
            /**
             * Class that instantiates the view for the tooltip that appears with selected nodes.
             * 
             * @param {DOM Element} elem - The current cell of the calling Jupyter notebook
             * @param {Model} model - The model object containg data for the view
             */
            var _observers = makeSignaller();
            var _tooltip = d3.select(elem).append("div")
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

            return {
                register: function(s){
                    _observers.add(s);
                },
                render: function(){
                    _tooltip.html(model.data["tipText"]);
                }
            }
        }

        // ---------------------------------------------
        // Main driver area 
        // ---------------------------------------------
        
        //model
        var model = createModel();
        //controller
        var controller = createController(model);
        //views
        var menu = createMenuView(element, model);
        var tooltip = createTooltipView(element, model);
        var chart = createChartView(element, model);
        
        //render all views one time
        menu.render();
        tooltip.render();
        chart.render();
        
        //register signallers with each class
        // tooltip is not interactive so 
        // it does not need a signaller yet
        menu.register(controller.dispatch);
        chart.register(controller.dispatch);

        model.register(menu.render);
        model.register(chart.render);
        model.register(tooltip.render);

    });

})(element);
