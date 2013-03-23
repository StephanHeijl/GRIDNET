$(function() {
	currentLocation = window.location.href.split("/");
	currentLocation = currentLocation.splice(0,currentLocation.length-1).join("/")
	console.log(currentLocation)
	
	function setBackground() {
		bgKey = "user_"+$("strong#userID").text()+"_background"
		if ( localStorage.getItem(bgKey+"_image")) {
			size = localStorage.getItem(bgKey+"_size")
			
			if(!size) {
				size = "cover";
			}
			
			bg = localStorage.getItem(bgKey+"_image");
			$("body").css( {
								"background-image":"url(data:image/png;base64,"+bg+")",
								"background-position":"center center",
								"background-size":size								
							} )
		} else {
			$("body").css( {
								"background-image":"url()",
							} )
		}
	}
	setBackground();
	
	function switchScreen(tile, screen) { // Switches screen to different set of tiles
		if (screen) {
			scr = currentLocation + "/screen.htm?screen="+screen

			if(tile) {
				tile.css({"transition":"0.2s","transform":"scale(2.5)","opacity":"0"})
				$("#tiles").css({"transition":"0.8s","transform":"translate(-"+$(document).width()*1.2+"px,0%)"})
				
				setTimeout(function() { $("#tiles").load(scr, function() { 
					$("#tiles").css({"transition":"0s","transform":"translate(100%,0%)"})
					$("#tiles").css({"transition":"0.8s","transform":"translate(0%,0%)"})
				}); }, 400);
				
			} else {
				$("#tiles").load(scr);
			}
				
		}
	}
	
	function switchCont(tile, cont) { // Switches the content panel
		if (cont) {
			// Handle optional format arguments
			args = []
			for (arg in arguments) {
				args.push(arguments[arg])
			}			
			format = JSON.stringify(args.slice(2))
			con = currentLocation + "/cont.htm?cont="+cont+"&format="+format
			
			if(tile) {
				$("#main").css({"transition":"0.8s","transform":"translate(-"+$(document).width()*1.2+"px,0%)"})
			
				setTimeout(function() {
					$("#main").load(con, function() {
						$("#main").css({"transition":"0s","transform":"translate(100%,0%)"})
						$("#main").css({"transition":"0.8s","transform":"translate(0%,0%)"})
					}); }, 400)
			} else {
				$("#main").load(con);
			}
		}
	}
	
	function doAction(tile,action) {
		if(action == undefined) {
			return false;
		}
		action = action.split(":")
		if(action[0] == "followurl") {
			window.location = action[1];
		} else {
			eval(action[0] + "(" + action[1] + ")")
		}
	}
	
	$(".tile, a").live("click", function() {
											switchScreen($(this), $(this).attr("screen"))
											switchCont($(this), $(this).attr("cont"))
											doAction($(this), $(this).attr("action"))
										});
	
	function fillNodeTasks() {
		tasks = {};
		$.getJSON( "tasks.get?node="+$("#field_Node").attr("value"), function(data) { 
			
			loadTaskTable(data);
		});
	}
	
	function loadTaskTable(tasks) {
		$.getJSON( "tasks.get", function(data) {
			$("table, input[type=submit]").remove()
			table = $("<table>")
			table.append("<thead> <tr> <td> <input type=\"checkbox\" /> </td> <td> Task </td> <td> Command/Path </td> </tr> </head>") 
			for (t in data) {
				// Make neat little DOM elements :D 
				row = $("<tr>")
				col1 = $("<td>")
				
				console.log(tasks)
				if (tasks.hasOwnProperty(parseInt(data[t][0]))) {
					cb = $("<input>", {"type":"checkbox", "checked":true, "name":"task_" + parseInt(data[t][0])})
					path = $("<input>", {"type":"text", "value":tasks[parseInt(data[t][0])], "name":"path_" + parseInt(data[t][0]), "placeholder": data[t][2]})
					help = $("<td>", {"tooltip":"This task is enabled. You can change the path, or leave it empty for the grid default."})
					console.log(tasks[parseInt(data[t][0])]);
				} else {
					cb = $("<input>", {"type":"checkbox", "checked":false, "name":"task_" + parseInt(data[t][0])})
					path = $("<input>", {"type":"text", "name":"path_" + parseInt(data[t][0]), "placeholder": data[t][2]})
					help = $("<td>", {"tooltip":"The node does not have this task enabled."})
				}
				col1.append(cb)
				col2 = $("<td>").text(data[t][1])
				col3 = $("<td>")
				col3.append(path)
				help.text("?")
				row.append(col1).append(col2).append(col3).append(help)
								
				table.append(row)
			}
			
			$("#main > form").append(table)
			$("#main > form").append($("<input>", {"type":"submit"}))
		});
	}
	
	function reloadNodes() {
		$("#field_Node").prop("disabled",true)
		$.get( "nodesDropdown.get" + "?" + 
									"task=" + $("select[name=Task]").val() +
									"&grid=" + $("#field_Grid").val() +
									"&online=" + ($("#online_only").is(":checked") ? 1 : 0) ,
		function(data) { 
			$("#field_Node").html(data)
			$("#field_Node").prop("disabled",false)
		});
	}
	
	$("#field_Node").live("click, focus", reloadNodes );
	$("select[reloadnodes]").live("change",reloadNodes);
	$("select[fillnodetasks]").live("change",fillNodeTasks);
	
	$("select[loadjson]").live("focus", function() {
		if( $(this).attr("loadjson").match(/nodesDropdown.get/) ) {
			return
		}
		
		sel = $(this)
		sel.prop("disabled",true)
		if(sel.attr("loaded")!="loaded") {
			$.get( sel.attr("loadjson"), function(data) { 
				sel.html(data)
				sel.attr("loaded","loaded")
				sel.prop("disabled",false)
			});
			return false;
		}
		sel.prop("disabled",false)
	});
	
	switchScreen(undefined, "start");
	switchCont(undefined, "start");	
	
	$("#newproject li > span").live("click", function() { 
		$(this).parent().toggleClass("configured")
		$(this).parent().children(".options").toggle(300);
		return false;
	});
	
	$(".removeJob").live("click", function() {
		job = $(this)
		noty({text:"Are you certain you want to remove this job and its results?", layout:"bottom", buttons: [
			{addClass: 'btn btn-primary', text: 'Yes, remove the job.', onClick: function($noty) {
				row = job.parents("tr")
				
				$.get("jobs/Remove?id=" + job.attr("name"), function() { 
					row.find("td").fadeOut(200, function(){ $(this).parent().remove();});
				});
			
				$noty.close();
			  }
			},
			{addClass: 'btn btn-primary', text: 'No, I want to keep the job.', onClick: function($noty) {
				$noty.close();
			  }
			}
		  ]})
	});
	
	$(".restartJob").live("click", function() {
		job = $(this)
		noty({text:"Are you certain you want to restart this job? You may lose your results in the process.", layout:"bottom", buttons: [
			{addClass: 'btn btn-primary', text: 'Yes, restart the job.', onClick: function($noty) {
				row = job.parents("tr")
				
				$.get("jobs/Refresh?id=" + job.attr("name"), function() { 
					row.children("td").children("progress").val(0)
					row.children("td:nth-child(5)").text("Refreshed")
				});
			
				$noty.close();
			  }
			},
			{addClass: 'btn btn-primary', text: 'No, don\'t alter the job state.', onClick: function($noty) {
				$noty.close();
			  }
			}
		  ]})
	});

	$("form[ajaxAction]").live("submit", function() {
		try {
			formData = new FormData($("form")[0]);
		} catch(err) {
			return false;
		}
		switchContAttr = $(this).attr("switchCont")

		$.ajax({
			url:$(this).attr("ajaxAction"), 
			type: "POST",
			data: formData, 
			success:function(data) {
						response = JSON.parse(data)
						if(response['Response'] == "OK") {
							if(switchContAttr && switchContAttr.length != 0) {
								switchCont($(this), switchContAttr)
							} else {	
								switchCont($(this), "successsubmit_generic")
							}
						} else {
							noty({text:"An error occured: "+response['Response'], layout:"bottom",type:"error"})
						}
					},
			xhr:	function() {  // custom xhr
						myXhr = $.ajaxSettings.xhr();
						return myXhr;
					},
			cache: false,
		    contentType: false,
		    processData: false
		});	
		return false
	});
	$("button#removeBackground").live("click", function() {
		noty({text:"Are you certain you want to remove your current background?", layout:"bottom", buttons: [
			{addClass: 'btn btn-primary', text: 'Yes, remove the background.', onClick: function($noty) {
				delete localStorage["user_"+$("strong#userID").text()+"_background_image"];
				delete localStorage["user_"+$("strong#userID").text()+"_background_size"];
				setTimeout(1000, setBackground)
				noty({text:"The background has been removed. You may need to reload the page to make the changes permanent.", type:"information", layout:"bottom"});
				$noty.close();
			  }
			},
			{addClass: 'btn btn-primary', text: 'No, I want to keep my background.', onClick: function($noty) {
				conf = false;
				$noty.close();
			  }
			}
		  ]})
	});
	
	$("form#changeBackground").live("submit", function() {
		formData = new FormData($(this)[0]);
		size = $("form#changeBackground input[name=background_size]:checked").val()
		$.ajax({
			url:"imageB64.get", 
			type: "POST",
			data: formData, 
			success:function(data) {
						response = JSON.parse(data)
						if(response['Response'] == "OK") {
							try {
							localStorage.setItem(
													"user_"+$("strong#userID").text()+"_background_image",
													response['encoded']
												);									
							localStorage.setItem(
													"user_"+$("strong#userID").text()+"_background_size",
													size
												);
												
							} catch(QuotaExceededError) {
								msg = "There are currently too many sessions with backgrounds on this computer " +
									   "the background is too large, or you have private mode turned on. " + 
									   "A background cannot be set";

								noty({text:msg, layout:"bottom",type:"error"})
							}
							setBackground();
						} else {
							noty({text:"An error occured: "+response['Response'], layout:"bottom",type:"error"})
						}
					},
			xhr:	function() {  // custom xhr
						myXhr = $.ajaxSettings.xhr();
						return myXhr;
					},
			cache: false,
		    contentType: false,
		    processData: false
		});	
	});
	
	dragging = false;
	$("#top_bar_handle").mousedown(function() {
		dragging = true;
		return false;
	});
	$("#top_bar_handle").mouseup(function(e) {
		if(e.pageX > 200) {
			$("#top_bar").animate({"height":"200px"},400);
		}
		dragging = false;
	});
	$("#top_bar_handle").mouseout(function foldNotifications(e) {
		if(dragging) {
			if(e.pageY > $("#top_bar").height()) {
				$("#top_bar").animate({"height":"200px"},400);
			} else {
				$("#top_bar").animate({"height":"12px"},400);
			}
			dragging = false;
		}
	});
	$("#top_bar_handle").mousemove(function(e) {
		if(dragging) {
			$("#top_bar").height(e.pageY+20);
		}
	});
	$("#top_bar_handle").click(function(e) {
		h = $("#top_bar").height();
		if(h == 12) {
			$("#top_bar").animate({"height":"200px"},400);
		} else if (h < 201){
			$("#top_bar").animate({"height":"12px"},400);
		}
	});
	
	$("#addFileField").live("click",function() {
		lastfilefield = $("#file_fields input").last().attr('name');
		
		n = lastfilefield.substr(lastfilefield.length-1);
		console.log(n);
		nn = 0
		if(parseInt(n)>=0) {
			nn = parseInt(n)+1
		}
		newfilefield = $("<input>",{'type':'file', 'name':'File_'+nn});
		$("#file_fields").append(newfilefield).append("<br/>");
	});
	
	$("#showOfflineNodes").live("click", function() {
		$(".node[state=offline]").css("display","table-row")
		$(this).fadeOut(200);
		return false;
	});
	
	$("#online_only").live("change", function() {
		if( $(this).is(':checked') ) {
			$("#field_Node").attr("loadjson", "nodesDropdown.get?online=1");
		} else {
			$("#field_Node").attr("loadjson", "nodesDropdown.get?online=0");
			$("#field_Node").attr("loaded", "0");
		}
		reloadNodes();
	});
	
	// This function handles showing the tooltips
	$("*[tooltip]").live("mousemove",function(e) {
		y = 50
		x = 10
		// Set the text in the tooltip to the text belonging to the element and adjust the tooltip position to follow the cursor
		$("#tooltip").text($(this).attr("tooltip")).css({"top":e.pageY-y,"left":e.pageX-x,"display":"block"})
	})
	// Hide the tooltip when leaving the element
	$("*[tooltip]").live("mouseleave",function(e) {
		$("#tooltip").css("display","none")
	})
	
});

