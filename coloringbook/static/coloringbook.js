/*
	(c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
	Author: Julian Gonggrijp, j.gonggrijp@uu.nl
	
	It is helpful to think of this script as an event-driven state machine.
*/

var base = (function() {
	var endpos = location.pathname.search('/book');
	if (endpos == -1) endpos = location.pathname.search('/admin');
	return location.pathname.slice(0, endpos);
}());
var colors = ["#d01", "#f90", "#ee4", "#5d2", "#06e", "#717", "#953"];
var color_chosen;
var simultaneous = false;
var first_command = null;
var last_command = null;
var page_onset;
var page, pages;
var pagenum = 0;
var page_data = [];
var form_data, evaluation_data = {};
var images = {};
var image_count = 0;
var sentence_image_delay = 6000;  // milliseconds

// Generates the HTML code for the form fields that let the subject
// add another language (i.e. the `count`th language).
lang_field = function (count) {
	var lang = '="language' + count + '"';
	var level = '="level' + count + '"';
	return '<label for' + lang + '>Taal ' + count + '</label>' +
		'<input type="text" name' + lang + 'id' + lang + ' required="required"/> ' +
		'<label for' + level + '>Niveau</label>' +
		'<input type="number" name' + level + 'id' + level + ' min="1" max="10" step="1"/><br/>';
}

// Generates the HTML code for a swatch.
button = function (color) {
	return $('<span class="color_choice" style="background-color: ' +
			color +
			';" id="' +
			color.substr(1, 3) +
			'"/>').data('color', color);
}

// All the things that need to be done after the DOM is ready.
init_application = function ( ) {
	$('#instructions').hide();
	$('#sentence').hide();
	$('#controls').hide();
	var now = new Date(),
	    century_ago = new Date();
	century_ago.setFullYear(now.getFullYear() - 100);
	$('#starting_form').validate({
		submitHandler: handle_form,
		onkeyup: false,
		rules: {
			birth: {
				daterange: [century_ago.toShortString(), now.toShortString()]
			}
		}
	});
	$('#ending_form').hide().validate({
		submitHandler: handle_evaluation,
		onkeyup: false
	});
	init_controls();
	create_swatches(colors);
	
	// The part below retrieves the data about the coloringbook pages.
	$.ajax({
		type: 'GET',
		url: window.location.pathname,
		dataType: 'json',
		success: function (resp, xmlstatus) {
			for (var l = resp.images.length, i = 0; i < l; ++i) {
				load_image(resp.images[i]);
			}
			image_count = resp.images.length;
			var sounds = [];
			for (var n = resp.sounds.length, i = 0; i < n; ++i) {
				sounds.push({name: resp.sounds[i]});
			}
			ion.sound({"sounds": sounds, path: base + '/static/', preload:true});
			pages = resp.pages;
			if (resp.simultaneous) {
				simultaneous = true;
				sentence_image_delay = 0; // show image at same time as sentence
				$('#sentence').css('font-size', '24pt');
			} else {
				sentence_image_delay = resp.duration;
				$('#sentence').css('font-size', '48pt');
			}
		},
		error: function (xhr, status, error) {
			alert(error);
			console.log(xhr);
		}
	});
}

// Return strings of the format YYYY-MM-DD.
Date.prototype.toShortString = function ( ) {
	return this.toISOString().substring(0, 10);
}

// Daterange checker for jQuery.validate.
// adapted from http://stackoverflow.com/questions/3761185/jquery-validate-date-range
$.validator.addMethod('daterange', function(value, element, arg) {
	if (this.optional(element)) return true;

	var startDate = Date.parse(arg[0]),
		endDate = Date.parse(arg[1]),
		enteredDate = Date.parse(value);

	if(isNaN(enteredDate)) return false;

	return ((startDate <= enteredDate) && (enteredDate <= endDate));
}, $.validator.format("De datum moet tussen {0} en {1} liggen."))

