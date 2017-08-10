var PORT = 60000;
var HOST = "http://dataweb.isis.rl.ac.uk" 
var showPrivate = true;
var privateRunInfo = ["TITLE", "_USERNAME"];
var instrument = getURLParameter("Instrument");
var nodeInstTitle = document.createElement("H2");
var nodeConfigTitle = document.createElement("H2");
var instrumentState;
var showHidden;
var timeout = 1000;

dictInstPV = {
    RUNSTATE: 'Run Status',
    RUNNUMBER: 'Run Number',
    _RBNUMBER: 'RB Number',
    _USERNAME: 'User(s)',
    TITLE: 'Title',
    TITLEDISP: 'Show Title',
    STARTTIME: 'Start Time',
    RUNDURATION: 'Total Run Time',
    RUNDURATION_PD: 'Period Run Time',
    GOODFRAMES: 'Good Frames (Total)',
    GOODFRAMES_PD: 'Good Frames (Period)',
    RAWFRAMES: 'Raw Frames (Total)',
    RAWFRAMES_PD: 'Raw Frames (Period)',
    PERIOD: 'Current Period',
    NUMPERIODS: 'Number of Periods',
    PERIODSEQ: 'Period Sequence',
    BEAMCURRENT: 'Beam Current',
    TOTALUAMPS: 'Total Uamps',
    COUNTRATE: 'Count Rate',
    DAEMEMORYUSED: 'DAE Memory Used',
    TOTALCOUNTS: 'Total DAE Counts',
    DAETIMINGSOURCE: 'DAE Timing Source',
    MONITORCOUNTS: 'Monitor Counts',
    MONITORSPECTRUM: 'Monitor Spectrum',
    MONITORFROM: 'Monitor From',
    MONITORTO: 'Monitor To',
    NUMTIMECHANNELS: 'Number of Time Channels',
    NUMSPECTRA: 'Number of Spectra'
};

/**
 * Gets the proper display title for a PV.
 *
 * @param {string} title The actual title of the PV.
 * @return {string} The title for display on the page.
 */
function getTitle(title) {
    if (title in dictInstPV){
        return dictInstPV[title];
    }
    return title;
}

/**
 * Checks whether a given group is the "None" group and replaces the title with "Other" if so.
 *
 * @param {string} title The title of the group.
 * @return {string} The correct title for the group.
 */
function checkGroupNone(title) {
    if (title === "NONE") {
        title = "OTHER";
    }
    return title;
}

/**
 * Returns the value of a parameter set in the URL.
 *
 * @param {string} name The name of the parameter.
 * @return {string} The value of the parameter.
 */
function getURLParameter(name) {
    return decodeURIComponent((new RegExp('[?|&]' + name + '=' + '([^&;]+?)(&|#|;|$)').exec(location.search)
            || [null, ''])[1].replace(/\+/g, '%20')) || null;
}

/**
 * Checks whether a list contains a certain element.
 *
 * @param list The list of elements.
 * @param elem The element to look for in the list.
 * @return {boolean} Whether elem is contained in list.
 */
function isInArray(list, elem) {
    return list.indexOf(elem) > -1;
}

/**
 * Converts a String PV value ("YES" / "NO") into a boolean.
 *
 * @param stringval The string to convert.
 * @return {boolean} The resulting boolean value.
 */
function getBoolean(stringval) {
    if (stringval.toUpperCase() == "NO") {
        return false;
    }
    return true;
}

/**
 * Clears a given node of all child elements.
 *
 * @param node The node to be cleared.
 */
function clear(node) {
    while (node.firstChild) {
        node.removeChild(node.firstChild);
    }
}

/**
 * Fetches the latest instrument data.
 */
function refresh() {
	$.ajax({
		url: HOST + ":" + PORT + "/",
		dataType: 'jsonp',
		data: {"Instrument": instrument},
		timeout: timeout,
		error: function(xhr, status, error){ 
			displayError();
		},
		success: function(data){ 
			parseObject(data);
		}
	});
}

/**
 * Parses fetched instrument data into a human-readable html page.
 */
function parseObject(obj) {
    // set up page
    instrumentState = obj;
	createTitle(obj)
    showHidden = document.getElementById("showHidden").checked;
	if ("DISPLAY" in instrumentState.inst_pvs) {
		showPrivate = getBoolean(instrumentState.inst_pvs["DISPLAY"]["value"]);
		delete instrumentState.inst_pvs["DISPLAY"];
	} else {
		showPrivate = true;
	}
    clear(nodeInstTitle);
    clear(nodeConfigTitle);

    // populate blocks
    var nodeGroups = document.getElementById("groups");
    getDisplayGroups(nodeGroups, instrumentState.groups);

    // populate run information
    var nodeInstPVs = document.getElementById("inst_pvs");
    var nodeInstPVList = document.createElement("ul");

    getDisplayRunInfo(nodeInstPVs, instrumentState.inst_pvs);

    nodeInstTitle.appendChild(document.createTextNode(instrument));
    nodeConfigTitle.appendChild(document.createTextNode("Configuration: " + instrumentState.config_name));

    document.getElementById("config_name").appendChild(nodeConfigTitle);
	
	setVisibilityMode('block');
};


