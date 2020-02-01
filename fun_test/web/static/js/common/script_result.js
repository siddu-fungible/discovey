///angular.module('FUN_XML', ['ngMaterial']);

function showAlert(message, alerttype) {
   $('#alert_placeholder').append('<br><br><br><div id="alertdiv" class="alert ' +  alerttype + '"><a class="close" data-dismiss="alert">×</a><pre>' + message + '</pre><span></span></div>');
    var timeout = 5000;
    if (alerttype === "alert-danger") {
        timeout = 60 * 1000;
    }
    setTimeout(function() {
       $("#alertdiv").remove();
    }, timeout);
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function setup_ajax() {
    var csrftoken = getCookie('csrftoken');
	$.ajaxSetup({
	    beforeSend: function(xhr, settings) {
		if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
		    xhr.setRequestHeader("X-CSRFToken", csrftoken);
		}
	    }
	});

}

function loadTopologyJson() {
    var container = document.getElementById('topology-json');
    dataPath = container.getAttribute("data-path");
    var options = {};
    var editor = new JSONEditor(container, options);
    console.log(dataPath);
    $.getJSON( dataPath, function( data ) {
        editor.set(data);
    });
}

jQuery(function($){

    $("#summary_toggle").click(function(e) {
        e.preventDefault();
        $("#wrapper").toggleClass("toggled");
        var txt = "";
        if ($("#summary_collapse").hasClass("fa-caret-square-o-left")) {
            $("#summary_collapse").removeClass("fa-caret-square-o-left");
            $("#summary_collapse").addClass("fa-caret-square-o-right");
        } else {
            $("#summary_collapse").removeClass("fa-caret-square-o-right");
            $("#summary_collapse").addClass("fa-caret-square-o-left");
        }
        $('.navbar').width(40);
        $('#test_suite').hide();
    });

    $(".test_case_summary").click(function(e) {
        var fullHref = $(this).attr("href");
        var primaryHref = fullHref.split("_top")[0];
        $(primaryHref).collapse('show');
    });

    $('#test_suite').click(function(){
        $('html,body').animate({scrollTop:0},'slow');return false;
    });

    $('.checkpointlink').click(function(){
        //$('.navbar').width(40);
        var parent_id = $(this).attr("parent-id");
        var parent = $("#" + parent_id);

        if ($(this).is("div")) {
            var this_href = $(this).attr("href").replace("#", '');
            var aId = this_href;
            //location.href = this_href;

            setTimeout(function(){
                $('html, body').animate({scrollTop: $("#" + aId).offset().top}, 1);

            },200);
            if (!$(parent).hasClass("in")) {
                $(parent).collapse('show');
            }

        } else {
            if ($(parent).hasClass("in")) {
                //$(parent).removeClass("in")
            } else {
                //$(parent).addClass("in")
                $(parent).collapse('show');
                var this_href = $(this).attr("href").replace("#", '');
                var aTag = $("a[name='"+ this_href +"']");
                //location.href = this_href;

                    $('html, body').animate({scrollTop: aTag.offset().top}, 500);
            }
        }



        //$('#test_suite').hide();
    });

    $('#test_case_summary_filter').keyup(function () {
        var rex = new RegExp($(this).val(), 'i');
        $('.test_case_summary_row').hide();
        $('.test_case_summary_row').filter(function () {
        return rex.test($(this).text());
        }).show();
    });


    $('.checkpointfilter').keyup(function () {
        var filterId = $(this).attr("id");
        var filterHref = filterId.split("__")[1];
        var rex = new RegExp($(this).val(), 'i');
        checkpointRowClass = ".checkpointrow_" + filterHref;
        $(checkpointRowClass).hide();
        $(checkpointRowClass).filter(function () {
        return rex.test($(this).text());
        }).show();
    });

    $("#test-case-publish-button").click(function(event){
        $("#test-case-publish-button").prop("disabled", true);
        event.preventDefault();
        var setup_summary = "Setup Summary"
        var setup_steps = "Setup Steps"

        var row_count = $('#documentation-table > tbody > tr').length;
        row_count = row_count - 1;
        step_size = 100/row_count;
        var current_step = 1;
        $('#documentation-table > tbody  > tr').each(function() {
            var one_row = [];
            var tableData = $(this).children("td").map(function() {
                //console.log($(this).text());
                one_row.push($(this).html())
            });

            if (one_row.length > 0) {     // Skip table header
                $("#progress-bar-container").css("display", "");
                one_row_dict = {}
                test_case_id = one_row[0];
                test_case_summary = one_row[1];
                one_row_dict["summary"] = test_case_summary;
                one_row_dict["id"] = test_case_id;
                one_row_dict["full_script_path"] = $("#documentation").attr("full-script-path")
                var regex = /<br\s*[\/]?>/gi;
                var steps = one_row[2].replace(regex, "\n");
                one_row_dict["steps"] = steps;
                if (test_case_id === "0"){
                    setup_summary = test_case_summary;
                    setup_steps = steps
                }
                one_row_dict["setup_summary"] = setup_summary;
                one_row_dict["setup_steps"] = setup_steps;
                setup_ajax();
                var url = "/publish";

                (function(test_case_summary){
                setTimeout(()=>{
                    $("#documentation-logs-table").css("display", "");
                    $("#documentation-logs-table").append("<tr><td>Publishing " + test_case_summary + " ... </td></tr>");
                    console.log("Appended");
                }, 0);
                }(test_case_summary));
                $.ajax({
                    url: url,
                    dataType: 'json',
                    type: 'post',
                    contentType: 'application/json',
                    data: JSON.stringify(one_row_dict),
                    success: function(data) {
                        if (data["status"] === "PASS") {  // TODO: How do we extract this string from fun_global?
                            $.each(data["logs"], function(index, value) {
                                $("#documentation-logs-table").css("display", "");  //TODO: redundant
                                $("#documentation-logs-table").append("<tr><td>" + value + "</td></tr>");

                                $("#publish-progress-bar").css("width", (step_size * current_step) + "%");
                                current_step += 1;
                                if(current_step == (row_count)) {
                                    $("#spinner").hide();
                                }
                            })
                        } else {
                            $.each(data["logs"], function(index, value) {
                                $("#documentation-logs-table").css("display", "");
                                $("#documentation-logs-table").append("<tr><td>" + value + "</td></tr>");
                            })
                        }
                    },
                    error: function(data) {
                        showAlert(data.responseText, "alert-danger");
                    }
                });


            }

            console.log("Incrementing step");
        });


        /*
        $.ajax({
            url: url,
            dataType: 'json',
            type: 'post',
            contentType: 'application/json',
            data: JSON.stringify(all_rows),
            success: function(data) {
                if (data["status"] === "PASS") {  // TODO: How do we extract this string from fun_global?
                    $.each(data["logs"], function(index, value) {
                        $("#documentation-logs-table").css("display", "");  //TODO: redundant
                        $("#documentation-logs-table").append("<tr><td>" + value + "</td></tr>");
                    })
                } else {
                    $.each(data["logs"], function(index, value) {
                        $("#documentation-logs-table").css("display", "");
                        $("#documentation-logs-table").append("<tr><td>" + value + "</td></tr>");
                    })
                }
            },
            error: function(data) {
                showAlert(data.responseText, "alert-danger");
            }
        });*/

    })

    $('.long_summary_button').click(function(){
       var buttonId = $(this).attr("id");
       var longDescriptionId = "#" + buttonId.replace("long_summary_button", "long_summary");
       if(!$(longDescriptionId).is(":hidden"))
         {
           $(longDescriptionId).hide();
         }
       else
         {
           $(longDescriptionId).show();
         }
    });



    $(document).ready(function() {
         /*angular
            .module('FUN_XML', ['ngMaterial'])*/
         loadTopologyJson();
    });

    $("#test-button").click(function(){
        $("#documentation-logs-table").css("display", "");
        $("#documentation-logs-table").append("<tr><td>ABC</td></tr>");
    });

    $("#fetch-script-button").click(function(){
        var url = "/get_script_content"
        var full_script_path = $("#documentation").attr("full-script-path");
        var payload = {"full_script_path": full_script_path};
        $.ajax({
            url: url,
            dataType: 'text',
            contentType: 'application/json',
            type: 'post',
            data: JSON.stringify(payload),

            success: function(data) {
                $("#code-section").text(data);
            },
            error: function(data) {
                showAlert(data.responseText, "alert-danger");
            }
        });

    });


});