// Put personalia form data into compact JSON format.
// Result saved globally.
handle_form = function (form) {
	$(form).hide();
	$('#instructions').show();
	var raw_form = $(form).serializeArray();
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

// Event handler for the "klaar" button.
finish_instructions = function ( ) {
	$('#instructions').hide();
	if (image_count > 0 && Object.keys(images).length == image_count) {
		start_page();
	} else {
		$(document).ajaxStop(start_page);
	}
}

// Add more language fields when requested.
init_controls = function ( ) {
	$('#starting_form >[name="more"]').click(function () {
		var self = $(this);
		var count = self.data('count');
		if (count) count++; else count = 1;
		self.data('count', count);
		self.before(lang_field(count));
	});
}

// Ensure that the page fills the screen exactly by scaling the SVG image.
set_image_dimensions = function ( ) {
	var image = $('svg');
	var win = $(window);
	var padding = $('body').css('padding').split('px')[0];
	var maxheight = win.height() - 2 * padding - 50 - $('.color_choice').outerHeight();
	if (simultaneous) maxheight -= $('#sentence').outerHeight();
	image.css('max-height', maxheight + 'px');
	image.css('max-width', win.width() - 2 * padding + 'px');
}

// Insert swatch buttons into the appropriate container element,
// adding click event handlers as well as a white button.
// Also sets the initially selected color.
insert_swatches = function (colors) {
	var swatches = $('#swatches');
	swatches.empty();
	for (index in colors) {
		swatches.append(button(colors[index]));
	}
	$(button('#fff')).appendTo(swatches);
	color_chosen = $('.color_choice').first();
	$('.color_choice').mousedown(function (event) {
		color_chosen.css('border-color', '#fff');
		color_chosen = $(this);
		color_chosen.css('border-color', '#000');
	});
	color_chosen.mousedown();
}

// Insert swatches and disguise the last (white) swatch as an eraser.
create_swatches = function (colors) {
	insert_swatches(colors);
		var eraser_path = base + '/static/lmproulx_eraser.png';
	$('.color_choice').last().append('<img src="' + eraser_path + '" title="Gum" alt="Gum"/>');
}

// Retrieve an SVG image by filename.
load_image = function (name) {
	$.ajax({
		type: 'GET',
		url: base + '/static/' + name,
		dataType: 'html',
		success: function (svg_resp, xmlstatus) {
			images[name] = svg_resp;
		},
		error: function (xhr, status, error) {
			alert(error);
		}
	});
}

// Add click event handlers to all .colorable areas in the SVG.
add_coloring_book_events = function ( ) {
	$('path[class~="colorable"]').mousedown(function (event) {
		event.preventDefault();  // helpful on touchscreen devices
		launch_fill_command(this, color_chosen.data('color'));
		$('#undo_redo').attr('value', 'Herstel');
	});
}

// Start a new coloring page by (dis)playing the sentence and set a
// timeout for displaying the image (possibly zero).
start_page = function ( ) {
	page = pages[pagenum];
	$('#sentence').html(page.text).show();
	window.setTimeout(start_image, sentence_image_delay);
	if (page.audio) {
		ion.sound.play(page.audio);
		if (simultaneous) {
			$('#speaker-icon').clone().attr({id: null}).click(function() {
				ion.sound.play(page.audio);
			}).show().prependTo('#sentence');
		}
	}
}

// Display the colorable image and prepare it for coloring.
// Initializes the clock for coloring actions.
start_image = function ( ) {
	var image = $('#coloring_book_image');
	image.empty();
	image.append(images[page.image]);
	if (! simultaneous) $('#sentence').hide();
	$('#controls').show();
	set_image_dimensions();
	add_coloring_book_events();
	page_onset = $.now();
}

// Serialize data and do some cleanup after the subject is done
// coloring the page. Prepare for the next stage, i.e. either another
// coloring page or the evaluation form.
end_page = function ( ) {
	$('#controls').hide();
	$('#sentence').hide();
	page_data.push(serialize_commands(first_command));
	if (++pagenum < pages.length) {
		first_command = last_command = null;
		start_page();
	} else {
		$('#ending_form').show();
	}
}

// Serialize the evaluation form data and trigger uploading of all data.
handle_evaluation = function (form) {
	var raw_data = $(form).serializeArray();
	for (var l = raw_data.length, i = 0; i < l; ++i) {
		evaluation_data[raw_data[i].name] = raw_data[i].value;
	}
	send_data();
}

// Upload all data and handle possible failure.
send_data = function ( ) {
	var data = {
		subject: form_data,
		results: page_data,
		evaluation: evaluation_data
	};
	$.ajax({
		type: 'POST',
		url: window.location.pathname + '/submit',
		'data': JSON.stringify(data),
		contentType: 'application/json',
		success: function (result) {
			var inst = $('#instructions');
			$('#ending_form').hide();
			if (result == 'Success') {
				inst.html(
					'Dank voor je deelname aan dit experiment.<br/>' +
					'Je invoer is opgeslagen. ' +
					'Je kunt het venster nu sluiten.'
				);
			} else {
				inst.html(
					'Dank voor je deelname aan dit experiment.<br/>' +
					'Door een technisch probleem is het opslaan van ' +
					'je invoer helaas niet gelukt. Zou je de inhoud ' +
					'van onderstaand kader willen kopiëren en opslaan, ' +
					'en dit als bijlage willen opsturen naar ' +
					'j.gonggrijp@uu.nl?<br/> Bij voorbaat dank!<br/>' +
					'<textarea id="errorbox"></textarea>'
				);
				$('#errorbox').width(300).height(200).val(JSON.stringify(data));
			}
			inst.show();
		}
	});
}

// Abstraction of an action taken by a test subject.
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

// Create a command object for filling a particular area in the
// drawing with a particular color.
// 
// Note of historical interest: there used to be other types of
// commands, but they became irrelevant when the user interface was
// simplified.
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

// Serialize all actions taken by the test subject (since
// `current_cmd`) into a single array, and return said array.
serialize_commands = function (current_cmd) {
	sequence = [];
	while (current_cmd) {
		sequence.push(current_cmd.json);
		current_cmd = current_cmd.next;
	}
	return sequence;
}