function clearBox(elementID){
    document.getElementById(elementID).innerHTML = "";
};

/**
 * creates a Title at the top looking similar to the IBEX GUI
 */
function createTitle(obj){
	clearBox("top_bar");
	
	document.getElementById("top_bar").innerHTML = "<div id = \"inst_name\"></div><table><tr id = table_part><th id = \"next_part\" style = \"padding: 10px; background-color:lightgrey ; border: black 2px solid\";></th></tr></table>";
	runStatus = obj["inst_pvs"]["RUNSTATE"]["value"];
	
	switch (runStatus){
		case "PROCESSING" || "UPDATING" || "STORING" || "SAVING" || "UNKNOWN":
			colour = "YELLOW";
			break;
		case "RUNNING":
			colour = "LIGHTGREEN";
			break;
		case "SETUP":
			colour = "LIGHTBLUE";
			break;
		case "PAUSED":
			colour = "RED";
			break;
		case "WAITING" || "VETOING":
			colour = "GOLDENROD";
			break;
		case "ENDING" || "ABORTING":
			colour = "BLUE";
			break;
		case "PAUSING":
			colour = "DARK_RED";
			break;
	};
	document.getElementById("inst_name").style = "padding: 10px; background-color:" +colour+"; border: black 2px solid";
	var title = document.createElement("h3"); 
	title.innerHTML = instrument.toUpperCase() + " is " + runStatus;
	var blockListClass = document.createAttribute("class");
	blockListClass.value = "text-center";
	title.setAttributeNode(blockListClass);
	document.getElementById("inst_name").appendChild(title);
	
	addItemToTable("Title", obj["inst_pvs"]["TITLE"]["value"]);
	addItemToTable("Users", obj["inst_pvs"]["_USERNAME"]["value"]);
	
	newPartOfTable();
	
	addItemToTable("Good / Raw Frames", obj["inst_pvs"]["GOODFRAMES"]["value"]+"/"+obj["inst_pvs"]["RAWFRAMES"]["value"]);
	addItemToTable("Current / Total", obj["inst_pvs"]["BEAMCURRENT"]["value"]+"/"+obj["inst_pvs"]["TOTALUAMPS"]["value"]);
	addItemToTable("Monitor Counts", obj["inst_pvs"]["MONITORCOUNTS"]["value"]);
	
	newPartOfTable();
	
	addItemToTable("Inst. Time", obj["inst_pvs"]["STARTTIME"]["value"]);
	addItemToTable("Run Time", obj["inst_pvs"]["RUNDURATION_PD"]["value"]);
	addItemToTable("Period", obj["inst_pvs"]["PERIOD"]["value"]+"/"+obj["inst_pvs"]["NUMPERIODS"]["value"]);
	
};


function newPartOfTable(){
	document.getElementById("next_part").removeAttribute("id");
	document.getElementById("table_part").innerHTML += "<th id = \"next_part\" style = \"padding: 10px; background-color:lightgrey ; border: black 2px solid\";></th>";
};

function addItemToTable(name, value) {
	var elem = document.createElement("h5");
	elem.innerHTML = name + ": " + value + "&nbsp;".repeat(30);
	document.getElementById("next_part").appendChild(elem);
}

/**
 * Display an error when connection to server couldn't be made.
 */
function displayError() {

    clear(nodeInstTitle);
    clear(nodeConfigTitle);
    nodeConfigTitle.appendChild(document.createTextNode("Could not connect to " + instrument + ", check IBEX server is running."));

	document.getElementById("top_bar").innerHTML = instrument;
	document.getElementById("config_name").appendChild(nodeConfigTitle);
	
	setVisibilityMode('none');
}

/*
 *  Sets the visibility of the run information, blocks and checkbox
 */
 function setVisibilityMode(mode){
	document.getElementById("run_information").style.display = mode;
	document.getElementById("blocks").style.display = mode;
	document.getElementById("showHiddenContainer").style.display = mode;
 }

/**
 * Adds html elements for a list of group objects to a given node.
 *
 * @param node The parent node.
 * @param groups The list of group objects to display.
 * @return The updated node.
 */
