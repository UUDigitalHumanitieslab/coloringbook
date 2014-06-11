/*
	(c) 2014 Julian Gonggrijp, j.gonggrijp@uu.nl, Utrecht University
*/

var colors = ['#b11', '#c93', '#dd5', '#2e4', '#14c', '#818', '#963', '#fff', '#000'];
var color_chosen;
var first_command = null;
var last_command = null;
var page_onset;
var page, pages;
var pagenum = 0;
var page_data = [];
var form_data;
var images = {};
var image_count = 0;
var sentence_image_delay = 5000;  // milliseconds

button = function (color) {
	return '<span class="color_choice" style="border: 5px solid #fff; background-color: ' +
			color +
			'; width: 60px; height: 60px; border-radius: 20px; display: inline-block;"/>';
}

init_application = function ( ) {
	$('#instructions').hide();
	$('#sentence').hide();
	$('#controls').hide();
	$('#starting_form').submit(handle_form);
	init_controls();
	create_swatches(colors);
	$.ajax({
		type: 'GET',
		url: $SCRIPT_ROOT + 'static/test.json',
		dataType: 'json',
		success: function (resp, xmlstatus) {
			for (i in resp.images) {
				var image = resp.images[i];
				load_image(image.url, image.data, image.id);
			}
			image_count = resp.images.length;
			pages = resp.pages;
			var sounds = [];
			for (i in pages) {
				if (pages[i].audio) sounds.push(pages[i].audio);
			}
			$.ionSound({ "sounds": sounds, path: $SCRIPT_ROOT + 'static/' });
		},
		error: function (xhr, status, error) {
			alert(error);
		}
	});
}

handle_form = function (event) {
	event.preventDefault();
	$(this).hide();
	$('#instructions').show();
	form_data = $(this).serializeArray();
}

finish_instructions = function ( ) {
	$('#instructions').hide();
	if (image_count > 0 && Object.keys(images).length == image_count) {
		start_page();
	} else {
		$(document).ajaxStop(start_page);
	}
}

init_controls = function ( ) {
	$('#reset_image').click(function (event) {
		launch_reset_command();
		$('#undo_redo').attr('value', 'Herstel');
	});

	$('#undo_redo').click(function (event) {
		if ($(this).attr('value') == 'Herstel' && last_command) {
			last_command.undo();
			last_command = last_command.prev;
			$(this).attr('value', 'Opnieuw');
		} else {
			last_command = last_command.next;
			last_command.do();
			$(this).attr('value', 'Herstel');
		}
	});
}

set_image_dimensions = function ( ) {
	var image = $('svg');
	var win = $(window);
	var padding = $('body').css('padding').split('px')[0];
	image.css('max-height', win.height() - padding - $('.color_choice').outerHeight() + 'px');
	image.css('max-width', win.width() - 2 * padding + 'px');
}

create_swatches = function (colors) {
	var swatches = $('#swatches');
	swatches.empty();
	for (index in colors) {
		swatches.append(button(colors[index]));
	}
	color_chosen = colors[colors.length - 1];
	$('.color_choice').click(function (event) {
		color_chosen = $(this).css('background-color');
		$('.color_choice').css('border-color', '#fff');
		$(this).css('border-color', '#000');
	}).first().click();
}

load_image = function (url, data, name) {
	$.ajax({
		type: 'GET',
		url: $SCRIPT_ROOT + 'static/' + url,
		data: data,
		dataType: 'html',
		success: function (svg_resp, xmlstatus) {
			images[name] = svg_resp;
		},
		error: function (xhr, status, error) {
			alert(error);
		}
	});
}

add_coloring_book_events = function ( ) {
	$('path[class="colorable"]').click(function (event) {
		event.preventDefault();  // helpful on touchscreen devices
		launch_fill_command(this, color_chosen);
		$('#undo_redo').attr('value', 'Herstel');
	});
}

start_page = function ( ) {
	page = pages[pagenum];
	$('#sentence').html(page.text).show();
	window.setTimeout(start_image, sentence_image_delay);
	$.ionSound.play(page.audio);
}

start_image = function ( ) {
	var image = $('#coloring_book_image');
	image.empty();
	image.append(images[page.image]);
	set_image_dimensions();
	add_coloring_book_events();
	$('#sentence').hide();
	$('#controls').show();
	$(document).scrollTop(400);
	page_onset = $.now();
}

end_page = function ( ) {
	$('#controls').hide();
	page_data.push({
		"id": page.id,
		"actions": serialize_commands(first_command)
	});
	if (++pagenum < pages.length) {
		first_command = last_command = null;
		start_page();
	} else {
		display_data();
	}
}

display_data = function ( ) {
	var data = {
		subject: form_data,
		results: page_data
	};
	$('#starting_form').html('<pre>' + JSON.stringify(data, null, '\t') + '</pre>').show();
}

command = function (previous) {
	if (previous) {
		this.prev = previous;
		if (previous.next) {
			if (previous.old_succ) {
				previous.old_succ.push(previous.next);
			} else {
				previous.old_succ = [previous.next];
			}
		}
		previous.next = this;
	} else {
		first_command = this;
		this.prev = new command(this);  // trick to prevent infinite recursion
		this.prev.next = this;
		this.next = null;
	}
	this.json = { toggle: [] };
	this.toggle = function ( ) { this.json.toggle.push($.now() - page_onset); };
	this.do = this.undo = function ( ) { };
}

launch_fill_command = function (target, value) {
	var cmd = new command(last_command);
	cmd.target = target;
	cmd.color = value;
	cmd.prior = $(target).attr('fill');
	cmd.do = function ( ) {
		this.toggle();
		$(cmd.target).attr('fill', this.color);
	}
	cmd.undo = function ( ) {
		this.toggle();
		$(this.target).attr('fill', this.prior);
	}
	cmd.json.action = 'fill';
	cmd.json.target = target.id;
	cmd.json.color = value;
	cmd.do();
	last_command = cmd;
}

launch_reset_command = function ( ) {
	var cmd = new command(last_command);
	cmd.target = $('path[class="colorable"]:not([fill="white"])');
	cmd.target.each(function ( ) {
		this.prior = $(this).attr('fill');
	});
	cmd.do = function ( ) {
		this.toggle();
		this.target.attr('fill', 'white');
	}
	cmd.undo = function ( ) {
		this.toggle();
		this.target.each(function ( ) {
			$(this).attr('fill', this.prior);
		});
	}
	cmd.json.action = 'reset';
	cmd.do();
	last_command = cmd;
}

serialize_commands = function (current_cmd) {
	sequence = [];
	while (current_cmd) {
		sequence.push(current_cmd.json);
		if (current_cmd.old_succ) {
			for (i in current_cmd.old_succ) {
				sequence = $.merge(sequence, serialize_commands(current_cmd.old_succ[i]));
			}
		}
		current_cmd = current_cmd.next;
	}
	return sequence;
}