function getCurrentJobs(all) {
	html = "";
	if(!all) {
		all = ""
	}
	statuses = new Array();
	statuses["Queued"] = 10;
	statuses["Submitted"] = 20;
	statuses["Working"] = 30;
	statuses["Completed"] = 100;
	
	$.getJSON("jobs.get?all="+all, function(data) { 
		html += "<thead><td>ID</td><td>Owner</td><td>Task</td><td>Created on</td><td colspan=2>Status</td></thead>"
		for(job in data) {
			id = data[job]['ID']
			
			
			
			html += "<tr>\n	 <td>"+id+"</td> \n\
						 <td>"+data[job]['Owner']+"</td> \n"
						 
			desc = data[job]['Description'].replace("'","&rsquo;")
			if(desc.length > 0 ) {
				if( desc.length < 75 ) {
					html+="<td tooltip='"+desc+"'>"+data[job]['Task']+"</td> \n"
				} else {
					html+="<td tooltip='"+desc.substring(0,72)+"...'>"+data[job]['Task']+"</td> \n"
				}
			} else {
				html+="<td tooltip='This job has no description.'>"+data[job]['Task']+"</td> \n"
			}		 
						 
			html+=      "<td>"+data[job]['Created_On']+"</td> \n\
						 <td>"+data[job]['Status']+"</a></td> \n\
						 <td><progress value="+statuses[data[job]['Status']]+" max=100></progress></td> \n\
						 \
						 <td><img src='files/img/refresh.png' class='restartJob' tooltip='Restart this job' name='" + id + "'/></td> \n"
			
			if(data[job]['Status'] == "Completed") {
				html+= "<td><a href='jobs/Results?id="+id+"'><img src='files/img/package_go.png' tooltip='Download results'></a></td>"
			} else {
				html+= "<td><img src='files/img/package_go_g.png' tooltip='No results are available'></td>"
			}
			
			html+= "<td><img src='files/img/cross.png' class='removeJob' tooltip='Remove this job.' name='"+id+"'/></td> \n\
					</tr>"
		}
		$("#currentJobs").html(html);
	})
	
}

