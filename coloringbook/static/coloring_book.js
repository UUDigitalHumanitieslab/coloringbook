/*
	(c) 2014 Julian Gonggrijp, j.gonggrijp@uu.nl, Utrecht University
*/

var colors = ['#b11', '#c93', '#dd5', '#2e4', '#14c', '#818', '#963'];
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
var sentence_image_delay = 500;  // milliseconds

lang_field = function (count) {
	var lang = 'name="language' + count + '"';
	var level = 'name="level' + count + '"';
	return '<label ' + lang + '>Taal ' + count + '</label>' +
		'<input type="text" ' + lang + '/> ' +
		'<label ' + level + '>Niveau</label>' +
		'<input type="number" ' + level + ' min="1" max="10" step="1"/><br/>';
}

button = function (color) {
	return $('<span class="color_choice" style="background-color: ' +
			color +
			';"/>').data('color', color);
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
	var raw_form = $(this).serializeArray();
	form_data = { languages: [] };
	for (i in raw_form) {
	    if (raw_form[i].name == 'nativelang') {
	        form_data.languages.push([raw_form[i].value, 10]);
	    } else if (raw_form[i].name.match('language[0-9]')) {
	        form_data.languages.push([raw_form[i].value]);
	    } else if (RegExp('[0-9]+').test(raw_form[i].name)) {
	        var level = RegExp('[0-9]+').exec(raw_form[i].name);
	        form_data.languages[level].push(parseInt(raw_form[i].value, 10));
	    } else {
	        form_data[raw_form[i].name] = raw_form[i].value;
	    }
	}
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
	$('#starting_form >[name="more"]').click(function () {
		var self = $(this);
		var count = self.data('count');
		if (count) count++; else count = 1;
		self.data('count', count);
		self.before(lang_field(count));
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
	$(button('#fff')).appendTo(swatches).append('<img src="' + $SCRIPT_ROOT + 'static/lmproulx_eraser.png" title="Gum" alt="Gum"/>');
	color_chosen = $('.color_choice').first();
	$('.color_choice').click(function (event) {
		color_chosen.css('border-color', '#fff');
		color_chosen = $(this);
		color_chosen.css('border-color', '#000');
	});
	color_chosen.click();
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
		launch_fill_command(this, color_chosen.data('color'));
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
	page_data.push(serialize_commands(first_command));
	if (++pagenum < pages.length) {
		first_command = last_command = null;
		start_page();
	} else {
		send_data();
	}
}

send_data = function ( ) {
	var data = {
		survey: 'test',
		subject: form_data,
		results: page_data
	};
	$.ajax({
		type: 'POST',
		url: $SCRIPT_ROOT + 'submit',
		'data': JSON.stringify(data),
		contentType: 'application/json',
		success: function (result) {
			alert(result);
		}
	});
}

command = function (previous) {
	if (previous) {
		this.prev = previous;
		previous.next = this;
	} else {
		first_command = this;
	}
	this.json = { };
	this.toggle = function ( ) { this.json.time = $.now() - page_onset; };
	this.do = function ( ) { };
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
	cmd.json.action = 'fill';
	cmd.json.target = target.id;
	cmd.json.color = value;
	cmd.do();
	last_command = cmd;
}

serialize_commands = function (current_cmd) {
	sequence = [];
	while (current_cmd) {
		sequence.push(current_cmd.json);
		current_cmd = current_cmd.next;
	}
	return sequence;
}