function getDisplayGroups(node, groups) {
    clear(node);
    for (var key in groups) {
        var group = groups[key];
        var nodeGroups = document.getElementById("groups");

        var nodeBlockList = document.createElement("UL");

        var blocks = instrumentState.groups[key];
        var displayBlocks = getDisplayBlocks(nodeBlockList, blocks);

        // Do not display empty groups
        if (displayBlocks.childElementCount != 0) {
            var nodeTitle = document.createElement("H3");
            nodeGroups.appendChild(nodeTitle);
            nodeTitle.appendChild(document.createTextNode(checkGroupNone(key)));
            nodeGroups.appendChild(nodeBlockList);

            var blockListStyle = document.createAttribute("style");
            blockListStyle.value = 'padding-left:20px';
            nodeBlockList.setAttributeNode(blockListStyle);

            node.appendChild(displayBlocks);
        }
    }
    return node;
}

/**
 * Adds a single block html element to the parent node
 *
 * @param node The parent node.
 * @param block The block to add.
 * @param blockName The name of the block to display.
 * @return The updated node.
 */
function displayOneBlock(node, block, blockName) {
    if(block["visibility"] == false && !showHidden){
        return;
    }

    var value = block["value"];
    var status_text = block["status"];
    var alarm = block["alarm"];
        
    var rc_inrange = block["rc_inrange"];
    var rc_enabled = block["rc_enabled"];
    var nodeBlock = document.createElement("LI");
    var nodeBlockText = document.createTextNode(blockName + ":\u00A0\u00A0");

    // write block name
    nodeBlock.appendChild(nodeBlockText);

    // write status if disconnected
    if (status_text == "Disconnected") {
	    writeStatus(nodeBlock, status_text);
    }
    // write value if is private
    else if ((isInArray(privateRunInfo, blockName)) && !showPrivate) {
	    writePrivateValue(nodeBlock);
    // write value, range info & alarms
    } else {
        nodeBlockText.nodeValue += value + "\u00A0\u00A0";
        // write range information about the PV
        if (rc_enabled === "YES" && (rc_inrange === "YES" || rc_inrange === "NO")) {
            writeRangeInfo(nodeBlock, rc_inrange);
        }
        // write alarm status if active
        if (!alarm.startsWith("null") && !alarm.startsWith("OK")) {
            writeAlarmInfo(nodeBlock, alarm);
        }
    }
    node.appendChild(nodeBlock);
}

/**
 * Adds html elements for a list of block objects to a given node.
 *
 * @param node The parent node.
 * @param blocks The list of block objects to display.
 * @return The updated node.
 */
function getDisplayBlocks(node, blocks) {
    for (var key in blocks) {
        var block = blocks[key];
        displayOneBlock(node, block, key);
    }
	
	return node;
}

/**
 * Adds html elements for the list of instrument information.
 *
 * @param node The parent node.
 * @param blocks The list of instrument blocks.
 * @return The updated node.
 */
function getDisplayRunInfo(node, blocks){
    clear(node)
    // Add all in order first
    for (var key in dictInstPV) {
        if (key in blocks) {
            var block = blocks[key];
            displayOneBlock(node, block, getTitle(key));
            delete blocks[key]
        }
    }

    // Add any left over on to the end
    getDisplayBlocks(node, blocks);
}

function writeStatus(nodeBlock, status_text) {
	var nodeBlockStatus = document.createElement("span");
	nodeBlockStatus.style = "color:blueviolet"
	nodeBlockStatus.appendChild(document.createTextNode(status_text.toUpperCase()));
	nodeBlock.appendChild(nodeBlockStatus);
}

function writePrivateValue(nodeBlock) {
	var nodeBlockStatus = document.createElement("I");
	nodeBlockStatus.appendChild(document.createTextNode("Unavailable"));
	nodeBlock.appendChild(nodeBlockStatus);
}

function writeRangeInfo(nodeBlock, rc_inrange) {
    var nodeBlockInrange = document.createElement("span");
    var colour = "Red";
    var mark_status = "\u274C"; // unicode cross mark

    if (rc_inrange == "YES") {
        colour = "Green";
        mark_status = "\u2713"; // unicode check mark
    }
	nodeBlockInrange.style = "color:"+color
    nodeBlockInrange.appendChild(document.createTextNode(mark_status));
    nodeBlock.appendChild(nodeBlockInrange);
}

function writeAlarmInfo(nodeBlock, alarm) {
    var nodeBlockAlarm = document.createElement("span");
    nodeBlockAlarm.style = "color:red"
	nodeBlockAlarm.appendChild(document.createTextNode("(" + alarm + ")"));
    nodeBlock.appendChild(nodeBlockAlarm);
}

// At the start, assume we can't connect
// This will update when a connection is made
$(document).ready(displayError());

$(document).ready(refresh());

setInterval(refresh, 5000);