function getCurrentGrids() {
	html = "<table>";
	statuses = new Array();
	
	$.getJSON("grids.get", function(data) { 
		html += "<thead><td></td><td>Name</td><td></td><td>Slot Status</td><td>Connected</td><td>Last Update</td></thead>"
		
		for(grid in data) {
			state = data[grid]['state']
					
			if (state == "Stale") {
				html+= "<tr class='grid grid_"+state+"' tooltip=\"This grid hasn't been updated in some time. It may still be active, but it can currently not be reached.\"><td><img src='files/img/world_grey.png' /></td>"
			} else {
				html+= "<tr class='grid grid_"+state+"' tooltip='This grid is online.'><td><img src='files/img/world.png' /></td>"
			}

			
			html+= "<td>"+grid+"<td/><td></td><td></td><td>"+data[grid]['last_update']+"</td></tr>"
			
			online = "";
			offline = "";
			for(node in data[grid]['nodes']) {			
				if(data[grid]['nodes'][node]['online']) {
					
					if(state == "Stale") {
						online+= "<tr class='node' state=online><td><img src='files/img/accept_grey.png' /></td><td>"+node+"<td/><td>"
					} else {
						online+= "<tr class='node' state=online><td><img src='files/img/accept.png' /></td><td>"+node+"<td/><td>"
					}
					
					for (slot in data[grid]['nodes'][node]['slots']) {
						online+= data[grid]['nodes'][node]['slots'][slot]+ "<br/>"
					}
					
					online+="</td><td>Yes</td></tr>"
				} else {
					offline+= "<tr class='node' state=offline><td><img src='files/img/stop.png' /></td><td>"+node+"<td/><td></td><td>No</td><td>"
				}
			}
			html += online + offline;
		}
		
		html+= "</table><br/><a id='showOfflineNodes' href='#'> Show offline nodes</a>"
		
		$("#currentGrids").html(html);
	})
	
}
