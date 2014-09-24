/*
    (c) 2014 Digital Humanities Lab, Faculty of Humanities, Utrecht University
    Author: Julian Gonggrijp, j.gonggrijp@uu.nl
*/

var colors = ["#d01", "#f90", "#ee4", "#5d2", "#06e", "#717", "#953"];
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
	var lang = '="language' + count + '"';
	var level = '="level' + count + '"';
	return '<label for' + lang + '>Taal ' + count + '</label>' +
		'<input type="text" name' + lang + 'id' + lang + ' required="required"/> ' +
		'<label for' + level + '>Niveau</label>' +
		'<input type="number" name' + level + 'id' + level + ' min="1" max="10" step="1"/><br/>';
}

button = function (color) {
	return $('<span class="color_choice" style="background-color: ' +
			color +
			';" id="' +
			color.substr(1, 3) +
			'"/>').data('color', color);
}

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
	init_controls();
	create_swatches(colors);
	$.ajax({
		type: 'GET',
		url: '/static/test.json',
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
			$.ionSound({ "sounds": sounds, path: '/static/' });
		},
		error: function (xhr, status, error) {
			alert(error);
		}
	});
}

Date.prototype.toShortString = function ( ) {
    return this.toISOString().substring(0, 10);
}

// adopted from http://stackoverflow.com/questions/3761185/jquery-validate-date-range
$.validator.addMethod('daterange', function(value, element, arg) {
    if (this.optional(element)) return true;

    var startDate = Date.parse(arg[0]),
        endDate = Date.parse(arg[1]),
        enteredDate = Date.parse(value);       

    if(isNaN(enteredDate)) return false;

    return ((startDate <= enteredDate) && (enteredDate <= endDate));
}, $.validator.format("De datum moet tussen {0} en {1} liggen."))

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

insert_swatches = function (colors) {
	var swatches = $('#swatches');
	swatches.empty();
	for (index in colors) {
		swatches.append(button(colors[index]));
	}
	$(button('#fff')).appendTo(swatches);
	color_chosen = $('.color_choice').first();
	$('.color_choice').click(function (event) {
		color_chosen.css('border-color', '#fff');
		color_chosen = $(this);
		color_chosen.css('border-color', '#000');
	});
	color_chosen.click();
}

create_swatches = function (colors) {
    insert_swatches(colors);
    $('.color_choice').last().append('<img src="/static/lmproulx_eraser.png" title="Gum" alt="Gum"/>');
}

load_image = function (url, data, name) {
	$.ajax({
		type: 'GET',
		url: '/static/' + url,
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
	$('path[class~="colorable"]').click(function (event) {
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
		url: '/submit',
		'data': JSON.stringify(data),
		contentType: 'application/json',
		success: function (result) {
			var inst = $('#instructions');
			if (result == 'Success') {
			    inst.html(
			        'Dank voor je deelname aan dit experiment.<br/>' +
                    'Je invoer is opgeslagen. ' +
                    'Je kunt het venster nu sluiten.' );
			} else {
			    inst.html(
			        'Dank voor je deelname aan dit experiment.<br/>' +
			        'Door een technisch probleem is het opslaan van ' +
			        'je invoer helaas niet gelukt. Zou je de inhoud ' +
			        'van onderstaand kader willen kopiëren en opslaan, ' +
			        'en dit als bijlage willen opsturen naar ' +
			        'j.gonggrijp@uu.nl?<br/> Bij voorbaat dank!<br/>' +
			        '<textarea id="errorbox"></textarea>'
			    )
			    $('#errorbox').width(300).height(200).val(JSON.stringify(data));
			}
			inst.show();
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
