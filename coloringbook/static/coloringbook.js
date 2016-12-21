/*
	(c) 2014-2016 Digital Humanities Lab, Utrecht University
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
var first_command, last_command;
var page_onset, page, pages, pagenum, page_data, form_data, evaluation_data;
var images = {};
var image_count, images_ready, sound_count, sounds_ready;
var sentence_image_delay = 6000;  // milliseconds

// ConnectivityFsm is based directly on the example from machina-js.org.
// Most important difference is that checkHeartbeat is simply a member
// of the state machine itself.
var ConnectivityFsm = machina.Fsm.extend({
	namespace: 'connectivity',

	initialState: 'probing',
	
	requestData: {
		url: 'ping',
		method: 'HEAD',
		timeout: 5000
	},

	checkHeartbeat: function() {
		var self = this;
		self.emit('checking-heartbeat');
		$.ajax(self.requestData).done(function() {
			self.emit('heartbeat');
		}).fail(function() {
			self.emit('no-heartbeat');
		});
	},

	initialize: function() {
		var self = this;
		self.on('heartbeat', function() {
			self.handle('heartbeat');
		});
		self.on('no-heartbeat', function() {
			self.handle('no-heartbeat');
		});
		$(window).bind('online', function() {
			self.handle('window.online');
		});
		$(window).bind( 'offline', function() {
			self.handle('window.offline');
		});
		$(window.applicationCache).bind('error', function() {
			self.handle('appCache.error');
		});
		$(window.applicationCache).bind('downloading', function() {
			self.handle('appCache.downloading');
		});
		$(document).on('resume', function () {
			self.handle('device.resume');
		});
		if (self.origin) self.requestData = _.create(self.requestData, {
			url: self.origin + self.requestData.url
		});
	},

	states: {
		probing: {
			_onEnter: function() {
				this.checkHeartbeat();
			},
			'heartbeat': 'online',
			'no-heartbeat': 'disconnected',
		},
		online: {
			'window.offline': 'probing',
			'appCache.error': 'probing',
			'request.timeout': 'probing',
			'device.resume': 'probing',
		},
		disconnected: {
			'window.online': 'probing',
			'appCache.downloading': 'probing',
			'device.resume': 'probing',
		}
	}
});

// Generates the HTML code for the form fields that let the subject
// add another language (i.e. the `count`th language).
function lang_field(count) {
	var lang = '="language' + count + '"';
	var level = '="level' + count + '"';
	return '<label for' + lang + '>' + extra_language_label + ' ' + count +
		'</label>' +
		'<input type="text" name' + lang + 'id' + lang +
		' required="required"/> ' +
		'<label for' + level + '>' + extra_language_level_label + '</label>' +
		'<input type="number" name' + level + 'id' + level + ' min="1" max="10" step="1"/><br/>';
}

// Generates the HTML code for a swatch.
function button(color) {
	return $(
		'<span class="color_choice" style="background-color: ' +
		color +
		';" id="' +
		color.substr(1, 3) +
		'"/>'
	).data('color', color);
}

// All the things that need to be done after the DOM is ready.
function init_application() {
	initCycle();
	$('#starting_form input[type="submit"]').hide();
	var now = new Date(),
	    century_ago = new Date();
	century_ago.setFullYear(now.getFullYear() - 100);
	$('#starting_form').validate({
		submitHandler: handle_form,
		onkeyup: false,
		rules: {
			birth: {
				daterange: [century_ago.toShortString(), now.toShortString()],
			},
		},
	});
	$('#ending_form').validate({
		submitHandler: handle_evaluation,
		onkeyup: false,
	});
	init_controls();
	create_swatches(colors);
	
	// The part below retrieves the data about the coloring pages.
	$.ajax({
		type: 'GET',
		url: window.location.pathname,
		dataType: 'json',
	}).done(initResources).fail(function(xhr, status, error) {
		alert(error);
		console.log(xhr);
	});
}

// What needs to be done when the survey is started (again)
function initCycle() {
	pagenum = 0;
	page_data = [];
	$('#starting_form').show()[0].reset();
	$('#instructions').hide();
	$('#sentence').hide();
	$('#speaker-icon').hide();
	$('#controls').hide();
	$('#ending_form').hide()[0].reset();
	$('#success_message').hide();
	$('#failure_message').hide();
}

// Retrieve the data and report when all is done.
function initResources(resp, xmlstatus) {
	var i;
	images_ready = sounds_ready = 0;
	for (image_count = resp.images.length, i = 0; i < image_count; ++i) {
		load_image(resp.images[i]);
	}
	var sounds = [];
	for (sound_count = resp.sounds.length, i = 0; i < sound_count; ++i) {
		sounds.push({name: resp.sounds[i]});
	}
	ion.sound({
		'sounds': sounds,
		path: base + '/media/',
		preload: true,
		ready_callback: sound_done,
	});
	pages = resp.pages;
	if (resp.simultaneous) {
		simultaneous = true;
		sentence_image_delay = 0; // show image at same time as sentence
		$('#sentence').css('font-size', '24pt');
	} else {
		sentence_image_delay = resp.duration;
		$('#sentence').css('font-size', '48pt');
	}
}

// Triggered when a sound is loaded, checks whether all resources are ready.
function sound_done() {
	if (++sounds_ready == sound_count && images_ready == image_count) {
		unlock_application();
	}
}

// Called when all resources are ready.
function unlock_application() {
	$('#patience').hide();
	$('#starting_form input[type="submit"]').show();
}

// Return strings of the format YYYY-MM-DD.
Date.prototype.toShortString = function() {
	return this.toISOString().substring(0, 10);
};

// Daterange checker for jQuery.validate.
// adapted from http://stackoverflow.com/questions/3761185/jquery-validate-date-range
$.validator.addMethod('daterange', function(value, element, arg) {
	if (this.optional(element)) return true;

	var startDate = Date.parse(arg[0]),
		endDate = Date.parse(arg[1]),
		enteredDate = Date.parse(value);

	if (isNaN(enteredDate)) return false;

	return ((startDate <= enteredDate) && (enteredDate <= endDate));
}, $.validator.format("De datum moet tussen {0} en {1} liggen."));

// Put personalia form data into compact JSON format.
// Result saved globally.
function handle_form(form) {
	$(form).hide();
	$('#instructions').show();
	var raw_form = $(form).serializeArray();
	form_data = { languages: [] };
	for (var i in raw_form) {
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
function finish_instructions() {
	$('#instructions').hide();
	if (image_count > 0 && Object.keys(images).length == image_count) {
		start_page();
	} else {
		$(document).ajaxStop(start_page);
	}
}

// Add more language fields when requested.
function init_controls() {
	$('#starting_form >[name="more"]').click(function() {
		var self = $(this);
		var count = self.data('count');
		if (count) count++; else count = 1;
		self.data('count', count);
		self.before(lang_field(count));
	});
}

// Ensure that the page fills the screen exactly by scaling the SVG image.
function set_image_dimensions() {
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
function insert_swatches(colors) {
	var swatches = $('#swatches');
	swatches.empty();
	for (var index in colors) {
		swatches.append(button(colors[index]));
	}
	$(button('#fff')).appendTo(swatches);
	color_chosen = $('.color_choice').first();
	$('.color_choice').mousedown(function(event) {
		color_chosen.css('border-color', '#fff');
		color_chosen = $(this);
		color_chosen.css('border-color', '#000');
	});
	color_chosen.mousedown();
}

// Insert swatches and disguise the last (white) swatch as an eraser.
function create_swatches(colors) {
	insert_swatches(colors);
		var eraser_path = base + '/static/lmproulx_eraser.png';
	$('.color_choice').last().append('<img src="' + eraser_path + '" title="Gum" alt="Gum"/>');
}

// Retrieve an SVG image by filename and check whether resources are complete.
function load_image(name) {
	$.ajax({
		type: 'GET',
		url: base + '/media/' + name,
		dataType: 'html',
		success: function(svg_resp, xmlstatus) {
			images[name] = svg_resp;
			if (++images_ready == image_count && sounds_ready == sound_count) {
				unlock_application();
			}
		},
		error: function(xhr, status, error) {
			alert(error);
		},
	});
}

// Add click event handlers to all .colorable areas in the SVG.
function add_coloring_book_events() {
	$('path[class~="colorable"]').mousedown(function(event) {
		event.preventDefault();  // helpful on touchscreen devices
		launch_fill_command(this, color_chosen.data('color'));
		$('#undo_redo').attr('value', 'Herstel');
	});
}

// Start a new coloring page by (dis)playing the sentence and set a
// timeout for displaying the image (possibly zero).
function start_page() {
	page = pages[pagenum];
	$('#sentence').html(page.text).show();
	first_command = last_command = null;
	window.setTimeout(start_image, sentence_image_delay);
	if (page.audio) {
		ion.sound.play(page.audio);
		$('#speaker-icon').show();
		if (simultaneous) {
			$('#speaker-icon').clone().attr({id: null}).prependTo('#sentence');
		}
	}
}

// Play the sound for the current page, if available.
// Click event handler for $('#speaker-icon') and its clones.
function play_sound() {
	ion.sound.play(pages[pagenum].audio);
}

// Display the colorable image and prepare it for coloring.
// Initializes the clock for coloring actions.
function start_image() {
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
function end_page() {
	$('#speaker-icon').hide();
	$('#controls').hide();
	$('#sentence').hide();
	page_data.push(serialize_commands(first_command));
	if (++pagenum < pages.length) {
		start_page();
	} else {
		$('#ending_form').show();
	}
}

// Serialize the evaluation form data and trigger uploading of all data.
function handle_evaluation(form) {
	var raw_data = $(form).serializeArray();
	evaluation_data = {};
	for (var l = raw_data.length, i = 0; i < l; ++i) {
		evaluation_data[raw_data[i].name] = raw_data[i].value;
	}
	send_data();
}

// Upload all data and handle possible failure.
function send_data() {
	var data = JSON.stringify({
		survey: window.location.href,
		subject: form_data,
		results: page_data,
		evaluation: evaluation_data,
	});
	$.ajax({
		type: 'POST',
		url: window.location.pathname + '/submit',
		'data': data,
		contentType: 'application/json',
		success: function(result) {
			$('#ending_form').hide();
			if (result == 'Success') {
				$('#success_message').show();
			} else {
				$('#failure_message').show();
				$('#errorbox').val(data).focus().select();
			}
		}
	});
}

// Abstraction of an action taken by a test subject.
function command(previous) {
	if (previous) {
		this.prev = previous;
		previous.next = this;
	} else {
		first_command = this;
	}
	this.json = { };
	this.toggle = function() { this.json.time = $.now() - page_onset; };
	this.do = function() { };
}

// Create a command object for filling a particular area in the
// drawing with a particular color.
// 
// Note of historical interest: there used to be other types of
// commands, but they became irrelevant when the user interface was
// simplified.
function launch_fill_command(target, value) {
	var cmd = new command(last_command);
	cmd.target = target;
	cmd.color = value;
	cmd.prior = $(target).attr('fill');
	cmd.do = function() {
		this.toggle();
		$(cmd.target).attr('fill', this.color);
	};
	cmd.json.action = 'fill';
	cmd.json.target = target.id;
	cmd.json.color = value;
	cmd.do();
	last_command = cmd;
}

// Serialize all actions taken by the test subject (since
// `current_cmd`) into a single array, and return said array.
function serialize_commands(current_cmd) {
	var sequence = [];
	while (current_cmd) {
		sequence.push(current_cmd.json);
		current_cmd = current_cmd.next;
	}
	return sequence;
}
